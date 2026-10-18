"""
LNP / liposome formulation predictor - working demo.
Input: four lipid roles (ionizable / helper / sterol / PEG) + molar percentages
+ payload type. Output: predicted particle size (nm) and polydispersity index (PDI),
plus a per-prediction breakdown of which formulation component is moving each number.
Models: gradient-boosted trees (HistGradientBoostingRegressor).
- m4_model.joblib: particle size (trained on log10(nm))
- m4_pdi_model.joblib: PDI (trained on raw 0-1 scale)
Both share the same 480-column input schema (m4_feature_columns.joblib).
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import joblib
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors, rdFingerprintGenerator
RDLogger.DisableLog('rdApp.*')

st.set_page_config(page_title="LNP Formulation Predictor", page_icon="🧬")

# ---------------------------------------------------------------------------
# Load models, feature-column order, the lipid lookup table, and the
# per-group baseline values used for the "what's driving this prediction" view.
# ---------------------------------------------------------------------------
@st.cache_resource
def load_artifacts():
    HERE = Path(__file__).resolve().parent
    size_model = joblib.load(HERE / 'm4_model.joblib')
    pdi_model = joblib.load(HERE / 'm4_pdi_model.joblib')
    feature_cols = joblib.load(HERE / 'm4_feature_columns.joblib')
    with open(HERE / 'lipid_lookup.json') as f:
        lookup = json.load(f)
    group_data = joblib.load(HERE / 'feature_group_baseline.joblib')
    return size_model, pdi_model, feature_cols, lookup, group_data

model, pdi_model, FEATURE_COLS, LIPID_LOOKUP, GROUP_DATA = load_artifacts()
BASELINE = GROUP_DATA['baseline']   # column -> typical (mean / most-common) value
GROUP_OF = GROUP_DATA['group_of']   # column -> one of the 6 groups below
GROUP_LABELS = {
    'ionizable': 'Ionizable lipid',
    'helper': 'Helper lipid',
    'sterol': 'Sterol',
    'peg': 'PEG-lipid',
    'payload': 'Payload',
    'process': 'Preparation method / process conditions',
}

DESC_FUNCS = {
    'MolWt': Descriptors.MolWt, 'LogP': Descriptors.MolLogP, 'TPSA': Descriptors.TPSA,
    'NumHDonors': Descriptors.NumHDonors, 'NumHAcceptors': Descriptors.NumHAcceptors,
    'NumRotatableBonds': Descriptors.NumRotatableBonds, 'RingCount': rdMolDescriptors.CalcNumRings,
}
N_BITS = 64  # must match the fingerprint size used at training time
mfpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=N_BITS)

def smiles_to_features(smi, role):
    """One SMILES -> descriptors + fingerprint for that role. None -> all NaN (role absent)."""
    out = {}
    if smi is None:
        for k in DESC_FUNCS:
            out[f'{role}_{k}'] = np.nan
        for i in range(N_BITS):
            out[f'{role}_fp_{i}'] = np.nan
        return out
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        st.error(f'Could not parse the SMILES given for {role}: {smi}')
        for k in DESC_FUNCS:
            out[f'{role}_{k}'] = np.nan
        for i in range(N_BITS):
            out[f'{role}_fp_{i}'] = np.nan
        return out
    for k, f in DESC_FUNCS.items():
        out[f'{role}_{k}'] = f(mol)
    fp = mfpgen.GetFingerprintAsNumPy(mol)
    for i in range(N_BITS):
        out[f'{role}_fp_{i}'] = int(fp[i])
    return out

def build_feature_row(role_smiles, role_status, role_pct, payload_smiles, payload_category):
    """Assemble one feature row identical to training. One-hot categories are derived
    from FEATURE_COLS (the column names pd.get_dummies actually produced at training
    time) rather than hand-listed, which avoids silent misalignment. Any training column
    this form has no input for (for example the preparation-method columns, which are not
    yet collected here) is left as missing and routed by the tree like any other gap."""
    row = {}
    for role in ['ionizable','helper','sterol','peg']:
        row.update(smiles_to_features(role_smiles.get(role), role))
        row[f'{role}_lipid_pct'] = role_pct.get(role, np.nan)
    row.update(smiles_to_features(payload_smiles, 'payload'))

    for c in FEATURE_COLS:
        if c in row:
            continue
        if c.startswith('payload_type_'):
            cat = c[len('payload_type_'):]
            row[c] = (payload_category == cat)
        else:
            matched = False
            for role in ['ionizable','helper','sterol','peg']:
                prefix = f'{role}_lipid_status_'
                if c.startswith(prefix):
                    status = c[len(prefix):]
                    row[c] = (role_status[role] == status)
                    matched = True
                    break
            if not matched:
                row[c] = np.nan  # unrecognised column (e.g. preparation method): leave missing and let the tree route it

    df_row = pd.DataFrame([row])
    return df_row[FEATURE_COLS]

def group_swap_predict(X_row, group):
    """Copy of X_row with every column in `group` replaced by its typical
    (training-set average, or most-common category) value, then predicted with
    both models. Used to show how much a formulation's specific values in one
    group move the prediction away from what a typical formulation would give."""
    cols = [c for c in X_row.columns if GROUP_OF.get(c) == group]
    X_mod = X_row.copy()
    for c in cols:
        X_mod[c] = BASELINE[c]
    X_mod = X_mod.astype(float)
    swapped_nm = 10 ** model.predict(X_mod)[0]
    swapped_pdi = float(np.clip(pdi_model.predict(X_mod)[0], 0.0, 1.0))
    return swapped_nm, swapped_pdi, len(cols)

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("🧬 LNP formulation predictor")
st.caption("Enter a lipid composition and molar percentages to get predicted particle size "
           "and polydispersity index (PDI). The particle-size model is trained on 1,564 "
           "published formulations; the PDI model on 1,275. Both accuracy notes are shown "
           "below each prediction, and both are currently weak under a fair test, see below.")

col1, col2 = st.columns(2)
with col1:
    ion_name = st.selectbox("Ionizable lipid", ["None (classic liposome)"] + sorted(LIPID_LOOKUP['ionizable'].keys()))
    ion_pct = st.number_input("Ionizable lipid, mol %", 0.0, 100.0, 40.0, disabled=(ion_name=="None (classic liposome)"))
    helper_name = st.selectbox("Helper lipid", sorted(LIPID_LOOKUP['helper'].keys()))
    helper_pct = st.number_input("Helper lipid, mol %", 0.0, 100.0, 10.0)
with col2:
    sterol_name = st.selectbox("Sterol", sorted(LIPID_LOOKUP['sterol'].keys()))
    sterol_pct = st.number_input("Sterol, mol %", 0.0, 100.0, 38.5)
    peg_name = st.selectbox("PEG-lipid", ["None"] + sorted(LIPID_LOOKUP['peg'].keys()))
    peg_pct = st.number_input("PEG-lipid, mol %", 0.0, 100.0, 1.5, disabled=(peg_name=="None"))

st.divider()
payload_mode = st.radio("Payload", ["Nucleic acid (mRNA, siRNA, ...)", "Small-molecule drug (enter SMILES)", "Empty formulation"], horizontal=True)
payload_smiles_input, payload_category = None, 'empty'
if payload_mode == "Nucleic acid (mRNA, siRNA, ...)":
    payload_category = st.selectbox("Nucleic acid type", ["mRNA","siRNA","DNA","ASO","protein","gold_nanoparticles"])
elif payload_mode == "Small-molecule drug (enter SMILES)":
    payload_smiles_input = st.text_input("Drug SMILES", placeholder="e.g. doxorubicin: CC1C(C(CC(O1)OC2C(CC3=C(C4=C(C(=C3O)O)C(=O)C5=C(C4=O)C=CC=C5OC)C2(C(=O)CO)O)N)O)O")
    payload_category = 'small_molecule_drug'

total_pct = (ion_pct if ion_name!="None (classic liposome)" else 0) + helper_pct + sterol_pct + (peg_pct if peg_name!="None" else 0)
if abs(total_pct - 100) > 5:
    st.warning(f"The four molar percentages sum to {total_pct:.1f}%. Real formulations sum to about 100%, and predictions are more reliable when they do.")

if st.button("Predict", type="primary"):
    # Validate a user-entered payload SMILES before predicting. Without this check,
    # an unparseable SMILES still produced a prediction built on missing payload
    # features, with only a small error message above it as the only sign of the problem.
    if payload_mode == "Small-molecule drug (enter SMILES)":
        if not payload_smiles_input or Chem.MolFromSmiles(payload_smiles_input) is None:
            st.error("Could not parse the payload SMILES. Enter a valid SMILES string, "
                      "or choose a different payload option, before predicting.")
            st.stop()

    role_smiles = {
        'ionizable': LIPID_LOOKUP['ionizable'].get(ion_name) if ion_name!="None (classic liposome)" else None,
        'helper': LIPID_LOOKUP['helper'].get(helper_name),
        'sterol': LIPID_LOOKUP['sterol'].get(sterol_name),
        'peg': LIPID_LOOKUP['peg'].get(peg_name) if peg_name!="None" else None,
    }
    role_status = {
        'ionizable': 'resolved' if role_smiles['ionizable'] else 'not_applicable',
        'helper': 'resolved',
        'sterol': 'resolved',
        'peg': 'resolved' if role_smiles['peg'] else 'not_applicable',
    }
    role_pct = {
        'ionizable': ion_pct if ion_name!="None (classic liposome)" else np.nan,
        'helper': helper_pct, 'sterol': sterol_pct,
        'peg': peg_pct if peg_name!="None" else np.nan,
    }
    X_row = build_feature_row(role_smiles, role_status, role_pct, payload_smiles_input, payload_category)

    pred_log = model.predict(X_row)[0]
    pred_nm = 10 ** pred_log
    pred_pdi = float(np.clip(pdi_model.predict(X_row)[0], 0.0, 1.0))

    c1, c2 = st.columns(2)
    with c1:
        st.success(f"### {pred_nm:.1f} nm")
        st.caption("Particle size. On a random train/test split this model reports R² = 0.66, "
                   "but formulations from the same publication are near-duplicates, so that "
                   "split lets the model recognise the source rather than learn the chemistry. "
                   "Under source-grouped validation, performance on genuinely unseen "
                   "chemistries is R² = -0.135.")
    with c2:
        st.success(f"### {pred_pdi:.2f} PDI")
        st.caption("Polydispersity index (0 to 1, lower is more uniform). Trained on 1,275 "
                   "formulations with a reported PDI, from 60 publications. Random-split "
                   "R² = 0.46; under source-grouped validation, R² = -0.033, close to a "
                   "flat average-only prediction. Treat this output as exploratory, less "
                   "mature than the size prediction.")

    st.caption("Both predictions used missing values for preparation method (mixing method, "
               "flow rate), which both models were trained on but this form does not yet "
               "collect. Treat these as a demonstration of the pipeline, not a substitute "
               "for experiment.")

    with st.expander("What's driving this prediction?", expanded=True):
        st.write(
            "For each component below, this replaces that component's columns with a "
            "typical value from the training data (the average, for a numeric property; "
            "the most common category, for a categorical one) and asks both models to "
            "predict again. The difference from the real prediction shows how much this "
            "formulation's specific value in that component is moving the number, relative "
            "to a typical formulation. This is a fast, dependency-free sensitivity check, "
            "not SHAP or a formal attribution method, and it describes the model's "
            "behaviour, not the underlying chemistry."
        )
        rows = []
        for g in sorted(set(GROUP_OF.values())):
            swapped_nm, swapped_pdi, n_cols = group_swap_predict(X_row, g)
            rows.append({
                'Component': GROUP_LABELS.get(g, g),
                'Effect on size': pred_nm - swapped_nm,
                'Effect on PDI': pred_pdi - swapped_pdi,
            })
        ddf = pd.DataFrame(rows).sort_values('Effect on size', key=lambda s: s.abs(), ascending=False)
        ddf_display = pd.DataFrame({
            'Component': ddf['Component'],
            'Effect on size': ddf['Effect on size'].map(lambda v: f"{v:+.1f} nm"),
            'Effect on PDI': ddf['Effect on PDI'].map(lambda v: f"{v:+.3f}"),
        })
        st.dataframe(ddf_display, hide_index=True, use_container_width=True)
        st.caption(
            "Positive: this component's specific value pushes the prediction higher than "
            "a typical formulation would give. Negative: lower. The preparation-method row "
            "compares 'no preparation-method input' (since this form does not collect one) "
            "against a typical reported preparation method, not a specific choice you made; "
            "it is a rough measure of how much that missing input matters here, not of a "
            "method you chose."
        )
