"""从 SMILES 到特征矩阵，一条命令跑通。

用法:
    python3 scripts/build_features.py --config configs/smallmol_baseline.yaml

产出（写进 config 的 data.out_dir）:
    units_<task>.parquet      分析单元表（目标 + 溯源列 + 分组键）
    features_<task>.parquet   特征矩阵（与 units 行一一对应、同序）
    feature_manifest.json     每个特征分块的列清单、版本号、禁止字段断言结果

设计约束（协议第七节）：
- 不做任何需要全体数据的变换。标准化、缺失值填充、指纹筛选全部留到交叉验证的训练折内
- 缺失值保留 NaN，不默默填 0
- 产出的特征矩阵会被逐列断言不含协议 7.2 节的禁止字段
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lnp import dataset as D  # noqa: E402
from lnp import features as F  # noqa: E402
from lnp import subset as S  # noqa: E402


def build_blocks(units: pd.DataFrame, cfg: dict, blocks: list[str]) -> tuple[pd.DataFrame, dict]:
    fp_cfg = cfg["features"]
    made: dict[str, pd.DataFrame] = {}

    if "m_desc" in blocks:
        made["m_desc"] = F.descriptor_block(units["payload_smiles"], "payload")
    if "m_fp" in blocks:
        made["m_fp"] = F.fingerprint_block(
            units["payload_smiles"],
            "payload",
            fp_cfg["payload_fp"]["radius"],
            fp_cfg["payload_fp"]["n_bits"],
        )
    if "f_comp" in blocks:
        made["f_comp"] = F.composition_block(units)
    if "f_lipid" in blocks:
        made["f_lipid"] = F.lipid_structure_block(
            units, fp_cfg["lipid_fp"]["radius"], fp_cfg["lipid_fp"]["n_bits"]
        )
    if "p" in blocks:
        made["p"] = F.process_block(units, fp_cfg["prep_method_min_count"])

    matrix = pd.concat([made[b] for b in blocks if b in made], axis=1)
    manifest = {b: list(made[b].columns) for b in blocks if b in made}
    return matrix, manifest


def assert_no_forbidden(matrix: pd.DataFrame, forbidden: list[str]) -> list[str]:
    """逐列断言不含禁止字段。命中就直接报错退出，不允许静默通过。"""
    hits = []
    for col in matrix.columns:
        low = col.lower()
        for bad in forbidden:
            # f_comp 块里的 *_lipid_pct 是 T1 的合法特征（制剂组成），
            # 禁止清单里的 particle_size_nm 等目标列才是要拦的，所以做精确前缀判断
            if bad.lower() in low:
                hits.append((col, bad))
    return hits


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/smallmol_baseline.yaml")
    ap.add_argument("--tasks", default="t1,t2,t3")
    ap.add_argument("--no-dedup", action="store_true", help="按行而非按唯一配方（敏感性检验）")
    ap.add_argument("--no-mw-limit", action="store_true", help="不设 MW 上限（敏感性检验）")
    ap.add_argument("--suffix", default="", help="产出文件名后缀，用于区分敏感性检验的产出")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    out_dir = ROOT / cfg["data"]["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(ROOT / cfg["data"]["source_csv"])
    sub_cfg = dict(cfg["subset"])
    if args.no_mw_limit:
        sub_cfg["max_payload_mw"] = None
    sub = S.select(
        raw,
        name=sub_cfg["name"],
        max_payload_mw=sub_cfg["max_payload_mw"],
        keep_probe_molecules=sub_cfg["keep_probe_molecules"],
    )

    import rdkit
    import sklearn

    manifest = {
        "config": args.config,
        "config_resolved": {"subset": sub_cfg, "features": cfg["features"]},
        "dedup": not args.no_dedup,
        "source_csv": cfg["data"]["source_csv"],
        "n_rows_source": int(len(raw)),
        "n_rows_subset": int(len(sub)),
        "versions": {
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "rdkit": rdkit.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "tasks": {},
    }

    for task in [t.strip() for t in args.tasks.split(",") if t.strip()]:
        units = D.BUILDERS[task](sub, dedup=not args.no_dedup)
        blocks = cfg["tasks"][task]["blocks"]
        matrix, block_cols = build_blocks(units, cfg, blocks)

        hits = assert_no_forbidden(matrix, cfg["forbidden_feature_substrings"])
        if hits:
            raise SystemExit(f"[{task}] 特征矩阵里出现禁止字段: {hits[:10]}")

        # units 表是分析单元清单，不是特征矩阵，所以可以带上原始目标值和组成列，
        # 供误差分析与审计使用（特征矩阵里不含它们，上面已断言）
        audit_cols = ["particle_size_nm", "pdi", *F.PCT_COLS, "prep_method_std"]
        keep = [c for c in (*D.PROVENANCE_COLS, *audit_cols) if c in units.columns]
        meta_cols = [c for c in units.columns if c.startswith(("target", "_", "group_", "task"))]
        units_out = units[keep + meta_cols].copy()

        units_out.to_parquet(out_dir / f"units_{task}{args.suffix}.parquet", index=False)
        matrix.astype("float32").to_parquet(
            out_dir / f"features_{task}{args.suffix}.parquet", index=False
        )

        nan_share = float(matrix.isna().to_numpy().mean())
        manifest["tasks"][task] = {
            "n_units": int(len(units)),
            "n_compounds": int(units["group_compound"].nunique()),
            "n_papers": int(units["paper_doi"].nunique()),
            "n_features": int(matrix.shape[1]),
            "blocks": {b: len(c) for b, c in block_cols.items()},
            # 指纹块只记列数和命名规则，不逐个列出 2048 个列名（否则 manifest 几百KB）
            "block_columns": {
                b: (cols if not any("_fp_" in c for c in cols) else [cols[0], "...", cols[-1]])
                for b, cols in block_cols.items()
            },
            "block_columns_non_fingerprint": {
                b: [c for c in cols if "_fp_" not in c] for b, cols in block_cols.items()
            },
            "overall_nan_share": round(nan_share, 4),
            "nan_share_by_block": {
                b: round(float(matrix[c].isna().to_numpy().mean()), 4) for b, c in block_cols.items()
            },
            "forbidden_check": "passed",
        }
        if task == "t1":
            manifest["tasks"][task]["target_summary"] = {
                "n": int(units["target"].notna().sum()),
                "log10_min": round(float(units["target"].min()), 4),
                "log10_median": round(float(units["target"].median()), 4),
                "log10_max": round(float(units["target"].max()), 4),
                "log10_sd": round(float(units["target"].std()), 4),
                "nm_min": round(float(units["particle_size_nm"].min()), 2),
                "nm_max": round(float(units["particle_size_nm"].max()), 2),
            }
        if task == "t3":
            manifest["tasks"][task]["class_counts"] = units["target"].value_counts().to_dict()
        if task == "t2":
            tcols = [f"target_{c}" for c in F.PCT_COLS]
            manifest["tasks"][task]["target_summary"] = {
                c: {
                    "min": round(float(units[c].min()), 3),
                    "median": round(float(units[c].median()), 3),
                    "max": round(float(units[c].max()), 3),
                }
                for c in tcols
            }
            manifest["tasks"][task]["sum_check"] = {
                "min": round(float(units[tcols].sum(axis=1).min()), 4),
                "max": round(float(units[tcols].sum(axis=1).max()), 4),
            }

        print(
            f"[{task}] 分析单元 {len(units):4d} | 化合物 {units['group_compound'].nunique():3d} | "
            f"论文 {units['paper_doi'].nunique():3d} | 特征 {matrix.shape[1]:5d} | "
            f"缺失占比 {nan_share:.1%}"
        )

    (out_dir / f"feature_manifest{args.suffix}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"写出: {(out_dir / f'feature_manifest{args.suffix}.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
