"""
修复后CV结果出乎意料：整体和LNP_Atlas的R²反而变差了（ALL: -0.000->-0.135,
LNP_Atlas: 0.048->-0.272），只有PMC_IVR变好了(-0.160->-0.069)，Luciani基本不变。
三处修复(A:flow_ratio harmonize / B:TFR单位修正2行 / C:三个类别列文本归一化)是一起做的，
不知道是谁的锅。这里把三处改动拆开单独测，看清楚到底是谁在起作用、怎么起作用的，
不能笼统地说"修复没用"就完事。
"""
import pandas as pd
import numpy as np
import re
import warnings
warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

FM_ORIG = '/mnt/user-data/uploads/Liposome AI algorithm-圣草酚/feature_matrix.parquet'
MERGED_ORIG = '/mnt/user-data/uploads/Liposome AI algorithm-圣草酚/merged_formulations.csv'
OUT_CSV = '/mnt/user-data/outputs/fix_ablation_cv_results.csv'

fm_base = pd.read_parquet(FM_ORIG)
merged = pd.read_csv(MERGED_ORIG)
assert (fm_base['formulation_id'].values == merged['formulation_id'].values).all()

EXCLUDE_COLS = {
    'source_dataset', 'source_row_id', 'formulation_id',
    'particle_size_nm', 'pdi', 'zeta_potential_mv', 'encapsulation_efficiency_pct', 'formation_ok',
    'paper_doi', 'process_notes',
    'ratio_order_was_ambiguous', 'composition_pct_was_renormalized',
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
    rows = [{'variant': label, 'source': 'ALL', 'n': len(d),
             'R2': r2_score(y, y_pred_log),
             'RMSE_nm': np.sqrt(mean_squared_error(10**y, 10**y_pred_log)),
             'MAE_nm': mean_absolute_error(10**y, 10**y_pred_log)}]
    for src in d.source_dataset.unique():
        idx = (d.source_dataset == src).values
        rows.append({'variant': label, 'source': src, 'n': int(idx.sum()),
                     'R2': r2_score(y[idx], y_pred_log[idx]),
                     'RMSE_nm': np.sqrt(mean_squared_error(10**y[idx], 10**y_pred_log[idx])),
                     'MAE_nm': mean_absolute_error(10**y[idx], 10**y_pred_log[idx])})
    out = pd.DataFrame(rows)
    print(f'\n--- {label} (特征数={X.shape[1]}) ---')
    print(out.to_string(index=False))
    return out


def apply_fix_A(fm):
    """只做flow_ratio_imbalance harmonization"""
    fm = fm.copy()
    is_luc = fm.source_dataset == 'Luciani'
    frr = fm.loc[is_luc, 'flow_ratio_imbalance'].astype(float)
    fm.loc[is_luc, 'flow_ratio_imbalance'] = np.maximum(frr, 1 - frr) / np.minimum(frr, 1 - frr)
    return fm


def apply_fix_B(fm):
    """只修2行TFR单位错误"""
    fm = fm.copy()
    tfr_text = fm['process_notes'].apply(
        lambda n: (re.search(r'total_flow_rate_ml_min:\s*([^;]+)', str(n)) or [None, None])[1]
        if re.search(r'total_flow_rate_ml_min:\s*([^;]+)', str(n)) else np.nan)
    bad = tfr_text.astype(str).str.contains(r'/h\b|L/h|mL/hr', case=False, regex=True, na=False)
    fm.loc[bad, 'total_flow_rate_ml_min_std'] = fm.loc[bad, 'total_flow_rate_ml_min_std'] / 60.0
    return fm


def apply_fix_C(fm):
    """只做3个类别列的大小写/空格/商标符号归一化"""
    fm = fm.copy()
    def normalize_text(s):
        if pd.isna(s):
            return s
        s2 = str(s).replace('™', '').replace('®', '')
        return re.sub(r'\s+', ' ', s2).strip()
    for col in ['measurement_instrument_std', 'device_or_chip_std', 'prep_method_std']:
        norm = fm[col].apply(normalize_text)
        key = norm.str.lower()
        rep = (pd.DataFrame({'key': key, 'val': fm[col]}).dropna(subset=['val'])
                 .groupby('key')['val'].agg(lambda s: s.value_counts().idxmax()))
        fm[col] = key.map(rep)
    return fm


print('='*78)
print('逐项消融：A(flow_ratio) / B(TFR单位) / C(类别归一化) 各自单独的影响')
print('='*78)
res_base = run_cv(fm_base, 'baseline(全部未修)')
res_A = run_cv(apply_fix_A(fm_base), 'only_A(flow_ratio harmonize)')
res_B = run_cv(apply_fix_B(fm_base), 'only_B(TFR单位修正)')
res_C = run_cv(apply_fix_C(fm_base), 'only_C(类别文本归一化)')

all_res = pd.concat([res_base, res_A, res_B, res_C], ignore_index=True)
all_res.to_csv(OUT_CSV, index=False)

print('\n=== 汇总对照表：整体 + 分来源 R²，四个变体并排 ===')
pivot = all_res.pivot(index='source', columns='variant', values='R2')
cols_order = ['baseline(全部未修)', 'only_A(flow_ratio harmonize)', 'only_B(TFR单位修正)', 'only_C(类别文本归一化)']
print(pivot[cols_order].to_string())
print(f'\n已保存: {OUT_CSV}')
print('done.')
