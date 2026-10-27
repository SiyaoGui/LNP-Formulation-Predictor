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
FORMULATION_TABLES = {
    "Yanes 2025": ROOT / "data" / "processed" / "formulations_yanes2025.csv",
    "Jaki 2026": ROOT / "data" / "processed" / "formulations_jaki2026.csv",
}
# B 类：分子属性表。列名按 docs/schema-partition-coefficients.md
PROPERTY_TABLES = {
    "Khawar 2022": ROOT / "data" / "processed" / "partition_coefficients.csv",
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
    return {
        "status": "已抽取",
        "path": str(path.relative_to(ROOT)),
        "records": int(len(df)),
        "unique_compounds": len(keys),
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
        print(f"  唯一化合物              {r['unique_compounds']}")
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
        r = {
            "status": "已抽取",
            "path": str(path.relative_to(ROOT)),
            "records": int(len(df)),
            "unique_compounds": len(keys),
            "unique_scaffolds": len(scafs) or None,
        }
        stats["probe_tables"][name] = r
        print(f"\n{name}  [已抽取]  {r['path']}")
        print(f"  记录数                  {r['records']}")
        print(f"  唯一化合物              {r['unique_compounds']}")
        if r["unique_scaffolds"]:
            print(f"  唯一骨架                {r['unique_scaffolds']}")
            if r["unique_scaffolds"] == 1:
                print("  注意：骨架数为 1，符合预期（衍生物序列），只能检验同骨架内分辨力")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print()
    print(f"已写入 {OUT_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
