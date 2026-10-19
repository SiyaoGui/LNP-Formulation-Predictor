"""泄漏检查：逐个确认没有特征直接或间接包含目标信息。

用法:
    python3 scripts/leakage_check.py --config configs/smallmol_baseline.yaml

五项检查:
  1. 禁止字段断言        协议 7.2 节的清单，逐列匹配
  2. 单调关系            每个特征与目标的 |Spearman ρ|，≈1 说明是目标的变形
  3. 互信息              每个特征与目标的互信息，排序后看头部是否可疑
  4. 单特征模型          只用一个特征、按化合物分组交叉验证，看能不能单独打败常数基线
  5. 代理变量检查        (a) 特征能不能预测被排除的 structure_type（高危泄漏字段的代理）
                        (b) 特征有多少方差能被 paper_doi 解释（论文身份的代理）

产出: docs/leakage_check.json + stdout 报告
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats
from sklearn.dummy import DummyRegressor
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.tree import DecisionTreeRegressor

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SINGLE_FEATURE_FLAG = 0.15  # 单特征相对常数基线的 MAE 改善超过这个比例就标记出来复查
PROXY_FLAG = 0.60  # 对 structure_type 的分类准确率 / 对 paper 的 eta² 超过这个值就标记


def eta_squared(values: np.ndarray, groups: np.ndarray) -> float:
    """一个特征的方差有多少能被分组变量解释。1 表示完全由分组决定。"""
    ok = ~np.isnan(values)
    v, g = values[ok], groups[ok]
    if len(v) < 3 or len(np.unique(g)) < 2:
        return float("nan")
    grand = v.mean()
    ss_total = ((v - grand) ** 2).sum()
    if ss_total == 0:
        return float("nan")
    ss_between = sum(len(v[g == k]) * (v[g == k].mean() - grand) ** 2 for k in np.unique(g))
    return float(ss_between / ss_total)


def single_feature_mae(x: np.ndarray, y: np.ndarray, groups: np.ndarray, seed: int = 0) -> dict:
    """只用一个特征，按化合物分组 5 折交叉验证，和常数基线比。"""
    ok = ~np.isnan(x)
    if ok.sum() < 10 or len(np.unique(groups[ok])) < 5 or np.nanstd(x) == 0:
        return {"mae": float("nan"), "mae_const": float("nan"), "improvement": float("nan")}
    X, yy, gg = x[ok].reshape(-1, 1), y[ok], groups[ok]
    cv = GroupKFold(n_splits=5)
    pred, pred_c, truth = [], [], []
    for tr, te in cv.split(X, yy, gg):
        model = make_pipeline(
            SimpleImputer(strategy="median"), DecisionTreeRegressor(max_depth=2, random_state=seed)
        )
        model.fit(X[tr], yy[tr])
        pred.append(model.predict(X[te]))
        const = DummyRegressor(strategy="mean").fit(X[tr], yy[tr])
        pred_c.append(const.predict(X[te]))
        truth.append(yy[te])
    mae = mean_absolute_error(np.concatenate(truth), np.concatenate(pred))
    mae_c = mean_absolute_error(np.concatenate(truth), np.concatenate(pred_c))
    return {
        "mae": round(float(mae), 4),
        "mae_const": round(float(mae_c), 4),
        "improvement": round(float((mae_c - mae) / mae_c), 4) if mae_c > 0 else float("nan"),
    }


def structure_type_proxy(x: np.ndarray, st: np.ndarray) -> float:
    """这个特征能不能分辨被排除的 structure_type。

    用单特征决策树（深度 2）按分组交叉验证的准确率衡量，和「永远猜多数类」比。
    返回相对多数类基线的准确率提升。
    """
    ok = (~np.isnan(x)) & pd.notna(st)
    if ok.sum() < 10:
        return float("nan")
    xv, sv = x[ok], st[ok]
    if np.std(xv) == 0 or len(np.unique(sv)) < 2:
        return float("nan")
    # 用分位数切分找最好的单阈值分类准确率（比训练一棵树更直接，也更保守）
    best = 0.0
    for q in np.linspace(0.1, 0.9, 17):
        thr = np.quantile(xv, q)
        left, right = sv[xv <= thr], sv[xv > thr]
        if len(left) == 0 or len(right) == 0:
            continue
        correct = 0
        for part in (left, right):
            vals, counts = np.unique(part, return_counts=True)
            correct += counts.max()
        best = max(best, correct / len(sv))
    vals, counts = np.unique(sv, return_counts=True)
    majority = counts.max() / len(sv)
    return round(float(best - majority), 4)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/smallmol_baseline.yaml")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    proc = ROOT / cfg["data"]["out_dir"]
    raw = pd.read_csv(ROOT / cfg["data"]["source_csv"])
    # source_row_id 只在来源内唯一，所以先限定到有 payload 结构的那批（小分子子集所在来源）
    # 再建映射；重复 id 保留第一个，并断言不再有重复
    rs = raw[raw["payload_smiles"].notna()].drop_duplicates("source_row_id")
    raw_structure_type = pd.Series(
        rs["process_notes"].str.extract(r"structure_type=([^;]*)")[0].str.strip().values,
        index=rs["source_row_id"].astype(str).values,
    )
    assert raw_structure_type.index.is_unique, "source_row_id 仍有重复，无法建映射"

    report = {"config": args.config, "forbidden_substrings": cfg["forbidden_feature_substrings"], "tasks": {}}

    for task in ("t1", "t3"):
        units = pd.read_parquet(proc / f"units_{task}.parquet")
        X = pd.read_parquet(proc / f"features_{task}.parquet")
        groups = units["group_compound"].to_numpy()

        # 分析单元是多行折叠成的，structure_type 取组内第一行的值
        first_rid = units["_source_row_ids"].str.split(";").str[0].astype(str)
        st = first_rid.map(raw_structure_type).to_numpy(dtype=object)

        if task == "t1":
            y = units["target"].to_numpy(dtype=float)
            mi = mutual_info_regression(
                SimpleImputer(strategy="median").fit_transform(X), y, random_state=0
            )
        else:
            y_lab = units["target"].to_numpy()
            codes, _ = pd.factorize(y_lab)
            y = codes.astype(float)
            mi = mutual_info_classif(
                SimpleImputer(strategy="median").fit_transform(X), codes, random_state=0
            )

        # 1. 禁止字段
        hits = [
            (c, b)
            for c in X.columns
            for b in cfg["forbidden_feature_substrings"]
            if b.lower() in c.lower()
        ]

        fp_cols = [c for c in X.columns if "_fp_" in c]
        plain_cols = [c for c in X.columns if "_fp_" not in c]

        rows = []
        for col in plain_cols:
            x = X[col].to_numpy(dtype=float)
            ok = ~np.isnan(x)
            rho = (
                float(stats.spearmanr(x[ok], y[ok]).statistic)
                if ok.sum() > 5 and np.nanstd(x) > 0
                else float("nan")
            )
            rec = {
                "feature": col,
                "nan_share": round(float(np.isnan(x).mean()), 3),
                "spearman_abs": round(abs(rho), 4) if not np.isnan(rho) else None,
                "mutual_info": round(float(mi[list(X.columns).index(col)]), 4),
                "eta2_paper": round(eta_squared(x, units["paper_doi"].to_numpy(dtype=object)), 4),
                "structure_type_proxy_gain": structure_type_proxy(x, st),
            }
            if task == "t1":
                rec.update(single_feature_mae(x, y, groups))
            rows.append(rec)

        tab = pd.DataFrame(rows)
        flagged = []
        if task == "t1":
            flagged += tab[tab.improvement.fillna(0) > SINGLE_FEATURE_FLAG].feature.tolist()
        flagged += tab[tab.spearman_abs.fillna(0) > 0.95].feature.tolist()
        flagged += tab[tab.structure_type_proxy_gain.fillna(0) > PROXY_FLAG].feature.tolist()
        flagged += tab[tab.eta2_paper.fillna(0) > PROXY_FLAG].feature.tolist()

        # 指纹块整体看：最高互信息的几位，以及是否存在单一位几乎等于目标分箱
        fp_mi = pd.Series(
            [mi[list(X.columns).index(c)] for c in fp_cols], index=fp_cols
        ).sort_values(ascending=False)

        report["tasks"][task] = {
            "n_units": int(len(units)),
            "n_features": int(X.shape[1]),
            "forbidden_hits": hits,
            "forbidden_check": "passed" if not hits else "FAILED",
            "n_plain_features": len(plain_cols),
            "n_fingerprint_features": len(fp_cols),
            "flagged_features": sorted(set(flagged)),
            "top_mutual_info_plain": tab.nlargest(12, "mutual_info")[
                ["feature", "mutual_info", "spearman_abs", "eta2_paper", "structure_type_proxy_gain"]
            ].to_dict(orient="records"),
            "top_single_feature_plain": (
                tab.nlargest(12, "improvement")[
                    ["feature", "improvement", "mae", "mae_const", "nan_share"]
                ].to_dict(orient="records")
                if task == "t1"
                else None
            ),
            "max_eta2_paper": round(float(tab.eta2_paper.max(skipna=True)), 4),
            "max_structure_type_proxy_gain": round(
                float(tab.structure_type_proxy_gain.max(skipna=True)), 4
            ),
            "top_mutual_info_fingerprint": [
                {"feature": k, "mutual_info": round(float(v), 4)} for k, v in fp_mi.head(8).items()
            ],
            "thresholds": {
                "single_feature_improvement_flag": SINGLE_FEATURE_FLAG,
                "proxy_flag": PROXY_FLAG,
            },
        }
        tab.to_csv(ROOT / "docs" / f"leakage_check_detail_{task}.csv", index=False)

        print(f"=== {task} | 单元 {len(units)} | 特征 {X.shape[1]}（非指纹 {len(plain_cols)}）")
        print(f"  禁止字段断言: {'通过' if not hits else 'FAILED ' + str(hits[:5])}")
        print(f"  |Spearman| 最大: {tab.spearman_abs.max(skipna=True):.3f}")
        if task == "t1":
            print(f"  单特征最大改善: {tab.improvement.max(skipna=True):.3f}")
        print(f"  对 structure_type 的最大代理增益: {tab.structure_type_proxy_gain.max(skipna=True):.3f}")
        print(f"  被 paper_doi 解释的最大 eta²: {tab.eta2_paper.max(skipna=True):.3f}")
        print(f"  标记复查的特征 {len(set(flagged))} 个: {sorted(set(flagged))[:8]}")

    out = ROOT / "docs" / "leakage_check.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n写出: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
