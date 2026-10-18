"""
M6 Step 1: SHAP可解释性分析（对应 M6_可解释性与精度提升方案.md 第2.1/2.5节）
复现train_m4.py的特征构造逻辑，对已训练的m4_model.joblib跑SHAP，
产出：(1)全量特征重要性表 (2)按角色/特征类型聚合 (3)多seed稳定性检查
不改动train_m4.py/m4_model.joblib本身，纯只读分析脚本。
"""
import pandas as pd
import numpy as np
import joblib
import warnings
warnings.filterwarnings('ignore')
import shap
from sklearn.ensemble import HistGradientBoostingRegressor

pd.set_option('display.width', 160)

# ========== 1) 复现 train_m4.py 的数据筛选 + 特征构造（保持完全一致，防止和生产模型对不上） ==========
df = pd.read_parquet('feature_matrix.parquet')
mask = (df.particle_size_nm.notna()) & (df.particle_size_nm <= 1000) & (df.formation_ok.fillna(1) != 0)
data = df[mask].copy()
y = np.log10(data.particle_size_nm.values)
print(f'训练集: {len(data)} 行')

EXCLUDE_COLS = {
    'source_dataset', 'source_row_id', 'formulation_id',
    'particle_size_nm', 'pdi', 'zeta_potential_mv', 'encapsulation_efficiency_pct', 'formation_ok',
    'paper_doi', 'process_notes',
    'ratio_order_was_ambiguous', 'composition_pct_was_renormalized',
}
status_cols = [c for c in data.columns if c.endswith('_lipid_status')]
process_cat_cols = ['prep_method_std', 'device_or_chip_std', 'measurement_instrument_std']
cat_cols_all = status_cols + process_cat_cols
fp_cols_all = [c for c in data.columns if '_fp_' in c]
fp_cols_keep = [c for c in fp_cols_all if int(c.rsplit('_', 1)[1]) < 64]

feature_cols_numeric = [c for c in data.columns
                         if c not in EXCLUDE_COLS and c not in cat_cols_all
                         and (c not in fp_cols_all or c in fp_cols_keep)]
X_numeric = data[feature_cols_numeric].copy()
X_status = pd.get_dummies(data[cat_cols_all], prefix=cat_cols_all)
X = pd.concat([X_numeric, X_status], axis=1)

feature_cols_saved = joblib.load('m4_feature_columns.joblib')
extra = set(X.columns) - set(feature_cols_saved)
missing = set(feature_cols_saved) - set(X.columns)
print(f'重建的特征列数: {X.shape[1]} | 保存的特征列数: {len(feature_cols_saved)} | 多出: {len(extra)} | 缺失: {len(missing)}')
X = X.reindex(columns=feature_cols_saved, fill_value=0)
assert list(X.columns) == list(feature_cols_saved), '列顺序/集合和m4_feature_columns.joblib对不上，不能直接复用生产模型！'
print('特征列已核对，和 m4_feature_columns.joblib 完全一致。')

# ========== 2) 加载生产模型，跑SHAP ==========
model = joblib.load('m4_model.joblib')
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)
print(f'SHAP values shape: {shap_values.shape}')

mean_abs_shap = np.abs(shap_values).mean(axis=0)
mean_shap = shap_values.mean(axis=0)

# ========== 3) 按角色/特征类型分类 ==========
def classify(col):
    if col.endswith('_lipid_pct'):
        return col.split('_lipid_pct')[0], 'composition_pct'
    if '_fp_' in col:
        return col.split('_fp_')[0], 'fingerprint_bit'
    for role in ['ionizable', 'helper', 'sterol', 'peg']:
        if col.startswith(role + '_lipid_status_'):
            return role, 'resolution_status'
    if col.startswith('prep_method_std_') or col.startswith('device_or_chip_std_') or col.startswith('measurement_instrument_std_'):
        return 'process', 'process_categorical'
    if col in ('flow_ratio_imbalance', 'total_flow_rate_ml_min_std', 'process_temp_c_std'):
        return 'process', 'process_numeric'
    if col.startswith('payload_type_'):
        return 'payload', 'payload_type_onehot'
    for role in ['ionizable', 'helper', 'sterol', 'peg', 'payload']:
        if col.startswith(role + '_'):
            return role, 'rdkit_descriptor'
    return 'other', 'other'

roles, kinds = zip(*[classify(c) for c in X.columns])
imp = pd.DataFrame({
    'feature': X.columns, 'role': roles, 'kind': kinds,
    'mean_abs_shap': mean_abs_shap, 'mean_shap_signed': mean_shap,
})
imp = imp.sort_values('mean_abs_shap', ascending=False).reset_index(drop=True)
imp['rank'] = imp.index + 1
imp.to_csv('shap_feature_importance.csv', index=False)
print('已保存 shap_feature_importance.csv')

total = imp['mean_abs_shap'].sum()
by_role = imp.groupby('role')['mean_abs_shap'].sum().sort_values(ascending=False)
by_kind = imp.groupby('kind')['mean_abs_shap'].sum().sort_values(ascending=False)
print('\n=== 按角色聚合的SHAP贡献占比 ===')
print((by_role / total * 100).round(1).astype(str) + '%')
print('\n=== 按特征类型聚合的SHAP贡献占比 ===')
print((by_kind / total * 100).round(1).astype(str) + '%')

print('\n=== Top 30 个体特征（不含指纹位，只看可直接解读的） ===')
readable = imp[imp['kind'] != 'fingerprint_bit'].head(30)
print(readable[['rank', 'feature', 'role', 'kind', 'mean_abs_shap', 'mean_shap_signed']].to_string(index=False))

print('\n=== Top 15 指纹位（仅报bit编号，语义解码留待后续） ===')
fp_top = imp[imp['kind'] == 'fingerprint_bit'].head(15)
print(fp_top[['rank', 'feature', 'role', 'mean_abs_shap']].to_string(index=False))

# ========== 4) 多seed稳定性检查 ==========
print('\n=== 多seed稳定性检查（train_m4.py默认random_state=42） ===')
seeds = [42, 0, 1, 7, 123]
top_n = 20
top_sets = {}
for s in seeds:
    m = HistGradientBoostingRegressor(random_state=s)
    m.fit(X, y)
    sv = shap.TreeExplainer(m).shap_values(X)
    mabs = np.abs(sv).mean(axis=0)
    top_feats = set(pd.Series(mabs, index=X.columns).sort_values(ascending=False).head(top_n).index)
    top_sets[s] = top_feats
    print(f'seed={s} 训练完成')

base = top_sets[42]
overlap_rows = []
for s in seeds:
    inter = len(base & top_sets[s])
    overlap_rows.append({'seed': s, 'overlap_with_seed42_top20': inter, 'overlap_pct': round(inter/top_n*100, 1)})
overlap_df = pd.DataFrame(overlap_rows)
overlap_df.to_csv('shap_stability_check.csv', index=False)
print(overlap_df.to_string(index=False))

# pairwise across all seed pairs too, not just vs seed42
all_pairs = []
for i, s1 in enumerate(seeds):
    for s2 in seeds[i+1:]:
        inter = len(top_sets[s1] & top_sets[s2])
        all_pairs.append(inter/top_n*100)
print(f'\n所有seed两两比较的top20重叠率: 均值={np.mean(all_pairs):.1f}%  最小={np.min(all_pairs):.1f}%  最大={np.max(all_pairs):.1f}%')

print('\n完成。')
