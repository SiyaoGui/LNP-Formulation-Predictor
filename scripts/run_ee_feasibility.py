"""包封率可学性验证：按 docs/ee-feasibility-protocol.md 执行。

用法:
    python3 scripts/run_ee_feasibility.py --out modeling/2026-10-20_ee-feasibility

复用 lnp/evaluation.py（与第一轮粒径完全相同的划分逻辑、基线、嵌套调参、
cluster bootstrap），只换目标变量、分组键和特征块。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lnp import evaluation as E  # noqa: E402
from lnp import features as F  # noqa: E402
from lnp import subset as S  # noqa: E402

DEDUP_KEY = (
    "lipid_inchikey",
    "ionizable_lipid_pct",
    "helper_lipid_pct",
    "sterol_lipid_pct",
    "peg_lipid_pct",
    "payload_type",
    "paper_doi",
    "prep_method_std",
)
# 协议 7.2 + 第八节：另禁用同批实验的其它测量结果
FORBIDDEN = (
    "particle_size_nm", "pdi", "zeta_potential", "encapsulation_efficiency",
    "structure_type", "process_notes", "release_curve_file", "source_row_id",
    "formulation_id", "paper_doi", "measurement_instrument", "formation_ok",
    "source_dataset", "was_ambiguous", "was_renormalized", "was_harmonized",
    "was_unit_corrected", "inchikey", "scaffold",
)
GROUPS = {"G1": "group_compound", "G2": "group_scaffold", "G3": "paper_doi"}


def build_units(cfg: dict) -> pd.DataFrame:
    raw = pd.read_csv(ROOT / cfg["data"]["source_csv"])
    e = raw[raw["encapsulation_efficiency_pct"].notna()].copy()
    keys = S.structure_keys(e["ionizable_lipid_smiles"])
    e["lipid_inchikey"] = keys["inchikey"].values
    e["lipid_scaffold"] = keys["scaffold"].values
    e = e[e["lipid_inchikey"].notna()].copy()

    k = (
        e[list(DEDUP_KEY)]
        .apply(lambda c: c.map(lambda v: "NA" if pd.isna(v) else str(v)))
        .agg("|".join, axis=1)
    )
    rows = []
    for _, grp in e.assign(_k=k.values).groupby("_k", sort=False):
        row = grp.iloc[0].copy()
        vals = grp["encapsulation_efficiency_pct"].dropna().astype(float)
        row["target"] = float(np.median(vals))
        row["_target_n_rows"] = int(len(vals))
        row["_target_spread"] = float(vals.max() - vals.min()) if len(vals) > 1 else 0.0
        rows.append(row)
    u = pd.DataFrame(rows).reset_index(drop=True)
    u["group_compound"] = u["lipid_inchikey"]
    u["group_scaffold"] = u["lipid_scaffold"]
    return u


def build_features(units: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, dict]:
    fp = cfg["features"]
    mol = F.ionizable_block(units, fp["payload_fp"]["radius"], fp["payload_fp"]["n_bits"])
    comp = F.composition_block(units)
    comp["ionizable_lipid_pct"] = units["ionizable_lipid_pct"].astype(float)
    comp["ionizable_lipid_pct_is_missing"] = units["ionizable_lipid_pct"].isna().astype(float)
    payload = F.payload_class_block(units)
    proc = F.process_block(units, fp["prep_method_min_count"])
    for c in ("flow_ratio_imbalance", "total_flow_rate_ml_min_std"):
        proc[c] = units[c].astype(float)
        proc[f"{c}_is_missing"] = units[c].isna().astype(float)

    X = pd.concat([mol, comp, payload, proc], axis=1)
    hits = [c for c in X.columns for b in FORBIDDEN if b.lower() in c.lower()]
    if hits:
        raise SystemExit(f"特征矩阵里出现禁止字段: {sorted(set(hits))[:10]}")

    mol_fp = [c for c in mol.columns if "_fp_" in c]
    mol_plain = [c for c in mol.columns if "_fp_" not in c]
    other_plain = list(comp.columns) + list(payload.columns) + list(proc.columns)
    sets = {
        "full": {"plain": mol_plain + other_plain, "fp": mol_fp},
        "b2_formulation_only": {"plain": other_plain, "fp": []},
        "b3_molecule_only": {"plain": mol_plain, "fp": mol_fp},
    }
    return X, sets


def pct_metrics(y_true, y_pred) -> dict:
    from scipy import stats
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    out = {
        "mae_pp": float(mean_absolute_error(y_true, y_pred)),
        "rmse_pp": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2_pooled": float(r2_score(y_true, y_pred)) if len(y_true) > 1 else float("nan"),
    }
    out["spearman"] = (
        float(stats.spearmanr(y_true, y_pred).statistic)
        if len(y_true) > 2 and np.std(y_pred) > 0
        else float("nan")
    )
    return out


def paired(a: E.OofResult, b: E.OofResult, seed: int) -> dict:
    oa, ob = np.argsort(a.index), np.argsort(b.index)
    ya, pa, g = a.y_true[oa], a.y_pred[oa], a.groups[oa]
    yb, pb = b.y_true[ob], b.y_pred[ob]
    assert np.array_equal(ya, yb), "配对样本不一致"

    def stat(idx):
        return pct_metrics(yb[idx], pb[idx])["mae_pp"] - pct_metrics(ya[idx], pa[idx])["mae_pp"]

    ci = E.cluster_bootstrap_ci(stat, g, seed=seed)
    ci["point"] = round(float(stat(np.arange(len(ya)))), 4)
    ci["excludes_zero"] = bool(
        np.isfinite(ci["lo"]) and np.isfinite(ci["hi"]) and (ci["lo"] > 0 or ci["hi"] < 0)
    )
    return ci


def learning_curve(units, X, sets, sim, out: Path, results: dict, seeds) -> pd.DataFrame:
    """按训练集里的唯一分子数切的学习曲线（G1 划分）。

    说明：这一段是在 G1/G2/G3 跑完、看到结果之后才加的，协议里没有事先写。
    它不改变任何判定标准（判定只看协议第九节的三档，已由 G1/G2 的结果决定），
    只是为数据规格提供「需要多少个分子」的依据。这一点在报告里也写明。
    """
    groups = units["group_compound"].to_numpy()
    y = units["target"].to_numpy(float)
    rows = []
    for frac in (0.2, 0.4, 0.6, 0.8, 1.0):
        for seed in seeds:
            rng = np.random.default_rng(2000 + seed)
            splits = E.make_splits(units, "S1", seed)
            for model in ("b0", "hgb"):
                preds, truths = [], []
                for tr, te in splits:
                    gs = np.unique(groups[tr])
                    k = max(2, int(round(len(gs) * frac)))
                    keep = set(rng.choice(gs, size=min(k, len(gs)), replace=False))
                    sub = np.array([i for i in tr if groups[i] in keep])
                    if len(sub) < 5:
                        continue
                    if model == "b0":
                        p = E.baseline_constant(y[sub], len(te), "regression")
                    else:
                        pipe, grid = E.model_space("hgb", sets["full"]["plain"], sets["full"]["fp"], seed)
                        try:
                            fitted = E.fit_nested(pipe, grid, X.iloc[sub], y[sub], groups[sub], "regression", seed)
                            p = fitted.predict(X.iloc[te])
                        except Exception:
                            p = E.baseline_constant(y[sub], len(te), "regression")
                    preds.append(p)
                    truths.append(y[te])
                if not preds:
                    continue
                yt, yp = np.concatenate(truths), np.concatenate(preds)
                m = pct_metrics(yt, yp)
                rows.append({
                    "fraction": frac,
                    "approx_train_molecules": int(round(len(np.unique(groups)) * 0.8 * frac)),
                    "seed": seed, "model": model,
                    "mae_pp": round(m["mae_pp"], 3), "r2_pooled": round(m["r2_pooled"], 4),
                })
                print(f"  LC frac={frac} seed{seed} {model:4s} MAE={m['mae_pp']:.2f}pp", flush=True)
    lc = pd.DataFrame(rows)
    if not lc.empty:
        lc.to_csv(out / "learning_curve.csv", index=False)
        results["learning_curve"] = (
            lc.groupby(["approx_train_molecules", "model"]).mae_pp
            .agg(["mean", "std", "min", "max"]).round(3).reset_index().to_dict(orient="records")
        )
        results["learning_curve_note"] = (
            "Added after G1/G2/G3 were run and seen; does not affect the pre-registered pass/fail "
            "criterion, which was already determined by G1 and G2."
        )
    return lc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/smallmol_baseline.yaml")
    ap.add_argument("--out", default="modeling/2026-10-20_ee-feasibility")
    ap.add_argument("--groups", default="G1,G2,G3")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--learning-curve", action="store_true", help="只跑学习曲线（G1 划分）")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)

    units = build_units(cfg)
    X, sets = build_features(units, cfg)
    y = units["target"].to_numpy(float)
    sim = F.tanimoto_matrix(
        units["ionizable_lipid_smiles"].tolist(), units["ionizable_lipid_smiles"].tolist(), 2, 2048
    )

    import rdkit, sklearn  # noqa: E401

    existing = {}
    mj = out / "metrics.json"
    if mj.exists():
        existing = json.loads(mj.read_text(encoding="utf-8"))

    results = {
        "protocol": "docs/ee-feasibility-protocol.md (frozen 2026-10-20, before any model was run)",
        "target": "encapsulation_efficiency_pct (no transform; error unit = percentage points)",
        "n_units": int(len(units)),
        "n_molecules": int(units.group_compound.nunique()),
        "n_scaffolds": int(units.group_scaffold.nunique()),
        "n_papers": int(units.paper_doi.nunique()),
        "payload_mix": units.payload_type.value_counts().to_dict(),
        "target_summary": {
            k: round(float(v), 2)
            for k, v in units.target.describe()[["mean", "std", "min", "50%", "max"]].items()
        },
        "feature_sets": {k: {"n_plain": len(v["plain"]), "n_fp": len(v["fp"])} for k, v in sets.items()},
        "seeds": list((0,) if args.quick else E.SEEDS),
        "n_bootstrap": E.N_BOOTSTRAP,
        "versions": {"rdkit": rdkit.__version__, "scikit_learn": sklearn.__version__},
        "by_split": existing.get("by_split", {}),
        "runs": existing.get("runs", []),
    }
    results["runs"].append({"groups": args.groups, "quick": args.quick})

    seeds = (0,) if args.quick else E.SEEDS
    if args.learning_curve:
        learning_curve(units, X, sets, sim, out, results, seeds=(0,) if args.quick else E.SEEDS)
        (out / "metrics.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        print(f"\n写出 {out}/metrics.json")
        return

    combos = [("b0", None), ("b1", None), ("ridge", "full"), ("rf", "full"), ("hgb", "full")]
    combos += [
        ("ridge", "b2_formulation_only"), ("hgb", "b2_formulation_only"),
        ("ridge", "b3_molecule_only"), ("hgb", "b3_molecule_only"),
    ]
    keys = ["mae_pp", "rmse_pp", "r2_pooled", "spearman"]
    oof_rows = []

    for scheme in [s.strip() for s in args.groups.split(",") if s.strip()]:
        col = GROUPS[scheme]
        u2 = units.copy()
        u2["group_compound"] = units[col].fillna("__NA__").astype(str)
        store = {}
        for model, fset in combos:
            label = model if fset is None else f"{model}@{fset}"
            per_seed, cis = [], []
            for seed in seeds:
                splits = E.make_splits(u2, "S1", seed)
                cols = sets[fset] if fset else {"plain": [], "fp": []}
                t0 = time.time()
                oof = E.run_oof(X, y, u2, splits, model, cols["plain"], cols["fp"], "regression", seed, sim)
                m = pct_metrics(oof.y_true, oof.y_pred)
                m["_fit_seconds"] = round(time.time() - t0, 1)
                per_seed.append(m)
                cis.append(
                    E.cluster_bootstrap_ci(
                        lambda idx: pct_metrics(oof.y_true[idx], oof.y_pred[idx])["mae_pp"],
                        oof.groups, seed=seed,
                    )
                )
                store[(label, seed)] = oof
                if scheme == "G1":
                    for i, idx in enumerate(oof.index):
                        oof_rows.append({
                            "model": label, "seed": seed, "unit_index": int(idx),
                            "y_true": float(oof.y_true[i]), "y_pred": float(oof.y_pred[i]),
                            "lipid": units.ionizable_lipid_name.iloc[idx],
                            "payload": units.payload_type.iloc[idx],
                            "paper_doi": units.paper_doi.iloc[idx],
                        })
                print(f"  {scheme} {label:28s} seed{seed} MAE={m['mae_pp']:6.2f}pp "
                      f"R2={m['r2_pooled']:+.3f} ({m['_fit_seconds']}s)", flush=True)
            summ = {}
            for k in keys:
                vals = [d[k] for d in per_seed if np.isfinite(d[k])]
                summ[k] = {
                    "mean": round(float(np.mean(vals)), 4),
                    "sd": round(float(np.std(vals, ddof=1)), 4) if len(vals) > 1 else 0.0,
                    "min": round(float(np.min(vals)), 4),
                    "max": round(float(np.max(vals)), 4),
                    "per_seed": [round(float(v), 4) for v in vals],
                } if vals else None
            results["by_split"].setdefault(scheme, {})[label] = {
                "summary": summ,
                "mae_ci_headline": {
                    "lo": round(float(np.median([c["lo"] for c in cis])), 3),
                    "hi": round(float(np.median([c["hi"] for c in cis])), 3),
                },
                "n_folds_fallback_to_constant": {f"seed{s}": store[(label, s)].n_fallback for s in seeds},
            }
        comp = {}
        for model, fset in combos:
            label = model if fset is None else f"{model}@{fset}"
            if label in ("b0", "b1"):
                continue
            for base in ("b0", "b1"):
                ps = [paired(store[(label, s)], store[(base, s)], s) for s in seeds]
                signs = [np.sign(p["point"]) for p in ps]
                comp[f"{label}_vs_{base}"] = {
                    "delta_mae_pp_per_seed": [p["point"] for p in ps],
                    "delta_mae_pp_mean": round(float(np.mean([p["point"] for p in ps])), 4),
                    "ci_headline": {
                        "lo": round(float(np.median([p["lo"] for p in ps])), 4),
                        "hi": round(float(np.median([p["hi"] for p in ps])), 4),
                    },
                    "n_seeds_ci_excludes_zero": int(sum(p["excludes_zero"] for p in ps)),
                    "sign_consistent_across_seeds": bool(len(set(signs)) == 1),
                    "beats_baseline": bool(
                        len(set(signs)) == 1 and signs[0] > 0
                        and sum(p["excludes_zero"] for p in ps) == len(ps)
                    ),
                }
        results["by_split"][scheme]["_vs_baselines"] = comp
        (out / "metrics.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )

    if oof_rows:
        pd.DataFrame(oof_rows).to_csv(out / "oof_predictions_G1.csv", index=False)
    units_cols = [c for c in (
        "ionizable_lipid_name", "lipid_inchikey", "lipid_scaffold", "payload_type", "paper_doi",
        "ionizable_lipid_pct", "helper_lipid_pct", "sterol_lipid_pct", "peg_lipid_pct",
        "prep_method_std", "target", "_target_n_rows", "_target_spread",
    ) if c in units.columns]
    units[units_cols].to_parquet(out / "units_ee.parquet", index=False)
    print(f"\n写出 {out}/metrics.json")


if __name__ == "__main__":
    main()
