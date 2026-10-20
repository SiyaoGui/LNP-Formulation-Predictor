"""第四步建模：按 docs/evaluation-protocol.md 执行，不中途改评估方式。

用法:
    python3 scripts/run_modeling.py --config configs/smallmol_baseline.yaml \
        --out modeling/2026-10-19_smallmol-baseline

跑的内容:
  T1 粒径回归   基线 b0/b1 -> ridge -> rf -> hgb；诊断基线 b2(无分子特征)/b3(只有分子特征)
                划分 S1/S2/S3/S4，种子 0-4，cluster bootstrap 95% CI，嵌套调参
  T2 脂质组成   探针：b0(成分中心)/b1/ridge/hgb，ILR 空间建模，原空间评估
  T3 类别组合   探针：b0(多数类)/b1/logreg/rf/hgb
  学习曲线      按训练集化合物数的 20/40/60/80/100%（S1，5 种子）

产出: metrics.json、oof_predictions.csv、learning_curve.csv、config_used.yaml
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lnp import evaluation as E  # noqa: E402

# 特征集定义。lipid 指纹（helper/sterol 各 512 位，39% 行缺失）不进模型：
# 58 行的训练折里无法可靠筛选 1024 个高缺失的二值位。脂质结构仍由 24 个脂质描述符
# 和 7 个派生标记表示。这个决定在跑任何模型之前写定（见 modeling README）。
def feature_sets(X: pd.DataFrame) -> dict:
    payload_fp = [c for c in X.columns if c.startswith("payload_fp_")]
    m_desc = [c for c in X.columns if c.startswith("payload_") and c not in payload_fp]
    lipid_fp = [c for c in X.columns if "_fp_" in c and c not in payload_fp]
    plain_all = [c for c in X.columns if "_fp_" not in c]
    f_and_p = [c for c in plain_all if c not in m_desc]
    return {
        "full": {"plain": plain_all, "fp": payload_fp},
        "b2_formulation_only": {"plain": f_and_p, "fp": []},
        "b3_molecule_only": {"plain": m_desc, "fp": payload_fp},
        "_excluded_lipid_fp": lipid_fp,
    }


def summarize(per_seed: list[dict], keys: list[str]) -> dict:
    out = {}
    for k in keys:
        vals = [d[k] for d in per_seed if d.get(k) is not None and np.isfinite(d[k])]
        if not vals:
            out[k] = None
            continue
        out[k] = {
            "mean": round(float(np.mean(vals)), 4),
            "sd": round(float(np.std(vals, ddof=1)), 4) if len(vals) > 1 else 0.0,
            "min": round(float(np.min(vals)), 4),
            "max": round(float(np.max(vals)), 4),
            "per_seed": [round(float(v), 4) for v in vals],
        }
    return out


def ci_of(oof: E.OofResult, metric_fn, key: str, seed: int) -> dict:
    def stat(idx):
        return metric_fn(oof.y_true[idx], oof.y_pred[idx])[key]

    return E.cluster_bootstrap_ci(stat, oof.groups, seed=seed)


def paired_ci(oof_a: E.OofResult, oof_b: E.OofResult, metric_fn, key: str, seed: int) -> dict:
    """a 相对 b 的改善（b 的指标 - a 的指标），正数表示 a 更好。两者用同一批样本。"""
    order_a = np.argsort(oof_a.index)
    order_b = np.argsort(oof_b.index)
    ya, pa, g = oof_a.y_true[order_a], oof_a.y_pred[order_a], oof_a.groups[order_a]
    yb, pb = oof_b.y_true[order_b], oof_b.y_pred[order_b]
    assert np.array_equal(np.asarray(ya), np.asarray(yb)), "配对样本不一致（两个模型的 out-of-fold 样本必须相同）"

    def stat(idx):
        return metric_fn(yb[idx], pb[idx])[key] - metric_fn(ya[idx], pa[idx])[key]

    ci = E.cluster_bootstrap_ci(stat, g, seed=seed)
    ci["point"] = round(float(stat(np.arange(len(ya)))), 4)
    ci["excludes_zero"] = bool(
        np.isfinite(ci["lo"]) and np.isfinite(ci["hi"]) and (ci["lo"] > 0 or ci["hi"] < 0)
    )
    return ci


# --------------------------------------------------------------------------- #
def run_t1(proc: Path, out: Path, results: dict, quick: bool, only_schemes=None) -> pd.DataFrame:
    units = pd.read_parquet(proc / "units_t1.parquet")
    X = pd.read_parquet(proc / "features_t1.parquet")
    y = units["target"].to_numpy(float)
    fs = feature_sets(X)
    sim = E.payload_similarity(units)

    combos = [("b0", None), ("b1", None), ("ridge", "full"), ("rf", "full"), ("hgb", "full")]
    combos += [
        ("ridge", "b2_formulation_only"),
        ("hgb", "b2_formulation_only"),
        ("ridge", "b3_molecule_only"),
        ("hgb", "b3_molecule_only"),
    ]
    schemes = only_schemes or (("S1",) if quick else E.SCHEMES)
    seeds = (0,) if quick else E.SEEDS
    metric_keys = ["mae_log", "rmse_log", "r2_pooled", "median_fold_error", "mae_nm", "spearman"]

    oof_rows = []
    store: dict = {}
    for scheme in schemes:
        for model, fset in combos:
            label = model if fset is None else f"{model}@{fset}"
            per_seed, cis = [], []
            for seed in seeds:
                splits = E.make_splits(units, scheme, seed)
                cols = fs[fset] if fset else {"plain": [], "fp": []}
                t0 = time.time()
                oof = E.run_oof(
                    X, y, units, splits, model, cols["plain"], cols["fp"], "regression", seed, sim
                )
                m = E.regression_metrics(oof.y_true, oof.y_pred)
                m["_fit_seconds"] = round(time.time() - t0, 1)
                per_seed.append(m)
                cis.append(ci_of(oof, E.regression_metrics, "mae_log", seed))
                store[(scheme, label, seed)] = oof
                if scheme == "S1":
                    for i, idx in enumerate(oof.index):
                        oof_rows.append(
                            {
                                "scheme": scheme,
                                "model": label,
                                "seed": seed,
                                "unit_index": int(idx),
                                "y_true_log10": float(oof.y_true[i]),
                                "y_pred_log10": float(oof.y_pred[i]),
                                "compound": units.payload_type.iloc[idx],
                                "paper_doi": units.paper_doi.iloc[idx],
                                "is_probe": bool(units.is_probe.iloc[idx]),
                            }
                        )
                print(
                    f"  T1 {scheme} {label:28s} seed{seed} MAE_log={m['mae_log']:.4f} "
                    f"R2={m['r2_pooled']:+.3f} ({m['_fit_seconds']}s)",
                    flush=True,
                )
            results["t1"].setdefault(scheme, {})[label] = {
                "summary": summarize(per_seed, metric_keys),
                "mae_log_ci_per_seed": cis,
                "mae_log_ci_headline": {
                    "lo": round(float(np.median([c["lo"] for c in cis])), 4),
                    "hi": round(float(np.median([c["hi"] for c in cis])), 4),
                },
                "n_units": int(len(units)),
                "fold_sizes_seed0": store[(scheme, label, seeds[0])].fold_sizes,
                "n_folds_fallback_to_constant": {
                    f"seed{s}": store[(scheme, label, s)].n_fallback for s in seeds
                },
                "best_params_seed0": [
                    {k: (v if not isinstance(v, (np.integer, np.floating)) else float(v)) for k, v in p.items()}
                    for p in store[(scheme, label, seeds[0])].best_params
                ],
            }

    # 与基线的配对比较
    for scheme in schemes:
        comp = {}
        for model, fset in combos:
            label = model if fset is None else f"{model}@{fset}"
            if label in ("b0", "b1"):
                continue
            for base in ("b0", "b1"):
                per_seed = [
                    paired_ci(
                        store[(scheme, label, s)],
                        store[(scheme, base, s)],
                        E.regression_metrics,
                        "mae_log",
                        s,
                    )
                    for s in seeds
                ]
                signs = [np.sign(p["point"]) for p in per_seed]
                comp[f"{label}_vs_{base}"] = {
                    "delta_mae_log_point_per_seed": [p["point"] for p in per_seed],
                    "delta_mae_log_mean": round(float(np.mean([p["point"] for p in per_seed])), 4),
                    "ci_headline": {
                        "lo": round(float(np.median([p["lo"] for p in per_seed])), 4),
                        "hi": round(float(np.median([p["hi"] for p in per_seed])), 4),
                    },
                    "n_seeds_ci_excludes_zero": int(sum(p["excludes_zero"] for p in per_seed)),
                    "sign_consistent_across_seeds": bool(len(set(signs)) == 1),
                    "beats_baseline": bool(
                        len(set(signs)) == 1
                        and signs[0] > 0
                        and sum(p["excludes_zero"] for p in per_seed) == len(per_seed)
                    ),
                }
        results["t1"].setdefault(scheme, {})["_vs_baselines"] = comp

    return pd.DataFrame(oof_rows)


def run_learning_curve(proc: Path, results: dict, quick: bool) -> pd.DataFrame:
    """按训练集化合物数的比例，不是行数（协议 10.2 节）。"""
    units = pd.read_parquet(proc / "units_t1.parquet")
    X = pd.read_parquet(proc / "features_t1.parquet")
    y = units["target"].to_numpy(float)
    fs = feature_sets(X)
    groups = units["group_compound"].to_numpy()
    fractions = [0.2, 0.4, 0.6, 0.8, 1.0]
    seeds = (0,) if quick else E.SEEDS
    rows = []
    for frac in fractions:
        for seed in seeds:
            rng = np.random.default_rng(1000 + seed)
            splits = E.make_splits(units, "S1", seed)
            for model in ("b0", "hgb"):
                preds, truths, grps = [], [], []
                n_fallback = 0
                for tr, te in splits:
                    tr_groups = np.unique(groups[tr])
                    k = max(2, int(round(len(tr_groups) * frac)))
                    keep = set(rng.choice(tr_groups, size=min(k, len(tr_groups)), replace=False))
                    tr_sub = np.array([i for i in tr if groups[i] in keep])
                    if len(tr_sub) < 5:
                        continue
                    if model == "b0":
                        p = E.baseline_constant(y[tr_sub], len(te), "regression")
                    else:
                        pipe, grid = E.model_space("hgb", fs["full"]["plain"], fs["full"]["fp"], seed)
                        try:
                            fitted = E.fit_nested(
                                pipe, grid, X.iloc[tr_sub], y[tr_sub], groups[tr_sub], "regression", seed
                            )
                            p = fitted.predict(X.iloc[te])
                        except Exception:
                            # 训练子集太小, 剔掉常量列后无可用特征 -> 降级成常数预测并计数
                            n_fallback += 1
                            p = E.baseline_constant(y[tr_sub], len(te), "regression")
                    preds.append(p)
                    truths.append(y[te])
                    grps.append(groups[te])
                if not preds:
                    continue
                yt, yp = np.concatenate(truths), np.concatenate(preds)
                m = E.regression_metrics(yt, yp)
                n_comp = int(round(len(np.unique(groups)) * 0.8 * frac))
                rows.append(
                    {
                        "fraction": frac,
                        "approx_train_compounds": n_comp,
                        "seed": seed,
                        "model": model,
                        "mae_log": round(m["mae_log"], 4),
                        "r2_pooled": round(m["r2_pooled"], 4),
                        "n_test": len(yt),
                        "n_folds_fallback_to_constant": n_fallback,
                    }
                )
                print(f"  LC frac={frac} seed{seed} {model:4s} MAE_log={m['mae_log']:.4f}", flush=True)
    lc = pd.DataFrame(rows)
    if not lc.empty:
        agg = (
            lc.groupby(["fraction", "approx_train_compounds", "model"])
            .mae_log.agg(["mean", "std", "min", "max"])
            .reset_index()
        )
        results["learning_curve"] = agg.to_dict(orient="records")
    return lc


def run_t3(proc: Path, results: dict, quick: bool, only_schemes=None) -> pd.DataFrame:
    units = pd.read_parquet(proc / "units_t3.parquet")
    X = pd.read_parquet(proc / "features_t3.parquet")
    y = units["target"].to_numpy()
    fs = feature_sets(X)
    sim = E.payload_similarity(units)
    schemes = only_schemes or (("S1",) if quick else ("S1", "S2", "S3", "S4"))
    seeds = (0,) if quick else E.SEEDS
    keys = ["balanced_accuracy", "macro_f1", "accuracy"]
    rows = []
    store = {}
    combos = [("b0", None), ("b1", None), ("logreg", "b3_molecule_only"), ("rf", "b3_molecule_only"), ("hgb", "b3_molecule_only")]
    for scheme in schemes:
        for model, fset in combos:
            label = model if fset is None else f"{model}@{fset}"
            per_seed, cis = [], []
            for seed in seeds:
                splits = E.make_splits(units, scheme, seed)
                cols = fs[fset] if fset else {"plain": [], "fp": []}
                oof = E.run_oof(
                    X, y, units, splits, model, cols["plain"], cols["fp"], "classification", seed, sim
                )
                m = E.classification_metrics(oof.y_true, oof.y_pred)
                per_seed.append(m)
                cis.append(
                    E.cluster_bootstrap_ci(
                        lambda idx: E.classification_metrics(oof.y_true[idx], oof.y_pred[idx])[
                            "balanced_accuracy"
                        ],
                        oof.groups,
                        seed=seed,
                    )
                )
                store[(scheme, label, seed)] = oof
                for i, idx in enumerate(oof.index):
                    rows.append(
                        {
                            "scheme": scheme,
                            "model": label,
                            "seed": seed,
                            "unit_index": int(idx),
                            "y_true": oof.y_true[i],
                            "y_pred": oof.y_pred[i],
                            "compound": units.payload_type.iloc[idx],
                        }
                    )
                print(f"  T3 {scheme} {label:24s} seed{seed} balacc={m['balanced_accuracy']:.3f}", flush=True)
            results["t3"].setdefault(scheme, {})[label] = {
                "summary": summarize(per_seed, keys),
                "balanced_accuracy_ci_headline": {
                    "lo": round(float(np.median([c["lo"] for c in cis])), 4),
                    "hi": round(float(np.median([c["hi"] for c in cis])), 4),
                },
            }
        comp = {}
        for model, fset in combos:
            label = model if fset is None else f"{model}@{fset}"
            if label in ("b0", "b1"):
                continue
            for base in ("b0", "b1"):
                per_seed = [
                    paired_ci(
                        store[(scheme, label, s)],
                        store[(scheme, base, s)],
                        lambda a, b: {
                            "neg_balacc": -E.classification_metrics(a, b)["balanced_accuracy"]
                        },
                        "neg_balacc",
                        s,
                    )
                    for s in seeds
                ]
                signs = [np.sign(p["point"]) for p in per_seed]
                comp[f"{label}_vs_{base}"] = {
                    "delta_balanced_accuracy_per_seed": [p["point"] for p in per_seed],
                    "delta_mean": round(float(np.mean([p["point"] for p in per_seed])), 4),
                    "ci_headline": {
                        "lo": round(float(np.median([p["lo"] for p in per_seed])), 4),
                        "hi": round(float(np.median([p["hi"] for p in per_seed])), 4),
                    },
                    "n_seeds_ci_excludes_zero": int(sum(p["excludes_zero"] for p in per_seed)),
                    "sign_consistent_across_seeds": bool(len(set(signs)) == 1),
                    "beats_baseline": bool(
                        len(set(signs)) == 1
                        and signs[0] > 0
                        and sum(p["excludes_zero"] for p in per_seed) == len(per_seed)
                    ),
                }
        results["t3"].setdefault(scheme, {})["_vs_baselines"] = comp
    results["t3"]["class_counts"] = pd.Series(y).value_counts().to_dict()
    return pd.DataFrame(rows)


def run_t2(proc: Path, results: dict, quick: bool) -> pd.DataFrame:
    """T2 探针：ILR 空间建模，原空间评估。协议 1.3 节。"""
    units = pd.read_parquet(proc / "units_t2.parquet")
    X = pd.read_parquet(proc / "features_t2.parquet")
    pct_cols = ["target_helper_lipid_pct", "target_sterol_lipid_pct", "target_peg_lipid_pct"]
    Y_pct = units[pct_cols].to_numpy(float)
    Z = E.ilr(Y_pct)  # 2 维 ILR 坐标
    fs = feature_sets(X)
    sim = E.payload_similarity(units)
    keys = ["aitchison_mean", "mae_pp_overall", "mae_pp_helper", "mae_pp_sterol", "mae_pp_peg"]
    seeds = (0,) if quick else E.SEEDS
    rows = []
    store = {}
    combos = [("b0", None), ("b1", None), ("ridge", "b3_molecule_only"), ("hgb", "b3_molecule_only")]
    for scheme in ("S4",):  # 8 个化合物，协议第五节规定 T2 用 LOCO
        for model, fset in combos:
            label = model if fset is None else f"{model}@{fset}"
            per_seed = []
            for seed in seeds:
                splits = E.make_splits(units, scheme, seed)
                cols = fs[fset] if fset else {"plain": [], "fp": []}
                if model == "b0":
                    # 成分中心：ILR 空间均值再逆变换（不是算术平均）
                    oof = E.run_oof(X, Z, units, splits, "b0", [], [], "multioutput", seed, sim)
                elif model == "b1":
                    oof = E.run_oof(X, Z, units, splits, "b1", [], [], "multioutput", seed, sim)
                else:
                    oof = E.run_oof(
                        X, Z, units, splits, model, cols["plain"], cols["fp"], "multioutput", seed, sim
                    )
                pred_pct = E.ilr_inv(oof.y_pred) * 100.0
                true_pct = E.ilr_inv(oof.y_true) * 100.0
                m = E.composition_metrics(true_pct, pred_pct)
                per_seed.append(m)
                store[(scheme, label, seed)] = (oof, true_pct, pred_pct)
                for i, idx in enumerate(oof.index):
                    rows.append(
                        {
                            "model": label,
                            "seed": seed,
                            "unit_index": int(idx),
                            "compound": units.payload_type.iloc[idx],
                            **{f"true_{c}": true_pct[i, j] for j, c in enumerate(["helper", "sterol", "peg"])},
                            **{f"pred_{c}": pred_pct[i, j] for j, c in enumerate(["helper", "sterol", "peg"])},
                        }
                    )
                print(
                    f"  T2 {scheme} {label:24s} seed{seed} aitchison={m['aitchison_mean']:.3f} "
                    f"mae_pp={m['mae_pp_overall']:.2f}",
                    flush=True,
                )
            results["t2"].setdefault(scheme, {})[label] = {"summary": summarize(per_seed, keys)}
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/smallmol_baseline.yaml")
    ap.add_argument("--out", default="modeling/2026-10-19_smallmol-baseline")
    ap.add_argument("--quick", action="store_true", help="只跑 S1 + seed 0，用于计时和调试")
    ap.add_argument("--tasks", default="t1,lc,t3,t2")
    ap.add_argument(
        "--schemes",
        default="",
        help="只跑指定划分（逗号分隔，如 S1,S2,S3）。分段跑是因为后台单条命令有 2 小时上限，"
        "全量 T1 的纯拟合时间约 102 分钟，加 bootstrap 会超。分段结果会合并进同一个 metrics.json",
    )
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    proc = ROOT / cfg["data"]["out_dir"]
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)

    import rdkit
    import sklearn

    X1 = pd.read_parquet(proc / "features_t1.parquet")
    fs = feature_sets(X1)
    only_schemes = tuple(s.strip() for s in args.schemes.split(",") if s.strip()) or None

    # 分段跑时把已有结果读回来合并，不覆盖（后台单条命令有 2 小时上限）
    existing = {}
    mj = out / "metrics.json"
    if mj.exists():
        existing = json.loads(mj.read_text(encoding="utf-8"))

    results = {
        "protocol": "docs/evaluation-protocol.md (frozen 2026-10-19, amended 2026-10-19 for T3)",
        "config": args.config,
        "quick_mode": args.quick,
        "seeds": list((0,) if args.quick else E.SEEDS),
        "schemes": list(("S1",) if args.quick else E.SCHEMES),
        "n_bootstrap": E.N_BOOTSTRAP,
        "feature_sets": {
            "full": {"n_plain": len(fs["full"]["plain"]), "n_fp": len(fs["full"]["fp"])},
            "b2_formulation_only": {"n_plain": len(fs["b2_formulation_only"]["plain"]), "n_fp": 0},
            "b3_molecule_only": {
                "n_plain": len(fs["b3_molecule_only"]["plain"]),
                "n_fp": len(fs["b3_molecule_only"]["fp"]),
            },
            "excluded_lipid_fingerprints": len(fs["_excluded_lipid_fp"]),
        },
        "fp_k_grid": list(E.FP_K_GRID),
        "versions": {
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "rdkit": rdkit.__version__,
            "scikit_learn": sklearn.__version__,
            "xgboost": "not installed (wheel download repeatedly interrupted); "
            "HistGradientBoostingRegressor used instead, same as previous round",
        },
        "t1": existing.get("t1", {}),
        "t2": existing.get("t2", {}),
        "t3": existing.get("t3", {}),
        "runs": existing.get("runs", []),
    }
    results["runs"].append(
        {"tasks": args.tasks, "schemes": list(only_schemes) if only_schemes else "all"}
    )

    tasks = [t.strip() for t in args.tasks.split(",")]
    t0 = time.time()

    def flush_metrics():
        results["total_runtime_seconds"] = round(time.time() - t0, 1)
        (out / "metrics.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )

    # 每跑完一段就落盘，后面哪一段出错也不会把前面的结果一起丢掉
    if "t1" in tasks:
        print("== T1 粒径回归", flush=True)
        sfx = "_" + "-".join(only_schemes) if only_schemes else ""
        run_t1(proc, out, results, args.quick, only_schemes).to_csv(
            out / f"oof_predictions_t1{sfx}.csv", index=False
        )
        flush_metrics()
    if "lc" in tasks:
        print("== 学习曲线", flush=True)
        run_learning_curve(proc, results, args.quick).to_csv(out / "learning_curve.csv", index=False)
        flush_metrics()
    if "t3" in tasks:
        print("== T3 类别组合分类", flush=True)
        sfx3 = "_" + "-".join(only_schemes) if only_schemes else ""
        run_t3(proc, results, args.quick, only_schemes).to_csv(
            out / f"oof_predictions_t3{sfx3}.csv", index=False
        )
        flush_metrics()
    if "t2" in tasks:
        print("== T2 脂质组成", flush=True)
        run_t2(proc, results, args.quick).to_csv(out / "oof_predictions_t2.csv", index=False)
        flush_metrics()

    flush_metrics()
    shutil.copy(ROOT / args.config, out / "config_used.yaml")
    shutil.copy(proc / "feature_manifest.json", out / "feature_manifest.json")
    print(f"\n写出 {out}/metrics.json  用时 {results['total_runtime_seconds']}s")


if __name__ == "__main__":
    main()
