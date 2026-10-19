"""可复用评估模块：划分、指标、基线、不确定度、嵌套调参、学习曲线。

这个模块实现 docs/evaluation-protocol.md 里写死的全部评估设定。之后对大分子子集跑
完全相同的流程时，直接复用这里的函数，保证两边口径一致（任务第 9 节要求）。

模块本身不含任何「小分子」特有的逻辑：任务类型、划分方式、种子、基线都是参数。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.feature_selection import f_classif, f_regression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    balanced_accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import tanimoto_matrix

SEEDS = (0, 1, 2, 3, 4)
N_SPLITS = 5
INNER_SPLITS = 3
N_BOOTSTRAP = 2000

# 协议第四节的四种划分方式
SCHEME_GROUP_COL = {"S1": "group_compound", "S2": "payload_scaffold", "S3": "paper_doi"}
SCHEMES = ("S1", "S2", "S3", "S4")


# --------------------------------------------------------------------------- #
# 划分
# --------------------------------------------------------------------------- #
def make_splits(units: pd.DataFrame, scheme: str, seed: int, n_splits: int = N_SPLITS):
    """返回 [(train_idx, test_idx), ...]。

    S1/S2/S3：按对应列分组的 K 折，分组顺序由 seed 打乱
    S4：留一化合物（LOCO），确定性，不依赖 seed
    """
    n = len(units)
    if scheme == "S4":
        groups = units["group_compound"].to_numpy()
        out = []
        for g in pd.unique(groups):
            test = np.where(groups == g)[0]
            train = np.where(groups != g)[0]
            if len(train) >= 5:
                out.append((train, test))
        return out

    col = SCHEME_GROUP_COL[scheme]
    groups = units[col].fillna("__NA__").astype(str).to_numpy()
    n_groups = len(np.unique(groups))
    k = min(n_splits, n_groups)
    gkf = GroupKFold(n_splits=k, shuffle=True, random_state=seed)
    return list(gkf.split(np.zeros((n, 1)), np.zeros(n), groups))


# --------------------------------------------------------------------------- #
# 指纹块：折内频率过滤 + 折内单变量筛选
# --------------------------------------------------------------------------- #
class FpBlock(BaseEstimator, TransformerMixin):
    """指纹处理，只在训练折上 fit（协议第七节要求）。

    1. 频率过滤：只保留训练折里出现频率在 [freq_lo, freq_hi] 之间的位
    2. 单变量筛选：按 f 统计量取前 k 位；k=0 表示完全不用指纹
    缺失值用训练折的众数填充（二值位的众数就是该位的多数取值）。
    """

    def __init__(self, k: int = 0, freq_lo: float = 0.1, freq_hi: float = 0.9, task: str = "regression"):
        self.k = k
        self.freq_lo = freq_lo
        self.freq_hi = freq_hi
        self.task = task

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        if self.k == 0 or X.shape[1] == 0:
            self.keep_ = np.array([], dtype=int)
            self.fill_ = np.zeros(X.shape[1])
            return self
        self.fill_ = np.nan_to_num(np.nanmedian(X, axis=0))
        Xf = np.where(np.isnan(X), self.fill_, X)
        freq = Xf.mean(axis=0)
        cand = np.where((freq >= self.freq_lo) & (freq <= self.freq_hi))[0]
        if len(cand) == 0:
            self.keep_ = np.array([], dtype=int)
            return self
        score_fn = f_regression if self.task == "regression" else f_classif
        with np.errstate(all="ignore"):
            scores, _ = score_fn(Xf[:, cand], y)
        scores = np.nan_to_num(scores, nan=-np.inf)
        order = np.argsort(scores)[::-1][: min(self.k, len(cand))]
        self.keep_ = cand[order]
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float)
        if len(self.keep_) == 0:
            return np.zeros((X.shape[0], 0))
        Xf = np.where(np.isnan(X), self.fill_, X)
        return Xf[:, self.keep_]

    def get_feature_names_out(self, input_features=None):
        return np.array([f"fp_sel_{i}" for i in range(len(self.keep_))])


# --------------------------------------------------------------------------- #
# 模型空间（协议第八节写死的网格）
# --------------------------------------------------------------------------- #
FP_K_GRID = [0, 32, 128]  # k=0 表示不用指纹，让折内交叉验证自己决定指纹有没有用


def _ct(plain_cols, fp_cols, impute: bool, scale: bool, task: str):
    plain_steps = []
    if impute:
        plain_steps.append(("imp", SimpleImputer(strategy="median", add_indicator=True)))
    if scale:
        plain_steps.append(("sc", StandardScaler()))
    plain = Pipeline(plain_steps) if plain_steps else "passthrough"
    return ColumnTransformer(
        [("plain", plain, list(plain_cols)), ("fp", FpBlock(task=task), list(fp_cols))],
        remainder="drop",
    )


def model_space(name: str, plain_cols, fp_cols, seed: int, task: str = "regression"):
    """返回 (pipeline, param_grid)。网格与协议第八节一致，不许扩大。"""
    if task == "regression":
        if name == "ridge":
            pipe = Pipeline(
                [("prep", _ct(plain_cols, fp_cols, True, True, task)), ("est", Ridge(random_state=None))]
            )
            grid = {"est__alpha": [0.01, 0.1, 1, 10, 100, 1000], "prep__fp__k": FP_K_GRID}
        elif name == "rf":
            pipe = Pipeline(
                [
                    ("prep", _ct(plain_cols, fp_cols, True, False, task)),
                    ("est", RandomForestRegressor(n_estimators=500, random_state=seed, n_jobs=1)),
                ]
            )
            grid = {
                "est__max_depth": [3, 5, None],
                "est__min_samples_leaf": [1, 2, 4],
                "prep__fp__k": FP_K_GRID,
            }
        elif name == "hgb":
            pipe = Pipeline(
                [
                    ("prep", _ct(plain_cols, fp_cols, False, False, task)),
                    ("est", HistGradientBoostingRegressor(random_state=seed)),
                ]
            )
            grid = {
                "est__max_depth": [2, 3],
                "est__learning_rate": [0.03, 0.1],
                "est__max_iter": [200, 500],
                "est__min_samples_leaf": [2, 5],
                "prep__fp__k": FP_K_GRID,
            }
        else:
            raise ValueError(name)
    elif task == "classification":
        if name == "logreg":
            pipe = Pipeline(
                [
                    ("prep", _ct(plain_cols, fp_cols, True, True, task)),
                    ("est", LogisticRegression(max_iter=5000, random_state=seed)),
                ]
            )
            grid = {"est__C": [0.01, 0.1, 1, 10, 100], "prep__fp__k": FP_K_GRID}
        elif name == "rf":
            pipe = Pipeline(
                [
                    ("prep", _ct(plain_cols, fp_cols, True, False, task)),
                    ("est", RandomForestClassifier(n_estimators=500, random_state=seed, n_jobs=1)),
                ]
            )
            grid = {
                "est__max_depth": [3, 5, None],
                "est__min_samples_leaf": [1, 2, 4],
                "prep__fp__k": FP_K_GRID,
            }
        elif name == "hgb":
            pipe = Pipeline(
                [
                    ("prep", _ct(plain_cols, fp_cols, False, False, task)),
                    ("est", HistGradientBoostingClassifier(random_state=seed)),
                ]
            )
            grid = {
                "est__max_depth": [2, 3],
                "est__learning_rate": [0.03, 0.1],
                "est__max_iter": [200, 500],
                "prep__fp__k": FP_K_GRID,
            }
        else:
            raise ValueError(name)
    elif task == "multioutput":
        if name == "ridge":
            pipe = Pipeline(
                [("prep", _ct(plain_cols, fp_cols, True, True, "regression")), ("est", Ridge())]
            )
            grid = {"est__alpha": [0.01, 0.1, 1, 10, 100, 1000], "prep__fp__k": FP_K_GRID}
        elif name == "hgb":
            pipe = Pipeline(
                [
                    ("prep", _ct(plain_cols, fp_cols, False, False, "regression")),
                    ("est", MultiOutputRegressor(HistGradientBoostingRegressor(random_state=seed))),
                ]
            )
            grid = {
                "est__estimator__max_depth": [2, 3],
                "est__estimator__learning_rate": [0.03, 0.1],
                "est__estimator__max_iter": [200, 500],
                "prep__fp__k": FP_K_GRID,
            }
        else:
            raise ValueError(name)
    else:
        raise ValueError(task)
    return pipe, grid


def fit_nested(pipe, grid, X_tr, y_tr, groups_tr, task: str, seed: int):
    """嵌套调参：内层按化合物分组的 3 折交叉验证，只用训练折（协议第八节）。"""
    n_groups = len(np.unique(groups_tr))
    if n_groups < 2:
        return clone(pipe).fit(X_tr, y_tr)
    inner = GroupKFold(n_splits=min(INNER_SPLITS, n_groups), shuffle=True, random_state=seed)
    scoring = {
        "regression": "neg_mean_absolute_error",
        "multioutput": "neg_mean_absolute_error",
        "classification": "balanced_accuracy",
    }[task]
    gs = GridSearchCV(pipe, grid, cv=inner, scoring=scoring, n_jobs=-1, refit=True, error_score="raise")
    gs.fit(X_tr, y_tr, groups=groups_tr)
    return gs


# --------------------------------------------------------------------------- #
# 基线
# --------------------------------------------------------------------------- #
def baseline_constant(y_tr, y_te_shape, task: str):
    if task == "classification":
        vals, counts = np.unique(y_tr, return_counts=True)
        return np.repeat(vals[counts.argmax()], y_te_shape)
    if task == "multioutput":
        return np.tile(np.asarray(y_tr).mean(axis=0), (y_te_shape, 1))
    return np.repeat(float(np.mean(y_tr)), y_te_shape)


def baseline_tanimoto(sim: np.ndarray, train_idx, test_idx, y, task: str):
    """B1：在训练折里找 Tanimoto 最相似的样本，直接用它的目标值。

    sim 是全样本两两相似度矩阵（NaN 表示至少一侧没有结构）。
    相似度并列时取全部并列邻居的中位数 / 众数 / 成分中心。
    """
    y = np.asarray(y)
    preds = []
    for i in test_idx:
        s = sim[i, train_idx]
        if np.all(np.isnan(s)):
            nb = train_idx
        else:
            best = np.nanmax(s)
            nb = train_idx[np.isclose(s, best, equal_nan=False) & ~np.isnan(s)]
            if len(nb) == 0:
                nb = train_idx
        vals = y[nb]
        if task == "classification":
            u, c = np.unique(vals, return_counts=True)
            preds.append(u[c.argmax()])
        elif task == "multioutput":
            preds.append(np.asarray(vals, dtype=float).mean(axis=0))
        else:
            preds.append(float(np.median(np.asarray(vals, dtype=float))))
    return np.array(preds)


# --------------------------------------------------------------------------- #
# 指标
# --------------------------------------------------------------------------- #
def regression_metrics(y_true, y_pred) -> dict:
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    err = np.abs(y_true - y_pred)
    out = {
        "mae_log": float(mean_absolute_error(y_true, y_pred)),
        "rmse_log": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2_pooled": float(r2_score(y_true, y_pred)) if len(y_true) > 1 else float("nan"),
        "median_fold_error": float(10 ** np.median(err)),
        "mae_nm": float(mean_absolute_error(10**y_true, 10**y_pred)),
        "rmse_nm": float(np.sqrt(mean_squared_error(10**y_true, 10**y_pred))),
    }
    if len(y_true) > 2 and np.std(y_pred) > 0:
        out["spearman"] = float(stats.spearmanr(y_true, y_pred).statistic)
    else:
        out["spearman"] = float("nan")
    return out


def classification_metrics(y_true, y_pred) -> dict:
    return {
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "accuracy": float(np.mean(np.asarray(y_true) == np.asarray(y_pred))),
    }


# 成分数据：ILR 变换（3 组分 -> 2 维），协议 1.3 节
_ILR_BASIS = np.array(
    [
        [1 / np.sqrt(2), 1 / np.sqrt(6)],
        [-1 / np.sqrt(2), 1 / np.sqrt(6)],
        [0.0, -2 / np.sqrt(6)],
    ]
)


def ilr(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, float)
    x = x / x.sum(axis=1, keepdims=True)
    lx = np.log(x)
    clr = lx - lx.mean(axis=1, keepdims=True)
    return clr @ _ILR_BASIS


def ilr_inv(z: np.ndarray) -> np.ndarray:
    clr = np.asarray(z, float) @ _ILR_BASIS.T
    e = np.exp(clr - clr.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


def composition_metrics(y_true_pct, y_pred_pct) -> dict:
    """y_* 是原空间百分比（每行加和 100）。主指标 Aitchison 距离。"""
    t = np.asarray(y_true_pct, float) / 100.0
    p = np.asarray(y_pred_pct, float) / 100.0
    p = np.clip(p, 1e-9, None)
    p = p / p.sum(axis=1, keepdims=True)
    d = np.linalg.norm(ilr(t) - ilr(p), axis=1)
    out = {"aitchison_mean": float(d.mean()), "aitchison_median": float(np.median(d))}
    names = ("helper", "sterol", "peg")
    per = []
    for j, nm in enumerate(names):
        mae_pp = float(np.mean(np.abs(t[:, j] - p[:, j]) * 100))
        out[f"mae_pp_{nm}"] = mae_pp
        out[f"r2_{nm}"] = (
            float(r2_score(t[:, j] * 100, p[:, j] * 100)) if len(t) > 1 else float("nan")
        )
        per.append(mae_pp)
    out["mae_pp_overall"] = float(np.mean(per))
    return out


# --------------------------------------------------------------------------- #
# Cluster bootstrap（协议第六节）
# --------------------------------------------------------------------------- #
def _cluster_resample(groups: np.ndarray, rng: np.random.Generator):
    uniq = np.unique(groups)
    picked = rng.choice(uniq, size=len(uniq), replace=True)
    idx = []
    for g in picked:
        idx.append(np.where(groups == g)[0])
    return np.concatenate(idx)


def cluster_bootstrap_ci(
    stat_fn, groups: np.ndarray, n: int = N_BOOTSTRAP, seed: int = 0
) -> dict:
    """按分组（化合物）重抽样，不是按行。协议第 6.1 节写明了理由。"""
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n):
        idx = _cluster_resample(groups, rng)
        try:
            v = stat_fn(idx)
        except Exception:
            v = np.nan
        if v is not None and np.isfinite(v):
            vals.append(float(v))
    if not vals:
        return {"lo": float("nan"), "hi": float("nan"), "n_valid": 0}
    return {
        "lo": float(np.percentile(vals, 2.5)),
        "hi": float(np.percentile(vals, 97.5)),
        "n_valid": len(vals),
    }


# --------------------------------------------------------------------------- #
# 跑一个 (任务, 划分, 种子, 模型) 的 out-of-fold 预测
# --------------------------------------------------------------------------- #
@dataclass
class OofResult:
    y_true: np.ndarray
    y_pred: np.ndarray
    groups: np.ndarray
    index: np.ndarray
    best_params: list = field(default_factory=list)
    fold_sizes: list = field(default_factory=list)


def run_oof(
    X: pd.DataFrame,
    y,
    units: pd.DataFrame,
    splits,
    model: str,
    plain_cols,
    fp_cols,
    task: str,
    seed: int,
    sim: np.ndarray | None = None,
) -> OofResult:
    """model ∈ {b0, b1, ridge/logreg, rf, hgb}。返回合并的 out-of-fold 预测。"""
    y_arr = np.asarray(y)
    preds, truths, grps, idxs, params, sizes = [], [], [], [], [], []
    groups_all = units["group_compound"].to_numpy()

    for train_idx, test_idx in splits:
        if model == "b0":
            p = baseline_constant(y_arr[train_idx], len(test_idx), task)
        elif model == "b1":
            p = baseline_tanimoto(sim, train_idx, test_idx, y_arr, task)
        else:
            pipe, grid = model_space(model, plain_cols, fp_cols, seed, task)
            fitted = fit_nested(
                pipe, grid, X.iloc[train_idx], y_arr[train_idx], groups_all[train_idx], task, seed
            )
            p = fitted.predict(X.iloc[test_idx])
            if hasattr(fitted, "best_params_"):
                params.append(fitted.best_params_)
        preds.append(np.asarray(p))
        truths.append(y_arr[test_idx])
        grps.append(groups_all[test_idx])
        idxs.append(test_idx)
        sizes.append(len(test_idx))

    cat = np.concatenate
    return OofResult(
        y_true=cat(truths) if task != "multioutput" else np.vstack(truths),
        y_pred=cat(preds) if task != "multioutput" else np.vstack(preds),
        groups=cat(grps),
        index=cat(idxs),
        best_params=params,
        fold_sizes=sizes,
    )


def payload_similarity(units: pd.DataFrame, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    smi = units["payload_smiles"].tolist()
    return tanimoto_matrix(smi, smi, radius, n_bits)
