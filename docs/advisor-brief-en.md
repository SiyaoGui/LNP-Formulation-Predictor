# LNP small-molecule baseline: advisor brief

2026-10-20

> Repo copy of the shared doc at https://claude.ai/code/artifact/a2219a1f-4902-45d7-8dce-375dde9ea290
> Full technical report: `modeling/2026-10-19_smallmol-baseline/README.md` (Chinese).

On the small-molecule data we have, no model beat the simplest possible baseline — always predicting the average particle size. The point estimate looked good (24% lower error), but the uncertainty is five times larger than the effect. Three pre-registered diagnostics agree on why: the drug's molecular properties carry essentially no information about the outcome in this dataset, and almost all of the usable signal comes from the manufacturing process. The useful finding is quantitative: the learning curve is still falling steeply at our data limit, so adding compounds should help, and we estimate 40–100 unique compounds are needed versus the 15 we have.

## How we judged it

The task: predict liposome particle size from the drug's molecular structure, the lipid formulation, and the manufacturing process. Data: 73 unique formulation experiments covering **15 unique small-molecule drugs** from 26 papers. One drug, doxorubicin, accounts for 30 of the 73 formulations.

Four things in the method matter for reading the results. All of them were written down and frozen before any model was run, so none of them was chosen after seeing the numbers.

**1. Two baselines the model had to beat.** A model is only useful if it beats the trivial alternatives.

- *Constant baseline*: ignore all inputs and always predict the average size of the training data. If a model cannot beat this, it has learned nothing.
- *Similarity baseline*: find the most chemically similar drug in the training set and copy its formulation's size. This is what a medicinal chemist does by hand.

**2. Splitting by compound, not by row.** If the same drug appears in both the training and test set, the model can memorise rather than generalise, and the score looks far better than it is. We always held out whole compounds. We also report a split by paper, which additionally prevents the model from recognising which lab the measurement came from.

**3. Confidence intervals, not single numbers.** With 15 compounds, a single score is close to meaningless. We resampled compounds 2,000 times to get a 95% interval, and repeated everything with 5 different random splits. A difference only counts if its interval excludes zero and its sign is consistent across all 5 repeats.

**4. Error is reported on a log scale.** Sizes span 30 to 820 nm, so we predict log10(size). An error of 0.19 means predictions are off by about 1.6-fold on average.

## Results: nothing beat the constant baseline

Mean absolute error on log10(size), averaged over 5 random splits. Lower is better.

| Model | Split by compound | Split by scaffold | Split by paper | Leave-one-compound-out |
|---|---|---|---|---|
| **Constant baseline** | **0.253** | **0.248** | **0.243** | **0.249** |
| **Similarity baseline** | **0.298** | **0.309** | **0.273** | **0.294** |
| Linear model (Ridge) | 0.342 | 0.330 | 0.270 | 0.361 |
| Random forest | 0.204 | 0.201 | 0.226 | 0.178 |
| Gradient boosting | 0.192 | 0.200 | 0.240 | 0.151 |
| Gradient boosting, **no molecular features** | 0.198 | 0.192 | 0.248 | 0.138 |
| Gradient boosting, **molecular features only** | 0.257 | 0.264 | 0.235 | 0.256 |

The best model looks 24% better than the constant baseline (0.192 vs 0.253). But the paired difference is +0.061 with a 95% interval of **[−0.052, +0.267]** — the interval crosses zero, none of the 5 repeats gave an interval excluding zero, and the sign of the difference was not even consistent across repeats. By the criterion fixed in advance, **this does not count as beating the baseline**.

The tree models did beat the similarity baseline. That is weak evidence, because the similarity baseline (0.298) is itself worse than simply predicting the average (0.253).

For scale: even the constant baseline's own error has a 95% interval of [0.128, 0.469]. With 15 compounds, whether doxorubicin lands in a resample changes the answer by a factor of three.

## Why accuracy is poor

Three checks, all specified before the models were run, point the same way.

**Check 1 — remove the molecular features and nothing changes.** Error goes from 0.192 to 0.198 when every molecular descriptor and fingerprint is deleted; under leave-one-compound-out it actually improves (0.151 to 0.138).

**Check 2 — keep only the molecular features and the model fails.** Error 0.257 against the constant baseline's 0.253. Molecular structure alone is worse than predicting the average.

Together these say the model's entire usable signal comes from the lipid formulation and the manufacturing process. **The drug's molecular properties contribute approximately nothing.** That is a statement about this dataset, not about the chemistry.

**Check 3 — splitting by paper removes most of the remaining advantage.** The gap over the constant baseline falls from +0.061 to +0.003. Each of the 26 papers tends to use one process and one lipid system, so a model that is allowed to see other formulations from the same paper is partly looking up that paper's typical size rather than learning chemistry.

### The clearest single example

Atenolol and propranolol appear in the same 1992 paper, with the same lipid compositions and only the preparation method differing:

| Preparation | Particle size |
|---|---|
| Thin-film hydration + **agitation** | 788 / 795 / 820 nm |
| Thin-film hydration + **sonication** | 30 / 31 / 32 nm |

The same drug, the same formulation, a different process: **25-fold difference in size**. And two drugs whose lipophilicity differs by two orders of magnitude (logP 0.45 vs 2.58) give identical sizes under the same process. In data shaped like this, molecular descriptors have no room to matter — process and chemistry are completely confounded.

### What the model actually does

It predicts near the middle of the distribution almost regardless of input. Samples whose true size is 31 nm are predicted at 113 nm; samples at 788 nm are predicted at 328 nm. Error is lowest in the 80–200 nm band where most of the data sits.

## How much more data is needed

We retrained the model on 20%, 40%, 60%, 80% and 100% of the available compounds. We subsampled **compounds**, not rows, because acquiring more data in practice means new drugs, not repeat measurements of the same one.

| Training compounds | 2 | 5 | 7 | 10 | 12 |
|---|---|---|---|---|---|
| Model (MAE, log10) | 0.309 | 0.302 | 0.259 | 0.225 | **0.192** |
| Constant baseline | 0.269 | 0.248 | 0.245 | 0.250 | 0.253 |

(Chart version in the shared doc; source figure `modeling/2026-10-19_smallmol-baseline/figures/fig1_learning_curve.png`.)

Two things matter here. The model does not beat the constant baseline until roughly 8 training compounds — below that it is worse than predicting the average. And the curve has **not flattened** at our limit of 12: the drop from 10 to 12 compounds is as large as the drop from 7 to 10. More compounds should still buy accuracy.

**Extrapolation (treat as an order of magnitude, not a promise).** The current advantage over the baseline is 0.061 and the confidence interval is about ±0.159 wide. Intervals shrink roughly with the square root of the number of compounds. If the advantage stays at 0.06, we would need about 7× the compounds (~105). If it grows to 0.10 as the curve suggests, about 2.5× (~40). So: **40 to 100 unique compounds, against the 15 we have.**

## What we recommend

**1. Collect compounds, and collect them in a specific shape.** The single most valuable study design is one paper comparing **several different drugs under one fixed manufacturing process**. That holds the process constant so a molecular effect becomes visible at all. Across our 26 papers, almost none are designed this way — which is the structural reason molecular descriptors learn nothing here.

**2. Reconsider the target variable.** Particle size is dominated by process. Encapsulation efficiency has a much more direct mechanistic link to a drug's lipophilicity and charge. We have **zero** encapsulation values on the small-molecule side, so this also requires new data — but it is likelier to be a learnable task.

**3. Do not invest in more modelling on the current data.** Larger or more complex models will overfit 73 formulations. The limit is the data, not the algorithm.

## What we cannot claim

- We cannot claim the model predicts particle size. It did not beat the constant baseline.
- We cannot claim it generalises to new chemical structures. With 15 compounds giving 15 distinct scaffolds, the compound split and the scaffold split are the same test, so that question was not answered.
- We cannot compare small molecules against large molecules yet. We have not run the large-molecule subset. When we do, note that in this database the small-molecule set is *entirely* the classical-liposome source and the large-molecule set is *entirely* the modern-LNP source — payload type, data source and particle chemistry are completely confounded. Any difference will have to be described as a difference between two datasets, not between molecule classes.
- One favourable-looking number should not be quoted in isolation: leave-one-compound-out gives R² = +0.63, but the same model gives R² = −0.14 when split by paper. The difference comes from the evaluation method, not from the model.

## Why this is still a useful result

The evaluation itself is the asset. The protocol was frozen before any model ran, splits hold out whole compounds, every number carries a confidence interval from 2,000 compound-level resamples, every result is reported across 5 random splits, and two baselines plus two diagnostic ablations were specified in advance. Everything is reproducible from the repository with two commands. That is the part a sceptical reviewer can check — and it is what converts "our accuracy is low" into "here is exactly which data would fix it, and how much."

## Secondary tasks (one line each)

- **Predicting the lipid composition from the molecule** (27 formulations, 8 compounds): the gradient-boosting model's every metric matched the constant baseline to three decimals. Zero signal.
- **Predicting which lipid classes are used** (60 formulations, 20 compounds, 4 classes): best balanced accuracy 0.273, where random guessing is 0.25.
