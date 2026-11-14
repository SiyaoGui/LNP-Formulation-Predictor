"""从 Xu 2022 抽取外部探针集，产出 data/processed/probe_xu2022.csv 及其化合物表。

来源: Xu, X. 等. Molecules 27(22), 7967, 2022.
      DOI 10.3390/molecules27227967，CC BY 4.0
授权登记: docs/data-licensing.md 第二节

**这是探针集，不进训练集。** 按用户要求单独留存。

重要：收集阶段对本文的预期是「19 个紫杉醇硼酸衍生物的结构与包封率数据」，
核对全文后这是错的。实际情况：
  - 19 个化合物只有**细胞毒性**数据（表 2 的 GI50），没有逐个的包封率
  - 只有 5 个（4a, 4d, 13a, 17a, 17c）尝试过载入脂质体
  - 其中 4 个（4a, 13a, 17a, 17c）载入失败，原文只给「明显沉降」的定性描述
  - 只有 4d 有定量包封率，而表 3/表 4/表 S1 全部是**固定载荷 4d 变配方**
  - 表 1 的 R 基团是图片，原文不提供 SMILES
所以本文是 L 类，不是 P 类。详见 docs/worklog/2026-10-29-抽取4-xu-探针.md

数据位置:
  表 3   正文 p6   铜离子梯度 6 个配方（变脂质比、铜浓度、铜盐与 pH）
  表 4   正文 p6   7 种梯度（6 种糖 + ATP），ATP 失败
  表 S1  补充 p1-2 乙酸钙梯度 6 个配方，全部失败
  表 S2  补充 p2   4d 最优配方的粒径/PDI/zeta/载药量
  正文 p5          5 个化合物的 logD 与 pKa，以及 4 个的载入失败
  正文 p11         4d 的 IUPAC 名与分子式

用法:
    python3 -I scripts/extract_xu2022_probe.py \\
        data/raw/xu2022_ptx_probe/molecules-27-07967.pdf \\
        <补充材料 PDF 的路径>

原始文件只读。补充材料在 molecules-27-07967-s001.zip 里，解压到仓库外的临时目录。
"""
import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed" / "probe_xu2022.csv"
OUT_CMPD = ROOT / "data" / "processed" / "probe_xu2022_compounds.csv"

SOURCE_DOI = "10.3390/molecules27227967"
SOURCE_LICENSE = "CC-BY-4.0"
SOURCE_ATTRIBUTION = (
    "Xu, Xiangwei; Liu, Yanhua; Shao, Shanshan; Li, Jinbo; Xu, Zhaochu; Yin, Yueling; "
    "Zhao, Linxiang; Wang, Yongjun; Liu, Dan. "
    "Synthesis of Paclitaxel Derivatives for Remote Loading into Liposomes and Improved "
    "Therapeutic Effect. Molecules 27(22), 7967, 2022. "
    "DOI: 10.3390/molecules27227967. Licensed under CC BY 4.0."
)

# 4d 的身份。原文 p11 给了 IUPAC 名与 HR-MS 分子式，但没有给 SMILES。
# 不从 IUPAC 名反推结构，那属于猜测，协议不允许
CMPD_4D_NAME = (
    "2'-O-[2-((2-((4-boronobenzyl)oxy)-2-oxoethyl)disulfaneyl)acetyl]taxol"
)
CMPD_4D_FORMULA = "C58H63BNO19S2"
CMPD_4D_MH_CALC = 1152.3523   # [M+H]+ 计算值
CMPD_4D_MW = 1151.34          # 中性分子，由 [M+H]+ 减去一个质子

# 表 3：按词坐标重建后的 6 行。两种独立重建（文本顺序、坐标分组）结果一致，
# 且与正文三处文字描述全部吻合，见脚本末尾的 verify_table3_against_prose()
TABLE3 = [
    # (脂质比 HSPC:Chol:DSPE-PEG2000 w/w/w, 铜浓度 mM, 内水相, EE%, EE 的 SD)
    ("19:1:0.25", 300, "Cu-gluconate (pH 7.4)", 76.34, 3.21),
    ("3:1:0.05",  300, "Cu-gluconate (pH 7.4)", 96.13, 1.33),
    ("3:1:0.05",  100, "Cu-gluconate (pH 7.4)", 50.34, 2.34),
    ("3:1:0.05",  200, "Cu-gluconate (pH 7.4)", 82.34, 3.98),
    ("3:1:0.05",  300, "Cu-gluconate",          85.23, 2.34),
    ("3:1:0.05",  300, "Cu(Ac)2",               71.78, 4.32),
]
TABLE3_BUFFER = "20 mM HEPES + 300 mM sucrose (pH 7.4, adjusted with triethylamine)"
TABLE3_DL = "1:10"

# 表 4：最优铜梯度配方下换内水相梯度。ATP 失败，原文记 "—"
TABLE4 = [
    ("glucose",   75.67,  3.89),
    ("sucrose",   59.425, 7.89),
    ("lactose",   69.87,  6.89),
    ("maltose",   63.71, 10.98),
    ("mannose",   82.77,  2.98),
    ("trehalose", 65.51,  8.88),
    ("ATP",       None,   None),
]

# 表 S1：乙酸钙梯度，6 个配方全部失败（原文 EE 列写 "---"）
TABLE_S1 = [
    ("3:1:0.05",  200, "200 mM Na2SO4"),
    ("19:1:0.25", 200, "200 mM Na2SO4"),
    ("3:1:0.05",  120, "120 mM Na2SO4"),
    ("3:1:0.05",  250, "250 mM Na2SO4"),
    ("3:1:0.05",  200, "200 mM Na2SO4 + 50 mM citric acid"),
    ("3:1:0.05",  200, "200 mM Na2SO4 + 100 mM citric acid"),
]

# 表 S2：4d 最优配方的表征
TABLE_S2 = {
    "particle_size_nm": 115.6, "particle_size_sd": 1.112,
    "pdi": 0.065, "pdi_sd": 0.004,
    "zeta_potential_mv": -14.65, "zeta_sd": 1.891,
    "drug_loading_pct": 9.02, "drug_loading_sd": 0.087,
}

# 正文 p5：5 个化合物的 logD / pKa，以及载入结果
COMPOUNDS = [
    # (编号, logD, pKa, 载入是否成功)
    ("4a",  2.466, 12.302, False),
    ("4d",  2.413, 12.301, True),
    ("13a", 2.540, 12.297, False),
    ("17a", 2.309, 12.302, False),
    ("17c", 2.559, 12.302, False),
]


def split_lipid_ratio(s):
    """'3:1:0.05' -> (HSPC, Chol, DSPE-PEG2000) 三个 w/w 份数。"""
    parts = [float(x) for x in s.split(":")]
    assert len(parts) == 3, s
    return parts


def base_fields(fid, loc, note):
    """探针集共用的固定列。"""
    return {
        "source_dataset": "Xu2022_probe",
        "formulation_id": fid,
        "is_probe": True,
        "payload_type": "compound_4d",
        "payload_name_as_reported": CMPD_4D_NAME,
        "payload_formula": CMPD_4D_FORMULA,
        "payload_mw_from_paper": CMPD_4D_MW,
        "mw_over_default_cap": True,          # 1151 Da，远超 900
        "payload_smiles": None,               # 原文表 1 的 R 基团是图片，不提供 SMILES
        "payload_inchikey": None,
        "payload_id_source": "name_only",     # 有 IUPAC 名与分子式，无结构
        "carrier_subtype": "classic_liposome",
        "helper_lipid_name": "HSPC",
        "sterol_lipid_name": "Cholesterol",
        "peg_lipid_name": "DSPE-PEG2000",
        "composition_unit_as_reported": "mass_ratio",   # w/w/w，不是 mol%
        "loading_mode": "active",             # 远程梯度载药
        "prep_method_std": "薄膜水化 + 远程梯度载药",
        "ee_method": "HPLC",
        "study_block_id": "xu2022_4d_formulation_screen",
        "block_varies_by": "lipid_and_process",
        "is_doe_or_screening_matrix": True,
        "value_read_from": "table",
        "source_location": loc,
        "data_quality_tier": "B",
        "extraction_confidence": "high",
        "needs_fulltext": False,
        "fulltext_status": "obtained",
        "source_doi": SOURCE_DOI,
        "source_license": SOURCE_LICENSE,
        "source_attribution": SOURCE_ATTRIBUTION,
        "extracted_by": "scripts/extract_xu2022_probe.py",
        "extraction_date": "2026-10-29",
        "notes": note,
    }


def build_formulations():
    recs = []

    # 表 3
    for i, (ratio, conc, inner, ee, sd) in enumerate(TABLE3, start=1):
        hspc, chol, peg = split_lipid_ratio(ratio)
        r = base_fields(
            f"xu2022_t3_{i}", "正文 Table 3",
            "铜离子梯度。变量：脂质质量比、铜浓度、铜盐与内水相 pH",
        )
        r.update({
            "helper_lipid_pct": hspc, "sterol_lipid_pct": chol, "peg_lipid_pct": peg,
            "composition_raw_verbatim": f"HSPC:Chol:DSPE-PEG2000 = {ratio} (w/w/w)",
            "inner_phase": inner,
            "inner_phase_conc_mm": conc,
            "external_buffer": TABLE3_BUFFER,
            "drug_to_lipid_ratio_as_reported": TABLE3_DL,
            "encapsulation_efficiency_pct": ee,
            "value_sd": sd,
            "value_sd_type": "SD",
            "formation_ok": True,
            "gradient_type": "metal_ion",
        })
        recs.append(r)

    # 表 4：沿用表 3 最优的铜梯度配方（3:1:0.05，300 mM），只换梯度种类
    for i, (grad, ee, sd) in enumerate(TABLE4, start=1):
        hspc, chol, peg = split_lipid_ratio("3:1:0.05")
        ok = ee is not None
        r = base_fields(
            f"xu2022_t4_{i}", "正文 Table 4",
            "糖类与 ATP 梯度。原文说沿用铜梯度的最优配方，但未逐行重述脂质比，"
            "此处按 3:1:0.05 填入并标 slot_assignment_uncertain"
            + ("" if ok else "。ATP 载入失败，原文 EE 列记 '—'"),
        )
        r.update({
            "helper_lipid_pct": hspc, "sterol_lipid_pct": chol, "peg_lipid_pct": peg,
            "composition_raw_verbatim": "HSPC:Chol:DSPE-PEG2000 = 3:1:0.05 (w/w/w)（推断，见 notes）",
            "slot_assignment_uncertain": True,
            "inner_phase": grad,
            "inner_phase_conc_mm": None,
            "external_buffer": TABLE3_BUFFER,
            "drug_to_lipid_ratio_as_reported": TABLE3_DL,
            "encapsulation_efficiency_pct": ee,
            "value_sd": sd,
            "value_sd_type": "SD" if ok else None,
            "formation_ok": ok,
            "gradient_type": "ATP" if grad == "ATP" else "saccharide",
        })
        recs.append(r)

    # 表 S1：全部失败。载荷不确定，原文只说对 5 个化合物试过乙酸钙梯度
    for i, (ratio, conc, counter) in enumerate(TABLE_S1, start=1):
        hspc, chol, peg = split_lipid_ratio(ratio)
        r = base_fields(
            f"xu2022_s1_{i}", "补充材料 Table S1",
            "乙酸钙梯度，EE 列原文写 '---'，即载药失败。"
            "原文未指明本表对应哪个化合物，只说对 4a/4d/13a/17a/17c 试过乙酸钙梯度，"
            "所以载荷按不确定处理",
        )
        r.update({
            "payload_type": "uncertain_one_of_4a_4d_13a_17a_17c",
            "payload_name_as_reported": None,
            "payload_formula": None,
            "payload_mw_from_paper": None,
            "payload_id_source": "uncertain",
            "helper_lipid_pct": hspc, "sterol_lipid_pct": chol, "peg_lipid_pct": peg,
            "composition_raw_verbatim": f"HSPC:Chol:DSPE-PEG2000 = {ratio} (w/w/w)",
            "inner_phase": f"Ca(Ac)2 {conc} mM",
            "inner_phase_conc_mm": conc,
            "external_buffer": counter,
            "drug_to_lipid_ratio_as_reported": "1:10",
            "encapsulation_efficiency_pct": None,
            "value_sd": None, "value_sd_type": None,
            "formation_ok": False,
            "gradient_type": "metal_ion",
            "qc_reason": "原文 EE 列为 '---'，是失败记录而非缺测",
        })
        recs.append(r)

    # 表 S2：4d 最优配方的表征。单独一行，不并进表 3 第 2 行
    hspc, chol, peg = split_lipid_ratio("3:1:0.05")
    r = base_fields(
        "xu2022_s2_optimal", "补充材料 Table S2",
        "4d 最优配方的粒径/PDI/zeta/载药量。组分与表 3 第 2 行（xu2022_t3_2）相同，"
        "但原文分开报，未说明是否同一批次，所以不并进那一行",
    )
    r.update({
        "helper_lipid_pct": hspc, "sterol_lipid_pct": chol, "peg_lipid_pct": peg,
        "composition_raw_verbatim": "HSPC:Chol:DSPE-PEG2000 = 3:1:0.05 (w/w/w)",
        "inner_phase": "Cu-gluconate (pH 7.4)",
        "inner_phase_conc_mm": 300,
        "external_buffer": TABLE3_BUFFER,
        "drug_to_lipid_ratio_as_reported": TABLE3_DL,
        "encapsulation_efficiency_pct": None,
        "particle_size_nm": TABLE_S2["particle_size_nm"],
        "size_metric": "Z_average",
        "pdi": TABLE_S2["pdi"],
        "zeta_potential_mv": TABLE_S2["zeta_potential_mv"],
        "drug_loading_pct": TABLE_S2["drug_loading_pct"],
        "value_sd": TABLE_S2["particle_size_sd"],
        "value_sd_type": "SD (粒径的；PDI/zeta/载药量的 SD 见 *_sd 列)",
        "pdi_sd": TABLE_S2["pdi_sd"],
        "zeta_sd": TABLE_S2["zeta_sd"],
        "drug_loading_sd": TABLE_S2["drug_loading_sd"],
        "formation_ok": True,
        "gradient_type": "metal_ion",
        "same_composition_as": "xu2022_t3_2",
    })
    recs.append(r)
    return recs


def build_compounds():
    """5 个尝试过载入的化合物。注意：19 个化合物只有细胞毒性，没有逐个包封率。"""
    out = []
    for code, logd, pka, ok in COMPOUNDS:
        out.append({
            "compound_code": code,
            "name_as_reported": CMPD_4D_NAME if code == "4d" else None,
            "formula": CMPD_4D_FORMULA if code == "4d" else None,
            "mw_from_paper": CMPD_4D_MW if code == "4d" else None,
            "smiles": None,          # 原文表 1 的 R 基团是图片
            "inchikey": None,
            "id_source": "name_only" if code == "4d" else "code_only",
            "logd": logd,
            "pka": pka,
            "loaded_successfully": ok,
            "load_outcome_is_quantitative": ok,
            "load_outcome_verbatim": (
                "copper gradient EE up to 96.13%" if ok
                else "failed in loading into the liposomes, showing obvious sedimentation"
            ),
            "source_location": "正文 2.4 节（logD/pKa 与载入结果）",
            "source_doi": SOURCE_DOI,
            "source_license": SOURCE_LICENSE,
            "source_attribution": SOURCE_ATTRIBUTION,
        })
    return out


def verify_table3_against_prose(df3):
    """用正文三处文字描述交叉验证表 3 的行列对应，防止合并单元格错位。"""
    checks = []
    g = df3.set_index("formulation_id")

    # 1 铜浓度越高 EE 越高（固定 3:1:0.05，Cu-gluconate pH 7.4）
    conc = [(100, "xu2022_t3_3"), (200, "xu2022_t3_4"), (300, "xu2022_t3_2")]
    ees = [g.loc[i, "encapsulation_efficiency_pct"] for _, i in conc]
    checks.append(("铜浓度越高 EE 越高", ees == sorted(ees)))

    # 2 3:1:0.05（Chol 份额更高）比 19:1:0.25 的 EE 高，同为 300 mM
    checks.append((
        "3:1:0.05 的 EE 高于 19:1:0.25",
        g.loc["xu2022_t3_2", "encapsulation_efficiency_pct"]
        > g.loc["xu2022_t3_1", "encapsulation_efficiency_pct"],
    ))

    # 3 中性葡萄糖酸铜最优，优于未调 pH 的葡萄糖酸铜与乙酸铜
    checks.append((
        "中性 Cu-gluconate 优于 Cu-gluconate 与 Cu(Ac)2",
        g.loc["xu2022_t3_2", "encapsulation_efficiency_pct"]
        > g.loc["xu2022_t3_5", "encapsulation_efficiency_pct"]
        > g.loc["xu2022_t3_6", "encapsulation_efficiency_pct"],
    ))
    return checks


def check_pdf_values(main_pdf, supp_pdf):
    """从 PDF 文本层回读几个关键数字，确认硬编码的表没有抄错。"""
    found = {}
    with pdfplumber.open(main_pdf) as pdf:
        t = "\n".join((p.extract_text() or "") for p in pdf.pages)
    for ee, _sd in [(e, s) for _, _, _, e, s in TABLE3]:
        found[f"T3 EE {ee}"] = f"{ee:.2f}" in t
    for grad, ee, _ in TABLE4:
        if ee is not None:
            found[f"T4 {grad} {ee}"] = str(ee) in t
    found["4d 分子式"] = "C H BNO S" in t.replace("\n", "")  # 下标被拆行，只查主干
    found["4d IUPAC 名"] = "boronobenzyl)oxy)-2-oxoethyl)disulfaneyl)acetyl]taxol" in t.replace("\n", "")
    for code, logd, pka, _ in COMPOUNDS:
        found[f"{code} logD {logd}"] = f"{logd}" in t
        found[f"{code} pKa {pka}"] = f"{pka}" in t

    if supp_pdf is not None:
        with pdfplumber.open(supp_pdf) as pdf:
            ts = "\n".join((p.extract_text() or "") for p in pdf.pages)
        for k, v in (("粒径", 115.6), ("PDI", 0.065), ("zeta", -14.65), ("载药量", 9.02)):
            found[f"S2 {k} {v}"] = str(abs(v)) in ts
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("main_pdf", help="正文 PDF")
    ap.add_argument("supp_pdf", nargs="?", help="补充材料 PDF（zip 解压后）")
    args = ap.parse_args()

    main_pdf = Path(args.main_pdf)
    if not main_pdf.is_file():
        print(f"找不到 {main_pdf}")
        return 1
    supp_pdf = Path(args.supp_pdf) if args.supp_pdf else None
    if supp_pdf is not None and not supp_pdf.is_file():
        print(f"找不到 {supp_pdf}")
        return 1

    df = pd.DataFrame(build_formulations())
    df.insert(0, "row_id", range(1, len(df) + 1))
    if "qc_flag" not in df.columns:
        df["qc_flag"] = "ok"
    df["qc_flag"] = df["qc_flag"].fillna("ok")

    cm = pd.DataFrame(build_compounds())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    cm.to_csv(OUT_CMPD, index=False)

    print("=" * 70)
    print("Xu 2022 探针集（不进训练集）")
    print("=" * 70)
    for loc, g in df.groupby("source_location", sort=False):
        ok = int(g["formation_ok"].sum())
        ee = int(g["encapsulation_efficiency_pct"].notna().sum())
        print(f"  {loc:<24} 记录 {len(g):>2}  成膜/载药成功 {ok:>2}  有定量 EE {ee:>2}")
    print(f"  {'合计':<24} 记录 {len(df):>2}  成膜/载药成功 "
          f"{int(df['formation_ok'].sum()):>2}  有定量 EE "
          f"{int(df['encapsulation_efficiency_pct'].notna().sum()):>2}")
    print()
    print("  载荷        1 个（compound 4d），无 SMILES，MW 1151 Da 超 900 上限")
    print(f"  EE 范围     {df['encapsulation_efficiency_pct'].min():.2f} - "
          f"{df['encapsulation_efficiency_pct'].max():.2f}")
    print()
    print("化合物表（尝试过载入脂质体的 5 个）")
    print(f"  记录 {len(cm)}，载入成功 {int(cm['loaded_successfully'].sum())}，"
          f"失败 {int((~cm['loaded_successfully']).sum())}（只有定性描述）")
    print(f"  有 logD/pKa 的 {int(cm['logd'].notna().sum())}，有 SMILES 的 "
          f"{int(cm['smiles'].notna().sum())}")
    print()

    print("表 3 行列对应的交叉验证（对照正文文字描述）")
    allok = True
    for name, ok in verify_table3_against_prose(df[df["source_location"] == "正文 Table 3"]):
        print(f"  [{'通过' if ok else '不通过'}] {name}")
        allok &= bool(ok)
    print()

    print("从 PDF 文本层回读硬编码的数字")
    vals = check_pdf_values(main_pdf, supp_pdf)
    bad = [k for k, v in vals.items() if not v]
    print(f"  核对 {len(vals)} 项，对上 {len(vals) - len(bad)} 项")
    if bad:
        print("  对不上的：")
        for k in bad:
            print(f"    {k}")
    if supp_pdf is None:
        print("  注意：未提供补充材料 PDF，表 S2 的 4 个数字未回读核对")
    print()
    print(f"已写入 {OUT.relative_to(ROOT)}")
    print(f"已写入 {OUT_CMPD.relative_to(ROOT)}")
    return 0 if (allok and not bad) else 2


if __name__ == "__main__":
    sys.exit(main())
