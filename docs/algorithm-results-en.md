# LNP modelling results: three rounds

2026-10-22

> Repo copy of the shared doc at https://claude.ai/artifact/2sF9c56BaUqnjBMruatN7X
> Detailed per-round reports are in `modeling/*/README.md` (Chinese).

We ran three modelling rounds under one frozen evaluation protocol. Two produced no usable model; one did, under a specific condition. The headline is not an accuracy number, it is a diagnosis: **particle size is governed by the manufacturing process and carries almost no molecular signal, whereas encapsulation efficiency does carry molecular signal, but only within a single experimental setting.** Across all three rounds the apparent advantage disappears whenever whole publications are held out, which identifies between-laboratory incomparability, not sample size, as the binding constraint.

---

## How a result is judged

Every round used the same protocol, written down and committed **before** any model was run. The protocol files are in the repository and their commit timestamps precede the result folders, so the criteria cannot have been chosen after seeing the numbers.

### Four reference models

The hardest problem in this kind of work is having no yardstick. We defined four, and every result is reported against them.

| | What it does | What it tells us |
|---|---|---|
| **B0, constant** | Ignores all inputs, always predicts the training mean | A model that cannot beat this has learned nothing. Hard floor |
| **B1, similarity** | Finds the most structurally similar molecule in the training set (Tanimoto on Morgan fingerprints) and copies its value | What a chemist does without a computer. A model that cannot beat this adds nothing to expert judgement |
| **B2, ablation** | Full model with **all molecular features deleted** | If performance is unchanged, the molecule was never contributing |
| **B3, ablation** | Full model with **only molecular features kept** | If this alone works, the molecule carries real signal |

B2 and B3 are the diagnostic instruments. Without them a failed round yields only the word "inaccurate"; with them it yields a reason.

### Splitting, repetition, uncertainty

**Grouped splitting.** Records sharing a molecule never appear on both sides of a train/test split, otherwise the model memorises rather than generalises. We additionally report splits that hold out whole **scaffolds** (ring systems with side chains stripped, so an entire chemical family leaves together) and whole **publications**.

**Five seeds.** The split depends on a random number. We fix five seeds, run everything five times, and require the result to hold in all five. An earlier version of this project reported R² = 0.43 from a single unsuitable split; under grouped evaluation the same data gives approximately zero.

**Cluster bootstrap confidence intervals.** Intervals come from resampling molecules, not rows, 2,000 times, because records of one molecule have correlated errors. A model counts as beating a baseline only if the paired difference has a 95% interval excluding zero **and** the sign is consistent across all five seeds.

### Algorithms

Ridge regression, random forest, and gradient-boosted trees, run in that order every time, with hyperparameters tuned by nested cross-validation inside the training folds only. No deep learning: at 73 to 370 samples it would fit noise.

---

## Round 1: particle size, small molecules

**Data.** 73 unique formulation experiments, **15 unique drugs**, 26 papers. Doxorubicin alone accounts for 30 of the 73. Target: log10 particle size, 30 to 820 nm.

**Result: no model beat the constant baseline, under any split.**

Gradient boosting reached 0.192 against the constant baseline's 0.253, a 24% improvement on the point estimate. But the paired difference was +0.061 with a 95% interval of **[-0.052, +0.267]**. Zero of five seeds gave an interval excluding zero, and the sign was not consistent across seeds. For scale, the constant baseline's own error interval is [0.128, 0.469]: with 15 compounds, whether doxorubicin falls into a bootstrap resample moves the answer by a factor of three.

**The ablations explain why.**

| | MAE (log10) |
|---|---|
| Constant baseline | 0.253 |
| Similarity baseline | 0.298, **worse than constant** |
| Full model | 0.192 |
| **B2, molecular features deleted** | **0.198, essentially unchanged** |
| **B3, molecular features only** | **0.257, worse than constant** |

Deleting the molecule costs nothing; keeping only the molecule is worse than guessing the mean. The usable signal comes entirely from lipid composition and process.

**The mechanism, in one example.** Atenolol and propranolol appear in the same 1992 paper with identical lipid compositions, differing only in preparation:

| Preparation | Particle size |
|---|---|
| Thin-film hydration + **agitation** | 788 / 795 / 820 nm |
| Thin-film hydration + **sonication** | 30 / 31 / 32 nm |

A 25-fold difference from the process alone, while two drugs differing by two orders of magnitude in logP give identical sizes under the same process. Process and chemistry are completely confounded in this data, so molecular descriptors have no room to act.

**Secondary tasks, both null.** Predicting lipid composition from the molecule (27 formulations, 8 compounds): the model matched the constant baseline to three decimal places. Predicting which lipid classes are used (60 formulations, 20 compounds, 4 classes): best balanced accuracy 0.273 against a chance level of 0.25.

---

## Round 2: encapsulation efficiency

Round 1 suggested the target variable was wrong. Particle size is physically governed by the process (extrusion pore size, sonication power), whereas encapsulation efficiency depends on the molecule's own partitioning behaviour: lipophilicity, charge state, hydrogen bonding. We tested that hypothesis.

**Data.** 370 analysis units, **197 unique ionisable lipids**, 28 scaffolds, 37 papers. Target: encapsulation efficiency in percent, median 82, standard deviation 22.5.

**Design note, stated up front.** The molecule that varies here is the **ionisable lipid**, not the payload: all 563 encapsulation records carry mRNA, siRNA or DNA payloads, which have no computable structure. So this round asks the structurally analogous question, with a different molecular role. A positive result does **not** directly transfer to "a small-molecule drug's own structure predicts its own encapsulation"; that still requires small-molecule encapsulation data, of which we currently have zero records.

**Result: every diagnostic from Round 1 reverses.**

| Diagnostic | Round 1, particle size | Round 2, encapsulation |
|---|---|---|
| Best model beats constant baseline | **No**, 0 of 5 seeds | **Yes**, 5 of 5 seeds, +4.99 points |
| Similarity baseline vs constant | Worse, 0.298 vs 0.253 | **Better**, 14.52 vs 18.40 |
| Molecular features only (B3) | Worse than constant, 0.257 vs 0.253 | **Better than constant**, 13.90 vs 18.40, 5 of 5 |
| Deleting molecular features (B2) | No effect, 0.198 vs 0.192 | **Clearly worse**, 15.25 vs 13.41 |

Molecular features alone (13.90) are nearly as good as everything combined (13.41) and better than formulation plus process alone (15.25). The molecule is the dominant signal, the exact inverse of Round 1.

**The scaffold split is a real test this time.** 197 molecules map to only 28 scaffolds, so holding out whole scaffolds genuinely tests generalisation to unseen chemistry. The advantage survived: +4.46 points, 5 of 5 seeds. In Round 1 this test had no discriminating power, because 15 compounds gave 15 distinct scaffolds, making the scaffold split identical to the compound split.

**But the advantage vanishes when publications are held out.**

| Split | Constant baseline | Model | Advantage |
|---|---|---|---|
| By molecule | 18.40 | 13.41 | **+4.99 points**, 5 of 5 |
| By scaffold | 19.82 | 15.36 | **+4.46 points**, 5 of 5 |
| **By publication** | 19.10 | 19.09 | **+0.01 points**, 0 of 5 |

The similarity baseline reverses direction across the same splits, which identifies the mechanism: it is 3.88 points **better** than constant under the molecule split and 1.79 points **worse** under the publication split. "The most similar lipid" is usually a lipid from the same paper, so the baseline is copying that paper's assay level rather than a chemical regularity. Assay method, N/P ratio, buffer and payload all differ between laboratories, and the same lipid can differ by 20 points between them.

**One further honest limitation.** No model significantly beat the similarity baseline under any split (+1.12 points, interval crossing zero). The signal we have is of the form "similar lipids encapsulate similarly", not a learned structure-property function that extrapolates.

---

## Round 3: large-molecule subset

Run as a by-product to test whether the pipeline was genuinely subset-configurable. It was: the large-molecule config differs from the small-molecule one by two lines, and no modelling code changed.

**Data.** 322 analysis units, 55 papers, but only **5 "compounds"** (mRNA, siRNA, DNA, ASO, protein) and 66.7% missing features, because nucleic acids have no SMILES and therefore no descriptors or fingerprints at all.

**Result: every model is worse than the constant baseline.** Under paper-grouped splitting: constant 0.1584, ridge 0.1680, random forest 0.1786, gradient boosting 0.1875. Ridge and random forest are worse with 5 of 5 seeds excluding zero on the negative side.

Two degeneracies are worth recording because they are instructive:

- **B2 and the full model produce byte-identical numbers.** The payload molecular block is entirely empty, so "all features" reduces to "formulation plus process". This independently confirms there is no molecular information on this side.
- **B3 degenerates in two different ways.** Gradient boosting has no usable feature left and falls back to a constant prediction, logged as 25 fallback folds. Ridge does not error: after imputation of all-empty columns only constant missing-indicator columns remain, so it outputs the training mean and matches the constant baseline on every seed. The second failure is silent. Our comparison script was initially fooled by it and reported that degenerate model as the large-molecule side's "best model". It now detects both forms and names the excluded models in its output.

**Cross-subset comparison.** Absolute errors are not comparable, since the two subsets have different target distributions. The comparable quantity is skill against each subset's own baseline, under the only split that is identically defined on both sides, which is by publication.

| | Small molecules | Large molecules |
|---|---|---|
| Analysis units | 73 | 322 |
| Skill vs constant baseline | +0.069 | **-0.061** |

**A confound that cannot be removed, and must be stated whenever these are compared:** in this database the small-molecule set is entirely the classical-liposome source and the large-molecule set is entirely the modern-LNP source. Payload class, data source and particle chemistry are completely collinear. Any difference is a difference between two datasets, not between molecule classes. This sentence is hard-coded into the comparison script so it cannot be omitted from an output.

---

## The single most important figure

Skill = (baseline error − model error) / baseline error. It is dimensionless, so the three rounds are comparable despite different units.

| Split | Round 1, particle size | Round 2, encapsulation | Round 3, large molecules |
|---|---|---|---|
| By molecule | +0.241, not significant | **+0.271, 5 of 5** | not applicable |
| By scaffold | +0.194, not significant | **+0.225, 5 of 5** | not applicable |
| **By publication** | +0.014, not significant | +0.000, not significant | **−0.061, worse than baseline** |

(Chart version in the shared doc.)

Round 2 is the only round with a real advantage, and it is real under both the molecule split and the scaffold split. In all three rounds the advantage is gone once whole publications are held out. Round 3 is worse than its baseline there.

Sample size does not explain this. The three rounds used 73, 370 and 322 analysis units, and the target variable changed between them. The pattern is unchanged.

---

## What we learned

**1. The target variable decides whether the problem is learnable, before any algorithm choice.** Particle size is physically set by the process: extrusion pore size, sonication power, flow rate. Encapsulation efficiency is set by the molecule's partitioning: logP, charge, hydrogen bonding. Three algorithm families gave the same ordering in both rounds, so the difference is not a modelling-technique difference.

**2. Experimental design decides identifiability, and no amount of data repairs a confounded design.** In the literature, nearly every paper pairs one drug with one process, so the molecular effect and the process effect cannot be separated. The atenolol and propranolol pair makes this concrete: 25-fold size difference from the process, zero difference between two chemically very different drugs.

**3. Between-laboratory incomparability is the binding constraint, and sample size does not relieve it.** Three datasets, two target variables, 73 to 370 units: the advantage goes to zero under publication-grouped splitting every time. For encapsulation the mechanism is identifiable, because the similarity baseline reverses sign across splits.

**4. Ablations are what turn a failure into a direction.** "Accuracy is low" is not actionable. "Deleting the molecular features changes nothing, and molecular features alone are worse than the mean" tells us to change the target variable, which we did, and it worked. The two ablation arms cost very little to run and carried most of the information in this project.

**5. Evaluation design is where self-deception happens.** An earlier version of this project reported R² = 0.43 under row-level random splitting. Under compound-grouped splitting the same data gives approximately zero; the gap was records of the same paper sitting on both sides of the split. We now also have two recorded cases of silent degeneracy, where a model produced plausible-looking numbers that were arithmetically identical to the constant baseline. Both were caught only because the baselines were computed alongside.

**A corollary that is good news.** Particle size being process-governed means the size window needed for follicular targeting can be dialled in by process control. It does not need a model. The quantities we genuinely cannot predict, and which do depend on the molecule, are encapsulation efficiency and drug loading.

---

## What follows

**Stop aggregating encapsulation data from the literature.** Round 2 shows the between-paper variation swamps the molecular signal. Adding more literature records will dilute, not strengthen, the relationship.

**Generate the data in one laboratory under one fixed protocol.** The design that makes the molecular effect identifiable is a single-factor one: fix the lipid composition, the process, the drug-to-lipid ratio and the assay, and vary only the molecule. Full specification is in `docs/data-spec-ee.md`.

- 40 to 60 molecules, at least 15 distinct scaffolds, logP and charge class deliberately spread. Because no model beat the similarity baseline, dense sampling near one scaffold would only reinforce nearest-neighbour lookup.
- At least 3 **independent preparation batches** per molecule. This measures the batch-to-batch standard deviation, which is the floor on any model's achievable error, and which we currently do not know.
- Eriodictyol plus 2 to 3 structurally related flavonoids, as the direct anchor for the lead programme.
- Staged: 12 to 16 molecules first, purely for method characterisation. Gate to the main study is batch-to-batch standard deviation below half the between-molecule standard deviation.

**Expected scale.** The encapsulation learning curve shows a 2.70-point advantage at 32 training molecules, 3.86 at 63, then flattening. That curve was measured on cross-paper-contaminated data, so a single-laboratory study should need no more, and probably fewer. This is an extrapolation, not a commitment.

**What this cannot tell us yet.** Whether a small-molecule drug's own structure predicts its own encapsulation, because the round that worked varied the carrier lipid, not the payload. Whether anything transfers to another lipid system or process. And nothing about in vivo behaviour: encapsulation efficiency is an in vitro quantity, several steps removed from follicular delivery.

---

## Reproducibility

Everything runs from the repository with two commands per round. Each result folder holds the frozen protocol, the configuration used, per-seed metrics, confidence intervals, out-of-fold predictions and figures.

| Artefact | Location |
|---|---|
| Round 1 protocol, frozen before modelling | `docs/evaluation-protocol.md` |
| Round 2 protocol, frozen before modelling | `docs/ee-feasibility-protocol.md` |
| Round 1 results | `modeling/2026-10-19_smallmol-baseline/` |
| Round 2 results | `modeling/2026-10-20_ee-feasibility/` |
| Round 3 results and cross-subset comparison | `modeling/2026-10-20_largemol-sideproduct/` |
| Data collection specification | `docs/data-spec-ee.md` |
| Shared evaluation module, identical across rounds | `lnp/evaluation.py` |

The two protocol files were committed before their result folders existed, which is checkable from the git history. Any later amendment is a separate commit stating the reason and what results existed at the time; one such amendment exists, adding a probe task during Round 1 feature engineering, before any model had been run.

One deviation worth flagging: XGBoost could not be installed in the compute environment, so gradient boosting is scikit-learn's `HistGradientBoostingRegressor` throughout. The same implementation was used in all rounds, so comparisons between rounds are unaffected.
