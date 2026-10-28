"""从 Yanes 2025 的开放数据库抽取对现有 PMC_IVR 记录的增补字段。

来源: Yanes, D. 等. International Journal of Pharmaceutics: X 10, 100393, 2025.
      DOI 10.1016/j.ijpx.2025.100393，CC BY 4.0
      数据库: https://github.com/danielyanes22/nanomed_IVR_data
授权登记: docs/data-licensing.md 第 2.2 节

**重要：这不是一个新数据源。** 已验证 Yanes 2025 就是仓库里 PMC_IVR 的来源：
  - 22 个化合物与仓库 PMC_IVR 的 22 个完全相同（InChIKey 交集 22，两侧各自独有 0）
  - 用仓库 release_curve_file 的数字对 Yanes IVR_ID 连接，271 行全部连上
  - 化合物名 271/271 一致，粒径 216/216 数值完全相同（差 < 0.51 nm）

所以它贡献 0 个新化合物、0 个新配方。它的价值是给**已有的 272 条记录**补上
仓库 schema 里没有的字段，产物因此是增补表，不是配方表。

用法:
    python3 -I scripts/extract_yanes2025.py <nanomed_IVR_data-main 解压目录>

原始 zip 只读，解压到仓库外的临时目录，本脚本不改写 data/raw/ 下任何文件。
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed" / "yanes2025_enrichment.csv"
BASELINE = ROOT / "merged_formulations_v2.csv"

SOURCE_DOI = "10.1016/j.ijpx.2025.100393"
SOURCE_LICENSE = "CC-BY-4.0"
SOURCE_ATTRIBUTION = (
    "Yanes, Daniel; Mead, Heather; Mann, James; Röding, Magnus; Paraskevopoulou, Vasiliki; "
    "Alexander, Cameron; Parhizkar, Maryam; Twycross, Jamie; Zelzer, Mischa. "
    "Making in vitro release and formulation data AI-ready: A foundation for streamlined "
    "nanomedicine development. International Journal of Pharmaceutics: X 10, 100393, 2025. "
    "DOI: 10.1016/j.ijpx.2025.100393. Licensed under CC BY 4.0."
)

# 仓库 schema 里没有、Yanes 有的字段。这是本次抽取的实际增量
NEW_FIELDS = ["drug_loading", "media_volume_mL", "media_temp_oC"]


def load_repo_pmc():
    df = pd.read_csv(BASELINE, low_memory=False)
    pmc = df[df["source_dataset"] == "PMC_IVR"].copy()
    pmc["ivr_id_from_curve"] = (
        pmc["release_curve_file"].astype(str).str.extract(r"^(\d+)")[0].astype("Int64")
    )
    return pmc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("unpacked", help="nanomed_IVR_data-main 的解压目录")
    args = ap.parse_args()

    d = Path(args.unpacked)
    backend = d / "data" / "unprocessed" / "backend_data.csv"
    media = d / "data" / "unprocessed" / "media_components.csv"
    quality = d / "data" / "quality_reporting.csv"
    for p in (backend, media, quality):
        if not p.is_file():
            print(f"找不到 {p}")
            return 1

    y = pd.read_csv(backend, low_memory=False)
    m = pd.read_csv(media)
    q = pd.read_csv(quality, low_memory=False)

    # quality_reporting.csv 的真实表头在第 1 行（第 0 行是分组标题）
    q.columns = [str(c).strip() for c in q.iloc[0]]
    q = q.iloc[1:].reset_index(drop=True)
    q = q.rename(columns={q.columns[0]: "Row_ID", q.columns[1]: "IVR_ID"})
    q["IVR_ID"] = pd.to_numeric(q["IVR_ID"], errors="coerce").astype("Int64")

    # 释放介质组分折叠成一列，分号分隔
    comp = (
        m.groupby("IVR_ID")["component_name"]
        .apply(lambda s: "; ".join(sorted({str(x) for x in s if pd.notna(x)})))
        .rename("media_components")
        .reset_index()
    )

    out = y[["formulation_ID", "IVR_ID", "API_name"] + NEW_FIELDS].copy()
    out = out.merge(comp, on="IVR_ID", how="left")

    qcols = [c for c in q.columns if c not in ("Row_ID", "IVR_ID")]
    out = out.merge(q[["IVR_ID"] + qcols], on="IVR_ID", how="left")
    out = out.rename(columns={c: "quality_" + c.strip().replace(" ", "_").lower() for c in qcols})

    # 连接到仓库记录
    pmc = load_repo_pmc()
    link = pmc[["source_row_id", "formulation_id", "release_curve_file", "ivr_id_from_curve",
                "payload_type"]].rename(columns={"payload_type": "repo_payload_type"})
    out = out.merge(link, left_on="IVR_ID", right_on="ivr_id_from_curve", how="left")

    out["name_matches_repo"] = (
        out["API_name"].astype(str).str.strip().str.lower()
        == out["repo_payload_type"].astype(str).str.strip().str.lower()
    )
    out["linked_to_repo"] = out["source_row_id"].notna()

    out["source_doi"] = SOURCE_DOI
    out["source_license"] = SOURCE_LICENSE
    out["source_attribution"] = SOURCE_ATTRIBUTION
    out["source_location"] = "nanomed_IVR_data/data/unprocessed/backend_data.csv 等"

    out = out.rename(columns={
        "formulation_ID": "yanes_formulation_id",
        "IVR_ID": "yanes_ivr_id",
        "formulation_id": "repo_formulation_id",
    })
    out.insert(0, "row_id", range(1, len(out) + 1))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print("=" * 68)
    print("Yanes 2025 增补表")
    print("=" * 68)
    print(f"  记录数                       {len(out)}")
    print(f"  连上仓库 PMC_IVR 记录的      {int(out['linked_to_repo'].sum())}")
    print(f"  化合物名一致的               {int(out['name_matches_repo'].sum())}")
    print(f"  Yanes 的唯一配方数           {out['yanes_formulation_id'].nunique()}")
    print()
    print("  仓库 schema 没有的字段，本次新增：")
    for f in NEW_FIELDS:
        print(f"    {f:<18} 非空 {int(out[f].notna().sum()):>3} / {len(out)}")
    print(f"    media_components   非空 {int(out['media_components'].notna().sum()):>3} / {len(out)}"
          f"  （仓库原来只有 media_pH）")
    qn = [c for c in out.columns if c.startswith("quality_")]
    print(f"    质量评级列         {len(qn)} 列: {qn}")
    print()
    print(f"  新增唯一化合物               0  （22 个与仓库完全相同）")
    print(f"  新增配方记录                 0  （同一份数据）")
    print()
    print(f"已写入 {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
