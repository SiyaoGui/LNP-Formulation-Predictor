"""特征计算：SMILES -> 描述符 / 指纹，以及制剂侧和工艺侧特征。

特征分块与协议 docs/evaluation-protocol.md 第七节一一对应：
  M-desc  payload 分子描述符（12 个）
  M-fp    payload Morgan 指纹
  F-comp  制剂组成（三类脂质占比）
  F-lipid 脂质结构特征（描述符 + 指纹）与组成结构标记
  P       工艺特征

设计约束（都写在协议里，这里只是实现）：
- 不做任何需要全体数据的变换（标准化、填充、特征选择全部留到交叉验证的训练折内做）
- 缺失值保留为 NaN，不默默填 0；只有在「该组分确实不存在」时才填 0，并另给 has_* 标记
- 不使用脂质名字的 one-hot：本子集 30 个 helper 名字里很多只出现一两次，
  等于论文身份的代理变量（协议 7.2 节）。改用结构描述符 + 化学含义明确的派生标记
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import Descriptors
from rdkit.Chem import rdFingerprintGenerator

RDLogger.DisableLog("rdApp.*")

# M2 合并脚本里多组分脂质 SMILES 的分隔符
MULTI_SMILES_SEP = " |&| "

# 天然来源混合物：没有单一结构式，不是数据缺失（PMC_IVR_lipid_component_smiles.csv 里
# smiles_status = mixture_no_single_smiles 的那批）
NATURAL_MIXTURE_LIPIDS = frozenset({"HSPC", "Soy PC", "EPC", "asolectin", "Egg SM"})

# M-desc：12 个 RDKit 描述符。物理含义写在 docs/feature-engineering.md 里。
DESCRIPTORS: tuple[tuple[str, callable], ...] = (
    ("mol_wt", Descriptors.MolWt),
    ("logp", Descriptors.MolLogP),
    ("tpsa", Descriptors.TPSA),
    ("hbd", Descriptors.NumHDonors),
    ("hba", Descriptors.NumHAcceptors),
    ("rot_bonds", Descriptors.NumRotatableBonds),
    ("ring_count", Descriptors.RingCount),
    ("aromatic_rings", Descriptors.NumAromaticRings),
    ("fraction_csp3", Descriptors.FractionCSP3),
    ("heavy_atoms", Descriptors.HeavyAtomCount),
    ("mol_mr", Descriptors.MolMR),
    ("balaban_j", Descriptors.BalabanJ),
)

DESCRIPTOR_NAMES = tuple(name for name, _ in DESCRIPTORS)


def _split_multi(smiles: str) -> list[str]:
    return [p.strip() for p in smiles.split(MULTI_SMILES_SEP) if p.strip()]


def _mols(smiles: str | float) -> list[Chem.Mol]:
    if not isinstance(smiles, str) or not smiles.strip():
        return []
    out = []
    for part in _split_multi(smiles):
        mol = Chem.MolFromSmiles(part)
        if mol is not None:
            out.append(mol)
    return out


def descriptor_row(smiles: str | float) -> dict[str, float]:
    """多组分时各描述符取算术均值（沿用 M3 的做法）。无结构时全部为 NaN。"""
    mols = _mols(smiles)
    if not mols:
        return {name: np.nan for name in DESCRIPTOR_NAMES}
    vals = {name: [] for name in DESCRIPTOR_NAMES}
    for mol in mols:
        for name, fn in DESCRIPTORS:
            try:
                vals[name].append(float(fn(mol)))
            except Exception:
                vals[name].append(np.nan)
    return {name: float(np.nanmean(v)) if len(v) else np.nan for name, v in vals.items()}


def fingerprint_row(smiles: str | float, radius: int, n_bits: int) -> np.ndarray | None:
    """Morgan 指纹。多组分时按位 OR（表示「这个角色里包含哪些结构特征」，不是加和）。"""
    mols = _mols(smiles)
    if not mols:
        return None
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)
    acc = np.zeros(n_bits, dtype=np.uint8)
    for mol in mols:
        arr = np.zeros(n_bits, dtype=np.uint8)
        DataStructs.ConvertToNumpyArray(gen.GetFingerprint(mol), arr)
        acc |= arr
    return acc


def fingerprint_block(
    smiles_series: pd.Series, prefix: str, radius: int, n_bits: int
) -> pd.DataFrame:
    """指纹矩阵。无结构的行整行为 NaN（不是 0，否则「没结构」会被当成「所有位都是 0」）。"""
    cols = [f"{prefix}_fp_{i}" for i in range(n_bits)]
    data = np.full((len(smiles_series), n_bits), np.nan, dtype=np.float32)
    for i, smiles in enumerate(smiles_series):
        fp = fingerprint_row(smiles, radius, n_bits)
        if fp is not None:
            data[i] = fp
    return pd.DataFrame(data, columns=cols, index=smiles_series.index)


def descriptor_block(smiles_series: pd.Series, prefix: str) -> pd.DataFrame:
    rows = [descriptor_row(s) for s in smiles_series]
    out = pd.DataFrame(rows, index=smiles_series.index)
    out.columns = [f"{prefix}_{c}" for c in out.columns]
    return out


def tanimoto_matrix(smiles_a: list[str], smiles_b: list[str], radius: int, n_bits: int) -> np.ndarray:
    """给 B1 相似性基线用的 Tanimoto 相似度矩阵。无结构的位置为 NaN。"""
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)

    def fps(smis):
        out = []
        for s in smis:
            mols = _mols(s)
            out.append(gen.GetFingerprint(mols[0]) if mols else None)
        return out

    fa, fb = fps(smiles_a), fps(smiles_b)
    m = np.full((len(fa), len(fb)), np.nan)
    for i, a in enumerate(fa):
        if a is None:
            continue
        for j, b in enumerate(fb):
            if b is None:
                continue
            m[i, j] = DataStructs.TanimotoSimilarity(a, b)
    return m


# --------------------------------------------------------------------------- #
# 制剂侧
# --------------------------------------------------------------------------- #

PCT_COLS = ("helper_lipid_pct", "sterol_lipid_pct", "peg_lipid_pct")
ROLES = ("helper", "sterol", "peg")


def composition_block(df: pd.DataFrame) -> pd.DataFrame:
    """F-comp：三类脂质占比 + 「这类组分在不在」的标记。

    关键处理（协议 1.4 节的修正）：占比列的 NaN 在这份数据里表示「该配方不含这类
    组分」，不是缺失值。判据是 `*_lipid_name` 与 `*_lipid_pct` 几乎完全同时存在同时
    缺失，且把 NaN 当 0 填回后每行三组分加总精确等于 100.000。

    所以：
      name 缺 + pct 缺  -> 该组分不存在，pct 填 0，has_* = 0
      name 有 + pct 缺  -> 真缺失（本子集 4 行），pct 保留 NaN，has_* = 1，
                           并由 *_pct_is_missing 标记，之后在训练折内填充
      name 有 + pct 有  -> 正常，has_* = 1
    """
    out = pd.DataFrame(index=df.index)
    for role in ROLES:
        name_col, pct_col = f"{role}_lipid_name", f"{role}_lipid_pct"
        has = df[name_col].notna()
        pct = df[pct_col].astype(float)
        truly_missing = has & pct.isna()
        out[f"has_{role}_lipid"] = has.astype(float)
        out[f"{role}_lipid_pct"] = pct.where(has, 0.0)
        out[f"{role}_lipid_pct_is_missing"] = truly_missing.astype(float)
    out["n_lipid_classes"] = out[[f"has_{r}_lipid" for r in ROLES]].sum(axis=1)
    return out


def lipid_structure_block(df: pd.DataFrame, radius: int, n_bits: int) -> pd.DataFrame:
    """F-lipid：三个脂质角色各自的描述符 + 指纹，加上化学含义明确的派生标记。

    派生标记为什么这么选（协议 7.2 节禁止用脂质名字 one-hot，因为 30 个名字里很多
    只出现一两次，等于论文身份的代理变量）：
      n_*_components        该角色由几个组分构成（单一脂质 vs 混合脂质，化学含义明确）
      *_is_natural_mixture  是不是天然来源混合物（这类没有单一结构式，缺结构是真实情况）
      peg_mw_da             PEG 链长（2000 / 5000 / 10000），从名字里解析。PEG 脂质
                            在原始表里 SMILES 覆盖率为 0%，链长是唯一可用且确有物理
                            含义的信息，比给一个编造的近似结构更诚实
    """
    blocks = [
        descriptor_block(df["helper_lipid_smiles"], "helper"),
        descriptor_block(df["sterol_lipid_smiles"], "sterol"),
        fingerprint_block(df["helper_lipid_smiles"], "helper", radius, n_bits),
        fingerprint_block(df["sterol_lipid_smiles"], "sterol", radius, n_bits),
    ]
    extra = pd.DataFrame(index=df.index)
    for role in ROLES:
        names = df[f"{role}_lipid_name"]
        n_comp = names.map(lambda v: float(len(str(v).split("+"))) if pd.notna(v) else np.nan)
        extra[f"n_{role}_components"] = n_comp
        extra[f"{role}_is_natural_mixture"] = names.map(
            lambda v: float(
                any(part.strip() in NATURAL_MIXTURE_LIPIDS for part in str(v).split("+"))
            )
            if pd.notna(v)
            else np.nan
        )
    extra["peg_mw_da"] = df["peg_lipid_name"].map(_parse_peg_mw)
    blocks.append(extra)
    return pd.concat(blocks, axis=1)


def _parse_peg_mw(name: str | float) -> float:
    """从 PEG 脂质名字解析 PEG 链的分子量。

    本子集只有 4 个取值：mPEG2000-DSPE-2k / mPEG2000-DSPE-LMWP / mPEG-DSPE-5K /
    mPEG-DSPE-10K。规则简单且显式，不做模糊匹配，无法解析时返回 NaN 而不是猜。
    """
    if not isinstance(name, str):
        return np.nan
    low = name.lower()
    if "10k" in low:
        return 10000.0
    if "5k" in low:
        return 5000.0
    if "2000" in low or "2k" in low:
        return 2000.0
    return np.nan


# --------------------------------------------------------------------------- #
# 工艺侧
# --------------------------------------------------------------------------- #

PREP_METHOD_MIN_COUNT = 5  # 出现次数低于这个值的制备方法归入 other，避免变成论文标识


def process_block(df: pd.DataFrame, prep_method_min_count: int = PREP_METHOD_MIN_COUNT) -> pd.DataFrame:
    """P：制备方法 one-hot + 工艺温度。

    制备方法有 16 类而分析单元只有几十个，出现一两次的类别等于论文标识，
    所以把低频类别合并成 other，阈值写进 config 可审计。
    缺失作为单独一类 missing，不丢样本（协议 7.3 节）。
    """
    out = pd.DataFrame(index=df.index)
    out["process_temp_c"] = df["process_temp_c_std"].astype(float)
    out["process_temp_c_is_missing"] = df["process_temp_c_std"].isna().astype(float)

    prep = df["prep_method_std"].fillna("missing").astype(str)
    counts = prep.value_counts()
    keep = set(counts[counts >= prep_method_min_count].index)
    prep_grouped = prep.map(lambda v: v if v in keep else "other")
    dummies = pd.get_dummies(prep_grouped, prefix="prep", dtype=float)
    return pd.concat([out, dummies], axis=1)
