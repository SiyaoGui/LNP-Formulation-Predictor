"""
M3: SMILES -> RDKit 描述符 + Morgan fingerprint -> feature matrix
输入: merged_formulations.csv (M2 产出)
输出: feature_matrix.parquet / feature_matrix_sample.csv, status_summary.csv, failed_smiles_log.csv

运行前提: pip install rdkit --break-system-packages
"""
import pandas as pd
import numpy as np
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors, rdFingerprintGenerator
import warnings
warnings.filterwarnings('ignore')
RDLogger.DisableLog('rdApp.*')

SMILES_JOIN_DELIM = ' |&| '  # 必须和 merge_schema.py 里 _lookup_composite_smiles 用的分隔符一致
                              # 不能用'+'：真实SMILES里的'+'是电荷符号（如磷脂[N+](C)(C)C），会被误切

df = pd.read_csv('merged_formulations.csv')
print('输入:', df.shape)

# =========================================================================
# 1) 补充已核实/近似的 SMILES（M2 阶段发现但没来得及并入的部分）
# =========================================================================
CHOLESTEROL_SMILES = 'CC(C)CCCC(C)C1CCC2C1(CCC3C2CC=C4C3(CCC(C4)O)C)C'  # PubChem CID 5997
CKK_E12_SMILES = ('O=C1NC(CCCCN(CC(CCCCCCCCCC)O)CC(CCCCCCCCCC)O)'
                   'C(NC1CCCCN(CC(CCCCCCCCCC)O)CC(CCCCCCCCCC)O)=O')  # CAS 1432494-65-9，
                   # 与web搜索独立给出的分子式C60H120N4O6交叉核对一致；LNP_Atlas原始数据里这个
                   # 电离脂质的SMILES是坏的（unclosed ring），源数据本身的问题，这里用核实过的替换

def peg_carbamate_dspe(mw):
    """mPEG-DSPE，氨基甲酸酯连接在DSPE游离氨基上。n=round(MW/44)是近似值，不是精确单一分子
    （PEG本身链长有分布）。"""
    n = round(mw/44)
    peg = 'C(=O)OCC' + 'OCC'*(n-1) + 'OC'
    return 'CCCCCCCCCCCCCCCCCC(=O)OCC(COP(=O)(O)OCCN' + peg + ')OC(=O)CCCCCCCCCCCCCCCCC'

def peg_carbonate_dmg(mw):
    """DMG-PEG，碳酸酯连接在DMG（二肉豆蔻酰甘油）游离羟基上。近似结构。"""
    n = round(mw/44)
    return 'CCCCCCCCCCCCCC(=O)OCC(OC(=O)CCCCCCCCCCCCC)COC(=O)O' + 'CC' + 'OCC'*(n-1) + 'OC'

def peg_ether_c14(mw):
    """C14-PEG，十四烷基醚键直接连PEG。近似结构。"""
    n = round(mw/44)
    return 'CCCCCCCCCCCCCCO' + 'CC' + 'OCC'*(n-1) + 'OC'

PEG2000_DSPE = peg_carbamate_dspe(2000)
PEG5000_DSPE = peg_carbamate_dspe(5000)
PEG10000_DSPE = peg_carbamate_dspe(10000)
DMG_PEG5K = peg_carbonate_dmg(5000)
C14_PEG2000 = peg_ether_c14(2000)
APPROXIMATED_SMILES_SET = {PEG2000_DSPE, PEG5000_DSPE, PEG10000_DSPE, DMG_PEG5K, C14_PEG2000}

for label, smi in [('PEG2000-DSPE',PEG2000_DSPE),('PEG5000-DSPE',PEG5000_DSPE),
                    ('PEG10000-DSPE',PEG10000_DSPE),('DMG-PEG5k',DMG_PEG5K),
                    ('C14-PEG2000',C14_PEG2000),('cKK-E12',CKK_E12_SMILES)]:
    assert Chem.MolFromSmiles(smi) is not None, f'{label} 解析失败！'
print('自建/替换的6个结构全部验证通过')

# Luciani：sterol=cholesterol（真实结构），peg=DSPE-PEG（假设PEG2000，原数据未指明链长）
is_luc = df.source_dataset == 'Luciani'
df.loc[is_luc, 'sterol_lipid_smiles'] = CHOLESTEROL_SMILES
df.loc[is_luc, 'peg_lipid_smiles'] = PEG2000_DSPE

# PMC_IVR：3个具名PEG脂质给近似结构（mPEG2000-DSPE-LMWP因为还带多肽，不强行近似，继续留空）
peg_name_map = {'mPEG2000-DSPE-2k': PEG2000_DSPE, 'mPEG-DSPE-5K': PEG5000_DSPE, 'mPEG-DSPE-10K': PEG10000_DSPE}
def resolve_ivr_peg(name):
    if pd.isna(name):
        return np.nan
    parts = str(name).split('+')  # 切名字（"HSPC+HePc"），名字不含'+'，安全
    smis = [peg_name_map.get(p) for p in parts]
    if any(s is None for s in smis):
        return np.nan
    return SMILES_JOIN_DELIM.join(smis)

is_ivr = df.source_dataset == 'PMC_IVR'
df.loc[is_ivr, 'peg_lipid_smiles'] = df.loc[is_ivr, 'peg_lipid_name'].apply(resolve_ivr_peg)

# LNP_Atlas：DMG-PEG5k / C14-PEG 2000 这两个具名类型给近似结构；cKK-E12换成核实过的真实结构
# （注意：有1行电离脂质名字是"Custom lipid"、恰好和cKK-E12共享同一个坏掉的原始SMILES，
#  不能假设它就是cKK-E12，不修，继续留在unparseable）
is_lnp = df.source_dataset == 'LNP_Atlas'
df.loc[is_lnp & (df.peg_lipid_name=='DMG-PEG5k') & df.peg_lipid_smiles.isna(), 'peg_lipid_smiles'] = DMG_PEG5K
df.loc[is_lnp & (df.peg_lipid_name=='C14-PEG 2000') & df.peg_lipid_smiles.isna(), 'peg_lipid_smiles'] = C14_PEG2000
df.loc[df.ionizable_lipid_name=='cKK-E12', 'ionizable_lipid_smiles'] = CKK_E12_SMILES

print()
print('=== 补充后 SMILES 覆盖率（并入近似/修复结构之后）===')
for c in ['ionizable_lipid_smiles','helper_lipid_smiles','sterol_lipid_smiles','peg_lipid_smiles','payload_smiles']:
    print(f'  {c}: {df[c].notna().sum()}/{len(df)} ({df[c].notna().mean()*100:.1f}%)')

# =========================================================================
# 2) 状态分类：not_applicable / unresolved / unparseable / approximated / resolved
# =========================================================================
parse_cache = {}
def parse_one(smi):
    if smi not in parse_cache:
        parse_cache[smi] = Chem.MolFromSmiles(smi)
    return parse_cache[smi]

def classify_role(name, smiles):
    if pd.isna(name):
        return 'not_applicable'      # 这个体系本来就没有这个角色（比如经典脂质体没有电离脂质）
    if pd.isna(smiles):
        return 'unresolved'          # 有名字，没结构（没查到/没核实）
    parts = str(smiles).split(SMILES_JOIN_DELIM)
    if any(parse_one(p) is None for p in parts):
        return 'unparseable'         # 有名字有SMILES字符串，但RDKit解析不出来——源数据本身有问题
    if any(p in APPROXIMATED_SMILES_SET for p in parts):
        return 'approximated'        # 用近似/理想化结构代替（比如PEG链长按MW反推）
    return 'resolved'                # 真实核实过的精确结构

for role in ['ionizable','helper','sterol','peg']:
    df[f'{role}_lipid_status'] = df.apply(
        lambda r: classify_role(r[f'{role}_lipid_name'], r[f'{role}_lipid_smiles']), axis=1)

status_summary = pd.DataFrame([
    {'role': role, 'status': status, 'count': cnt}
    for role in ['ionizable','helper','sterol','peg']
    for status, cnt in df[f'{role}_lipid_status'].value_counts().items()
])
status_summary.to_csv('status_summary.csv', index=False)
print()
print('=== 各角色状态分布 ===')
print(status_summary.pivot(index='role', columns='status', values='count').fillna(0).astype(int).to_string())

# =========================================================================
# 3) 全量SMILES解析校验 + failed list（原M3计划要求的步骤：不能只抽5个就上全量）
# =========================================================================
COMPOSITE_COLS = ['ionizable_lipid_smiles','helper_lipid_smiles','sterol_lipid_smiles','peg_lipid_smiles']
ATOMIC_COLS = ['payload_smiles']  # payload_smiles永远是单一真实分子，从不做多组分拼接，不能按分隔符切

failed_records = []
def check_col(col, splittable):
    for idx, val in df[col].items():
        if pd.isna(val):
            continue
        parts = str(val).split(SMILES_JOIN_DELIM) if splittable else [str(val)]
        for p in parts:
            if parse_one(p) is None:
                failed_records.append({'row_index': idx, 'column': col, 'smiles_fragment': p,
                                        'formulation_id': df.loc[idx,'formulation_id'],
                                        'source_dataset': df.loc[idx,'source_dataset']})
for col in COMPOSITE_COLS:
    check_col(col, splittable=True)
for col in ATOMIC_COLS:
    check_col(col, splittable=False)

failed_df = pd.DataFrame(failed_records)
failed_df.to_csv('failed_smiles_log.csv', index=False)
print()
print(f'=== 全量解析校验：{len(parse_cache)} 个不重复SMILES片段，解析失败 {len(failed_df)} 条（已写入 failed_smiles_log.csv）===')

# =========================================================================
# 4) 描述符 + Morgan fingerprint
# =========================================================================
DESC_FUNCS = {
    'MolWt': Descriptors.MolWt, 'LogP': Descriptors.MolLogP, 'TPSA': Descriptors.TPSA,
    'NumHDonors': Descriptors.NumHDonors, 'NumHAcceptors': Descriptors.NumHAcceptors,
    'NumRotatableBonds': Descriptors.NumRotatableBonds, 'RingCount': rdMolDescriptors.CalcNumRings,
}
N_BITS = 512  # M4阶段如需更高分辨率可调大重算
mfpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=N_BITS)

def mol_descriptors(smi_combo):
    """同一角色如果是多组分复合值（用分隔符连接），描述符取均值，指纹做按位OR合并。"""
    if pd.isna(smi_combo):
        return None
    parts = str(smi_combo).split(SMILES_JOIN_DELIM)
    mols = [parse_one(p) for p in parts]
    if any(m is None for m in mols):
        return None
    descs = {k: float(np.mean([f(m) for m in mols])) for k, f in DESC_FUNCS.items()}
    fp = np.zeros(N_BITS, dtype=int)
    for m in mols:
        fp = np.bitwise_or(fp, mfpgen.GetFingerprintAsNumPy(m).astype(int))
    return descs, fp

ROLE_COLS = {'ionizable':'ionizable_lipid_smiles','helper':'helper_lipid_smiles',
             'sterol':'sterol_lipid_smiles','peg':'peg_lipid_smiles','payload':'payload_smiles'}
feature_blocks = {}
for role, col in ROLE_COLS.items():
    desc_rows, fp_rows = [], []
    for val in df[col]:
        result = mol_descriptors(val)
        if result is None:
            desc_rows.append({k: np.nan for k in DESC_FUNCS})
            fp_rows.append(np.full(N_BITS, np.nan))
        else:
            d, fp = result
            desc_rows.append(d); fp_rows.append(fp)
    desc_df = pd.DataFrame(desc_rows).add_prefix(f'{role}_')
    fp_df = pd.DataFrame(fp_rows, columns=[f'{role}_fp_{i}' for i in range(N_BITS)])
    feature_blocks[role] = pd.concat([desc_df, fp_df], axis=1)
    print(f'{role}: {int(desc_df[f"{role}_MolWt"].notna().sum())}/{len(df)} 行算出了描述符+指纹')

# payload_type 类别编码：LNP_Atlas的核酸大类保留原样；PMC_IVR的具体药物名统一归一类
# （具体是哪个药物已经由payload_smiles算出的分子描述符/指纹表达，不需要也不该再重复开一列，
#  否则会变成"记住这个药物名字→查表得到答案"的捷径，而不是真的从结构学习）
TRUE_CATEGORIES = {'mRNA','siRNA','DNA','ASO','protein','gold_nanoparticles','empty','mRNA, siRNA'}
payload_category = df['payload_type'].apply(lambda x: x if pd.isna(x) or x in TRUE_CATEGORIES else 'small_molecule_drug')
payload_dummies = pd.get_dummies(payload_category.fillna('unknown'), prefix='payload_type')

# =========================================================================
# 5) 组装最终特征矩阵
# =========================================================================
id_cols = df[['source_dataset','source_row_id','formulation_id']]
status_cols = df[[f'{r}_lipid_status' for r in ['ionizable','helper','sterol','peg']]]
pct_cols = df[['ionizable_lipid_pct','helper_lipid_pct','sterol_lipid_pct','peg_lipid_pct']]
target_cols = df[['particle_size_nm','pdi','zeta_potential_mv','encapsulation_efficiency_pct','formation_ok']]
meta_cols = df[['ratio_order_was_ambiguous','composition_pct_was_renormalized','paper_doi','process_notes']]

# 2026-07-31新增：结构化工艺参数（M4分组CV暴露"组间方差>组内方差"之后，回头从三个源的
# 原始数据里挖出来的——之前process_notes是把这些信息拼成一段文本整体丢弃，模型完全看不到）。
# 类别列（prep_method_std/device_or_chip_std/measurement_instrument_std）保持原始字符串，
# 和status_cols一样留给train_m4.py统一做get_dummies；数值列直接传，树模型原生处理NaN。
process_cat_cols = df[['prep_method_std','device_or_chip_std','measurement_instrument_std']]
process_num_cols = df[['flow_ratio_imbalance','total_flow_rate_ml_min_std','process_temp_c_std']]
print()
print('=== 新增工艺特征覆盖率 ===')
for c in list(process_cat_cols.columns) + list(process_num_cols.columns):
    print(f'  {c}: {df[c].notna().sum()}/{len(df)} ({df[c].notna().mean()*100:.1f}%)')

final = pd.concat(
    [id_cols, status_cols, pct_cols] +
    [feature_blocks[r] for r in ['ionizable','helper','sterol','peg','payload']] +
    [payload_dummies, process_cat_cols, process_num_cols, target_cols, meta_cols],
    axis=1
)
print()
print('最终特征矩阵 shape:', final.shape)
final.to_parquet('feature_matrix.parquet', index=False)
final.to_csv('feature_matrix_sample.csv', index=False)
print('已保存 feature_matrix.parquet / feature_matrix_sample.csv')
