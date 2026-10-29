"""
task#13: 用修复后的数据重新跑分组CV，和修复前的数字硬碰硬对比。
不预设结论——如实报告，不管是变好、不变还是变差。
"""
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

pd.set_option('display.width', 160)

HERE = os.path.dirname(os.path.abspath(__file__))
FM_ORIG = os.path.join(HERE, 'feature_matrix.parquet')
V2_MERGED = os.path.join(HERE, 'merged_formulations_v2.csv')
OUT_FM_V2 = os.path.join(HERE, 'feature_matrix_v2.parquet')
OUT_CV_CSV = os.path.join(HERE, 'fix_verification_cv_results.csv')
OUT_ETA_CSV = os.path.join(HERE, 'fix_verification_eta_squared.csv')

# ============================================================
# 1) 构造 feature_matrix_v2.parquet：只替换5个被修复的process列+加2个审计flag，
#    其余2624列(RDKit描述符/指纹/status/payload dummies等)完全不变，直接复用
#    （已验证两个表逐行source_dataset+source_row_id+formulation_id完全对齐）
# ============================================================
fm = pd.read_parquet(FM_ORIG)
v2 = pd.read_csv(V2_MERGED)
assert (fm['formulation_id'].values == v2['formulation_id'].values).all(), '行不对齐，禁止直接覆盖！'

PATCHED_COLS = ['flow_ratio_imbalance', 'total_flow_rate_ml_min_std',
                'measurement_instrument_std', 'device_or_chip_std', 'prep_method_std']
fm_v2 = fm.copy()
for c in PATCHED_COLS:
    fm_v2[c] = v2[c].values
fm_v2['flow_ratio_imbalance_was_harmonized'] = v2['flow_ratio_imbalance_was_harmonized'].values
fm_v2['total_flow_rate_ml_min_std_was_unit_corrected'] = v2['total_flow_rate_ml_min_std_was_unit_corrected'].values
fm_v2.to_parquet(OUT_FM_V2, index=False)
print(f'feature_matrix_v2.parquet 已保存: {fm_v2.shape} (原始 {fm.shape})')

# ============================================================
# 2) 完全复刻 train_m4.py 的CV方法论，对 fm(原始) 和 fm_v2(修复后) 各跑一遍
# ============================================================
EXCLUDE_COLS = {
    'source_dataset', 'source_row_id', 'formulation_id',
    'particle_size_nm', 'pdi', 'zeta_potential_mv', 'encapsulation_efficiency_pct', 'formation_ok',
    'paper_doi', 'process_notes',
    'ratio_order_was_ambiguous', 'composition_pct_was_renormalized',
    # v2独有的2个审计flag列：本身携带"是不是Luciani/是不是这2行"的信息，属于本次修复
    # 引入的元信息，不应该被当成一个新的"有没有效"特征混进去评价，和process_notes同样处理排除
    'flow_ratio_imbalance_was_harmonized', 'total_flow_rate_ml_min_std_was_unit_corrected',
}
PROCESS_CAT_COLS = ['prep_method_std', 'device_or_chip_std', 'measurement_instrument_std']


def build_X_y(data):
    mask = (data.particle_size_nm.notna()) & (data.particle_size_nm <= 1000) & (data.formation_ok.fillna(1) != 0)
    d = data[mask].copy()
    y = np.log10(d.particle_size_nm.values)
    status_cols = [c for c in d.columns if c.endswith('_lipid_status')]
    cat_cols_all = status_cols + PROCESS_CAT_COLS
    fp_cols_all = [c for c in d.columns if '_fp_' in c]
    fp_cols_keep = [c for c in fp_cols_all if int(c.rsplit('_', 1)[1]) < 64]
    feature_cols_numeric = [c for c in d.columns
                             if c not in EXCLUDE_COLS and c not in cat_cols_all
                             and (c not in fp_cols_all or c in fp_cols_keep)]
    X_numeric = d[feature_cols_numeric].copy()
    X_status = pd.get_dummies(d[cat_cols_all], prefix=cat_cols_all)
    X = pd.concat([X_numeric, X_status], axis=1)
    groups = d['paper_doi'].copy()
    null_mask = groups.isna()
    groups.loc[null_mask] = [f'__no_doi_row_{i}__' for i in d.index[null_mask]]
    return d, X, y, groups


def run_cv(data, label):
    d, X, y, groups = build_X_y(data)
    gkf = GroupKFold(n_splits=5, shuffle=True, random_state=42)
    model = HistGradientBoostingRegressor(random_state=42)
    y_pred_log = cross_val_predict(model, X, y, cv=gkf, groups=groups)
    rows = []
    r2_all = r2_score(y, y_pred_log)
    rmse_all = np.sqrt(mean_squared_error(10**y, 10**y_pred_log))
    mae_all = mean_absolute_error(10**y, 10**y_pred_log)
    rows.append({'variant': label, 'source': 'ALL', 'n': len(d), 'R2': r2_all, 'RMSE_nm': rmse_all, 'MAE_nm': mae_all})
    for src in d.source_dataset.unique():
        idx = (d.source_dataset == src).values
        r2_s = r2_score(y[idx], y_pred_log[idx])
        rmse_s = np.sqrt(mean_squared_error(10**y[idx], 10**y_pred_log[idx]))
        mae_s = mean_absolute_error(10**y[idx], 10**y_pred_log[idx])
        rows.append({'variant': label, 'source': src, 'n': int(idx.sum()), 'R2': r2_s, 'RMSE_nm': rmse_s, 'MAE_nm': mae_s})
    out = pd.DataFrame(rows)
    print(f'\n--- {label} (特征数={X.shape[1]}) ---')
    print(out.to_string(index=False))
    return out


print('\n' + '='*78)
print('B) 分组CV对比：修复前 vs 修复后（完全复刻train_m4.py方法论，仅数据不同）')
print('='*78)
res_before = run_cv(fm, 'BEFORE_fix(原始)')
res_after = run_cv(fm_v2, 'AFTER_fix(修复后)')
combined = pd.concat([res_before, res_after], ignore_index=True)
combined.to_csv(OUT_CV_CSV, index=False)

print('\n=== 核心对照表：整体 + 分来源 R² ===')
pivot = combined.pivot(index='source', columns='variant', values='R2')
pivot['delta'] = pivot['AFTER_fix(修复后)'] - pivot['BEFORE_fix(原始)']
print(pivot.to_string())

# ============================================================
# 3) eta-squared复核：flow_ratio_imbalance修复前后，"组间方差占比"是否真的下降了
# ============================================================
def eta_squared(values, groups):
    d_ = pd.DataFrame({'v': values, 'g': groups}).dropna(subset=['v'])
    if d_['g'].nunique() < 2 or len(d_) < 3:
        return np.nan
    grand_mean = d_['v'].mean()
    ss_total = ((d_['v'] - grand_mean) ** 2).sum()
    group_means = d_.groupby('g')['v'].transform('mean')
    ss_between = ((group_means - grand_mean) ** 2).sum()
    return ss_between / ss_total if ss_total > 0 else np.nan


print('\n' + '='*78)
print('C) eta-squared复核：flow_ratio_imbalance 修复前 vs 修复后的"组间(按paper_doi)方差占比"')
print('   （越接近1，说明这一列越像论文身份代理；越低说明越像独立测量的连续信号）')
print('='*78)
d_before, _, _, groups_before = build_X_y(fm)
d_after, _, _, groups_after = build_X_y(fm_v2)
eta_before = eta_squared(d_before['flow_ratio_imbalance'], groups_before)
eta_after = eta_squared(d_after['flow_ratio_imbalance'], groups_after)
print(f'  修复前 eta² = {eta_before:.3f}')
print(f'  修复后 eta² = {eta_after:.3f}')
pd.DataFrame([{'stage': 'before_fix', 'eta_squared': eta_before},
              {'stage': 'after_fix', 'eta_squared': eta_after}]).to_csv(OUT_ETA_CSV, index=False)

print(f'\n已保存: {OUT_FM_V2}')
print(f'已保存: {OUT_CV_CSV}')
print(f'已保存: {OUT_ETA_CSV}')
print('\ndone.')
