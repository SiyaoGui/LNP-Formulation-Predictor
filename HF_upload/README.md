---
title: LNP Formulation Predictor
emoji: 🧬
colorFrom: blue
colorTo: purple
sdk: streamlit
app_file: src/streamlit_app.py
pinned: false
---

# LNP Formulation Predictor

Predicts particle size (nm) and polydispersity index (PDI) for a lipid nanoparticle /
liposome formulation from its composition: the four lipid roles (ionizable, helper,
sterol, PEG-lipid), their molar percentages, and the payload type. Each prediction
comes with a breakdown of which formulation component is driving it.

## Method

Molecular structures are resolved to SMILES and featurised with RDKit, using molecular
descriptors and Morgan fingerprints per lipid role and payload. Two gradient-boosted
tree models (HistGradientBoostingRegressor) share this same input schema:

- **Particle size**, trained on 1,564 published formulations, drawn from three public
  sources: LNP Atlas (1,092), a systematic microfluidic liposome dataset (570), and an
  in-vitro-release database (272), after removing failed formulations and non-nanoscale
  particles.
- **PDI**, trained on the 1,275 of those formulations (60 publications) that reported a
  PDI value.

Both models also use preparation parameters (mixing method, total flow rate, flow rate
ratio) where the source paper reported them. The form does not yet collect these for a
new prediction, so a live prediction currently uses missing values for that part of the
input, for both outputs.

Encapsulation efficiency is not modelled yet. The only source with usable coverage is
LNP Atlas; the other two sources report it for zero rows, so a model trained today would
really be a single-source LNP Atlas model wearing a three-source label. It is next in
line once a second data source covers it.

## Reported performance, and its limits

**Particle size.** Under a random train/test split the model reports R² = 0.66 overall.
That figure is **inflated**: formulations from the same publication are near-duplicates,
so a random split places them in both training and test sets and the model can score
well by recognising the source rather than learning the chemistry. Under source-grouped
cross-validation, where all formulations from one publication sit on one side of the
split, performance on genuinely unseen chemistries is R² = -0.135. That is the number
that describes what a new user would experience, and it is the central technical problem
this project is working on.

That number recently got worse, not better, and that was deliberate. An earlier version
of this model was able to use preparation-method values as a shortcut for recognising
which publication a formulation came from, instead of learning real chemistry-to-size
relationships. Fixing that data leakage removed an artificial performance boost, so the
honestly-measured number dropped. It is a more accurate description of what this model
can currently do than a higher number would be.

**PDI.** Under a random split, R² = 0.46; under the same source-grouped validation,
R² = -0.033, close to what a flat average-only prediction would give. Per source, the
grouped result is +0.03 (LNP Atlas), -0.18 (Luciani), 0.00 (in-vitro-release), so even
this near-zero overall number is not evenly earned across sources. This output is newer
and less mature than particle size, and is presented as exploratory.

**Per-prediction breakdown.** Each prediction is shown with a breakdown across six
components (the four lipid roles, payload, and preparation method): for each, the model
is re-run with that component's values replaced by a typical training-set value, and the
shift in the prediction is reported. This is a fast, dependency-free sensitivity check,
not SHAP or a formal attribution method. It explains the model's behaviour on this input,
not the underlying chemistry, and the preparation-method component in particular reflects
having no input there at all, not a specific method choice.

This demo is therefore a proof of the pipeline, not a validated screening tool.

## Roadmap

- Encapsulation efficiency: blocked on getting a second data source that reports it; see above
- Collect preparation parameters (mixing method, flow rates) as form inputs, not just as training data
- Stratify by lipid chemical family instead of pooling all published chemistries (tested at small scale and not yet viable; too few examples survive per family)
- Confidence bounds per prediction (the per-component breakdown added now covers attribution; bounds are still open)
- Wet-lab validation of predicted formulations with a CRO or academic partner

Siyao Gui, MSc in Engineering, Technical University of Denmark
