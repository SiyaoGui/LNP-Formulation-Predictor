"""
LNP / 脂质体配方粒径预测器 —— M5 最小可用demo
输入：四个脂质角色(电离/辅助/固醇/PEG) + 摩尔占比 + payload类型 → 预测粒径(nm)
模型：M4训练的 HistGradientBoostingRegressor（见 m4_model.joblib）
"""
import json
import numpy as np
import pandas as pd
import streamlit as st
import joblib
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors, rdFingerprintGenerator
RDLogger.DisableLog('rdApp.*')

st.set_page_config(page_title="LNP Formulation Predictor", page_icon="🧬")

# ---------------------------------------------------------------------------
# 加载模型 + 特征列顺序 + 脂质名字库
# ---------------------------------------------------------------------------
@st.cache_resource
def load_artifacts():
    model = joblib.load('m4_model.joblib')
    feature_cols = joblib.load('m4_feature_columns.joblib')
    with open('lipid_lookup.json') as f:
        lookup = json.load(f)
    return model, feature_cols, lookup

model, FEATURE_COLS, LIPID_LOOKUP = load_artifacts()

DESC_FUNCS = {
    'MolWt': Descriptors.MolWt, 'LogP': Descriptors.MolLogP, 'TPSA': Descriptors.TPSA,
    'NumHDonors': Descriptors.NumHDonors, 'NumHAcceptors': Descriptors.NumHAcceptors,
    'NumRotatableBonds': Descriptors.NumRotatableBonds, 'RingCount': rdMolDescriptors.CalcNumRings,
}
N_BITS = 64  # 和 train_m4.py 里用的位数一致，特征列名才能对上
mfpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=N_BITS)

def smiles_to_features(smi, role):
    """单个SMILES -> 该角色的描述符+指纹字典。smi为None时全部返回NaN（对应'未提供该角色'）。"""
    out = {}
    if smi is None:
        for k in DESC_FUNCS:
            out[f'{role}_{k}'] = np.nan
        for i in range(N_BITS):
            out[f'{role}_fp_{i}'] = np.nan
        return out
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        st.error(f'{role} 的 SMILES 无法解析: {smi}')
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
    """组装成和训练时完全一致的一行特征。不手写one-hot的类别清单——直接照着
    FEATURE_COLS（训练时pd.get_dummies实际产出的列名）反推每一列该填什么，
    避免"类别名字手抄漏了/多了"这种低级但难查的错位bug（app.py v1就踩过一次）。"""
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
                row[c] = np.nan  # 不认识的列（理论上不该出现），保守填NaN让模型自己路由

    df_row = pd.DataFrame([row])
    return df_row[FEATURE_COLS]

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("🧬 LNP / 脂质体配方粒径预测器")
st.caption("M0–M5 demo · 输入脂质组合和摩尔占比，预测配方粒径(nm) · 训练数据：LNP Atlas + Luciani + PMC IVR，共1934条配方，"
           "过滤失败/非常规颗粒后1564条用于建模，5折CV整体R²=0.43（详见项目文档）")

col1, col2 = st.columns(2)
with col1:
    ion_name = st.selectbox("电离脂质 (ionizable lipid)", ["无 (经典脂质体不需要)"] + sorted(LIPID_LOOKUP['ionizable'].keys()))
    ion_pct = st.number_input("电离脂质摩尔占比 %", 0.0, 100.0, 40.0, disabled=(ion_name=="无 (经典脂质体不需要)"))
    helper_name = st.selectbox("辅助脂质 (helper lipid)", sorted(LIPID_LOOKUP['helper'].keys()))
    helper_pct = st.number_input("辅助脂质摩尔占比 %", 0.0, 100.0, 10.0)
with col2:
    sterol_name = st.selectbox("固醇 (sterol)", sorted(LIPID_LOOKUP['sterol'].keys()))
    sterol_pct = st.number_input("固醇摩尔占比 %", 0.0, 100.0, 38.5)
    peg_name = st.selectbox("PEG化脂质 (PEG-lipid)", ["无"] + sorted(LIPID_LOOKUP['peg'].keys()))
    peg_pct = st.number_input("PEG化脂质摩尔占比 %", 0.0, 100.0, 1.5, disabled=(peg_name=="无"))

st.divider()
payload_mode = st.radio("载荷 (payload)", ["核酸类（mRNA/siRNA等）", "小分子药物（输入SMILES）", "不载药（空白配方）"], horizontal=True)
payload_smiles_input, payload_category = None, 'empty'
if payload_mode == "核酸类（mRNA/siRNA等）":
    payload_category = st.selectbox("核酸类型", ["mRNA","siRNA","DNA","ASO","protein","gold_nanoparticles"])
elif payload_mode == "小分子药物（输入SMILES）":
    payload_smiles_input = st.text_input("药物 SMILES", placeholder="例如阿霉素: CC1C(C(CC(O1)OC2C(CC3=C(C4=C(C(=C3O)O)C(=O)C5=C(C4=O)C=CC=C5OC)C2(C(=O)CO)O)N)O)O")
    payload_category = 'small_molecule_drug'

total_pct = (ion_pct if ion_name!="无 (经典脂质体不需要)" else 0) + helper_pct + sterol_pct + (peg_pct if peg_name!="无" else 0)
if abs(total_pct - 100) > 5:
    st.warning(f"四项摩尔占比加总 = {total_pct:.1f}%，偏离100%较多，建议调整（模型没有强制要求，但更接近真实配方会更准）")

if st.button("预测粒径", type="primary"):
    role_smiles = {
        'ionizable': LIPID_LOOKUP['ionizable'].get(ion_name) if ion_name!="无 (经典脂质体不需要)" else None,
        'helper': LIPID_LOOKUP['helper'].get(helper_name),
        'sterol': LIPID_LOOKUP['sterol'].get(sterol_name),
        'peg': LIPID_LOOKUP['peg'].get(peg_name) if peg_name!="无" else None,
    }
    role_status = {
        'ionizable': 'resolved' if role_smiles['ionizable'] else 'not_applicable',
        'helper': 'resolved',
        'sterol': 'resolved',
        'peg': 'resolved' if role_smiles['peg'] else 'not_applicable',
    }
    role_pct = {
        'ionizable': ion_pct if ion_name!="无 (经典脂质体不需要)" else np.nan,
        'helper': helper_pct, 'sterol': sterol_pct,
        'peg': peg_pct if peg_name!="无" else np.nan,
    }
    X_row = build_feature_row(role_smiles, role_status, role_pct, payload_smiles_input, payload_category)
    pred_log = model.predict(X_row)[0]
    pred_nm = 10**pred_log
    st.success(f"### 预测粒径: {pred_nm:.1f} nm")
    st.caption("这是M4 baseline模型（R²≈0.43，按来源拆分后LNP体系R²=0.64、经典脂质体R²=0.40、"
               "PMC_IVR体系R²=-0.32）给出的点估计，不是精确值——尤其是PMC_IVR风格的配方（经典脂质体+小分子药物），"
               "模型目前预测效果不可靠，结果仅供参考，不要当成实验结果的替代。")
