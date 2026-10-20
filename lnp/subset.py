"""子集选择：small_molecule / large_molecule / all。

换子集只需要改配置里的 subset.name，不用改任何流程代码（任务第 9 节要求）。
子集定义与 docs/data-inventory.md 第二节一致。
"""

from __future__ import annotations

import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")

# 大分子 payload：核酸与蛋白
LARGE_PAYLOADS = frozenset({"mRNA", "siRNA", "DNA", "ASO", "protein", "mRNA, siRNA"})

# 空载与无机颗粒：既不是小分子也不是大分子
NON_DRUG_PAYLOADS = frozenset({"empty", "gold_nanoparticles"})

# 荧光示踪剂/探针类分子。用户 2026-10-19 确认保留在小分子子集里，
# 但打标记，只用于误差分析，不作为特征（协议 7.2 节）。
PROBE_PAYLOADS = frozenset({"rhodamine b", "sulforhodamine B", "carboxyfluorescein", "calcein"})

SUBSET_NAMES = ("small_molecule", "large_molecule", "all")


def _payload_mw(smiles: str | float) -> float | None:
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    mol = Chem.MolFromSmiles(smiles)
    return None if mol is None else Descriptors.MolWt(mol)


def _payload_scaffold(smiles: str | float) -> str | None:
    """Murcko 骨架，给协议 S2 骨架划分用。无环分子返回空字符串，无结构返回 None。"""
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False)


def annotate(df: pd.DataFrame) -> pd.DataFrame:
    """加上子集判断需要的派生列，不做过滤。"""
    out = df.copy()
    out["payload_mw"] = [_payload_mw(s) for s in out["payload_smiles"]]
    out["payload_scaffold"] = [_payload_scaffold(s) for s in out["payload_smiles"]]
    out["is_probe"] = out["payload_type"].isin(PROBE_PAYLOADS)
    out["payload_is_large"] = out["payload_type"].isin(LARGE_PAYLOADS)
    out["payload_is_nondrug"] = out["payload_type"].isin(NON_DRUG_PAYLOADS)
    out["payload_has_structure"] = out["payload_smiles"].notna() & out["payload_mw"].notna()
    return out


def select(
    df: pd.DataFrame,
    name: str = "small_molecule",
    max_payload_mw: float | None = 900.0,
    keep_probe_molecules: bool = True,
) -> pd.DataFrame:
    """按子集名过滤。

    small_molecule: payload 有可解析结构、不是核酸/蛋白、不是空载/无机，可选 MW 上限
    large_molecule: payload 是核酸或蛋白（这些 payload 没有 SMILES，MW 上限不适用）
    all:            不过滤
    """
    if name not in SUBSET_NAMES:
        raise ValueError(f"subset.name 必须是 {SUBSET_NAMES} 之一，收到 {name!r}")

    d = annotate(df)

    if name == "all":
        return d

    if name == "large_molecule":
        return d[d["payload_is_large"]].copy()

    mask = d["payload_has_structure"] & ~d["payload_is_large"] & ~d["payload_is_nondrug"]
    if max_payload_mw is not None:
        mask &= d["payload_mw"] <= max_payload_mw
    if not keep_probe_molecules:
        mask &= ~d["is_probe"]
    return d[mask].copy()


def payload_group_key(df: pd.DataFrame) -> pd.Series:
    """交叉验证的分组键。

    小分子：payload 的 InChIKey（避免同一化合物两种 SMILES 写法被当成两个分组）。
    大分子：payload 没有结构，退化为 payload_type（协议 11.2 节已说明这个退化，
    以及大分子侧要额外按可离子化脂质和论文分组）。
    """
    keys = []
    for smiles, ptype in zip(df["payload_smiles"], df["payload_type"]):
        if isinstance(smiles, str) and smiles.strip():
            mol = Chem.MolFromSmiles(smiles)
            if mol is not None:
                keys.append(Chem.MolToInchiKey(mol))
                continue
        keys.append(f"TYPE:{ptype}")
    return pd.Series(keys, index=df.index, name="group_compound")


def _first_component(smiles: str | float) -> str | None:
    """多组分 SMILES 取第一个组分（分隔符见 features.MULTI_SMILES_SEP）。"""
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    first = smiles.split(" |&| ")[0].strip()
    return first or None


def structure_keys(smiles_series: pd.Series) -> pd.DataFrame:
    """给任意一列 SMILES 算 InChIKey 和 Murcko 骨架，用作交叉验证的分组键。

    包封率验证里分组键是可离子化脂质而不是 payload（协议 docs/ee-feasibility-protocol.md
    第三节说明了为什么）。
    """
    iks, scafs = [], []
    for s in smiles_series:
        f = _first_component(s)
        mol = Chem.MolFromSmiles(f) if f else None
        if mol is None:
            iks.append(None)
            scafs.append(None)
            continue
        iks.append(Chem.MolToInchiKey(mol))
        scafs.append(MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False))
    return pd.DataFrame({"inchikey": iks, "scaffold": scafs}, index=smiles_series.index)
