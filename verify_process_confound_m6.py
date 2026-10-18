"""
M6 后续验证（用户已确认要跑）：
A) 工艺特征是否几乎完全由paper_doi决定（组间方差占比 / 每篇论文唯一值数）
B) 去掉全部6个工艺特征，重跑按paper_doi分组CV，和M4文档已有数字对比
只读诊断脚本。因本次device_bash挂载暂时不可用，改在云端容器里跑，
读取的是从设备暂存过来的 feature_matrix.parquet（内容与设备上的文件一致）。
"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

pd.set_option('display.width', 160)

SRC = '/mnt/user-data/uploads/Liposome AI algorithm-圣草酚/feature_matrix.parquet'
OUT_CSV = '/mnt/user-data/outputs/process_feature_ablation_results.csv'

df = pd.read_parquet(SRC)
mask = (df.particle_size_nm.notna()) & (df.particle_size_nm <= 1000) & (df.formation_ok.fillna(1) != 0)
data = df[mask].copy()
print(f'训练集: {len(data)} 行\n')

PROCESS_CAT_COLS = ['prep_method_std', 'device_or_chip_std', 'measurement_instrument_std']
PROCESS_NUM_COLS = ['flow_ratio_imbalance', 'total_flow_rate_ml_min_std', 'process_temp_c_std']

groups_full = data['paper_doi'].copy()
null_mask = groups_full.isna()
groups_full.loc[null_mask] = [f'__no_doi_row_{i}__' for i in data.index[null_mask]]

# ========== A) 工艺特征是不是几乎等于paper_doi ==========
print('='*70)
print('A) 工艺特征 vs paper_doi：组间方差占比 + 每篇论文唯一值数')
print('='*70)


def eta_squared(values, groups):
    """组间方差占比（eta squared）：越接近1，说明这一列几乎完全由分组(论文)决定，
    组内（同一篇论文内部）几乎没有变化——即这一列更像"论文身份标签"而不是独立测量的连续变量。"""
    d = pd.DataFrame({'v': values, 'g': groups}).dropna(subset=['v'])
    if d['g'].nunique() < 2 or len(d) < 3:
        return np.nan, np.nan, np.nan
    grand_mean = d['v'].mean()
    ss_total = ((d['v'] - grand_mean) ** 2).sum()
    group_means = d.groupby('g')['v'].transform('mean')
    ss_between = ((group_means - grand_mean) ** 2).sum()
    eta2 = ss_between / ss_total if ss_total > 0 else np.nan
    uniq_per_paper = d.groupby('g')['v'].nunique()
    return eta2, uniq_per_paper.mean(), (uniq_per_paper == 1).mean()


print(f'{"特征":32s} {"eta2(组间方差占比)":>18s} {"平均每篇论文唯一值数":>20s} {"单值论文占比":>12s}')
for col in PROCESS_NUM_COLS:
    eta2, mean_uniq, single_val_pct = eta_squared(data[col], groups_full)
    print(f'{col:32s} {eta2:>18.3f} {mean_uniq:>20.2f} {single_val_pct*100:>11.1f}%')

print()
print('分类型工艺列（prep_method_std等）：每篇论文是否只出现1种取值')
for col in PROCESS_CAT_COLS:
    d = pd.DataFrame({'v': data[col], 'g': groups_full}).dropna(subset=['v'])
    uniq_per_paper = d.groupby('g')['v'].nunique()
    print(f'  {col:28s} 覆盖{len(d)}行 | 单值论文占比: {(uniq_per_paper==1).mean()*100:.1f}% | 平均每篇论文唯一值数: {uniq_per_paper.mean():.2f}')

print()
print('--- 专门核实Luciani（此前判断"全部427行来自同一篇论文"）---')
luc = data[data.source_dataset == 'Luciani']
print(f'Luciani行数: {len(luc)} | 唯一paper_doi数: {luc.paper_doi.nunique()}')
print(f'Luciani的 flow_ratio_imbalance 唯一值: {sorted(luc.flow_ratio_imbalance.dropna().unique().tolist())}')
print(f'Luciani的 total_flow_rate_ml_min_std 唯一值: {sorted(luc.total_flow_rate_ml_min_std.dropna().unique().tolist())}')

# ========== B) 去掉工艺特征重跑分组CV ==========
print()
print('='*70)
print('B) 去掉全部6个工艺特征，重跑按paper_doi分组CV（对比M4文档已有数字）')
print('='*70)

EXCLUDE_COLS = {
    'source_dataset', 'source_row_id', 'formulation_id',
    'particle_size_nm', 'pdi', 'zeta_potential_mv', 'encapsulation_efficiency_pct', 'formation_ok',
    'paper_doi', 'process_notes',
    'ratio_order_was_ambiguous', 'composition_pct_was_renormalized',
}
status_cols = [c for c in data.columns if c.endswith('_lipid_status')]
fp_cols_all = [c for c in data.columns if '_fp_' in c]
fp_cols_keep = [c for c in fp_cols_all if int(c.rsplit('_', 1)[1]) < 64]

y = np.log10(data.particle_size_nm.values)


def build_X(include_process):
    cat_cols_all = status_cols + (PROCESS_CAT_COLS if include_process else [])
    exclude = set(EXCLUDE_COLS)
    if not include_process:
        exclude |= set(PROCESS_NUM_COLS)
    feature_cols_numeric = [c for c in data.columns
                             if c not in exclude and c not in cat_cols_all
                             and c not in (PROCESS_CAT_COLS if not include_process else [])
                             and (c not in fp_cols_all or c in fp_cols_keep)]
    X_numeric = data[feature_cols_numeric].copy()
    X_status = pd.get_dummies(data[cat_cols_all], prefix=cat_cols_all)
    return pd.concat([X_numeric, X_status], axis=1)


def run_grouped_cv(include_process, label):
    X = build_X(include_process)
    gkf = GroupKFold(n_splits=5, shuffle=True, random_state=42)
    model = HistGradientBoostingRegressor(random_state=42)
    y_pred_log = cross_val_predict(model, X, y, cv=gkf, groups=groups_full)
    r2_overall = r2_score(y, y_pred_log)
    rows = [{'source': 'ALL', 'n': len(data), 'R2': r2_overall,
             'RMSE_nm': np.sqrt(mean_squared_error(10**y, 10**y_pred_log)),
             'MAE_nm': mean_absolute_error(10**y, 10**y_pred_log)}]
    for src in data.source_dataset.unique():
        idx = (data.source_dataset == src).values
        r2_s = r2_score(y[idx], y_pred_log[idx])
        rmse_s = np.sqrt(mean_squared_error(10**y[idx], 10**y_pred_log[idx]))
        mae_s = mean_absolute_error(10**y[idx], 10**y_pred_log[idx])
        rows.append({'source': src, 'n': int(idx.sum()), 'R2': r2_s, 'RMSE_nm': rmse_s, 'MAE_nm': mae_s})
    out = pd.DataFrame(rows)
    out.insert(0, 'variant', label)
    print(f'\n特征数: {X.shape[1]} ({label})')
    print(out.to_string(index=False))
    return out


res_with = run_grouped_cv(True, 'WITH_process_features')
res_without = run_grouped_cv(False, 'WITHOUT_process_features')

combined = pd.concat([res_with, res_without], ignore_index=True)
combined.to_csv(OUT_CSV, index=False)
print(f'\n已保存 {OUT_CSV}')

print('\n=== 对照表：整体R² ===')
print(f'  WITH    process features: {res_with.iloc[0].R2:.3f}')
print(f'  WITHOUT process features: {res_without.iloc[0].R2:.3f}')
print(f'  (M4文档记录的历史数字：无工艺特征时期 R²=-0.044，补工艺特征后 R²=-0.000，供交叉核对)')
print('\n完成。')
