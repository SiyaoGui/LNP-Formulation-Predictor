"""报告外部数据集抽取后，唯一化合物数相对基线的增量。

瓶颈指标是**唯一化合物数**，不是记录数（依据 `docs/data-inventory.md` 第三、五节：
272 条小分子记录只对应 22 个唯一化合物，按化合物分组后测试集只剩 3 到 4 个）。
所以每抽完一个数据集都要报这组数字，而不是报记录数。

用法:
    python3 scripts/report_compound_gain.py
输出:
    docs/compound_gain_stats.json（机器可读）+ stdout 可读报告

口径说明（重要，不许合并这两类）:
  A 类 配方表  贡献「配方记录 + 化合物」，直接抬高唯一化合物数
  B 类 分子属性表（如分配系数）贡献「化合物属性」，**本身不增加配方记录**。
       它对瓶颈的贡献取决于是否有配方数据配得上这些化合物，所以单独报
       「能连上现有配方记录的化合物数」，不混进合并后的唯一化合物数
"""
import json
import sys
from pathlib import Path

import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors
from rdkit.Chem.Scaffolds import MurckoScaffold

RDLogger.DisableLog("rdApp.*")

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "merged_formulations_v2.csv"
OUT_JSON = ROOT / "docs" / "compound_gain_stats.json"

# 与 scripts/data_inventory.py 保持一致的小分子子集定义
LARGE_PAYLOADS = {"mRNA", "siRNA", "DNA", "ASO", "protein", "mRNA, siRNA"}
NON_DRUG_PAYLOADS = {"empty", "gold_nanoparticles"}
MW_CAP = 900.0

# A 类：配方表。抽取脚本的产物，列名按 docs/literature-protocol.md 第三节
# Yanes 2025 不在这里：已验证它就是仓库 PMC_IVR 的来源，抽出来是 C 类增补表，
# 不是新的配方表（见 scripts/extract_yanes2025.py 的证明）
FORMULATION_TABLES = {
    "Jaki 2026": ROOT / "data" / "processed" / "formulations_jaki2026.csv",
}
# B 类：分子属性表。列名按 docs/schema-partition-coefficients.md
PROPERTY_TABLES = {
    "Khawar 2022": ROOT / "data" / "processed" / "partition_coefficients.csv",
}
# C 类：对现有记录的增补表。不增加记录也不增加化合物，只给已有记录补字段
ENRICHMENT_TABLES = {
    "Yanes 2025": ROOT / "data" / "processed" / "yanes2025_enrichment.csv",
}
# 探针集：单独报，不计入训练集的任何统计
PROBE_TABLES = {
    "Xu 2022": ROOT / "data" / "processed" / "probe_xu2022.csv",
}


def inchikey_and_mw(smiles):
    """返回 (inchikey, mw, murcko_scaffold)；无法解析则返回 (None, None, None)。"""
    if not isinstance(smiles, str) or not smiles.strip():
        return None, None, None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, None, None
    try:
        key = Chem.MolToInchiKey(mol)
    except Exception:
        key = None
    try:
        scaf = MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False)
    except Exception:
        scaf = None
    return key, Descriptors.MolWt(mol), scaf


def load_baseline():
    """现有小分子子集：返回 (DataFrame, {inchikey}, {smiles}, {scaffold})。"""
    df = pd.read_csv(BASELINE, low_memory=False)
    sm = df[
        df["payload_smiles"].notna()
        & (df["payload_smiles"].astype(str).str.strip() != "")
        & ~df["payload_type"].isin(LARGE_PAYLOADS)
        & ~df["payload_type"].isin(NON_DRUG_PAYLOADS)
    ].copy()
    props = sm["payload_smiles"].map(inchikey_and_mw)
    sm["inchikey"] = [p[0] for p in props]
    sm["mw"] = [p[1] for p in props]
    sm["scaffold"] = [p[2] for p in props]
    return sm


def key_set(series):
    return {k for k in series.dropna().unique() if k}


def describe_formulation_table(name, path, base_keys):
    """A 类：配方表。"""
    if not path.is_file():
        return {"status": "尚未抽取", "path": str(path.relative_to(ROOT))}
    df = pd.read_csv(path, low_memory=False)
    col = "payload_inchikey" if "payload_inchikey" in df.columns else None
    if col is None and "payload_smiles" in df.columns:
        df["payload_inchikey"] = [inchikey_and_mw(s)[0] for s in df["payload_smiles"]]
        col = "payload_inchikey"
    if col is None:
        return {
            "status": "列缺失",
            "path": str(path.relative_to(ROOT)),
            "note": "既无 payload_inchikey 也无 payload_smiles，无法统计化合物",
        }
    keys = key_set(df[col])
    in_cap = None
    if "mw_over_default_cap" in df.columns:
        in_cap = len(key_set(df.loc[df["mw_over_default_cap"] != True, col]))  # noqa: E712
    # 唯一化合物按 InChIKey 数，没有 SMILES 的载荷算 0 个。但「0 个」会被误读成
    # 「这篇没有载荷」。所以同时报按名字数的载荷数，以及其中缺结构的个数
    named = (
        sorted(set(df["payload_type"].dropna().astype(str).str.strip()) - {""})
        if "payload_type" in df.columns else []
    )
    no_struct = [
        n for n in named
        if not key_set(df.loc[df["payload_type"].astype(str).str.strip() == n, col])
    ]
    return {
        "status": "已抽取",
        "path": str(path.relative_to(ROOT)),
        "records": int(len(df)),
        "unique_compounds": len(keys),
        "named_payloads": named,
        "named_payloads_without_structure": no_struct,
        "unique_compounds_within_mw_cap": in_cap,
        "overlap_with_baseline": len(keys & base_keys),
        "new_compounds": len(keys - base_keys),
        "licence": sorted(set(df["source_license"].dropna())) if "source_license" in df.columns else None,
        "_keys": keys,
    }


def describe_property_table(name, path, base_keys):
    """B 类：分子属性表。不增加配方记录。"""
    if not path.is_file():
        return {"status": "尚未抽取", "path": str(path.relative_to(ROOT))}
    df = pd.read_csv(path, low_memory=False)
    if "inchikey" not in df.columns:
        return {
            "status": "列缺失",
            "path": str(path.relative_to(ROOT)),
            "note": "没有 inchikey 列，无法连接",
        }
    keys = key_set(df["inchikey"])
    by_type = {}
    if "coefficient_type" in df.columns:
        for t, g in df.groupby("coefficient_type"):
            by_type[str(t)] = {
                "records": int(len(g)),
                "unique_compounds": len(key_set(g["inchikey"])),
            }
    experimental = None
    if "value_origin" in df.columns:
        experimental = int((df["value_origin"] == "experimental").sum())
    return {
        "status": "已抽取",
        "path": str(path.relative_to(ROOT)),
        "records": int(len(df)),
        "records_experimental": experimental,
        "unique_compounds": len(keys),
        "by_coefficient_type": by_type or None,
        # 决定性的数字：能连上现有配方记录的化合物数
        "connectable_to_baseline": len(keys & base_keys),
        "not_connectable": len(keys - base_keys),
        "licence": sorted(set(df["source_license"].dropna())) if "source_license" in df.columns else None,
        "_keys": keys,
    }


def main() -> int:
    if not BASELINE.is_file():
        print(f"找不到基线文件 {BASELINE.relative_to(ROOT)}")
        return 1

    sm = load_baseline()
    base_all = key_set(sm["inchikey"])
    in_cap = sm[sm["mw"] <= MW_CAP]
    base_cap = key_set(in_cap["inchikey"])

    print("=" * 72)
    print("基线（现有小分子子集）")
    print("=" * 72)
    print(f"记录数（无 MW 上限）        {len(sm)}")
    print(f"记录数（MW <= {MW_CAP:.0f} Da）     {len(in_cap)}")
    print(f"唯一化合物（InChIKey）      {len(base_all)}")
    print(f"唯一化合物（MW <= {MW_CAP:.0f}）    {len(base_cap)}")
    print(f"唯一化合物（payload_smiles）{sm['payload_smiles'].nunique()}")
    n_scaf = len(key_set(sm["scaffold"]))
    n_empty_scaf = int((sm["scaffold"] == "").sum())
    print(f"唯一 Murcko 骨架（非空）    {n_scaf}")
    print(f"骨架为空的记录（链状分子）  {n_empty_scaf}")
    print(f"来源论文（唯一 DOI）        {sm['paper_doi'].nunique()}")
    print()
    print("两处口径说明，避免和已有文档的数字对不上：")
    print("1. InChIKey 口径会把同一化合物的不同 SMILES 写法合并，payload_smiles 口径不会。")
    print("   docs/data-inventory.md 报的 22 是后者；本脚本两个都报，当前两者相等。")
    print("2. 骨架数本脚本只数非空骨架。docs/data-inventory.md 报的 21 把空骨架也算作")
    print("   一个取值（Hydroxy-alpha-sanshool 是链状分子，Murcko 骨架为空）。")
    print()

    stats = {
        "baseline": {
            "records": int(len(sm)),
            "records_within_mw_cap": int(len(in_cap)),
            "unique_compounds_inchikey": len(base_all),
            "unique_compounds_inchikey_within_mw_cap": len(base_cap),
            "unique_compounds_smiles": int(sm["payload_smiles"].nunique()),
            "unique_scaffolds": len(key_set(sm["scaffold"])),
            "source_papers": int(sm["paper_doi"].nunique()),
        },
        "formulation_tables": {},
        "property_tables": {},
        "probe_tables": {},
    }

    # A 类
    print("=" * 72)
    print("A 类：配方表（贡献配方记录 + 化合物）")
    print("=" * 72)
    gained = set()
    any_a = False
    for name, path in FORMULATION_TABLES.items():
        r = describe_formulation_table(name, path, base_all)
        keys = r.pop("_keys", set())
        stats["formulation_tables"][name] = r
        print(f"\n{name}  [{r['status']}]  {r['path']}")
        if r["status"] != "已抽取":
            continue
        any_a = True
        gained |= keys
        print(f"  记录数                  {r['records']}")
        print(f"  载荷（按名字）          {len(r['named_payloads'])}  {r['named_payloads']}")
        print(f"  唯一化合物（按结构）    {r['unique_compounds']}")
        if r["named_payloads_without_structure"]:
            print(f"    其中无 SMILES 的      {r['named_payloads_without_structure']}")
            print(f"    -> 这些载荷无法参与按化合物分组的建模，不计入下面的合并数")
        if r["unique_compounds_within_mw_cap"] is not None:
            print(f"  唯一化合物（MW 上限内） {r['unique_compounds_within_mw_cap']}")
        print(f"  与基线重叠              {r['overlap_with_baseline']}")
        print(f"  新增化合物              {r['new_compounds']}")
        print(f"  授权                    {r['licence']}")
    if not any_a:
        print("\n（尚无已抽取的配方表）")

    combined = base_all | gained
    print()
    print("-" * 72)
    print(f"合并后唯一化合物数：{len(base_all)} -> {len(combined)}  （净增 {len(combined) - len(base_all)}）")
    print("-" * 72)
    stats["combined"] = {
        "unique_compounds_before": len(base_all),
        "unique_compounds_after": len(combined),
        "net_gain": len(combined) - len(base_all),
    }

    # B 类
    print()
    print("=" * 72)
    print("B 类：分子属性表（不增加配方记录，单独报可连接数）")
    print("=" * 72)
    any_b = False
    for name, path in PROPERTY_TABLES.items():
        r = describe_property_table(name, path, base_all)
        r.pop("_keys", None)
        stats["property_tables"][name] = r
        print(f"\n{name}  [{r['status']}]  {r['path']}")
        if r["status"] != "已抽取":
            continue
        any_b = True
        print(f"  记录数                  {r['records']}")
        if r["records_experimental"] is not None:
            print(f"  其中实测值              {r['records_experimental']}")
        print(f"  唯一化合物              {r['unique_compounds']}")
        if r["by_coefficient_type"]:
            for t, v in sorted(r["by_coefficient_type"].items()):
                print(f"    {t:<12} 记录 {v['records']:<6} 化合物 {v['unique_compounds']}")
        print(f"  **能连上现有配方记录**  {r['connectable_to_baseline']}  <- 决定性数字")
        print(f"  连不上的化合物          {r['not_connectable']}")
        print(f"  授权                    {r['licence']}")
    if not any_b:
        print("\n（尚无已抽取的分子属性表）")

    # C 类
    print()
    print("=" * 72)
    print("C 类：增补表（给已有记录补字段，不增加记录也不增加化合物）")
    print("=" * 72)
    stats["enrichment_tables"] = {}
    for name, path in ENRICHMENT_TABLES.items():
        if not path.is_file():
            stats["enrichment_tables"][name] = {"status": "尚未抽取", "path": str(path.relative_to(ROOT))}
            print(f"\n{name}  [尚未抽取]  {path.relative_to(ROOT)}")
            continue
        df = pd.read_csv(path, low_memory=False)
        linked = int(df["linked_to_repo"].sum()) if "linked_to_repo" in df.columns else None
        newcols = [c for c in df.columns
                   if c not in ("row_id", "source_doi", "source_license", "source_attribution",
                                "source_location", "linked_to_repo", "name_matches_repo")
                   and not c.startswith(("repo_", "yanes_"))]
        r = {
            "status": "已抽取",
            "path": str(path.relative_to(ROOT)),
            "records": int(len(df)),
            "linked_to_repo_records": linked,
            "new_unique_compounds": 0,
            "new_formulation_records": 0,
            "added_columns": newcols,
            "licence": sorted(set(df["source_license"].dropna())) if "source_license" in df.columns else None,
        }
        stats["enrichment_tables"][name] = r
        print(f"\n{name}  [已抽取]  {r['path']}")
        print(f"  记录数                  {r['records']}")
        if linked is not None:
            print(f"  连上仓库现有记录的      {linked}")
        print(f"  新增唯一化合物          0")
        print(f"  新增配方记录            0")
        print(f"  给现有记录补的字段      {len(newcols)} 列")
        print(f"  授权                    {r['licence']}")

    # 探针集
    print()
    print("=" * 72)
    print("探针集（不进训练集，不计入上面任何统计）")
    print("=" * 72)
    for name, path in PROBE_TABLES.items():
        if not path.is_file():
            stats["probe_tables"][name] = {"status": "尚未抽取", "path": str(path.relative_to(ROOT))}
            print(f"\n{name}  [尚未抽取]  {path.relative_to(ROOT)}")
            continue
        df = pd.read_csv(path, low_memory=False)
        col = "payload_inchikey" if "payload_inchikey" in df.columns else "inchikey"
        keys = key_set(df[col]) if col in df.columns else set()
        scafs = key_set(df["scaffold"]) if "scaffold" in df.columns else set()
        named = (
            sorted(set(df["payload_type"].dropna().astype(str).str.strip()) - {""})
            if "payload_type" in df.columns else []
        )
        n_quant = (
            int(df["encapsulation_efficiency_pct"].notna().sum())
            if "encapsulation_efficiency_pct" in df.columns else None
        )
        n_fail = (
            int((df["formation_ok"] == False).sum())  # noqa: E712
            if "formation_ok" in df.columns else None
        )
        r = {
            "status": "已抽取",
            "path": str(path.relative_to(ROOT)),
            "records": int(len(df)),
            "named_payloads": named,
            "unique_compounds": len(keys),
            "unique_scaffolds": len(scafs) or None,
            "records_with_quantitative_ee": n_quant,
            "records_failed_to_form": n_fail,
        }
        stats["probe_tables"][name] = r
        print(f"\n{name}  [已抽取]  {r['path']}")
        print(f"  记录数                  {r['records']}")
        print(f"  载荷（按名字）          {len(named)}  {named}")
        print(f"  唯一化合物（按结构）    {r['unique_compounds']}")
        if n_quant is not None:
            print(f"  其中有定量 EE 的        {n_quant}")
        if n_fail:
            print(f"  载药失败的记录          {n_fail}  （定性失败，不是缺测）")
        if r["unique_scaffolds"]:
            print(f"  唯一骨架                {r['unique_scaffolds']}")
        # 探针集的用途是检验「同骨架内的小修饰能否被模型分辨」。这要求
        # 多个化合物 + 各自的结构。两个条件都不满足时必须说清楚，否则这张表
        # 会被当成能用的探针集
        if r["unique_compounds"] <= 1:
            print()
            print("  **这个探针集不能用于原定用途。** 原定用途是检验同骨架内的小修饰")
            print("  能否被模型分辨，这需要多个化合物、每个都有结构和定量 EE。实际：")
            print(f"    有结构（SMILES）的化合物   {r['unique_compounds']}")
            print(f"    有定量 EE 的化合物         {len([n for n in named if 'uncertain' not in n])}")
            print("  所以它只能当作「单载荷下变配方」的区组用，和 Jaki 2026 同类。")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print()
    print(f"已写入 {OUT_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
