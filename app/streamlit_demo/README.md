---
title: LNP Formulation Predictor
emoji: 🧬
colorFrom: blue
colorTo: purple
sdk: streamlit
app_file: app.py
pinned: false
---

# LNP Formulation Predictor

Predicts particle size (nm) for a lipid nanoparticle / liposome formulation from its
composition: the four lipid roles (ionizable, helper, sterol, PEG-lipid), their molar
percentages, and the payload type.

## Method

Molecular structures are resolved to SMILES and featurised with RDKit — molecular
descriptors and Morgan fingerprints per lipid role and payload. A gradient-boosted
tree model (HistGradientBoostingRegressor) is trained on 1,564 published formulations,
drawn from three public sources: LNP Atlas (1,092), a systematic microfluidic liposome
dataset (570), and an in-vitro-release database (272), after removing failed
formulations and non-nanoscale particles.

## Reported performance, and its limits

Under a random train/test split the model reports R² = 0.43 overall. That figure is
**inflated**: formulations from the same publication are near-duplicates, so a random
split places them in both training and test sets and the model can score well by
recognising the source rather than learning the chemistry.

Under source-grouped cross-validation — where all formulations from one publication
sit on one side of the split — performance on genuinely unseen chemistries falls close
to zero. That is the number that describes what a new user would experience, and it is
the central technical problem this project is working on.

This demo is therefore a proof of the pipeline, not a validated screening tool.

## Roadmap

- Model encapsulation efficiency and PDI, the endpoints practitioners rank above particle size
- Stratify by lipid chemical family instead of pooling all published chemistries
- Extract process parameters still held only as free text in source papers
- Add per-prediction feature attribution and confidence bounds
- Wet-lab validation of ~20 predicted formulations with a CRO

Siyao Gui — MSc in Engineering, Technical University of Denmark
