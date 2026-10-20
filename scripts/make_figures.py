"""画图：从建模产出的 csv / metrics.json 生成 figures/ 下的图。

用法:
    python3 scripts/make_figures.py --dir modeling/2026-10-19_smallmol-baseline

配色取自经校验的默认分类配色前两槽（蓝 #2a78d6 / 橙 #eb6834）。
两槽在 light 模式下全配对校验通过：CVD ΔE 24.7、常视 ΔE 33.6、对比度 ≥3:1。
顺序型（混淆矩阵）用单一蓝色 ramp，不用彩虹。全程没有双 y 轴。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_MUTED = "#8a8a85"
SERIES_1 = "#2a78d6"  # 模型
SERIES_2 = "#eb6834"  # 基线
GRID = "#e6e5e1"
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CMAP_BLUE = LinearSegmentedColormap.from_list("seq_blue", SEQ_BLUE)


def style_axes(ax, *, xlabel="", ylabel="", title="", grid_axis="y"):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=INK_2, labelsize=9, length=3, width=0.8)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, linewidth=0.8, alpha=0.9)
        ax.set_axisbelow(True)
    if xlabel:
        ax.set_xlabel(xlabel, color=INK_2, fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK_2, fontsize=10)
    if title:
        ax.set_title(title, color=INK, fontsize=11, loc="left", pad=10)


def new_fig(w, h):
    fig, ax = plt.subplots(figsize=(w, h), facecolor=SURFACE)
    return fig, ax


def save(fig, path: Path):
    fig.savefig(path, dpi=160, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print(f"  写出 {path.name}")


# --------------------------------------------------------------------------- #
def fig_learning_curve(d: Path, figs: Path):
    f = d / "learning_curve.csv"
    if not f.exists():
        return
    lc = pd.read_csv(f)
    if lc.empty:
        return
    fig, ax = new_fig(7.2, 4.4)
    labels = {"hgb": "梯度提升树（完整特征）", "b0": "常数基线（预测训练集均值）"}
    colors = {"hgb": SERIES_1, "b0": SERIES_2}
    styles = {"hgb": "-", "b0": "--"}
    for model in ("hgb", "b0"):
        sub = lc[lc.model == model]
        if sub.empty:
            continue
        g = sub.groupby("approx_train_compounds").mae_log.agg(["mean", "min", "max"]).reset_index()
        x = g.approx_train_compounds.to_numpy()
        ax.fill_between(x, g["min"], g["max"], color=colors[model], alpha=0.12, linewidth=0)
        ax.plot(
            x,
            g["mean"],
            styles[model],
            color=colors[model],
            linewidth=1.8,
            marker="o",
            markersize=6,
            markeredgecolor=SURFACE,
            markeredgewidth=1.2,
            label=labels[model],
        )
        ax.annotate(
            f"{g['mean'].iloc[-1]:.3f}",
            (x[-1], g["mean"].iloc[-1]),
            textcoords="offset points",
            xytext=(8, 0),
            color=INK_2,
            fontsize=9,
            va="center",
        )
    style_axes(
        ax,
        xlabel="训练集里的化合物数（近似）",
        ylabel="合并 out-of-fold MAE（log10 空间）",
        title="学习曲线：按化合物数增加训练数据，误差怎么变\n阴影是 5 个种子的最小到最大范围",
    )
    leg = ax.legend(frameon=False, fontsize=9, loc="upper right")
    for t in leg.get_texts():
        t.set_color(INK_2)
    save(fig, figs / "fig1_learning_curve.png")


def fig_model_comparison(d: Path, figs: Path):
    m = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
    t1 = m.get("t1", {})
    schemes = [s for s in ("S1", "S2", "S3", "S4") if s in t1]
    if not schemes:
        return
    order = [
        "b0",
        "b1",
        "ridge@full",
        "rf@full",
        "hgb@full",
        "ridge@b2_formulation_only",
        "hgb@b2_formulation_only",
        "ridge@b3_molecule_only",
        "hgb@b3_molecule_only",
    ]
    pretty = {
        "b0": "B0 常数基线",
        "b1": "B1 Tanimoto 最近邻",
        "ridge@full": "Ridge 完整特征",
        "rf@full": "随机森林 完整特征",
        "hgb@full": "梯度提升树 完整特征",
        "ridge@b2_formulation_only": "B2 Ridge 无分子特征",
        "hgb@b2_formulation_only": "B2 梯度提升树 无分子特征",
        "ridge@b3_molecule_only": "B3 Ridge 只有分子特征",
        "hgb@b3_molecule_only": "B3 梯度提升树 只有分子特征",
    }
    titles = {
        "S1": "S1 按化合物分组",
        "S2": "S2 按骨架分组",
        "S3": "S3 按论文分组",
        "S4": "S4 留一化合物",
    }
    fig, axes = plt.subplots(
        1, len(schemes), figsize=(4.0 * len(schemes), 4.6), sharey=True, facecolor=SURFACE
    )
    axes = np.atleast_1d(axes)
    present = [k for k in order if k in t1[schemes[0]]]
    ypos = np.arange(len(present))[::-1]
    for ax, scheme in zip(axes, schemes):
        for y, key in zip(ypos, present):
            rec = t1[scheme].get(key)
            if not rec or not rec["summary"].get("mae_log"):
                continue
            s = rec["summary"]["mae_log"]
            ci = rec.get("mae_log_ci_headline", {})
            is_base = key in ("b0", "b1")
            c = SERIES_2 if is_base else SERIES_1
            if np.isfinite(ci.get("lo", np.nan)):
                ax.plot([ci["lo"], ci["hi"]], [y, y], color=c, linewidth=1.8, alpha=0.45,
                        solid_capstyle="round")
            ax.plot([s["min"], s["max"]], [y, y], color=c, linewidth=4.0, alpha=0.25,
                    solid_capstyle="round")
            ax.plot(s["mean"], y, "o", color=c, markersize=7, markeredgecolor=SURFACE,
                    markeredgewidth=1.2)
            ax.annotate(f"{s['mean']:.3f}", (s["mean"], y), textcoords="offset points",
                        xytext=(0, 9), ha="center", color=INK_2, fontsize=8)
        style_axes(ax, xlabel="MAE（log10 空间），越小越好", title=titles.get(scheme, scheme),
                   grid_axis="x")
        ax.set_yticks(ypos)
        ax.set_yticklabels([pretty.get(k, k) for k in present], fontsize=9, color=INK)
    handles = [
        plt.Line2D([], [], color=SERIES_1, marker="o", linestyle="-", markersize=7, linewidth=1.8,
                   label="模型"),
        plt.Line2D([], [], color=SERIES_2, marker="o", linestyle="-", markersize=7, linewidth=1.8,
                   label="必须打败的基线"),
    ]
    leg = fig.legend(handles=handles, frameon=False, fontsize=9, ncol=2,
                     loc="lower center", bbox_to_anchor=(0.5, -0.04))
    for t in leg.get_texts():
        t.set_color(INK_2)
    fig.suptitle(
        "各模型与基线的 MAE 对比：圆点是 5 个种子的均值，细线是 cluster bootstrap 95% 区间，粗浅线是跨种子范围",
        color=INK, fontsize=11, x=0.01, ha="left",
    )
    fig.tight_layout(rect=(0, 0.02, 1, 0.94))
    save(fig, figs / "fig2_model_comparison.png")


def _load_oof(d: Path, task: str) -> pd.DataFrame:
    """分段跑会产生多个带划分后缀的 oof 文件，这里合并。"""
    files = sorted(d.glob(f"oof_predictions_{task}*.csv"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def _best_model_oof(d: Path) -> tuple[pd.DataFrame, str]:
    oof = _load_oof(d, "t1")
    m = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
    s1 = m["t1"]["S1"]
    cand = {
        k: v["summary"]["mae_log"]["mean"]
        for k, v in s1.items()
        if k not in ("_vs_baselines",) and not k.startswith("b") and v["summary"].get("mae_log")
    }
    best = min(cand, key=cand.get)
    return oof[oof.model == best].copy(), best


def fig_pred_vs_obs(d: Path, figs: Path):
    if not list(d.glob("oof_predictions_t1*.csv")):
        return
    oof, best = _best_model_oof(d)
    g = oof.groupby("unit_index").agg(
        y_true=("y_true_log10", "first"),
        y_pred=("y_pred_log10", "mean"),
        is_probe=("is_probe", "first"),
        compound=("compound", "first"),
    )
    fig, ax = new_fig(5.6, 5.4)
    lo = float(min(g.y_true.min(), g.y_pred.min())) - 0.08
    hi = float(max(g.y_true.max(), g.y_pred.max())) + 0.08
    ax.plot([lo, hi], [lo, hi], "--", color=INK_MUTED, linewidth=1.2, zorder=1)
    for flag, color, label in ((False, SERIES_1, "药物分子"), (True, SERIES_2, "荧光探针分子")):
        sub = g[g.is_probe == flag]
        if sub.empty:
            continue
        ax.scatter(sub.y_true, sub.y_pred, s=46, color=color, edgecolor=SURFACE, linewidth=1.2,
                   zorder=3, label=label)
    style_axes(
        ax,
        xlabel="实测粒径 log10(nm)",
        ylabel="预测粒径 log10(nm)（5 个种子平均）",
        title=f"预测 vs 实测（{best}，S1 按化合物分组）\n虚线是完全一致线",
        grid_axis="both",
    )
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    leg = ax.legend(frameon=False, fontsize=9, loc="upper left")
    for t in leg.get_texts():
        t.set_color(INK_2)
    save(fig, figs / "fig3_pred_vs_obs.png")


def fig_error_by_compound(d: Path, figs: Path):
    if not list(d.glob("oof_predictions_t1*.csv")):
        return
    oof, best = _best_model_oof(d)
    oof["abs_err"] = (oof.y_true_log10 - oof.y_pred_log10).abs()
    g = (
        oof.groupby("compound")
        .agg(mae=("abs_err", "mean"), n=("abs_err", "size"), is_probe=("is_probe", "first"))
        .sort_values("mae")
    )
    fig, ax = new_fig(7.4, max(3.2, 0.34 * len(g) + 1.6))
    y = np.arange(len(g))
    colors = [SERIES_2 if p else SERIES_1 for p in g.is_probe]
    ax.barh(y, g.mae, color=colors, height=0.62, zorder=3)
    for yi, (val, n) in enumerate(zip(g.mae, g.n)):
        ax.annotate(f"{val:.3f}  (n={n // 5})", (val, yi), textcoords="offset points",
                    xytext=(6, 0), va="center", color=INK_2, fontsize=8)
    style_axes(ax, xlabel="该化合物的平均绝对误差（log10 空间）",
               title=f"哪些化合物预测得最差（{best}，S1，5 个种子合并）\nn 是该化合物的配方数",
               grid_axis="x")
    ax.set_yticks(y)
    ax.set_yticklabels(g.index, fontsize=9, color=INK)
    ax.set_xlim(0, float(g.mae.max()) * 1.35)
    handles = [
        plt.Line2D([], [], color=SERIES_1, marker="s", linestyle="", markersize=8, label="药物分子"),
        plt.Line2D([], [], color=SERIES_2, marker="s", linestyle="", markersize=8, label="荧光探针分子"),
    ]
    leg = ax.legend(handles=handles, frameon=False, fontsize=9, loc="lower right")
    for t in leg.get_texts():
        t.set_color(INK_2)
    save(fig, figs / "fig4_error_by_compound.png")


def fig_t3_confusion(d: Path, figs: Path):
    oof = _load_oof(d, "t3")
    if oof.empty:
        return
    m = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
    s1 = m.get("t3", {}).get("S1", {})
    cand = {
        k: v["summary"]["balanced_accuracy"]["mean"]
        for k, v in s1.items()
        if k != "_vs_baselines" and not k.startswith("b") and v["summary"].get("balanced_accuracy")
    }
    if not cand:
        return
    best = max(cand, key=cand.get)
    sub = oof[(oof.model == best) & (oof.scheme == "S1")]
    labels = ["helper_only", "helper_peg", "helper_sterol", "helper_sterol_peg"]
    cm = pd.crosstab(sub.y_true, sub.y_pred).reindex(index=labels, columns=labels, fill_value=0)
    norm = cm.div(cm.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    fig, ax = new_fig(5.8, 5.0)
    im = ax.imshow(norm.to_numpy(), cmap=CMAP_BLUE, vmin=0, vmax=1)
    for i in range(len(labels)):
        for j in range(len(labels)):
            v = norm.to_numpy()[i, j]
            ax.text(j, i, f"{cm.to_numpy()[i, j]}", ha="center", va="center",
                    color="#ffffff" if v > 0.55 else INK, fontsize=10)
    style_axes(ax, title=f"T3 混淆矩阵（{best}，S1，5 个种子合并）\n格内是计数，底色是按真实类别归一化的比例",
               grid_axis=None)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9, color=INK)
    ax.set_yticklabels(labels, fontsize=9, color=INK)
    ax.set_xlabel("预测类别", color=INK_2, fontsize=10)
    ax.set_ylabel("真实类别", color=INK_2, fontsize=10)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=INK_2, labelsize=8)
    save(fig, figs / "fig5_t3_confusion.png")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="modeling/2026-10-19_smallmol-baseline")
    args = ap.parse_args()
    d = ROOT / args.dir
    figs = d / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.sans-serif"] = [
        "Noto Sans CJK SC", "Noto Sans CJK JP", "WenQuanYi Zen Hei", "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    print(f"画图到 {figs}")
    fig_learning_curve(d, figs)
    fig_model_comparison(d, figs)
    fig_pred_vs_obs(d, figs)
    fig_error_by_compound(d, figs)
    fig_t3_confusion(d, figs)


if __name__ == "__main__":
    main()
