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
import base64
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
st.set_page_config(page_title="LipidLens", page_icon=str(HERE / "logo_mark.png"), layout="wide")

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
# Page style: LipidLens tokens and components, kept in style.css next to this file
# (colours, type and spacing from brand/tokens in the GitHub repository).
# ---------------------------------------------------------------------------
st.markdown("<style>" + (HERE / "style.css").read_text(encoding="utf-8") + "</style>",
            unsafe_allow_html=True)

GITHUB = "https://github.com/SiyaoGui/LNP-Formulation-Predictor"


def svg_data_uri(name):
    """An SVG file from this folder as a data URI for an <img>, so the ids inside
    each illustration (gradients, filters) cannot clash with the others."""
    data = (HERE / name).read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(data).decode("ascii")


def html(markup):
    """Render one HTML block on a single line, so Markdown never reads an
    indented line as code."""
    st.markdown(" ".join(s.strip() for s in markup.splitlines()), unsafe_allow_html=True)


def title_block(text, first=False):
    """Section title in a cream block."""
    cls = "ll-title ll-title--first" if first else "ll-title"
    html(f'<h2 class="{cls}">{text}</h2>')


def text_block(*paragraphs):
    html('<div class="ll-text">' + "".join(f"<p>{p}</p>" for p in paragraphs) + "</div>")


# Round 2 (encapsulation efficiency), gradient-boosted trees against the two baselines:
# mean drop in MAE (percentage points) with its 95% interval, from
# modeling/2026-10-20_ee-feasibility/metrics.json (hgb@full_vs_b0, hgb@full_vs_b1).
EE_RESULTS = [
    ("New molecule", (4.99, 3.76, 6.20), (1.12, -0.77, 3.22)),
    ("New chemical family", (4.46, 1.60, 6.51), (0.89, -2.14, 4.99)),
    ("New lab (paper held out)", (0.01, -3.81, 4.73), (1.80, -6.77, 6.47)),
]


def signed(v):
    return f"{v:+.2f}".replace("-", "−")


def ee_chart_svg():
    """Two-panel dot-and-interval chart. Internal back-test coding: filled grey
    square with a dark outline and a solid interval line."""
    half, width = 8.0, 300.0
    k = width / (2 * half)
    rows_y = (90, 150, 210)
    parts = ['<svg class="ll-chart" viewBox="0 0 960 290" role="img" aria-label="Error reduction of the '
             'round 2 model against the constant and nearest-neighbour baselines, with 95% intervals">']
    for (label, _, _), y in zip(EE_RESULTS, rows_y):
        bold = ' font-weight="600"' if label.startswith("New lab") else ""
        parts.append(f'<text x="0" y="{y + 4}" font-size="14" fill="#1B211E"{bold}>{label}</text>')
    panels = ((230.0, "Compared with the constant baseline"),
              (600.0, "Compared with the nearest-neighbour baseline"))
    for i, (x0, title) in enumerate(panels):
        z = x0 + width / 2
        parts.append(f'<text x="{x0:.0f}" y="30" font-size="15" font-weight="600" fill="#1E2B23">{title}</text>')
        parts.append(f'<line x1="{x0:.0f}" y1="240" x2="{x0 + width:.0f}" y2="240" stroke="#8F9792"/>')
        parts.append(f'<line x1="{z:.0f}" y1="56" x2="{z:.0f}" y2="240" stroke="#1B211E" stroke-width="2"/>')
        for t in (-8, -4, 0, 4, 8):
            lab = "0" if t == 0 else signed(t)[:-3]
            parts.append(f'<text x="{z + t * k:.1f}" y="260" font-size="12" fill="#4F5853" '
                         f'text-anchor="middle">{lab}</text>')
        parts.append(f'<text x="{z:.0f}" y="282" font-size="12" fill="#4F5853" text-anchor="middle">'
                     'Error reduction (percentage points)</text>')
        for (_, b0, b1), y in zip(EE_RESULTS, rows_y):
            m, lo, hi = b0 if i == 0 else b1
            xm, xl, xh = z + m * k, z + lo * k, z + hi * k
            parts.append(f'<g stroke="#3C4440" stroke-width="2"><line x1="{xl:.1f}" y1="{y}" x2="{xh:.1f}" y2="{y}"/>'
                         f'<line x1="{xl:.1f}" y1="{y - 6}" x2="{xl:.1f}" y2="{y + 6}"/>'
                         f'<line x1="{xh:.1f}" y1="{y - 6}" x2="{xh:.1f}" y2="{y + 6}"/></g>')
            parts.append(f'<rect x="{xm - 5:.1f}" y="{y - 5}" width="10" height="10" fill="#B4BAB5" '
                         'stroke="#1B211E" stroke-width="1.5"/>')
            parts.append(f'<text x="{xm:.1f}" y="{y - 14}" font-size="12" font-weight="600" fill="#1B211E" '
                         f'text-anchor="middle">{signed(m)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def predicted_card(value):
    """Model output: hollow dashed cyan frame labelled PREDICTED."""
    html(f'<div class="ll-pred"><span class="ll-pred-tag">PREDICTED</span>'
         f'<span class="ll-pred-num">{value}</span></div>')


def html_table(header, rows):
    """Table with 1px rules and tabular figures."""
    head = "".join(f"<th>{h}</th>" for h in header)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    html(f'<div class="ll-scroll"><table class="ll-table"><thead><tr>{head}</tr></thead>'
         f'<tbody>{body}</tbody></table></div>')

# Header, first screen and status strip in one block, so the colour bands touch.
STATUS = [
    ("done", "Done", "Three modelling rounds on published data, each protocol frozen before the run"),
    ("progress", "In progress", "Design of our first fixed-protocol encapsulation experiment"),
    ("planned", "Planned", "Optical bench prototype of the measuring module"),
]
status_html = "".join(
    f'<div class="ll-stat"><span class="ll-mark ll-mark--{k}" aria-hidden="true"></span>'
    f'<div><div class="ll-stat-k">{label}</div><div class="ll-stat-v">{text}</div></div></div>'
    for k, label, text in STATUS
)
html(
    f'<div class="ll-band ll-header"><div class="ll-wrap">'
    f'<img src="{svg_data_uri("logo_white.svg")}" alt="LipidLens">'
    '<span class="ll-kicker">Research prototype</span></div></div>'
    '<div class="ll-band ll-hero"><div class="ll-wrap">'
    '<h1 class="ll-display">Lipid carriers, made by measurement.</h1>'
    '<p class="ll-lede">We are building a measuring and control module for the microfluidic mixers that '
    'labs already use to make lipid nanoparticles and liposomes. It is designed to measure each batch as '
    'it is made, adjust the process, and record every run in one format, so that formulation models can '
    'learn from comparable data.</p>'
    '<div class="ll-note"><strong>Research prototype.</strong> The hardware has not been built, and '
    'nothing on this page has been validated by an independent lab. The first application we are working '
    'towards is small-molecule liposomes for brain delivery.</div></div></div>'
    f'<div class="ll-band ll-status" role="region" aria-label="Project status"><div class="ll-wrap">'
    f'{status_html}</div></div>'
)

tab_overview, tab_data, tab_hw, tab_demo = st.tabs(
    ["Overview", "What the data showed", "Hardware plan", "Earlier model (demo)"]
)

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
with tab_overview:
    col_text, col_fig = st.columns(2, gap="large")
    with col_text:
        title_block("The problem", first=True)
        text_block(
            "Lipid drug carriers are still designed by copying a recipe from a paper and testing it by hand. "
            "In interviews with equipment vendors, a lipid supplier, a contract manufacturer and "
            "users in academia and industry, no one we asked used a prediction tool. Microfluidic mixers "
            "control the mixing, but they do not measure what they make: size is measured offline after "
            "the run, and encapsulation efficiency later still."
        )
        title_block("What we learned from the data")
        text_block(
            "We first tried machine learning on published formulations. Within one experimental setting, "
            "molecular structure does predict encapsulation efficiency. <strong>Across labs the advantage "
            "disappears</strong>, because every lab prepares and measures samples in its own way. Adding more "
            "literature data does not fix that. The details are in the next tab."
        )
    with col_fig:
        html(
            f'<figure class="ll-figure" style="margin-top:32px"><img src="{svg_data_uri("liposome.svg")}" '
            'alt="Schematic cross-section of a liposome: a lipid bilayer around a watery core">'
            '<figcaption class="ll-cap">What we make: a liposome. Schematic, not to scale; liposomes for drug '
            'delivery are often 50 to 200 nm across.</figcaption></figure>'
        )
    title_block("What we are building")
    text_block(
        "A module that sits at the outlet of an existing mixer. It is designed to measure particle size "
        "near-line, use the reading to correct flow and lipid concentration, and later add encapsulation "
        "efficiency. Every run is stored with its prediction and its offline measurement."
    )
    LEVELS = [("done", "L0", "Mixer", "Exists today"), ("", "L1", "Recommend", "Software, next"),
              ("planned", "L2", "Measure", "First prototype"), ("planned", "L3", "Self-correct", "Planned"),
              ("planned", "L4", "Explore", "Long-term goal")]
    html('<ol class="ll-ladder" aria-label="Levels L0 to L4">' + "".join(
        f'<li class="{k}"><span class="ll-lv">{lv}</span><span class="ll-ln">{name}</span>'
        f'<span class="ll-ls">{note}</span></li>' for k, lv, name, note in LEVELS) + '</ol>')
    st.caption("Filled: exists. Solid outline: next. Dashed: planned.")
    title_block("Team")
    text_block(
        "Siyao Gui (models and software; MSc, Technical University of Denmark) and "
        "Akanksha Appaiah (lipid formulation and wet lab).",
        f'Code, data and the full modelling report: <a href="{GITHUB}">GitHub</a>',
    )

# ---------------------------------------------------------------------------
# What the data showed
# ---------------------------------------------------------------------------
with tab_data:
    title_block("Three modelling rounds on published data", first=True)
    text_block(
        "For each round the evaluation protocol was written down and committed before any model was "
        "trained, so the pass criteria could not be chosen after seeing the results. Every result is "
        "compared with a constant baseline that always predicts the mean."
    )
    html_table(["Round", "Data", "Target", "Result"], [
        ["1", "73 formulations, 15 small-molecule drugs, 26 papers", "Particle size",
         "No model beat the constant baseline"],
        ["2", "370 units, 197 ionisable lipids, 37 papers", "Encapsulation efficiency",
         "Beat the baseline in 5 of 5 seeds, until whole papers were held out"],
        ["3", "322 units, 5 payload classes, 55 papers", "Particle size, large molecules",
         "Every model did worse than the baseline"],
    ])

    title_block("Round 2: how much the model reduced the error")
    text_block(
        "Encapsulation efficiency, gradient-boosted trees. Each square is the drop in mean absolute error "
        "compared with a baseline, in percentage points, with its 95% confidence interval. Right of the "
        "zero line means the model did better."
    )
    html(
        f'<figure class="ll-figure"><div class="ll-scroll">{ee_chart_svg()}</div>'
        '<figcaption class="ll-cap ll-legend"><span><span class="ll-sq" aria-hidden="true"></span>'
        'Internal back-test on published data</span><span>Independent lab test: none yet</span>'
        '<span>Source: modeling/2026-10-20_ee-feasibility/metrics.json on GitHub; 5 seeds</span>'
        '</figcaption></figure>'
    )

    title_block("What this means")
    text_block(
        "Particle size depends mostly on how the particles are made. Removing every molecular feature "
        "barely changed the error (<strong>0.192 to 0.198</strong>), and a model given only molecular "
        "features did worse than the baseline (<strong>0.257 against 0.253</strong>). One paper in the data "
        "made atenolol and propranolol with the same lipids: agitation gave about 800 nm, sonication about "
        "30 nm.",
        "Encapsulation efficiency carries a molecular signal, which fits the chemistry: it depends on "
        "lipophilicity, charge and hydrogen bonding. But labs use different assays, N/P ratios, buffers "
        "and payloads, and the same lipid can differ by <strong>20 percentage points</strong> between two "
        "papers. So the signal holds inside one setting and disappears across labs.",
        "None of these numbers is a model accuracy. No model has yet beaten the nearest-neighbour "
        "baseline, which copies the value of the most similar molecule in the training set. The next "
        "step is data measured one way: our own encapsulation experiment under a fixed protocol, and "
        "later the module itself.",
    )

# ---------------------------------------------------------------------------
# Hardware plan
# ---------------------------------------------------------------------------
with tab_hw:
    title_block("A module for the mixer a lab already has", first=True)
    html(
        f'<figure class="ll-figure"><div class="ll-schematic"><span class="ll-label">SCHEMATIC</span>'
        f'<img src="{svg_data_uri("chip_module.svg")}" alt="Top view of a microfluidic mixer with the '
        'add-on sensor at the outlet and a flow controller"></div>'
        '<figcaption class="ll-cap">The chip is existing equipment; the module is a concept in development. '
        'Pumps and chips are bought off the shelf. The new parts are the sensor at the outlet and the '
        'controller that writes settings back to the pumps.</figcaption></figure>'
    )

    title_block("What the sensor measures")
    html_table(["Generation", "Measures", "How"], [
        ["1", "Particle size, PDI, concentration, aggregation, clogging",
         "Light scattering at two or more angles, using their ratio; no reagents"],
        ["2", "Encapsulation efficiency",
         "Near-line assay; method for small-molecule payloads still to be chosen"],
        ["3", "Nucleic-acid concentration, pH, conductivity", "UV at 260 nm, pH and conductivity probes"],
    ])
    text_block(
        "The first version is near-line rather than in-line: standard light scattering cannot measure a "
        "flowing sample, so a valve diverts a small volume into a static flow cell, measures it and "
        "flushes. A delay of 30 to 60 seconds is enough for process control."
    )

    title_block("How the loop works")
    LOOP = ["Set a target size for the current formulation.",
            "Run two or three flow settings and estimate size for each.",
            "Fit the local relationship between flow and size.",
            "Run the settings that hit the target and check the result.",
            "Send a sample to offline DLS to recalibrate the sensor."]
    html('<ol class="ll-steps">' + "".join(
        f'<li><span class="ll-num" aria-hidden="true">{n}</span><span>{s}</span></li>'
        for n, s in enumerate(LOOP, 1)) + '</ol>')
    text_block(
        "Flow rate alone has limited reach: above a certain flow, size stops falling. The second lever is "
        "total lipid concentration, set by an extra dilution pump. The loop does not depend on the "
        "literature model; a good prediction only saves a run or two."
    )

    title_block("Prototype plan")
    html_table(["Stage", "Pass if"], [
        ["1 Optical bench", "Size and concentration separated on calibration beads; under 15% error"],
        ["2 Mixing bench", "Reproducible, tunable liposomes; at least 30 paired data points"],
        ["3 Closed loop", "Two target sizes hit, three runs each within ±10%"],
        ["4a Encapsulation sensor", "Near-line value within 5 percentage points of offline"],
    ])
    st.caption("Stages 1 to 3 are budgeted at 14,000 to 21,000 DKK. Full plan in hardware/README.md on GitHub.")


# ---------------------------------------------------------------------------
# Earlier model (demo)
# ---------------------------------------------------------------------------
with tab_demo:
    html(
        '<div class="ll-note" style="margin-top:32px">This is the first model we built, in September 2026: '
        'particle size and PDI from lipid composition. It is kept here to show the pipeline. Our later '
        'evaluation found that particle size is set mainly by the process, and under a fair test (whole '
        'papers held out) this model does no better than predicting the average. <strong>Do not use its '
        'numbers for decisions.</strong></div>'
    )
    title_block("Particle size and PDI from lipid composition")
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
            predicted_card(f"{pred_nm:.1f} nm")
            st.caption("Particle size. On a random train/test split this model reports R² = 0.66, "
                       "but formulations from the same publication are near-duplicates, so that "
                       "split lets the model recognise the source rather than learn the chemistry. "
                       "Under source-grouped validation, performance on genuinely unseen "
                       "chemistries is R² = -0.135.")
        with c2:
            predicted_card(f"{pred_pdi:.2f} PDI")
            st.caption("Polydispersity index (0 to 1, lower is more uniform). Trained on 1,275 "
                       "formulations with a reported PDI, from 60 publications. Random-split "
                       "R² = 0.46; under source-grouped validation, R² = -0.033, close to a "
                       "flat average-only prediction. Treat this output as exploratory, less "
                       "mature than the size prediction.")

        st.caption("PREDICTED, not measured: hollow dashed frames mark model output. No uncertainty "
                   "interval is shown because under a paper-grouped test this model is no better than "
                   "the average.")
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

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
html(
    '<div class="ll-band ll-footer"><div class="ll-wrap">'
    '<div><b>LipidLens</b><span class="ll-mut">Siyao Gui and Akanksha Appaiah</span></div>'
    f'<div><b>Code, data and modelling reports</b><a href="{GITHUB}">github.com/SiyaoGui/LNP-Formulation-Predictor</a></div>'
    '<div><b>Status</b><span class="ll-mut">Research prototype. Page updated November 2026.</span></div>'
    '</div></div>'
)
