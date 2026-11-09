"""LipidLens chart helpers (matplotlib).

Evidence rule (mandatory, see brand manual, section Data visualisation):
  VALIDATED  independent lab, criteria fixed in advance  -> filled dark marker, solid line
  INTERNAL   our own or published data, back-tests       -> grey fill with dark edge, solid line
  PREDICTED  model output or simulation                  -> hollow marker, dashed line, hatched area
  ILLUSTRATIVE (made-up numbers for explaining)          -> any of the above PLUS the stamp() label
Never show predicted or illustrative values without the matching encoding and a legend entry.
"""
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
INK, PAPER, GRID, MUTED = "#1B211E", "#FBFAF6", "#D2D6D1", "#4F5853"
V1, V2, V3, V4 = "#1F3A2B", "#3B7DA6", "#C99A3A", "#A7BFAE"
INTERNAL_FILL = "#B4BAB5"
LIPID = {"Ionizable lipid": "#4FA3A5", "Helper phospholipid": "#6F95D8",
         "Cholesterol": "#B7A983", "PEG-lipid": "#8FB394"}
SEQ = LinearSegmentedColormap.from_list("lipidlens_seq", ["#F3F5EF", "#B3C6B5", "#4C6D56", "#1E3B2A"])
DIV = LinearSegmentedColormap.from_list("lipidlens_div", ["#2F6283", "#9DBBD2", "#F3F5EF", "#E2C27A", "#A06A12"])

def use():
    """Register the bundled Archivo files (fonts/ folder, OFL) and load the style."""
    fd = os.path.join(HERE, "fonts")
    if os.path.isdir(fd):
        for f in os.listdir(fd):
            if f.endswith(".ttf"):
                font_manager.fontManager.addfont(os.path.join(fd, f))
    plt.style.use(os.path.join(HERE, "lipidlens.mplstyle"))

def stamp(ax, text="ILLUSTRATIVE DATA, NOT RESULTS"):
    """Mandatory label for any chart whose numbers are not real results. Sits above the chart title."""
    fig = ax.figure
    fig.text(ax.get_position().x0, 1.0, text, ha="left", va="bottom", fontsize=8, fontweight=700, color=INK,
             bbox=dict(boxstyle="square,pad=0.35", fc="#F2EFE3", ec=INK, lw=0.8))

def points(ax, x, y, tier, label=None, color=None, **kw):
    if tier == "validated":
        return ax.scatter(x, y, s=34, c=color or V1, edgecolors=INK, linewidths=0.6, label=label, zorder=3, **kw)
    if tier == "internal":
        return ax.scatter(x, y, s=34, c=INTERNAL_FILL, edgecolors=INK, linewidths=0.9, marker="s", label=label, zorder=3, **kw)
    if tier == "predicted":
        return ax.scatter(x, y, s=38, facecolors="none", edgecolors=color or V2, linewidths=1.4, label=label, zorder=3, **kw)
    raise ValueError("tier must be validated, internal or predicted")

def line(ax, x, y, tier, label=None, color=None, **kw):
    ls = "--" if tier == "predicted" else "-"
    return ax.plot(x, y, ls=ls, color=color or (V2 if tier == "predicted" else V1), marker="", label=label, **kw)

def band(ax, x, lo, hi, tier, label=None, color=None):
    c = color or (V2 if tier == "predicted" else V1)
    if tier == "predicted":
        ax.fill_between(x, lo, hi, facecolor="none", edgecolor=c, hatch="////", linewidth=0, alpha=0.6, label=label)
        ax.plot(x, lo, ls=":", marker="", color=c, lw=0.9); ax.plot(x, hi, ls=":", marker="", color=c, lw=0.9)
    else:
        ax.fill_between(x, lo, hi, color=c, alpha=0.18, linewidth=0, label=label)

def composition(ax, recipes, predicted=()):
    """recipes: {name: {lipid: mol_fraction}}; names in `predicted` get hatching."""
    names = list(recipes)[::-1]
    for i, n in enumerate(names):
        left = 0
        for lip, col in LIPID.items():
            v = recipes[n].get(lip, 0)
            ax.barh(i, v, left=left, color=col, edgecolor=INK, linewidth=0.6,
                    hatch="////" if n in predicted else None, label=lip if i == len(names) - 1 else None)
            if v >= 0.08:
                ax.text(left + v / 2, i, f"{v*100:.0f}", ha="center", va="center", fontsize=8, color=INK, bbox=dict(boxstyle="square,pad=0.15", fc=PAPER, ec="none"))
            left += v
    ax.set_yticks(range(len(names)), names)
    ax.set_xlim(0, 1); ax.set_xlabel("Molar fraction"); ax.grid(False)
    ax.xaxis.set_major_formatter(mpl.ticker.PercentFormatter(1.0))
    ax.legend(ncol=4, loc="upper left", bbox_to_anchor=(0, -0.22), handlelength=1.2)
