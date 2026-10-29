"""从 Jaki 2026 抽取 DoE 配方矩阵，产出 data/processed/formulations_jaki2026.csv。

来源: Jaki, M.; Köll-Weber, M.; Lembeck, J.; Wittmann, M.; Süss, R.
      International Journal of Pharmaceutics: X 12, 100627, 2026.
      DOI 10.1016/j.ijpx.2026.100627，CC BY 4.0
授权登记: docs/data-licensing.md 第 2.3 节
schema: docs/literature-protocol.md 第三节

两个来源，合计 45 个配方，载荷全部是 PROTAC ACBI2：

  A. DoE 设计 40 个配方
     设计矩阵 = 补充材料 docx 表 8（A:DOPC, B:DOPG, C:Cholesterol,
     D:DSPE-mPEG2000, E:pH, F:lipid concentration）
     响应     = 补充材料 docx 表 9（Z-Average, PDI, Zeta, D/L-Ratio, IE）
     两张表按 Run 号对齐

  B. 确认实验 5 个配方
     正文 PDF 的 Table 3，三次重复的均值，附 95% 预测区间
     从 PDF 文本层解析，不是结构化表格对象

**ACBI2 的分子量是 1064 Da，超过协议 N1 的 900 Da 上限**，所以全部记录
标 mw_over_default_cap = TRUE，默认不进主数据集。

**ACBI1 与 ACBI3 没有配方数据。** 摘要里的 "across three distinct PROTACs"
指的是 HPLC 方法的适用性，不是三个载荷各有 DoE。正文中这两个名字只出现在
方法验证段落里。

用法:
    python3 -I scripts/extract_jaki2026.py <mmc1.docx> <main.pdf>
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import pdfplumber
from docx import Document

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed" / "formulations_jaki2026.csv"

SOURCE_DOI = "10.1016/j.ijpx.2026.100627"
SOURCE_LICENSE = "CC-BY-4.0"
SOURCE_ATTRIBUTION = (
    "Jaki, Miriam; Köll-Weber, Monika; Lembeck, Jan; Wittmann, Maximilian; Süss, Regine. "
    "A DoE-Dual centrifugation-driven screening platform for liposomal incorporation of "
    "poorly soluble APIs: Application to the PROTAC ACBI2. "
    "International Journal of Pharmaceutics: X 12, 100627, 2026. "
    "DOI: 10.1016/j.ijpx.2026.100627. Licensed under CC BY 4.0."
)

T_DESIGN = 8    # docx 表 8：DoE 设计矩阵
T_RESPONSE = 9  # docx 表 9：DoE 响应

# ACBI2 的理化性质，取自补充材料 Table A.1
ACBI2_MW = 1064.0


def num(x):
    """把单元格文本转成浮点。处理 Unicode 减号与 PDF 的 (cid:0) 负号。"""
    if x is None:
        return None
    s = str(x).strip().replace("−", "-").replace("–", "-").replace("(cid:0)", "-")
    s = re.sub(r"-\s+", "-", s)
    s = re.sub(r"[^\d.\-]", "", s)
    if s in ("", "-", "."):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def rows_of(doc, idx):
    return [[c.text.strip() for c in r.cells] for r in doc.tables[idx].rows]


def parse_doe(doc):
    """docx 表 8 + 表 9 按 Run 号对齐，返回 {run: {...}}。"""
    design, resp = {}, {}

    for r in rows_of(doc, T_DESIGN):
        run = num(r[1]) if len(r) > 1 else None
        if run is None or num(r[3]) is None:
            continue  # 表头行
        design[int(run)] = {
            "doe_block": r[0].strip(),
            "build_type": r[2].strip(),
            "dopc_pct": num(r[3]),
            "dopg_pct": num(r[4]),
            "chol_pct": num(r[5]),
            "pegdspe_pct": num(r[6]),
            "ph": num(r[7]),
            "lipid_conc_pct": num(r[8]) if len(r) > 8 else None,
        }

    for r in rows_of(doc, T_RESPONSE):
        run = num(r[0]) if r else None
        if run is None or num(r[1]) is None:
            continue
        resp[int(run)] = {
            "z_average_nm": num(r[1]),
            "pdi": num(r[2]),
            "zeta_mv": num(r[3]),
            "dl_ratio_pct": num(r[4]),
            "ie_pct": num(r[5]),
        }

    out = []
    for run in sorted(set(design) & set(resp)):
        rec = {"run": run, "subset": "doe"}
        rec.update(design[run])
        rec.update(resp[run])
        out.append(rec)
    return out, sorted(set(design) ^ set(resp))


CONF_HEAD = re.compile(
    r"^(\d)\s+([\d.]+)\s*/\s*([\d.]+)\s*/\s*([\d.]+)\s*/\s*([\d.]+)\s+(\d)\s+(\d+)\s"
)


def parse_confirmation(pdf_path):
    """正文 Table 3 的 5 个确认实验。取 Mean 列（三次重复的实测均值）。"""
    with pdfplumber.open(pdf_path) as pdf:
        page = next(
            (p.extract_text() or "") for p in pdf.pages
            if "Locations and results of the confirmation runs" in (p.extract_text() or "")
        )
    lines = page.splitlines()
    start = next(i for i, l in enumerate(lines) if "Formulation location" in l)
    recs, cur = [], None
    for line in lines[start:]:
        s = line.strip()
        m = CONF_HEAD.match(s)
        if m:
            if cur:
                recs.append(cur)
            cur = {
                "run": 100 + int(m.group(1)),  # 和 DoE 的 run 号区分开
                "conf_id": int(m.group(1)),
                "subset": "confirmation",
                "doe_block": "confirmation",
                "build_type": "Confirmation",
                "dopc_pct": float(m.group(2)),
                "dopg_pct": float(m.group(3)),
                "chol_pct": float(m.group(4)),
                "pegdspe_pct": float(m.group(5)),
                "ph": float(m.group(6)),
                "lipid_conc_pct": float(m.group(7)),
            }
            s = s[m.end():].strip()
        if cur is None:
            continue
        # 每个响应行形如 "<名称> low mean high"，取中间那个 mean
        for key, pat in (
            ("z_average_nm", r"Z-Average"),
            ("pdi", r"PDI"),
            ("zeta_mv", r"Zeta"),
            ("dl_ratio_pct", r"D/L-Ratio"),
            ("conc_acbi2", r"c\(ACBI2\)"),
            ("ie_pct", r"IE"),
        ):
            mm = re.match(pat + r"\s+(.*)$", s)
            if mm:
                vals = [num(v) for v in re.findall(r"(?:\(cid:0\)\s*)?-?[\d.]+", mm.group(1))]
                vals = [v for v in vals if v is not None]
                if len(vals) >= 3 and key not in cur:
                    cur[key] = vals[1]  # 中间列 = Mean
                break
        if s.startswith("Fig."):
            break
    if cur:
        recs.append(cur)
    return recs


def to_repo_schema(rec):
    """映射到 docs/literature-protocol.md 第三节的字段。"""
    comp = [rec.get("dopc_pct"), rec.get("dopg_pct"), rec.get("chol_pct"), rec.get("pegdspe_pct")]
    total = sum(c for c in comp if c is not None)
    helper = (rec.get("dopc_pct") or 0) + (rec.get("dopg_pct") or 0)
    helper_name = "+".join(
        n for n, v in (("DOPC", rec.get("dopc_pct")), ("DOPG", rec.get("dopg_pct"))) if v
    ) or None
    n_helper = sum(1 for v in (rec.get("dopc_pct"), rec.get("dopg_pct")) if v)
    return {
        "source_dataset": "Jaki2026",
        "source_row_id": rec["run"],
        "formulation_id": f"jaki2026_{rec['subset']}_{rec['run']}",
        "ionizable_lipid_name": None, "ionizable_lipid_smiles": None, "ionizable_lipid_pct": None,
        "helper_lipid_name": helper_name,
        "helper_lipid_smiles": None,
        "helper_lipid_pct": helper or None,
        "sterol_lipid_name": "Cholesterol" if rec.get("chol_pct") else None,
        "sterol_lipid_smiles": None,
        "sterol_lipid_pct": rec.get("chol_pct") or None,
        "peg_lipid_name": "DSPE-mPEG2000" if rec.get("pegdspe_pct") else None,
        "peg_lipid_smiles": None,
        "peg_lipid_pct": rec.get("pegdspe_pct") or None,
        "particle_size_nm": rec.get("z_average_nm"),
        "size_metric": "Z_average",
        "pdi": rec.get("pdi"),
        "zeta_potential_mv": rec.get("zeta_mv"),
        "zeta_measurement_medium": None,
        "encapsulation_efficiency_pct": rec.get("ie_pct"),
        "ee_method": "HPLC",
        "ee_free_drug_separation": "centrifugation",
        "drug_to_lipid_ratio": rec.get("dl_ratio_pct"),
        "drug_to_lipid_unit": "mol_pct",
        "payload_type": "ACBI2",
        "payload_smiles": None,
        "payload_inchikey": None,
        "payload_cas": None,
        "payload_id_source": "uncertain",
        "payload_mw_from_paper": ACBI2_MW,
        "mw_over_default_cap": True,
        "is_probe": False,
        "carrier_subtype": "classic_liposome",
        "total_lipid_slots_filled": sum(1 for c in comp if c),
        "n_components_in_helper_slot": n_helper,
        "slot_assignment_uncertain": bool(rec.get("dopg_pct")),
        # 仓库 schema 只有 4 个脂质槽位，DOPG 没有对应槽位，只能和 DOPC 一起塞进
        # helper 槽。但 DOPG 是阴离子脂质，是本文 zeta 电位的主要驱动因素，折叠后
        # 这个信息在 helper_lipid_pct 里看不出来。所以单独留两列，建模时可直接用。
        "component_dopc_pct": rec.get("dopc_pct"),
        "component_dopg_pct": rec.get("dopg_pct"),
        "anionic_lipid_frac_of_total": (
            round(rec["dopg_pct"] / total, 4)
            if rec.get("dopg_pct") and total else (0.0 if total else None)
        ),
        "composition_raw_verbatim": (
            f"DOPC/DOPG/Cholesterol/DSPE-mPEG2000 = "
            f"{rec.get('dopc_pct')}/{rec.get('dopg_pct')}/{rec.get('chol_pct')}/{rec.get('pegdspe_pct')} %"
        ),
        "composition_unit_as_reported": "mol_pct",
        "composition_pct_sums_to": round(total, 2) if total else None,
        "composition_pct_was_renormalized": False,
        "ratio_order_was_ambiguous": False,
        "prep_method_std": "双离心 (dual centrifugation)",
        "extrusion_pore_nm": None, "extrusion_passes": None,
        "device_or_chip_std": None, "total_flow_rate_ml_min_std": None,
        "flow_ratio_imbalance": None, "process_temp_c_std": None,
        "aqueous_phase_ph": rec.get("ph"),
        "aqueous_phase_buffer": None, "organic_phase_solvent": None,
        "lipid_concentration_pct": rec.get("lipid_conc_pct"),
        "loading_mode": "passive",
        "measurement_instrument_std": None,
        "n_replicates": 3 if rec["subset"] == "confirmation" else None,
        "value_sd": None, "value_sd_type": None,
        "formation_ok": True,
        "process_notes": f"DoE {rec.get('build_type')}; block={rec.get('doe_block')}",
        "study_block_id": f"jaki2026_{rec.get('doe_block')}",
        "block_varies_by": "multiple",
        "is_doe_or_screening_matrix": True,
        "value_read_from": "table" if rec["subset"] == "doe" else "table",
        "source_location": (
            "Supporting Information Table 8+9 (DoE)" if rec["subset"] == "doe"
            else "Main text Table 3 (confirmation runs, PDF text layer)"
        ),
        "data_quality_tier": "B",
        "extraction_confidence": "high" if rec["subset"] == "doe" else "medium",
        "needs_fulltext": False,
        "fulltext_status": "obtained",
        "source_doi": SOURCE_DOI,
        "source_license": SOURCE_LICENSE,
        "source_attribution": SOURCE_ATTRIBUTION,
        "extracted_by": "claude",
        "extraction_date": "2026-10-29",
        "qc_flag": "ok",
        "qc_reason": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docx")
    ap.add_argument("pdf")
    args = ap.parse_args()

    doc = Document(args.docx)
    doe, unmatched = parse_doe(doc)
    conf = parse_confirmation(args.pdf)

    rows = [to_repo_schema(r) for r in doe + conf]
    df = pd.DataFrame(rows)

    # 组分加总偏离 100 超过 0.5 的标 suspect
    bad = df["composition_pct_sums_to"].notna() & (
        (df["composition_pct_sums_to"] - 100).abs() > 0.5
    )
    df.loc[bad, "qc_flag"] = "suspect"
    df.loc[bad, "qc_reason"] = "四个脂质组分加总偏离 100 超过 0.5"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    print("=" * 68)
    print("Jaki 2026 配方表")
    print("=" * 68)
    print(f"  DoE 配方        {len(doe)}")
    print(f"  确认实验配方    {len(conf)}")
    print(f"  合计            {len(df)}")
    if unmatched:
        print(f"  设计与响应对不上的 Run: {unmatched}")
    print()
    print(f"  载荷            ACBI2（唯一载荷），MW {ACBI2_MW} Da")
    print(f"  超 900 Da 上限  {int(df['mw_over_default_cap'].sum())} / {len(df)}  全部")
    print(f"  组分加总异常    {int(bad.sum())}")
    print()
    for col, label in (("encapsulation_efficiency_pct", "包封率 IE"),
                       ("particle_size_nm", "粒径"), ("pdi", "PDI"),
                       ("zeta_potential_mv", "Zeta"), ("drug_to_lipid_ratio", "D/L 比")):
        s = df[col].dropna()
        if len(s):
            print(f"  {label:<10} 非空 {len(s):>3}  范围 {s.min():8.2f} - {s.max():8.2f}  中位 {s.median():7.2f}")
    print()
    print(f"已写入 {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
