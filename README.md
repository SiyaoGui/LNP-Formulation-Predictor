# LNP Formulation Predictor

Code, data and results for predicting how lipid nanoparticle and liposome formulations behave from the molecules in them. This is the modelling work behind LipidLens.

## Where things stand (22 October 2026)

We ran three modelling rounds on published formulation data. For each round the evaluation protocol was written down and committed before any model was trained, so the pass criteria could not be picked after seeing the results.

| Round | Data | Target | Result |
|---|---|---|---|
| 1 | 73 formulations, 15 small-molecule drugs, 26 papers | Particle size | No model beat a constant baseline that always predicts the mean |
| 2 | 370 units, 197 ionisable lipids, 37 papers | Encapsulation efficiency | The best model beat the constant baseline in 5 of 5 seeds, until whole papers were held out |
| 3 | 322 units, 5 payload classes, 55 papers | Particle size, large molecules | Every model did worse than the constant baseline |

Particle size depends mostly on how the particles are made. Removing every molecular feature barely changed the error (0.192 to 0.198), and a model given only molecular features did worse than the baseline (0.257 against 0.253). One paper in the data made atenolol and propranolol with the same lipids: agitation gave about 800 nm, sonication about 30 nm.

Encapsulation efficiency is a different case. There the molecular features carry most of the signal, which fits the chemistry, since encapsulation depends on lipophilicity, charge and hydrogen bonding.

In all three rounds the advantage over the baseline fell to about zero once whole papers were held out. Labs use different assays, N/P ratios, buffers and payloads, and the same lipid can differ by 20 percentage points between two papers. The rounds grew from 73 to 370 units and this did not change, so more literature data will not fix it.

The next step is to measure encapsulation ourselves under one fixed protocol. The specification is in `docs/data-spec-ee.md`. Longer term, the data should come from our own instrument: a measuring and control module for microfluidic mixers that records every run in one format. The plan is in `hardware/README.md`; none of it has been built yet.

None of these numbers should be read as model accuracy. No model has yet beaten the nearest-neighbour baseline, which copies the value of the most similar molecule in the training set. An early version of this project reported R² = 0.43 from a random row split that put records from the same paper in both training and test sets; with grouped splits the same data gives about zero.

## Repository layout

| Path | Contents |
|---|---|
| `lnp/` | Shared modules: subset definitions, features, dataset building, evaluation |
| `scripts/` | Entry points, one per step, each can be rerun on its own |
| `configs/` | Run configurations; switching between the small- and large-molecule subsets is a one-line change |
| `data/raw/` | Source tables: the merged three-source table (1,934 rows), the LNP Atlas export and lipid SMILES |
| `data/processed/`, `data/processed_large/` | Analysis units and feature matrices |
| `modeling/` | One folder per run, never edited afterwards; `modeling/INDEX.md` lists them |
| `docs/` | Frozen protocols, results, data specification, glossary and work logs |
| `hardware/` | Plan for the measuring and control module: levels L0 to L4, architecture, control loop, prototype stages and the run record format |
| `app/` | The Streamlit demo and the Hugging Face Space bundle for the earlier particle-size model |
| `archive/2026-09_first-model/` | Code, data, results and notes from the first model, built in September 2026 |

For a first read: `docs/algorithm-results-en.md` summarises the three rounds in English, `docs/data-spec-ee.md` describes the planned experiment and `docs/glossary.md` explains the baselines and splits. The handoff notes and per-round reports are in Chinese.

## Reproducing the results

```bash
pip install scikit-learn rdkit pyarrow matplotlib tabulate

# Round 1: particle size, small molecules
python3 scripts/build_features.py --config configs/smallmol_baseline.yaml
python3 scripts/run_modeling.py   --config configs/smallmol_baseline.yaml --out modeling/<date>_<name>
python3 scripts/render_tables.py  --dir   modeling/<date>_<name>
python3 scripts/make_figures.py   --dir   modeling/<date>_<name>

# Round 2: encapsulation efficiency
python3 scripts/run_ee_feasibility.py --groups G1 --out modeling/<date>_<name>

# Large-molecule subset: same code, different config
python3 scripts/build_features.py --config configs/largemol_baseline.yaml --tasks t1
```

Gradient boosting uses scikit-learn's `HistGradientBoostingRegressor` in every round, so the rounds are comparable. A full Round 1 fit takes about 100 minutes; `run_modeling.py --schemes` runs it in parts.

## Rules for new work

Each modelling run gets its own folder, `modeling/YYYY-MM-DD_<name>/`, and earlier folders stay as they are. A frozen protocol is not changed to improve a result. If it has to change, that goes in a separate commit that states the reason and which results already existed. Results are reported with confidence intervals and the spread across seeds, never the best seed alone.

## Scope

This repository holds code, training data, model files and technical notes. Personal and business documents from the project folder are not included.
