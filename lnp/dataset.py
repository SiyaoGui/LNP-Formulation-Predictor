"""分析单元构建：从原始行去重成「唯一配方实验」，并定义 T1 / T2 / T3 的目标。

去重规则来自协议 docs/evaluation-protocol.md 第 1.1 节：
  一个分析单元 = 一个唯一配方实验，不是一行记录。
  原始数据里一行等于一条体外释放曲线实验，同一配方在不同释放介质/方法下出现多行，
  而粒径是配方的固有属性，按行评估会让有效样本量虚高三倍。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import features as F
from .subset import payload_group_key

# 协议 1.1 节写死的去重键
T1_DEDUP_KEY = (
    "payload_smiles",
    "helper_lipid_name",
    "helper_lipid_pct",
    "sterol_lipid_pct",
    "peg_lipid_pct",
    "paper_doi",
    "prep_method_std",
)
T2_DEDUP_KEY = (
    "payload_smiles",
    "helper_lipid_pct",
    "sterol_lipid_pct",
    "peg_lipid_pct",
    "paper_doi",
)

# 溯源列：带进分析单元表便于审计和误差分析，但不是特征
PROVENANCE_COLS = (
    "payload_type",
    "payload_smiles",
    "payload_mw",
    "is_probe",
    "paper_doi",
    "helper_lipid_name",
    "sterol_lipid_name",
    "peg_lipid_name",
    "source_dataset",
)

MAX_PARTICLE_SIZE_NM = 1000.0  # 协议 1.2 节写死，排除 MLV/LMVV 多层囊泡

PATTERN_LABELS = {
    "100": "helper_only",
    "110": "helper_sterol",
    "101": "helper_peg",
    "111": "helper_sterol_peg",
}


def _join_key(df: pd.DataFrame, cols) -> pd.Series:
    return (
        df[list(cols)]
        .apply(lambda c: c.map(lambda v: "NA" if pd.isna(v) else str(v)))
        .agg("|".join, axis=1)
    )


def _presence_pattern(df: pd.DataFrame) -> pd.Series:
    name_cols = [f"{r}_lipid_name" for r in F.ROLES]
    return df[name_cols].notna().apply(lambda r: "".join("1" if x else "0" for x in r), axis=1)


def _collapse(df: pd.DataFrame, key: pd.Series, target_col: str | None, how: str) -> pd.DataFrame:
    """把同一键的多行折叠成一个分析单元。

    目标值按 how 聚合（T1 用 median，避免个别离群测量主导）；特征来源列取组内第一个
    非空值，并记录组内行数与目标值的组内离散程度，便于审计。
    """
    out_rows = []
    for _, grp in df.assign(_key=key.values).groupby("_key", sort=False):
        row = grp.iloc[0].copy()
        if target_col is not None:
            vals = grp[target_col].dropna().astype(float)
            row[target_col] = float(getattr(np, how)(vals)) if len(vals) else np.nan
            row["_target_n_rows"] = int(len(vals))
            row["_target_spread"] = float(vals.max() - vals.min()) if len(vals) > 1 else 0.0
        row["_n_source_rows"] = int(len(grp))
        row["_source_row_ids"] = ";".join(str(v) for v in grp["source_row_id"].tolist())
        out_rows.append(row)
    out = pd.DataFrame(out_rows).drop(columns=["_key"], errors="ignore")
    return out.reset_index(drop=True)


def t1_units(df: pd.DataFrame, dedup: bool = True) -> pd.DataFrame:
    """T1 粒径回归的分析单元。目标 log10(particle_size_nm)。"""
    d = df[
        df["particle_size_nm"].notna()
        & (df["particle_size_nm"] <= MAX_PARTICLE_SIZE_NM)
        & (df["formation_ok"].fillna(1) != 0)
    ].copy()
    if dedup:
        d = _collapse(d, _join_key(d, T1_DEDUP_KEY), "particle_size_nm", "median")
    d["target"] = np.log10(d["particle_size_nm"].astype(float))
    d["group_compound"] = payload_group_key(d).values
    d["task"] = "t1"
    return d.reset_index(drop=True)


def t2_units(df: pd.DataFrame, dedup: bool = True) -> pd.DataFrame:
    """T2 脂质组成回归的分析单元。只保留三组分齐全的配方（协议 1.3 节）。"""
    d = df[df[list(F.PCT_COLS)].notna().all(axis=1)].copy()
    if dedup:
        d = _collapse(d, _join_key(d, T2_DEDUP_KEY), None, "median")
    for col in F.PCT_COLS:
        d[f"target_{col}"] = d[col].astype(float)
    d["group_compound"] = payload_group_key(d).values
    d["task"] = "t2"
    return d.reset_index(drop=True)


def t3_units(df: pd.DataFrame, dedup: bool = True) -> pd.DataFrame:
    """T3 脂质类别组合分类的分析单元（协议 1.4 节）。

    保留至少有一类脂质占比数据的配方；类别标签来自 helper/sterol/peg 三个名字列的
    有无组合。三列全空的真缺失行（IVR_formulation_41 / 49）被排除。
    """
    d = df[df[list(F.PCT_COLS)].notna().any(axis=1)].copy()
    if dedup:
        d = _collapse(d, _join_key(d, T2_DEDUP_KEY), None, "median")
    pattern = _presence_pattern(d)
    d["target_pattern"] = pattern.values
    d["target"] = pattern.map(PATTERN_LABELS).values
    d = d[d["target"].notna()].copy()
    d["group_compound"] = payload_group_key(d).values
    d["task"] = "t3"
    return d.reset_index(drop=True)


BUILDERS = {"t1": t1_units, "t2": t2_units, "t3": t3_units}
