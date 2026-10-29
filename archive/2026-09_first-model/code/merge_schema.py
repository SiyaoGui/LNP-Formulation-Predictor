import pandas as pd
import numpy as np
import re
import os

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 220)

HERE = os.path.dirname(os.path.abspath(__file__))
# 注意(2026-10-19迁移审计添加)：下面三处原始源文件未包含在本仓库中
# (LNP_Atlas原始CSV、Luciani CSV、PMC_IVR sqlite db)，本脚本在本仓库环境下
# 无法端到端跑通，只作为合并逻辑的历史记录保留。可复现的入口见
# docs/migration-report.md。

UNIFIED_COLS = [
    'source_dataset','source_row_id','formulation_id',
    'ionizable_lipid_name','ionizable_lipid_smiles','ionizable_lipid_pct',
    'helper_lipid_name','helper_lipid_smiles','helper_lipid_pct',
    'sterol_lipid_name','sterol_lipid_smiles','sterol_lipid_pct',
    'peg_lipid_name','peg_lipid_smiles','peg_lipid_pct',
    'particle_size_nm','pdi','zeta_potential_mv','encapsulation_efficiency_pct',
    'payload_type','payload_smiles',
    'formation_ok','process_notes','release_curve_file',
    'paper_doi','ratio_order_was_ambiguous','composition_pct_was_renormalized',
    # ---- 2026-07-31 新增：结构化工艺参数（之前三个源的工艺信息全部被塞进process_notes文本里，
    # 从未拆成独立列参与建模——这是M4分组CV发现"组间方差>组内方差"之后回头挖出来的，
    # 三个源原始数据里其实都有可解析的结构化工艺字段，只是没有被用） ----
    'prep_method_std','device_or_chip_std','flow_ratio_imbalance',
    'total_flow_rate_ml_min_std','process_temp_c_std','measurement_instrument_std',
]

def _kv_extract(text, key):
    """从'key1: val1; key2: val2; ...'格式的文本里取某个key的value，取不到返回NaN"""
    if pd.isna(text):
        return np.nan
    for part in str(text).split(';'):
        if ':' in part:
            k, v = part.split(':', 1)
            if k.strip() == key:
                v = v.strip()
                return v if v else np.nan
    return np.nan

def _parse_temp_c(s):
    """把'room temperature'/'25°C'/'22°C for formulation, 35°C for encapsulation'等文本
    近似解析成一个摄氏度数值——取第一个能找到的温度数字，room temperature按25°C算。
    这是粗粒度近似，不是精确值，目的是给模型一个"大概是常温/冷藏/加热"的量级信号。"""
    if pd.isna(s):
        return np.nan
    s = str(s)
    if re.search(r'room temperature', s, re.IGNORECASE):
        return 25.0
    m = re.search(r'(-?\d+\.?\d*)\s*°?C', s)
    return float(m.group(1)) if m else np.nan

def _parse_flow_ratio_imbalance(s):
    """把'3:1 (ethanol:aqueous)'这类文本解析成一个≥1的"不对称程度"数值
    （3:1和1:3都算3.0，不区分哪边是水相哪边是有机相——这个方向性信息在部分行里
    有括号说明、部分没有，为了稳健性统一取绝对不对称程度，而不是强行猜测方向）。"""
    if pd.isna(s):
        return np.nan
    m = re.match(r'^\s*(\d+\.?\d*)\s*:\s*(\d+\.?\d*)', str(s))
    if not m:
        return np.nan
    a, b = float(m.group(1)), float(m.group(2))
    if a == 0 or b == 0:
        return np.nan
    return max(a, b) / min(a, b)

# ---------- 1) LNP Atlas ----------
lnp = pd.read_csv(os.path.join(HERE, 'LNP_Atlas_DB_202509_v1_raw_not_in_repo.csv'), encoding='cp949')  # 原始文件未入库，见上方说明

def split_ratio(r):
    try:
        parts = [float(x) for x in str(r).split(':')]
    except ValueError:
        return [np.nan]*4
    if len(parts) == 4:
        return parts
    return [np.nan]*4

ratios = lnp['lipid_molar_ratio'].apply(split_ratio)
lnp['_ion_pct']  = ratios.apply(lambda x: x[0])
lnp['_ster_pct'] = ratios.apply(lambda x: x[2])
_pos1 = ratios.apply(lambda x: x[1])
_pos3 = ratios.apply(lambda x: x[3])
lnp['_peg_pct']  = np.minimum(_pos1, _pos3)
lnp['_help_pct'] = np.maximum(_pos1, _pos3)
lnp['_ratio_order_ambiguous'] = (_pos1.notna() & _pos3.notna() & (_pos1 != _pos3))

def clean_num(s):
    if pd.isna(s): return np.nan
    s = str(s).strip()
    if re.match(r'^[<>~]', s):
        return np.nan
    if re.search(r'(?<=\d)\s*-\s*\d', s):
        return np.nan
    m = re.match(r'^(-?\d+\.?\d*)', s)
    return float(m.group(1)) if m else np.nan

# ---- 解析synthesis_info里的结构化工艺字段（key:value文本，100%覆盖synthesis_method）----
_syn = lnp['synthesis_info']
lnp['_prep_method'] = _syn.apply(lambda v: _kv_extract(v, 'synthesis_method'))
lnp['_device'] = _syn.apply(lambda v: _kv_extract(v, 'device_used'))
lnp['_flow_ratio_raw'] = _syn.apply(lambda v: _kv_extract(v, 'flow_rate_ratio'))
lnp['_flow_ratio_imbalance'] = lnp['_flow_ratio_raw'].apply(_parse_flow_ratio_imbalance)
lnp['_tfr_raw'] = _syn.apply(lambda v: _kv_extract(v, 'total_flow_rate_ml_min'))
lnp['_tfr_num'] = lnp['_tfr_raw'].apply(clean_num)
lnp['_temp_raw'] = _syn.apply(lambda v: _kv_extract(v, 'temperature_condition'))
lnp['_temp_c'] = lnp['_temp_raw'].apply(_parse_temp_c)

lnp_out = pd.DataFrame({
    'source_dataset': 'LNP_Atlas',
    'source_row_id': lnp['lnp_id'].astype(str),
    'formulation_id': 'LNPAtlas_' + lnp['lnp_id'].astype(str),
    'ionizable_lipid_name': lnp['ionizable_lipid'],
    'ionizable_lipid_smiles': lnp['ionizable_lipid_smiles'],
    'ionizable_lipid_pct': lnp['_ion_pct'],
    'helper_lipid_name': lnp['helper_lipid'],
    'helper_lipid_smiles': lnp['helper_lipid_smiles'],
    'helper_lipid_pct': lnp['_help_pct'],
    'sterol_lipid_name': lnp['sterol_lipid'],
    'sterol_lipid_smiles': lnp['sterol_lipid_smiles'],
    'sterol_lipid_pct': lnp['_ster_pct'],
    'peg_lipid_name': lnp['peg_lipid'],
    'peg_lipid_smiles': lnp['peg_lipid_smiles'],
    'peg_lipid_pct': lnp['_peg_pct'],
    'particle_size_nm': lnp['particle_size_nm_std'].apply(clean_num),
    'pdi': lnp['pdi_std'].apply(clean_num),
    'zeta_potential_mv': lnp['zeta_potential_mv_std'].apply(clean_num),
    'encapsulation_efficiency_pct': lnp['encapsulation_efficiency_percent_std'].apply(clean_num),
    'payload_type': lnp['target_type'],
    'payload_smiles': np.nan,
    'formation_ok': np.nan,
    'process_notes': lnp['synthesis_info'],
    'release_curve_file': np.nan,
    'paper_doi': lnp['paper_doi'],
    'ratio_order_was_ambiguous': lnp['_ratio_order_ambiguous'],
    'composition_pct_was_renormalized': False,
    'prep_method_std': lnp['_prep_method'],
    'device_or_chip_std': lnp['_device'],
    'flow_ratio_imbalance': lnp['_flow_ratio_imbalance'],
    'total_flow_rate_ml_min_std': lnp['_tfr_num'],
    'process_temp_c_std': lnp['_temp_c'],
    'measurement_instrument_std': np.nan,
})

# ---------- 2) Luciani ----------
luc = pd.read_csv(os.path.join(HERE, '02_Liposome_data_raw_not_in_repo.csv'))  # 原始文件未入库，见上方说明
formation_ok = (luc['Size'] <= 1000) & (luc['PDI'] <= 1)

luc_out = pd.DataFrame({
    'source_dataset': 'Luciani',
    'source_row_id': luc.index.astype(str),
    'formulation_id': 'Luciani_' + luc.index.astype(str),
    'ionizable_lipid_name': np.nan,
    'ionizable_lipid_smiles': np.nan,
    'ionizable_lipid_pct': np.nan,
    'helper_lipid_name': luc['Lipid'],
    'helper_lipid_smiles': luc['SMILES'],
    'helper_lipid_pct': luc['Lipid n%'],
    'sterol_lipid_name': 'cholesterol',
    'sterol_lipid_smiles': np.nan,
    'sterol_lipid_pct': luc['CHOL %'],
    'peg_lipid_name': 'DSPE-PEG',
    'peg_lipid_smiles': np.nan,
    'peg_lipid_pct': luc['DSPE-PEG %'],
    'particle_size_nm': luc['Size'],
    'pdi': luc['PDI'],
    'zeta_potential_mv': np.nan,
    'encapsulation_efficiency_pct': np.nan,
    'payload_type': 'empty',
    'payload_smiles': np.nan,
    'formation_ok': formation_ok,
    'process_notes': ('CHIP=' + luc['CHIP'].astype(str) + '; FRR=' + luc['FRR'].astype(str)
                       + '; TFR=' + luc['TFR'].astype(str) + '; Population=' + luc['Population'].astype(str)),
    'release_curve_file': np.nan,
    'paper_doi': '10.1101/2024.07.01.600773',
    'ratio_order_was_ambiguous': False,
    'composition_pct_was_renormalized': False,
    'prep_method_std': 'Microfluidic (chip-based)',
    'device_or_chip_std': 'Luciani_chip_' + luc['CHIP'].astype(str),
    # 注意：FRR是microfluidics里常见定义的flow rate ratio(0-1之间的分数)，
    # 和LNP_Atlas的"3:1"这种比例文本不是同一套量纲，两边只是"物理概念相近"，
    # 不是精确对齐的同一个数值——这是跨源工艺特征里唯一做了近似合并的一处，如实说明。
    'flow_ratio_imbalance': luc['FRR'],
    'total_flow_rate_ml_min_std': luc['TFR'],  # 注意：全部恒为12，方差为0，模型用不上，但如实带上
    'process_temp_c_std': np.nan,
    'measurement_instrument_std': np.nan,
})

# ---------- 3) PMC IVR ----------
import sqlite3

_conn = sqlite3.connect(os.path.join(HERE, 'liposome_IVR_raw_not_in_repo.db'))  # 原始文件未入库，见上方说明

_cn = pd.read_sql('SELECT * FROM component_name', _conn)
_cn['role'] = 'helper'
_cn.loc[_cn.component_name.str.contains('PEG', case=False), 'role'] = 'peg'
_cn.loc[_cn.component_name.str.contains('Cholesterol', case=False) & ~_cn.component_name.str.contains('sialic'), 'role'] = 'sterol'

_fc = pd.read_sql('SELECT * FROM formulation_composition', _conn)
_fc = _fc.merge(_cn[['ID','component_name','role']], left_on='component_ID', right_on='ID', suffixes=('','_c'))
_agg = (_fc.groupby(['formulation_ID','role'])
           .agg(name=('component_name', lambda x: '+'.join(x)),
                pct=('molar_ratio', lambda x: x.sum(min_count=1)))  # min_count=1: 全NaN的组要保持NaN，不能被pandas悄悄算成0
           .reset_index())
_wide = _agg.pivot(index='formulation_ID', columns='role', values=['name','pct'])
_wide.columns = [f'{b}_{a}' for a,b in _wide.columns]
_wide = _wide.reset_index()

# ---- 复查：formulation_composition 里摩尔比总和不等于100的情况（用户要求复查）----
# 141个配方里 139 个 (98.6%) 加总在 98-105 之间，属于正常mol%口径+四舍五入噪音。
# 只有2个真正例外：formulation_ID=3（DSPC:Chol:PEG=2.00:1.00:0.14，总和3.14）和
# formulation_ID=7（HSPC:Chol=1.5:1，总和2.50）——已去原始论文核实，这两个配方原文本身
# 就是按"摩尔比"（如"2:1:0.14"）报的，不是mol%，例如1_2.pdf method部分原文写
# "with mole ratio 2:1:0.14"；1_3.pdf表格里同一张表其余行是"57/38/5"这种百分比，
# 唯独LMVVD这一行写的是"1.5/1"——同一篇论文内部报告口径就不统一，是原始文献的问题，
# 不是数据库或本脚本的错误。
# 另外2个配方（ID=41, 49，都来自AmBisome相关论文）molar_ratio全部是NaN——纯粹是原始数据
# 缺失，不是百分比格式问题。这2个配方在旧版脚本里因为pandas对全NaN分组求和会静默返回0.0
# （而不是NaN），导致合并表误显示为"helper/sterol_pct=0%"；已用 min_count=1 修复，现在
# 正确显示为缺失值。
#
# ---- 归一化：把所有配方的 helper/sterol/peg_pct 统一换算成真正的 mol%（加总=100）----
# 之前一版只是在文档里"标注"了3号、7号配方是原始比例而非百分比，没有真的改数值——
# 这是不完整的修复，会让人以为PEG占比只有0.14%（实际应是0.14/3.14*100=4.5%）。
# 这次直接按行归一化：每个组分的pct除以该配方三列总和再乘100，min_count=1保证
# 全NaN的配方（41/49）归一化后依然是NaN，不会变成除零错误。归一化幅度超过±2%的
# 配方会在 composition_pct_was_renormalized 标记为True，方便审计。
_pct_cols = [c for c in ['helper_pct','sterol_pct','peg_pct'] if c in _wide.columns]
_row_total = _wide[_pct_cols].sum(axis=1, min_count=1)
_wide['composition_pct_was_renormalized'] = (_row_total.notna() & ((_row_total - 100).abs() > 2))
for _c in _pct_cols:
    _wide[_c] = _wide[_c] / _row_total * 100

_formulation = pd.read_sql('SELECT * FROM formulation', _conn)
_cppcqa = pd.read_sql('SELECT * FROM formulation_CPPs_CQAs', _conn)
_api = pd.read_sql('SELECT * FROM API_name', _conn)
_ivr = pd.read_sql('SELECT * FROM IVR', _conn)
_papers = pd.read_sql('SELECT * FROM papers', _conn)

_full = (_ivr.merge(_formulation, left_on='formulation_ID', right_on='ID', suffixes=('_ivr','_form'))
             .merge(_cppcqa, on='formulation_ID', how='left', suffixes=('','_cpp'))
             .merge(_api, left_on='API_ID', right_on='ID', suffixes=('','_api'))
             .merge(_wide, on='formulation_ID', how='left')
             .merge(_papers[['ID','doi']], left_on='paper_id', right_on='ID', suffixes=('','_paper')))

_smiles_ref = pd.read_csv(os.path.join(HERE, 'PMC_IVR_lipid_component_smiles.csv'))  # 这一个文件实际在本仓库里
_name2smiles = dict(zip(_smiles_ref.component_name, _smiles_ref.smiles))

SMILES_JOIN_DELIM = ' |&| '  # 专用分隔符：真实SMILES里的'+'是电荷符号（比如磷脂[N+](C)(C)C），
                              # 不能借用'+'当多组分连接符，否则解析时会把带电原子错误切开

def _lookup_composite_smiles(name):
    if pd.isna(name):
        return np.nan
    parts = str(name).split('+')  # 这里切的是"组分名字"（比如"HSPC+HePc"），名字本身不含'+'，安全
    smis = [_name2smiles.get(p) for p in parts]
    if any(pd.isna(s) or s == '' for s in smis):
        return np.nan
    return SMILES_JOIN_DELIM.join(smis)  # 这里连接的是SMILES本身，必须用安全分隔符

_full['_helper_smiles'] = _full.get('helper_name').apply(_lookup_composite_smiles) if 'helper_name' in _full else np.nan
_full['_sterol_smiles'] = _full.get('sterol_name').apply(_lookup_composite_smiles) if 'sterol_name' in _full else np.nan
_full['_peg_smiles']    = _full.get('peg_name').apply(_lookup_composite_smiles) if 'peg_name' in _full else np.nan

ivr_out = pd.DataFrame({
    'source_dataset': 'PMC_IVR',
    'source_row_id': _full['ID_ivr'].astype(str),
    'formulation_id': 'IVR_formulation_' + _full['formulation_ID'].astype(str),
    'ionizable_lipid_name': np.nan,
    'ionizable_lipid_smiles': np.nan,
    'ionizable_lipid_pct': np.nan,
    'helper_lipid_name': _full.get('helper_name'),
    'helper_lipid_smiles': _full['_helper_smiles'],
    'helper_lipid_pct': _full.get('helper_pct'),
    'sterol_lipid_name': _full.get('sterol_name'),
    'sterol_lipid_smiles': _full['_sterol_smiles'],
    'sterol_lipid_pct': _full.get('sterol_pct'),
    'peg_lipid_name': _full.get('peg_name'),
    'peg_lipid_smiles': _full['_peg_smiles'],
    'peg_lipid_pct': _full.get('peg_pct'),
    'particle_size_nm': _full['particle_size_nm'],
    'pdi': _full['PDI'],
    'zeta_potential_mv': _full['zeta_potential'],
    'encapsulation_efficiency_pct': np.nan,
    'payload_type': _full['API_name'],
    'payload_smiles': _full['SMILES'],
    'formation_ok': np.nan,
    'process_notes': ('release_method=' + _full['release_method'].astype(str)
                       + '; structure_type=' + _full['structure_type'].astype(str)
                       + '; media_pH=' + _full['media_pH'].astype(str)
                       + '; media_temp_oC=' + _full['media_temp_oC'].astype(str)
                       + '; preparation_method=' + _full['preparation_method'].astype(str)),
    'release_curve_file': _full['ID_ivr'].astype(str) + '..csv',
    'paper_doi': _full['doi'],
    'ratio_order_was_ambiguous': False,
    'composition_pct_was_renormalized': _full.get('composition_pct_was_renormalized').fillna(False) if 'composition_pct_was_renormalized' in _full else False,
    # formulation_CPPs_CQAs表里本来就有这些结构化字段，之前只用了structure_type（做outlier过滤）
    # 和preparation_method（塞进process_notes文本），其它几列从没被拉出来当过特征
    'prep_method_std': _full.get('preparation_method'),
    'device_or_chip_std': np.nan,
    'flow_ratio_imbalance': np.nan,
    'total_flow_rate_ml_min_std': np.nan,
    'process_temp_c_std': _full.get('incubation_temp_oC'),
    'measurement_instrument_std': _full.get('PS_instrument'),
})

merged = pd.concat([lnp_out[UNIFIED_COLS], luc_out[UNIFIED_COLS], ivr_out[UNIFIED_COLS]], ignore_index=True)

print('MERGED SHAPE:', merged.shape)
print()
print(merged['source_dataset'].value_counts())
print()

ivr = merged[merged.source_dataset=='PMC_IVR']
print('=== PMC_IVR name/smiles coverage ===')
for c in ['helper_lipid_name','helper_lipid_smiles','sterol_lipid_name','sterol_lipid_smiles','peg_lipid_name','peg_lipid_smiles']:
    print(f'  {c}: {ivr[c].notna().sum()}/{len(ivr)} ({ivr[c].notna().mean()*100:.1f}%)')

print()
print('=== 归一化审计：composition_pct_was_renormalized=True 的配方 ===')
_renorm = ivr[ivr.composition_pct_was_renormalized == True]
print(_renorm[['formulation_id','helper_lipid_pct','sterol_lipid_pct','peg_lipid_pct']].drop_duplicates().to_string())
print(f'共 {_renorm.formulation_id.nunique()} 个配方被重新归一化（阈值：原始总和偏离100超过±2）')

merged.to_csv('merged_formulations.csv', index=False)
merged.to_parquet('merged_formulations.parquet', index=False)
print('saved.')
