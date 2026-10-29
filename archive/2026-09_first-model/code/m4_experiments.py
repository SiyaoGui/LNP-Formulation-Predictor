"""
M4改进试验脚本：在分组CV(按paper_doi,防泄漏)下测试几个改进方向，逐一跑、记录结果。
不覆盖 train_m4.py（那个是生产脚本），这个是探索用的一次性脚本。
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import warnings, sys
warnings.filterwarnings('ignore')

df = pd.read_parquet('feature_matrix.parquet')
mask = (df.particle_size_nm.notna()) & (df.particle_size_nm <= 1000) & (df.formation_ok.fillna(1) != 0)
data_all = df[mask].copy()

EXCLUDE_COLS = {
    'source_dataset','source_row_id','formulation_id',
    'particle_size_nm','pdi','zeta_potential_mv','encapsulation_efficiency_pct','formation_ok',
    'paper_doi','process_notes',
    'ratio_order_was_ambiguous','composition_pct_was_renormalized',
}

def build_groups(data):
    groups = data['paper_doi'].copy()
    null_mask = groups.isna()
    groups.loc[null_mask] = [f'__no_doi_row_{i}__' for i in data.index[null_mask]]
    return groups

def build_X(data, fp_bits=64, include_fp=True, include_source=False):
    status_cols = [c for c in data.columns if c.endswith('_lipid_status')]
    fp_cols_all = [c for c in data.columns if '_fp_' in c]
    fp_cols_keep = [c for c in fp_cols_all if int(c.rsplit('_',1)[1]) < fp_bits] if include_fp else []
    feature_cols_numeric = [c for c in data.columns
                             if c not in EXCLUDE_COLS and c not in status_cols
                             and (c not in fp_cols_all or c in fp_cols_keep)]
    X_numeric = data[feature_cols_numeric].copy()
    X_status = pd.get_dummies(data[status_cols], prefix=status_cols)
    parts = [X_numeric, X_status]
    if include_source:
        X_src = pd.get_dummies(data[['source_dataset']], prefix='source')
        parts.append(X_src)
    return pd.concat(parts, axis=1)

def run_experiment(name, data, model_kwargs=None, fp_bits=64, include_fp=True, include_source=False, n_splits=5):
    model_kwargs = model_kwargs or {}
    X = build_X(data, fp_bits=fp_bits, include_fp=include_fp, include_source=include_source)
    y = np.log10(data.particle_size_nm.values)
    groups = build_groups(data)
    n_groups = groups.nunique()
    n_splits_eff = min(n_splits, n_groups)
    gkf = GroupKFold(n_splits=n_splits_eff, shuffle=True, random_state=42)
    model = HistGradientBoostingRegressor(random_state=42, **model_kwargs)
    y_pred_log = cross_val_predict(model, X, y, cv=gkf, groups=groups)
    r2 = r2_score(y, y_pred_log)
    y_true_nm, y_pred_nm = 10**y, 10**y_pred_log
    rmse = np.sqrt(mean_squared_error(y_true_nm, y_pred_nm))
    mae = mean_absolute_error(y_true_nm, y_pred_nm)
    print(f'[{name}] n={len(data)} groups={n_groups} features={X.shape[1]} kwargs={model_kwargs} '
          f'fp_bits={fp_bits if include_fp else 0} src_feat={include_source}  ->  '
          f'R²={r2:.3f}  RMSE={rmse:.1f}nm  MAE={mae:.1f}nm')
    sys.stdout.flush()
    return {'name': name, 'n': len(data), 'n_groups': n_groups, 'n_features': X.shape[1],
            'R2': r2, 'RMSE_nm': rmse, 'MAE_nm': mae}

results = []

# ---- Exp 1: LNP_Atlas-only, 默认参数（去掉跨源池化的混淆，最干净的一个子问题）----
data_lnp = data_all[data_all.source_dataset == 'LNP_Atlas'].copy()
results.append(run_experiment('1_LNP_Atlas_only_baseline', data_lnp))

# ---- Exp 2: LNP_Atlas-only + 正则化更强的超参数 ----
results.append(run_experiment('2_LNP_Atlas_only_regularized', data_lnp,
    model_kwargs=dict(max_leaf_nodes=15, min_samples_leaf=30, l2_regularization=1.0,
                       learning_rate=0.05, max_iter=300)))

# ---- Exp 3: LNP_Atlas-only + 去掉指纹，只留描述符+配比+状态 ----
results.append(run_experiment('3_LNP_Atlas_only_no_fingerprint', data_lnp, include_fp=False))

# ---- Exp 4: LNP_Atlas-only + 正则化 + 无指纹 ----
results.append(run_experiment('4_LNP_Atlas_only_reg_no_fp', data_lnp, include_fp=False,
    model_kwargs=dict(max_leaf_nodes=15, min_samples_leaf=30, l2_regularization=1.0,
                       learning_rate=0.05, max_iter=300)))

pd.DataFrame(results).to_csv('m4_experiments_results.csv', index=False)
print()
print('全部结果已存 m4_experiments_results.csv')
