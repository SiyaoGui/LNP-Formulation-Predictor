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

The next step is to measure encapsulation ourselves under one fixed protocol. The specification is in `docs/data-spec-ee.md`; its first phase was revised on 23 October 2026 in `docs/phase1-design.md`, after an independent review of round 2 (`docs/round2-review-2026-10-23.md`, script `scripts/within_paper_check.py`) found that within single papers the molecular features carry almost no ranking signal. Longer term, the data should come from our own instrument: a measuring and control module for microfluidic mixers that records every run in one format. The plan is in `hardware/README.md`; none of it has been built yet.

None of these numbers should be read as model accuracy. No model has yet beaten the nearest-neighbour baseline, which copies the value of the most similar molecule in the training set. An early version of this project reported R² = 0.43 from a random row split that put records from the same paper in both training and test sets; with grouped splits the same data gives about zero.

## Repository layout

| Path | Contents |
|---|---|
| `lnp/` | Shared modules: subset definitions, features, dataset building, evaluation |
| `scripts/` | Modelling entry points, one per step, the PubMed and dataset-repository scans used in the literature review, and the extraction scripts for the external datasets in `data/raw/` |
| `configs/` | Run configurations; switching between the small- and large-molecule subsets is a one-line change |
| `data/raw/` | Source tables: the merged three-source table (1,934 rows), the LNP Atlas export and lipid SMILES. Each external dataset from the October 2026 extraction round has its own folder with the original files, a README (source, download date, changes made) and a licence note; see `data/raw/README.md` |
| `data/consensus_harvest/` | Raw Consensus literature harvest (`papers_all.tsv`, 746 search blocks) and the pipeline scripts behind `docs/master-candidates.csv`; see its `README.md` |
| `data/candidate/` | Hand-transcribed data from two papers, kept out of the training set; see its own README for the sources, checks and recorded contradictions |
| `data/processed/`, `data/processed_large/` | Analysis units and feature matrices, plus the tables extracted from the external datasets |
| `modeling/` | One folder per run, never edited afterwards; `modeling/INDEX.md` lists them |
| `docs/` | Frozen protocols, results, data specification, glossary, the literature review (below) and work logs |
| `docs/funding-ops/` | Method and format notes for the funding and investor-entry calendar, plus two read-only checking scripts. Content of the calendar itself is not in this repository |
| `hardware/` | Plan for the measuring and control module: levels L0 to L4, architecture, control loop, prototype stages and the run record format |
| `app/` | The Hugging Face Space (project page plus the earlier particle-size model as a demo) and a standalone Streamlit demo |
| `brand/` | Visual identity: logo, colour and type tokens, icons, scientific illustrations, chart styles, motion and hardware photography rules |
| `archive/2026-09_first-model/` | Code, data, results and notes from the first model, built in September 2026 |

For a first read: `docs/negative-result-brief-en.md` is a one-page English summary for outside readers, `docs/algorithm-results-en.md` summarises the three rounds in English, `docs/data-spec-ee.md` and `docs/phase1-design.md` describe the planned experiment and `docs/glossary.md` explains the baselines and splits. The handoff notes and per-round reports are in Chinese.

## Literature review (October to November 2026)

A structured search of the published literature ran from 28 October to 9 November 2026. The candidate table `docs/master-candidates.csv` holds 9,464 rows, one per unique DOI, of which 6,810 are marked as still needing full text. The reports listed below were written against an earlier 469-paper version of that table and have not been redone against the full one, so their counts and conclusions describe the smaller set. The files are in Chinese.

| File | Question it answers |
|---|---|
| `docs/consensus-sweep-summary.md` | Overall numbers and conclusions; start here |
| `docs/next-actions.md` | Next steps, each tied to the finding that supports it |
| `docs/brain-delivery-evidence.md` | Evidence for the first application, brain delivery across the blood-brain barrier |
| `docs/organ-tropism-evidence.md` | Published cases where changing the formulation measurably changed organ distribution |
| `docs/validation-evidence.md` | What independent validation and success criteria look like in the literature |
| `docs/heterogeneity-ceiling.md` | How far encapsulation of one molecule varies between studies |
| `docs/feature-mechanism.md` | Which molecular features should predict small-molecule encapsulation |
| `docs/open-datasets.md` | Open formulation datasets and their licences |
| `docs/reporting-standards.md` | Reporting standards, and why inconsistent reporting limits models |
| `docs/competitive-landscape.md` | Published work by other groups and companies |
| `docs/fulltext-acquisition-list.md` | The 152 papers that need full text, with licence status |
| `docs/membrane-specific.md` | Earlier membrane-specific search; its conclusions are superseded |
| `docs/literature-sourcing/` | The search brief and prompts used on 22 October 2026 to screen for papers that hold the process fixed and vary only the molecule, and the screening log template |

If you are picking up the data-engineering work on that corpus, start from `docs/handoff-data-engineering-2026-11-11.md`. The raw harvest and the pipeline that produced the table are in `data/consensus_harvest/`.

## External datasets (26 to 29 October 2026)

This round asked whether published datasets could add new compounds to the training data. The collection rules were frozen before any search (`docs/literature-protocol.md`), and each dataset's licence was checked before download (`docs/data-licensing.md`). Four datasets under CC BY 4.0 were extracted into `data/processed/`:

| Dataset | What it holds | What it added |
|---|---|---|
| Khawar 2022 | 490 lipid-water partition coefficients for 423 compounds | One compound overlaps the existing formulation records |
| Yanes 2025 | The open release database behind the existing PMC_IVR table | No new compounds; nine extra fields for 271 of the 272 existing records |
| Jaki 2026 | 45 formulations of one PROTAC from a design of experiments | Encapsulation values, but no structure recorded for the payload |
| Xu 2022 | 20 records for paclitaxel derivatives, 7 of them failed loading | Encapsulation values, but no structure recorded for the payloads |

None of the four added a small molecule with both a structure and an encapsulation value, which is what the models need. Five further datasets are on hold because their licences do not allow use in this project. The handoff for this round, in Chinese, is `docs/handoff-literature-data.md`.

## Reproducing the results

```bash
pip install scikit-learn rdkit pyarrow matplotlib tabulate
pip install pdfplumber python-docx   # only needed by the extraction scripts, scripts/extract_*.py

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

`rdkit` is required: `scripts/build_features.py`, `scripts/data_inventory.py`, `scripts/report_compound_gain.py` and `scripts/extract_khawar2022.py` stop with an import error without it. The counts in `docs/data-inventory.md` were computed with RDKit 2026.09.1; later versions gave the same unique-compound and scaffold counts. The commands for re-running the four extractions are in section 3 of `docs/handoff-literature-data.md`. `python3 scripts/record_raw_checksums.py --verify` checks that the files under `data/raw/` still match their registered checksums; a local copy of the ignored `standardisation_nm_IVR.zip` shows up there as one unregistered file.

## Rules for new work

Each modelling run gets its own folder, `modeling/YYYY-MM-DD_<name>/`, and earlier folders stay as they are. A frozen protocol is not changed to improve a result. If it has to change, that goes in a separate commit that states the reason and which results already existed. Results are reported with confidence intervals and the spread across seeds, never the best seed alone.

## Scope

This repository holds code, training data, model files and technical notes. Personal and business documents from the project folder are not included.
