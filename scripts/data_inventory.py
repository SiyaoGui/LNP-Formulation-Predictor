"""数据盘点脚本：统计 merged_formulations_v2.csv 的小分子子集规模、目标变量完整度、
分子量阈值划分、唯一化合物与骨架数、泄漏嫌疑字段。

用法: python3 scripts/data_inventory.py
输出: docs/data_inventory_stats.json（机器可读）+ stdout 可读报告
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "merged_formulations_v2.csv"
OUT_JSON = ROOT / "docs" / "data_inventory_stats.json"

# 大分子 payload 的取值（核酸/蛋白），用于 large_molecule 子集定义
LARGE_PAYLOADS = {"mRNA", "siRNA", "DNA", "ASO", "protein", "mRNA, siRNA"}
NON_DRUG_PAYLOADS = {"empty", "gold_nanoparticles"}

TARGETS = [
    "particle_size_nm",
    "pdi",
    "zeta_potential_mv",
    "encapsulation_efficiency_pct",
]
COMP_COLS = ["ionizable_lipid_pct", "helper_lipid_pct", "sterol_lipid_pct", "peg_lipid_pct"]


def parse_notes(series, field):
    return series.str.extract(field + r"=([^;]*)")[0].str.strip()


def mol_props(smiles):
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        return None
    scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=m, includeChirality=False)
    return {
        "mol_wt": Descriptors.MolWt(m),
        "heavy_atoms": m.GetNumHeavyAtoms(),
        "logp": Descriptors.MolLogP(m),
        "tpsa": Descriptors.TPSA(m),
        "hbd": Descriptors.NumHDonors(m),
        "hba": Descriptors.NumHAcceptors(m),
        "rot_bonds": Descriptors.NumRotatableBonds(m),
        "rings": Descriptors.RingCount(m),
        "scaffold": scaffold,
    }


def main():
    if not SRC.exists():
        sys.exit(f"找不到数据文件: {SRC}")
    df = pd.read_csv(SRC)
    stats = {"source_file": SRC.name, "n_rows_total": int(len(df))}

    stats["rows_by_source"] = df.source_dataset.value_counts().to_dict()
    stats["rows_by_payload_type"] = df.payload_type.value_counts().to_dict()

    # 子集划分：小分子 = payload 有 SMILES 且不是核酸/蛋白/空载/无机
    is_large = df.payload_type.isin(LARGE_PAYLOADS)
    is_nondrug = df.payload_type.isin(NON_DRUG_PAYLOADS)
    is_small = df.payload_smiles.notna() & ~is_large & ~is_nondrug
    stats["subset_sizes"] = {
        "small_molecule": int(is_small.sum()),
        "large_molecule": int(is_large.sum()),
        "empty_or_nondrug": int(is_nondrug.sum()),
        "unassigned": int((~is_small & ~is_large & ~is_nondrug).sum()),
    }
    stats["small_molecule_sources"] = df.loc[is_small, "source_dataset"].value_counts().to_dict()
    stats["large_molecule_sources"] = df.loc[is_large, "source_dataset"].value_counts().to_dict()

    sm = df[is_small].copy()
    sm["structure_type"] = parse_notes(sm.process_notes, "structure_type")
    sm["media_ph"] = parse_notes(sm.process_notes, "media_pH")
    sm["release_method"] = parse_notes(sm.process_notes, "release_method")

    # 每个唯一化合物的分子性质
    rows = []
    for smi, grp in sm.groupby("payload_smiles"):
        p = mol_props(smi)
        rec = {
            "payload_type": grp.payload_type.iloc[0],
            "smiles": smi,
            "n_records": int(len(grp)),
            "n_papers": int(grp.paper_doi.nunique()),
            "n_with_size": int(grp.particle_size_nm.notna().sum()),
            "n_with_pdi": int(grp.pdi.notna().sum()),
            "n_with_zeta": int(grp.zeta_potential_mv.notna().sum()),
            "n_with_full_composition": int(
                grp[["helper_lipid_pct", "sterol_lipid_pct", "peg_lipid_pct"]].notna().all(axis=1).sum()
            ),
            "smiles_parsed": p is not None,
        }
        if p:
            rec.update({k: (round(v, 2) if isinstance(v, float) else v) for k, v in p.items()})
        rows.append(rec)
    comp = pd.DataFrame(rows).sort_values("n_records", ascending=False)
    stats["n_unique_compounds"] = int(len(comp))
    stats["n_unique_scaffolds"] = int(comp.scaffold.nunique())
    stats["smiles_parse_failures"] = int((~comp.smiles_parsed).sum())
    stats["compounds"] = comp.to_dict(orient="records")

    # 分子量阈值
    thresholds = [500, 700, 800, 900, 1000, 1200, 1500]
    stats["mw_thresholds"] = {}
    for t in thresholds:
        keep = comp[comp.mol_wt <= t]
        n_rec = int(keep.n_records.sum())
        stats["mw_thresholds"][str(t)] = {
            "n_compounds": int(len(keep)),
            "n_records": n_rec,
            "excluded_compounds": sorted(comp.loc[comp.mol_wt > t, "payload_type"].tolist()),
        }

    # 目标变量完整度（小分子子集内）
    tgt = {}
    for c in TARGETS + COMP_COLS:
        col = sm[c]
        tgt[c] = {
            "n_nonnull": int(col.notna().sum()),
            "pct_nonnull": round(float(col.notna().mean() * 100), 1),
            "n_compounds_with_value": int(sm.loc[col.notna(), "payload_smiles"].nunique()),
            "n_papers_with_value": int(sm.loc[col.notna(), "paper_doi"].nunique()),
        }
        if col.notna().any() and pd.api.types.is_numeric_dtype(col):
            q = col.dropna()
            tgt[c].update(
                {
                    "min": round(float(q.min()), 3),
                    "p25": round(float(q.quantile(0.25)), 3),
                    "median": round(float(q.median()), 3),
                    "p75": round(float(q.quantile(0.75)), 3),
                    "max": round(float(q.max()), 3),
                }
            )
    stats["targets_small_molecule"] = tgt

    # 成分数据：三组分齐全的行
    full_mask = sm[["helper_lipid_pct", "sterol_lipid_pct", "peg_lipid_pct"]].notna().all(axis=1)
    sm_full = sm[full_mask]
    stats["full_composition"] = {
        "n_records": int(full_mask.sum()),
        "n_compounds": int(sm_full.payload_smiles.nunique()),
        "n_papers": int(sm_full.paper_doi.nunique()),
        "by_compound": sm_full.payload_type.value_counts().to_dict(),
        "sum_min": round(float(sm_full[["helper_lipid_pct", "sterol_lipid_pct", "peg_lipid_pct"]].sum(axis=1).min()), 3),
        "sum_max": round(float(sm_full[["helper_lipid_pct", "sterol_lipid_pct", "peg_lipid_pct"]].sum(axis=1).max()), 3),
    }
    presence_pattern = (
        sm[["helper_lipid_pct", "sterol_lipid_pct", "peg_lipid_pct"]]
        .notna()
        .apply(lambda r: "".join("1" if x else "0" for x in r), axis=1)
    )
    stats["composition_presence_patterns"] = presence_pattern.value_counts().to_dict()

    # 重复度：同一化合物+同一配方算一个唯一配方
    def joinkey(frame, cols):
        return frame[cols].apply(lambda c: c.map(lambda x: "NA" if pd.isna(x) else str(x))).agg("|".join, axis=1)

    k_comp = ["payload_smiles", "helper_lipid_name", "helper_lipid_pct", "sterol_lipid_pct", "peg_lipid_pct"]
    stats["dedup"] = {
        "n_records": int(len(sm)),
        "n_unique_compound_plus_composition": int(joinkey(sm, k_comp).nunique()),
        "n_unique_plus_paper": int(joinkey(sm, k_comp + ["paper_doi"]).nunique()),
        "n_unique_plus_paper_and_conditions": int(joinkey(sm, k_comp + ["paper_doi", "process_notes"]).nunique()),
        "n_papers": int(sm.paper_doi.nunique()),
    }

    # 工艺/实验条件字段
    proc = {}
    for c in [
        "prep_method_std",
        "device_or_chip_std",
        "flow_ratio_imbalance",
        "total_flow_rate_ml_min_std",
        "process_temp_c_std",
        "measurement_instrument_std",
    ]:
        proc[c] = {
            "n_nonnull": int(sm[c].notna().sum()),
            "n_unique": int(sm[c].nunique()),
            "top": {str(k): int(v) for k, v in sm[c].value_counts().head(5).items()},
        }
    for c in ["structure_type", "media_ph", "release_method"]:
        proc[c] = {
            "n_nonnull": int(sm[c].notna().sum()),
            "n_unique": int(sm[c].nunique()),
            "top": {str(k): int(v) for k, v in sm[c].value_counts().head(6).items()},
        }
    stats["process_features_small_molecule"] = proc

    # 泄漏嫌疑：structure_type 与粒径的关系
    st = sm.dropna(subset=["particle_size_nm"]).groupby("structure_type").particle_size_nm.agg(
        ["count", "median", "min", "max"]
    )
    stats["leakage_check_structure_type_vs_size"] = {
        k: {kk: (round(float(vv), 2) if isinstance(vv, (int, float, np.floating)) else vv) for kk, vv in v.items()}
        for k, v in st.to_dict(orient="index").items()
    }
    stats["size_gt_1000nm_rows"] = int((sm.particle_size_nm > 1000).sum())
    stats["size_excl_multilamellar"] = {
        "n": int(sm.loc[~sm.structure_type.isin(["MLV", "LMVV"]), "particle_size_nm"].notna().sum()),
        "median": round(float(sm.loc[~sm.structure_type.isin(["MLV", "LMVV"]), "particle_size_nm"].median()), 2),
        "max": round(float(sm.loc[~sm.structure_type.isin(["MLV", "LMVV"]), "particle_size_nm"].max()), 2),
    }

    # 脂质侧字段
    lip = {}
    for c in ["helper_lipid_name", "sterol_lipid_name", "peg_lipid_name", "ionizable_lipid_name"]:
        lip[c] = {
            "n_nonnull": int(sm[c].notna().sum()),
            "n_unique": int(sm[c].nunique()),
            "n_multi_component": int(sm[c].dropna().str.contains(r"\+").sum()),
            "top": {str(k): int(v) for k, v in sm[c].value_counts().head(5).items()},
        }
    for c in ["helper_lipid_smiles", "sterol_lipid_smiles", "peg_lipid_smiles"]:
        lip[c] = {"n_nonnull": int(sm[c].notna().sum()), "pct": round(float(sm[c].notna().mean() * 100), 1)}
    stats["lipid_fields_small_molecule"] = lip

    stats["release_curve_files_referenced"] = int(sm.release_curve_file.notna().sum())
    stats["release_curve_files_present_in_repo"] = int(
        sum((ROOT / str(f)).exists() for f in sm.release_curve_file.dropna().unique())
    )

    stats["versions"] = {
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "rdkit": __import__("rdkit").__version__,
        "python": sys.version.split()[0],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    # stdout 可读摘要
    print(f"总记录 {stats['n_rows_total']}  小分子 {stats['subset_sizes']['small_molecule']}"
          f"  大分子 {stats['subset_sizes']['large_molecule']}  空载/非药 {stats['subset_sizes']['empty_or_nondrug']}"
          f"  未归类 {stats['subset_sizes']['unassigned']}")
    print(f"小分子唯一化合物 {stats['n_unique_compounds']}  唯一Murcko骨架 {stats['n_unique_scaffolds']}"
          f"  论文 {stats['dedup']['n_papers']}  唯一(化合物+配方) {stats['dedup']['n_unique_compound_plus_composition']}")
    print("\n分子量阈值:")
    for t, v in stats["mw_thresholds"].items():
        print(f"  <= {t:>4s} Da : {v['n_compounds']:2d} 化合物 / {v['n_records']:3d} 条  排除: {', '.join(v['excluded_compounds']) or '无'}")
    print("\n目标变量（小分子子集内）:")
    for c, v in stats["targets_small_molecule"].items():
        print(f"  {c:30s} n={v['n_nonnull']:3d} ({v['pct_nonnull']:5.1f}%)  化合物={v['n_compounds_with_value']:2d}  论文={v['n_papers_with_value']:2d}")
    print(f"\n三组分齐全: {stats['full_composition']['n_records']} 条 / {stats['full_composition']['n_compounds']} 化合物 / {stats['full_composition']['n_papers']} 论文")
    print(f"释放曲线文件引用 {stats['release_curve_files_referenced']} 个, 仓库里实际存在 {stats['release_curve_files_present_in_repo']} 个")
    print(f"\n写出: {OUT_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
