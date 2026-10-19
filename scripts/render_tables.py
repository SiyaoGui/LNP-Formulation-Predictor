"""把 metrics.json 渲染成 markdown 表格，供建模文件夹的 README 直接引用。

用法:
    python3 scripts/render_tables.py --dir modeling/2026-10-19_smallmol-baseline

表格由脚本生成而不是手抄，避免转抄错误。产出写到 <dir>/results_tables.md，
README 里的数字应与这个文件一致（README 负责解释，表格负责数字）。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

PRETTY = {
    "b0": "B0 常数基线",
    "b1": "B1 Tanimoto 最近邻",
    "ridge@full": "Ridge（完整特征）",
    "rf@full": "随机森林（完整特征）",
    "hgb@full": "梯度提升树（完整特征）",
    "ridge@b2_formulation_only": "B2 Ridge（无分子特征）",
    "hgb@b2_formulation_only": "B2 梯度提升树（无分子特征）",
    "ridge@b3_molecule_only": "B3 Ridge（只有分子特征）",
    "hgb@b3_molecule_only": "B3 梯度提升树（只有分子特征）",
    "logreg@b3_molecule_only": "逻辑回归（只有分子特征）",
    "rf@b3_molecule_only": "随机森林（只有分子特征）",
}
SCHEME_NAME = {
    "S1": "S1 按化合物分组",
    "S2": "S2 按骨架分组",
    "S3": "S3 按论文分组",
    "S4": "S4 留一化合物",
}
ORDER = list(PRETTY)


def fmt(v, nd=3):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    return f"{v:.{nd}f}"


def t1_tables(m: dict) -> list[str]:
    out = []
    t1 = m.get("t1", {})
    for scheme in ("S1", "S2", "S3", "S4"):
        if scheme not in t1:
            continue
        rows = []
        for key in ORDER:
            rec = t1[scheme].get(key)
            if not rec or not rec["summary"].get("mae_log"):
                continue
            s = rec["summary"]
            ci = rec.get("mae_log_ci_headline", {})
            rows.append(
                {
                    "模型": PRETTY.get(key, key),
                    "MAE_log 均值": fmt(s["mae_log"]["mean"], 4),
                    "跨种子 sd": fmt(s["mae_log"]["sd"], 4),
                    "跨种子范围": f'{fmt(s["mae_log"]["min"],3)} – {fmt(s["mae_log"]["max"],3)}',
                    "95% CI": f'[{fmt(ci.get("lo"),3)}, {fmt(ci.get("hi"),3)}]',
                    "R² 合并": fmt(s["r2_pooled"]["mean"], 3) if s.get("r2_pooled") else "—",
                    "平均差几倍": fmt(s["median_fold_error"]["mean"], 2)
                    if s.get("median_fold_error")
                    else "—",
                    "MAE(nm)": fmt(s["mae_nm"]["mean"], 1) if s.get("mae_nm") else "—",
                    "Spearman": fmt(s["spearman"]["mean"], 3) if s.get("spearman") else "—",
                }
            )
        if rows:
            out.append(f"\n### T1 · {SCHEME_NAME[scheme]}\n")
            out.append(pd.DataFrame(rows).to_markdown(index=False))
    return out


def t1_baseline_tables(m: dict) -> list[str]:
    out = ["\n### T1 · 与必须打败的基线的配对比较\n"]
    out.append(
        "ΔMAE_log 正数表示模型比基线好。判定看 95% CI 是否跨过 0（协议第十节），"
        "不是看点估计大小。\n"
    )
    rows = []
    for scheme in ("S1", "S2", "S3", "S4"):
        comp = m.get("t1", {}).get(scheme, {}).get("_vs_baselines", {})
        for key, rec in comp.items():
            model, base = key.rsplit("_vs_", 1)
            rows.append(
                {
                    "划分": scheme,
                    "模型": PRETTY.get(model, model),
                    "对比基线": base.upper(),
                    "ΔMAE_log 均值": fmt(rec["delta_mae_log_mean"], 4),
                    "95% CI": f'[{fmt(rec["ci_headline"]["lo"],4)}, {fmt(rec["ci_headline"]["hi"],4)}]',
                    "CI 排除 0 的种子数": f'{rec["n_seeds_ci_excludes_zero"]}/{len(rec["delta_mae_log_point_per_seed"])}',
                    "跨种子符号一致": "是" if rec["sign_consistent_across_seeds"] else "否",
                    "打败基线": "**是**" if rec["beats_baseline"] else "否",
                }
            )
    if rows:
        out.append(pd.DataFrame(rows).to_markdown(index=False))
    return out


def lc_table(d: Path, m: dict) -> list[str]:
    f = d / "learning_curve.csv"
    if not f.exists():
        return []
    lc = pd.read_csv(f)
    if lc.empty:
        return []
    g = (
        lc.groupby(["fraction", "approx_train_compounds", "model"])
        .mae_log.agg(["mean", "std", "min", "max"])
        .reset_index()
    )
    piv = g.pivot_table(index=["fraction", "approx_train_compounds"], columns="model",
                        values=["mean", "min", "max"])
    rows = []
    for (frac, ncomp), r in piv.iterrows():
        rows.append(
            {
                "训练数据比例": f"{int(frac*100)}%",
                "训练集化合物数（近似）": int(ncomp),
                "梯度提升树 MAE_log": fmt(r.get(("mean", "hgb")), 4),
                "梯度提升树 跨种子范围": f'{fmt(r.get(("min","hgb")),3)} – {fmt(r.get(("max","hgb")),3)}',
                "常数基线 MAE_log": fmt(r.get(("mean", "b0")), 4),
            }
        )
    return ["\n### 学习曲线（按训练集化合物数，不是行数）\n", pd.DataFrame(rows).to_markdown(index=False)]


def t3_tables(m: dict) -> list[str]:
    t3 = m.get("t3", {})
    out = []
    for scheme in ("S1", "S2", "S3", "S4"):
        if scheme not in t3:
            continue
        rows = []
        for key in ORDER:
            rec = t3[scheme].get(key)
            if not rec or not rec["summary"].get("balanced_accuracy"):
                continue
            s = rec["summary"]
            ci = rec.get("balanced_accuracy_ci_headline", {})
            rows.append(
                {
                    "模型": PRETTY.get(key, key),
                    "balanced accuracy": fmt(s["balanced_accuracy"]["mean"], 3),
                    "跨种子 sd": fmt(s["balanced_accuracy"]["sd"], 3),
                    "跨种子范围": f'{fmt(s["balanced_accuracy"]["min"],3)} – {fmt(s["balanced_accuracy"]["max"],3)}',
                    "95% CI": f'[{fmt(ci.get("lo"),3)}, {fmt(ci.get("hi"),3)}]',
                    "macro F1": fmt(s["macro_f1"]["mean"], 3) if s.get("macro_f1") else "—",
                    "普通准确率": fmt(s["accuracy"]["mean"], 3) if s.get("accuracy") else "—",
                }
            )
        if rows:
            out.append(f"\n### T3 · {SCHEME_NAME[scheme]}（4 类，多数类占 45%）\n")
            out.append(pd.DataFrame(rows).to_markdown(index=False))
    rows = []
    for scheme in ("S1", "S2", "S3", "S4"):
        for key, rec in t3.get(scheme, {}).get("_vs_baselines", {}).items():
            model, base = key.rsplit("_vs_", 1)
            rows.append(
                {
                    "划分": scheme,
                    "模型": PRETTY.get(model, model),
                    "对比基线": base.upper(),
                    "Δbalanced accuracy": fmt(rec["delta_mean"], 4),
                    "95% CI": f'[{fmt(rec["ci_headline"]["lo"],4)}, {fmt(rec["ci_headline"]["hi"],4)}]',
                    "打败基线": "**是**" if rec["beats_baseline"] else "否",
                }
            )
    if rows:
        out.append("\n### T3 · 与基线的配对比较\n")
        out.append(pd.DataFrame(rows).to_markdown(index=False))
    return out


def t2_tables(m: dict) -> list[str]:
    t2 = m.get("t2", {})
    out = []
    for scheme, models in t2.items():
        rows = []
        for key in ORDER:
            rec = models.get(key)
            if not rec or not rec["summary"].get("aitchison_mean"):
                continue
            s = rec["summary"]
            rows.append(
                {
                    "模型": PRETTY.get(key, key),
                    "Aitchison 距离": fmt(s["aitchison_mean"]["mean"], 3),
                    "跨种子范围": f'{fmt(s["aitchison_mean"]["min"],3)} – {fmt(s["aitchison_mean"]["max"],3)}',
                    "整体 MAE（百分点）": fmt(s["mae_pp_overall"]["mean"], 2),
                    "helper MAE（百分点）": fmt(s["mae_pp_helper"]["mean"], 2),
                    "sterol MAE（百分点）": fmt(s["mae_pp_sterol"]["mean"], 2),
                    "PEG MAE（百分点）": fmt(s["mae_pp_peg"]["mean"], 2),
                }
            )
        if rows:
            out.append(f"\n### T2 · 脂质组成（{scheme}，8 个化合物，27 个配方）\n")
            out.append(pd.DataFrame(rows).to_markdown(index=False))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="modeling/2026-10-19_smallmol-baseline")
    args = ap.parse_args()
    d = ROOT / args.dir
    m = json.loads((d / "metrics.json").read_text(encoding="utf-8"))

    parts = [
        "# 结果表（由 scripts/render_tables.py 从 metrics.json 生成，不要手改）\n",
        f"协议：{m.get('protocol')}\n",
        f"种子：{m.get('seeds')}　划分：{m.get('schemes')}　bootstrap 次数：{m.get('n_bootstrap')}\n",
        f"特征集：{json.dumps(m.get('feature_sets'), ensure_ascii=False)}\n",
        f"指纹位数网格 k：{m.get('fp_k_grid')}（k=0 表示不用指纹）\n",
        f"版本：{json.dumps(m.get('versions'), ensure_ascii=False)}\n",
    ]
    parts += t1_tables(m)
    parts += t1_baseline_tables(m)
    parts += lc_table(d, m)
    parts += t3_tables(m)
    parts += t2_tables(m)
    (d / "results_tables.md").write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"写出 {d / 'results_tables.md'}")


if __name__ == "__main__":
    main()
