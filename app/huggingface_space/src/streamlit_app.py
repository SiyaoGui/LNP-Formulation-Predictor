"""
LipidLens project page with the earlier formulation model as a demo tab.

Earlier model (September 2026), kept as a demo:
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

HERE = Path(__file__).resolve().parent
st.set_page_config(page_title="LipidLens", page_icon="🔬", layout="wide")

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
# Page style: LipidLens colours and type
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stText, p, li, td, th, label, input, button, h1, h2, h3, h4 {
  font-family: 'Archivo', Arial, sans-serif;
}
.block-container { max-width: 1080px; padding-top: 2rem; }
h1, h2, h3 { color: #1E2B23; letter-spacing: 0; }
.ll-band { height: 8px; background: #3A5442; margin: 0 0 24px 0; }
.ll-lede { font-size: 1.25rem; line-height: 1.5; color: #1B211E; max-width: 760px; }
.ll-note { background: #F2EFE3; padding: 14px 18px; color: #1B211E; margin: 8px 0 20px 0; }
.ll-muted { color: #4F5853; }
.ll-num { font-size: 2.2rem; font-weight: 700; color: #1E2B23; line-height: 1.1; }
.ll-cap { color: #4F5853; font-size: 0.95rem; }
.ll-bars { display: flex; gap: 40px; align-items: flex-end; height: 260px; border-bottom: 2px solid #1B211E; margin-top: 12px; }
.ll-bar { width: 150px; display: flex; flex-direction: column; align-items: center; gap: 6px; }
.ll-bar span { font-weight: 700; font-size: 1.4rem; color: #1E2B23; }
.ll-barlabels { display: flex; gap: 40px; }
.ll-barlabels div { width: 150px; text-align: center; color: #4F5853; padding-top: 6px; }
.ll-steps { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; margin: 8px 0 4px 0; }
.ll-step { width: 168px; padding: 12px 14px; color: #1E2B23; }
.ll-step b { display: block; font-size: 1.05rem; }
.ll-step small { color: #4F5853; font-size: 0.9rem; }
.ll-done { background: #3A5442; color: #FBFAF6; }
.ll-done small { color: #E8EDE6; }
.ll-next { border: 2px solid #3A5442; }
.ll-plan { border: 2px dashed #3A5442; }
</style>
""", unsafe_allow_html=True)

GITHUB = "https://github.com/SiyaoGui/LNP-Formulation-Predictor"

st.markdown('<div class="ll-band">&nbsp;</div>', unsafe_allow_html=True)
st.image((HERE / "logo.svg").read_text(), width=280)
st.markdown(
    '<p class="ll-lede">LipidLens is a measuring and control module for the microfluidic mixers '
    'that labs already use to make lipid nanoparticles and liposomes. It measures every batch as it '
    'is made, corrects the process, and records each run in one format, so that formulation models '
    'can finally learn from comparable data.</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="ll-note">Research prototype. The hardware has not been built yet, and no result on '
    'this page has been validated by an independent lab. The first application we are working towards '
    'is small-molecule liposomes for brain delivery.</div>',
    unsafe_allow_html=True,
)

tab_overview, tab_data, tab_hw, tab_demo = st.tabs(
    ["Overview", "What the data showed", "Hardware plan", "Earlier model (demo)"]
)

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
with tab_overview:
    st.subheader("The problem")
    st.write(
        "Lipid drug carriers are still designed by copying a recipe from a paper and testing it by hand. "
        "In interviews with equipment vendors, a lipid supplier, a contract manufacturer and "
        "users in academia and industry, no one we asked used a prediction tool. Microfluidic mixers "
        "control the mixing, but they do not measure what they make: size is measured offline after "
        "the run, and encapsulation efficiency later still."
    )
    st.subheader("What we learned from the data")
    st.write(
        "We first tried machine learning on published formulations. Within one experimental setting, "
        "molecular structure does predict encapsulation efficiency. Across labs the advantage disappears, "
        "because every lab prepares and measures samples in its own way. Adding more literature data "
        "does not fix that. The details are in the next tab."
    )
    st.subheader("What we are building")
    st.write(
        "A module that sits at the outlet of an existing mixer. It measures particle size near-line, "
        "uses the reading to correct flow and lipid concentration, and later adds encapsulation "
        "efficiency. Every run is stored with its prediction and its offline measurement."
    )
    st.markdown(
        '<div class="ll-steps">'
        '<div class="ll-step ll-done" style="height:96px"><b>L0 Mixer</b><small>exists today</small></div>'
        '<div class="ll-step ll-next" style="height:108px"><b>L1 Recommend</b><small>software, next</small></div>'
        '<div class="ll-step ll-plan" style="height:120px"><b>L2 Measure</b><small>first prototype</small></div>'
        '<div class="ll-step ll-plan" style="height:132px"><b>L3 Self-correct</b><small>planned</small></div>'
        '<div class="ll-step ll-plan" style="height:144px"><b>L4 Explore</b><small>long-term goal</small></div>'
        '</div><p class="ll-cap">Filled: exists. Solid outline: next. Dashed: planned.</p>',
        unsafe_allow_html=True,
    )
    st.subheader("Team")
    st.write(
        "Siyao Gui (models and software; MSc, Technical University of Denmark) and "
        "Akanksha Appaiah (lipid formulation and wet lab)."
    )
    st.markdown(f"Code, data and the full modelling report: [GitHub]({GITHUB})")

# ---------------------------------------------------------------------------
# What the data showed
# ---------------------------------------------------------------------------
with tab_data:
    st.subheader("Three modelling rounds on published data")
    st.write(
        "For each round the evaluation protocol was written down and committed before any model was "
        "trained, so the pass criteria could not be chosen after seeing the results. Every result is "
        "compared with a constant baseline that always predicts the mean."
    )
    st.table(pd.DataFrame({
        "Round": ["1", "2", "3"],
        "Data": ["73 formulations, 15 small-molecule drugs, 26 papers",
                 "370 units, 197 ionisable lipids, 37 papers",
                 "322 units, 5 payload classes, 55 papers"],
        "Target": ["Particle size", "Encapsulation efficiency", "Particle size, large molecules"],
        "Result": ["No model beat the constant baseline",
                   "Beat the baseline in 5 of 5 seeds, until whole papers were held out",
                   "Every model did worse than the baseline"],
    }).set_index("Round"))

    st.subheader("Encapsulation efficiency: how much better than the average")
    st.markdown(
        '<div class="ll-bars">'
        '<div class="ll-bar"><span>+27%</span><div style="width:120px;height:200px;background:#3A5442"></div></div>'
        '<div class="ll-bar"><span>+23%</span><div style="width:120px;height:166px;background:#3A5442"></div></div>'
        '<div class="ll-bar"><span style="color:#A3372B">0%</span><div style="width:120px;height:4px;background:#A3372B"></div></div>'
        '</div>'
        '<div class="ll-barlabels"><div>New molecule</div><div>New chemical family</div>'
        '<div style="color:#A3372B;font-weight:600">New lab (paper held out)</div></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Skill = (baseline error minus model error) / baseline error, round 2. "
        "The first two are significant in 5 of 5 seeds; the third is not."
    )

    st.subheader("What this means")
    st.markdown(
        "Particle size depends mostly on how the particles are made. Removing every molecular feature "
        "barely changed the error (0.192 to 0.198), and a model given only molecular features did worse "
        "than the baseline (0.257 against 0.253). One paper in the data made atenolol and propranolol "
        "with the same lipids: agitation gave about 800 nm, sonication about 30 nm.\n\n"
        "Encapsulation efficiency carries a molecular signal, which fits the chemistry: it depends on "
        "lipophilicity, charge and hydrogen bonding. But labs use different assays, N/P ratios, buffers "
        "and payloads, and the same lipid can differ by 20 percentage points between two papers. So the "
        "signal holds inside one setting and disappears across labs.\n\n"
        "None of these numbers is a model accuracy. No model has yet beaten the nearest-neighbour "
        "baseline, which copies the value of the most similar molecule in the training set. The next "
        "step is data measured one way: our own encapsulation experiment under a fixed protocol, and "
        "later the module itself."
    )

# ---------------------------------------------------------------------------
# Hardware plan
# ---------------------------------------------------------------------------
with tab_hw:
    st.subheader("A module for the mixer a lab already has")
    st.image((HERE / "chip_module.svg").read_text(), width="stretch",
             caption="Schematic. The chip is existing equipment; the module is a concept in development.")
    st.write(
        "Pumps and chips are bought off the shelf. The new parts are the sensor at the outlet and the "
        "controller that writes settings back to the pumps."
    )

    st.subheader("What the sensor measures")
    st.table(pd.DataFrame({
        "Generation": ["1", "2", "3"],
        "Measures": ["Particle size, PDI, concentration, aggregation, clogging",
                     "Encapsulation efficiency",
                     "Nucleic-acid concentration, pH, conductivity"],
        "How": ["Light scattering at two or more angles, using their ratio; no reagents",
                "Near-line assay; method for small-molecule payloads still to be chosen",
                "UV at 260 nm, pH and conductivity probes"],
    }).set_index("Generation"))
    st.write(
        "The first version is near-line rather than in-line: standard light scattering cannot measure a "
        "flowing sample, so a valve diverts a small volume into a static flow cell, measures it and "
        "flushes. A delay of 30 to 60 seconds is enough for process control."
    )

    st.subheader("How the loop works")
    st.markdown(
        "1. Set a target size for the current formulation.\n"
        "2. Run two or three flow settings and estimate size for each.\n"
        "3. Fit the local relationship between flow and size.\n"
        "4. Run the settings that hit the target and check the result.\n"
        "5. Send a sample to offline DLS to recalibrate the sensor."
    )
    st.write(
        "Flow rate alone has limited reach: above a certain flow, size stops falling. The second lever is "
        "total lipid concentration, set by an extra dilution pump. The loop does not depend on the "
        "literature model; a good prediction only saves a run or two."
    )

    st.subheader("Prototype plan")
    st.table(pd.DataFrame({
        "Stage": ["1 Optical bench", "2 Mixing bench", "3 Closed loop", "4a Encapsulation sensor"],
        "Pass if": ["Size and concentration separated on calibration beads; under 15% error",
                    "Reproducible, tunable liposomes; at least 30 paired data points",
                    "Two target sizes hit, three runs each within ±10%",
                    "Near-line value within 5 percentage points of offline"],
    }).set_index("Stage"))
    st.caption("Stages 1 to 3 are budgeted at 14,000 to 21,000 DKK. Full plan in hardware/README.md on GitHub.")


# ---------------------------------------------------------------------------
# Earlier model (demo)
# ---------------------------------------------------------------------------
with tab_demo:
    st.markdown(
        '<div class="ll-note">This is the first model we built, in September 2026: particle size and PDI '
        'from lipid composition. It is kept here to show the pipeline. Our later evaluation found that '
        'particle size is set mainly by the process, and under a fair test (whole papers held out) this '
        'model does no better than predicting the average. Do not use its numbers for decisions.</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Particle size and PDI from lipid composition")
    st.caption("Size model trained on 1,564 published formulations, PDI model on 1,275. "
               "Grouped by paper, R² is -0.135 for size and -0.033 for PDI.")
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
            st.dataframe(ddf_display, hide_index=True, width="stretch")
            st.caption(
                "Positive: this component's specific value pushes the prediction higher than "
                "a typical formulation would give. Negative: lower. The preparation-method row "
                "compares 'no preparation-method input' (since this form does not collect one) "
                "against a typical reported preparation method, not a specific choice you made; "
                "it is a rough measure of how much that missing input matters here, not of a "
                "method you chose."
            )
