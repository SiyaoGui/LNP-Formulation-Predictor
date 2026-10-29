"""
M6 修复脚本（task#12）：基于task#10/#11探索结果，修复merged_formulations.csv里
被识别出的工艺列口径/单位问题。两个原始源文件(Luciani CSV、PMC_IVR sqlite db)
在当前环境下已不可访问（已核实，见M6文档新增章节），所以这是在merge_schema.py
产出的合并表基础上打补丁，不是从原始数据重新merge。

修复清单（只修有充分证据支持、机制清楚的问题；纯语义层面的碎片化只记录不自动改）：
A) flow_ratio_imbalance：Luciani存的是原始FRR定义(=OrgFR/TFR，恒<1)，
   LNP_Atlas存的是"不对称度"定义(=max(a,b)/min(a,b)，恒>=1)——两者数值区间
   完全不重叠(已验证)。用Luciani自己数据字典给出的恒等式 TFR=OrgFR+AqFR，
   把FRR换算成同样的"不对称度"定义：max(FRR,1-FRR)/min(FRR,1-FRR)。
B) total_flow_rate_ml_min_std：修复2行单位错误——process_notes原始文本明确写的是
   "17000 mL/h (17 L/h)"，旧的clean_num()只抓了数字没检查单位，误当成17000 mL/min，
   已扫描全部335行非空值确认只有这2行(同一篇论文)有此问题。
C) measurement_instrument_std / device_or_chip_std / prep_method_std：
   大小写+首尾空格+™®符号归一化，同组内统一成最常见的原始写法。
   （更深的同义词/品牌名合并问题——比如"NanoAssemblr"家族至少15种写法——
    已量化记录在M6文档里，本次不做自动语义合并，避免误判）
"""
import pandas as pd
import numpy as np
import re
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'merged_formulations.csv')
OUT_CSV = os.path.join(HERE, 'merged_formulations_v2.csv')
OUT_PARQUET = os.path.join(HERE, 'merged_formulations_v2.parquet')

df = pd.read_csv(SRC)
print(f'输入: {df.shape}')

# ============================================================
# A) flow_ratio_imbalance
# ============================================================
is_luc = df.source_dataset == 'Luciani'
frr = df.loc[is_luc, 'flow_ratio_imbalance'].astype(float)
harmonized = np.maximum(frr, 1 - frr) / np.minimum(frr, 1 - frr)

df['flow_ratio_imbalance_was_harmonized'] = False
df.loc[is_luc, 'flow_ratio_imbalance_was_harmonized'] = True
df.loc[is_luc, 'flow_ratio_imbalance'] = harmonized

print('\n=== 修复A: flow_ratio_imbalance ===')
print(f'  Luciani 修复前(原始FRR) range: [{frr.min():.3f}, {frr.max():.3f}]  (定义上恒<1)')
print(f'  Luciani 修复后(不对称度)  range: [{harmonized.min():.3f}, {harmonized.max():.3f}]  (定义上恒>=1)')
lnp_range = df.loc[df.source_dataset == 'LNP_Atlas', 'flow_ratio_imbalance'].dropna()
print(f'  LNP_Atlas (未变) range: [{lnp_range.min():.3f}, {lnp_range.max():.3f}]')
overlap_after = set(harmonized.round(2)) & set(lnp_range.round(2))
print(f'  修复后两源数值重叠(四舍五入到小数点后2位)个数: {len(overlap_after)} (修复前是0)')

# ============================================================
# B) total_flow_rate_ml_min_std 单位修正
# ============================================================
def extract_tfr_raw_text(notes):
    m = re.search(r'total_flow_rate_ml_min:\s*([^;]+)', str(notes))
    return m.group(1).strip() if m else np.nan

tfr_text = df['process_notes'].apply(extract_tfr_raw_text)
bad_unit_mask = tfr_text.str.contains(r'/h\b|L/h|mL/hr', case=False, regex=True, na=False)

df['total_flow_rate_ml_min_std_was_unit_corrected'] = False
df.loc[bad_unit_mask, 'total_flow_rate_ml_min_std_was_unit_corrected'] = True
before_vals = df.loc[bad_unit_mask, 'total_flow_rate_ml_min_std'].copy()
df.loc[bad_unit_mask, 'total_flow_rate_ml_min_std'] = df.loc[bad_unit_mask, 'total_flow_rate_ml_min_std'] / 60.0

print('\n=== 修复B: total_flow_rate_ml_min_std 单位修正 ===')
print(f'  受影响行数: {bad_unit_mask.sum()}  formulation_id: {df.loc[bad_unit_mask, "formulation_id"].tolist()}')
print(f'  修复前: {before_vals.tolist()}  ->  修复后: {df.loc[bad_unit_mask, "total_flow_rate_ml_min_std"].tolist()}')

# ============================================================
# C) 类别列文本归一化（大小写/空格/商标符号，不做语义合并）
# ============================================================
def normalize_text(s):
    if pd.isna(s):
        return s
    s2 = str(s).replace('™', '').replace('®', '')
    s2 = re.sub(r'\s+', ' ', s2).strip()
    return s2

print('\n=== 修复C: 类别列文本归一化 ===')
for col in ['measurement_instrument_std', 'device_or_chip_std', 'prep_method_std']:
    before_n = df[col].nunique(dropna=True)
    before_nonnull = df[col].notna().sum()
    norm = df[col].apply(normalize_text)
    key = norm.str.lower()
    rep = (pd.DataFrame({'key': key, 'val': df[col]})
             .dropna(subset=['val'])
             .groupby('key')['val']
             .agg(lambda s: s.value_counts().idxmax()))
    new_col = key.map(rep)
    after_nonnull = new_col.notna().sum()
    assert after_nonnull == before_nonnull, f'{col}: 非空值数量对不上！{before_nonnull} -> {after_nonnull}'
    df[col] = new_col
    after_n = df[col].nunique(dropna=True)
    print(f'  {col}: {before_n} 种取值 -> {after_n} 种取值 (非空行数不变: {before_nonnull})')

# ============================================================
# 保存
# ============================================================
df.to_csv(OUT_CSV, index=False)
df.to_parquet(OUT_PARQUET, index=False)
print(f'\n已保存 {OUT_CSV}')
print(f'已保存 {OUT_PARQUET}')
print(f'shape: {df.shape} (原始: 1934 x 26 + 3个新增审计列 = 1934 x 29)')
print('done.')
