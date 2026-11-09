import numpy as np, matplotlib.pyplot as plt, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lipidlens_viz as lv
lv.use()
rng = np.random.default_rng(4); O = os.path.dirname(os.path.abspath(__file__))
def save(fig, n): fig.savefig(f"{O}/{n}.svg"); fig.savefig(f"{O}/{n}.png"); plt.close(fig)

# 1 line
fig, ax = plt.subplots(figsize=(6.4, 3.6)); x = np.arange(1, 9)
ym = 120 - 6*x + rng.normal(0, 2, 8)
lv.line(ax, x, ym, "internal"); lv.points(ax, x, ym, "internal", "Measured, internal")
lv.line(ax, x, 118 - 6.5*x, "predicted", "Model prediction")
ax.set(title="Particle size over mixing runs", xlabel="Run", ylabel="Size (nm)"); ax.legend(); lv.stamp(ax); save(fig, "01_line")
# 2 scatter
fig, ax = plt.subplots(figsize=(6.4, 3.6))
for i, (c, m) in enumerate([(lv.V1, "o"), (lv.V2, "s"), (lv.V3, "^")]):
    ax.scatter(rng.uniform(1, 5, 18), rng.uniform(60, 140, 18), c=c, marker=m, edgecolors=lv.INK, linewidths=0.5, s=30, label=f"Lipid family {'ABC'[i]}")
ax.set(title="Size against flow-rate ratio", xlabel="Flow-rate ratio, water : ethanol", ylabel="Size (nm)"); ax.legend(); lv.stamp(ax); save(fig, "02_scatter")
# 3 bar
fig, ax = plt.subplots(figsize=(6.4, 3.6)); cats = ["Recipe 1", "Recipe 2", "Recipe 3", "Recipe 4"]
v = [82, 74, 69, 51]; ax.bar(cats, v, color=[lv.V1, lv.V1, lv.V1, lv.INTERNAL_FILL], edgecolor=lv.INK, linewidth=0.6)
ax.bar(["Recipe 5"], [60], facecolor="none", edgecolor=lv.V2, hatch="////", linewidth=1.2, label="Predicted, not measured")
ax.set(title="Encapsulation efficiency", ylabel="%", ylim=(0, 100)); ax.legend(loc="upper right", bbox_to_anchor=(1, 0.93)); lv.stamp(ax); save(fig, "03_bar")
# 4 heatmap
fig, ax = plt.subplots(figsize=(6.4, 3.8)); Z = rng.uniform(0, 1, (6, 8))
im = ax.imshow(Z, cmap=lv.SEQ, aspect="auto"); ax.grid(False)
ax.set(title="Predicted score by recipe and membrane", xlabel="Recipe", ylabel="Membrane model")
ax.set_xticks(range(8), [f"R{i+1}" for i in range(8)]); ax.set_yticks(range(6), [f"M{i+1}" for i in range(6)])
for (i, j), z in np.ndenumerate(Z): ax.text(j, i, f"{z:.1f}", ha="center", va="center", fontsize=7, color="#FBFAF6" if z > 0.55 else lv.INK)
fig.colorbar(im, ax=ax, shrink=0.8).outline.set_linewidth(0.5); lv.stamp(ax, "ILLUSTRATIVE, PREDICTED VALUES"); save(fig, "04_heatmap")
# 5 predicted vs measured
fig, ax = plt.subplots(figsize=(5, 5)); m = rng.uniform(60, 160, 30)
lv.points(ax, m[:18], m[:18] + rng.normal(0, 12, 18), "internal", "Internal back-test (published data)")
lv.points(ax, [], [], "validated", "Independent lab test: none yet")
ax.plot([50, 170], [50, 170], color=lv.INK, lw=1); ax.fill_between([50, 170], [40, 160], [60, 180], color=lv.V4, alpha=0.25, lw=0, label="plus or minus 10 nm")
ax.set(xlim=(50, 170), ylim=(50, 170), title="Predicted against measured size", xlabel="Measured size (nm)", ylabel="Predicted size (nm)"); ax.set_aspect("equal"); ax.grid(True, axis="both")
ax.legend(loc="upper left"); lv.stamp(ax); save(fig, "05_pred_vs_measured")
# 6 uncertainty
fig, ax = plt.subplots(figsize=(6.4, 3.6)); x = np.linspace(1, 6, 40); mu = 140 - 12*x + 2*np.sin(x*2)
lv.band(ax, x, mu - 4 - 1.5*x, mu + 4 + 1.5*x, "predicted", "90% prediction interval"); lv.line(ax, x, mu, "predicted", "Predicted mean")
xm = np.array([1.5, 2.5, 3.5]); lv.points(ax, xm, 140 - 12*xm + rng.normal(0, 3, 3), "internal", "Measured, internal")
ax.set(title="Prediction with uncertainty", xlabel="Flow-rate ratio, water : ethanol", ylabel="Size (nm)"); ax.legend(); lv.stamp(ax); save(fig, "06_uncertainty")
# 7 composition
fig, ax = plt.subplots(figsize=(6.4, 3.4))
lv.composition(ax, {"Reference recipe (literature)": {"Ionizable lipid": .50, "Helper phospholipid": .10, "Cholesterol": .385, "PEG-lipid": .015},
                    "Ranked 1": {"Ionizable lipid": .40, "Helper phospholipid": .20, "Cholesterol": .35, "PEG-lipid": .05},
                    "Ranked 2": {"Ionizable lipid": .35, "Helper phospholipid": .15, "Cholesterol": .45, "PEG-lipid": .05}},
               predicted=("Ranked 1", "Ranked 2"))
ax.set_title("Lipid composition, hatched = predicted"); lv.stamp(ax); save(fig, "07_composition")
print("done")
