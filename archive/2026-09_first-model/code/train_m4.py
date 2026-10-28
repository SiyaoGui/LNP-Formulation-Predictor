"""
M4: 定target -> split -> 训练模型 -> 报一个可引用的指标
target: particle_size_nm (log10变换，过滤到<=1000nm且排除失败配方)
模型: HistGradientBoostingRegressor（sklearn自带的梯度提升树，替代原计划的XGBoost——
      本次环境网络代理不稳定，xgboost的wheel包(130-300MB)反复下载中断，多次重试后放弃，
      改用sklearn自带实现，同属梯度提升树家族，原生支持缺失值，效果不会有本质差异）
运行前提: pip install scikit-learn（不需要xgboost/rdkit，本脚本只吃M3产出的feature_matrix.parquet）
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import KFold, GroupKFold, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import joblib
import warnings
warnings.filterwarnings('ignore')

df = pd.read_parquet('feature_matrix.parquet')
print('输入:', df.shape)

# =========================================================================
# 1) 筛选训练集
# =========================================================================
# particle_size_nm 长尾里的极端值（>1000nm，最大到113万nm）几乎全部对应两种情况，
# 不该和正常纳米颗粒放进同一个回归任务：
#  (a) Luciani里formation_ok=0的失败配方（脂质聚集成团，不是成型的颗粒）
#  (b) PMC_IVR里少数刻意做成微米级的MLV/多层囊泡（process_notes的structure_type字段能看到），
#      这是另一类真实但不同的颗粒体系，物理机制和纳米级单层脂质体/LNP不是一回事
# 统一按纳米药物递送领域的标准定义过滤到 <=1000nm（同时把a、b两种情况筛掉，比按来源分别写规则更一致），
# 再单独核实一遍Luciani有没有"没被size筛掉但formation_ok=0"的漏网之鱼。
mask = (df.particle_size_nm.notna()) & (df.particle_size_nm <= 1000) & (df.formation_ok.fillna(1) != 0)
data = df[mask].copy()
print(f'训练集: {len(data)} 行（原始{df.particle_size_nm.notna().sum()}行里排除了失败配方/微米级颗粒/缺失值），'
      f'按来源: {data.source_dataset.value_counts().to_dict()}')

y = np.log10(data.particle_size_nm.values)  # 右偏分布，log10变换是这类回归的标准做法

# =========================================================================
# 2) 特征列：排除ID/文本/其它target/QA元信息（避免泄漏），指纹用64位/角色（计算资源折中，
#    见 M4_建模说明.md 里512位版本的对比结果，64位和512位表现几乎一样，先用轻量版）
# =========================================================================
EXCLUDE_COLS = {
    'source_dataset','source_row_id','formulation_id',
    'particle_size_nm','pdi','zeta_potential_mv','encapsulation_efficiency_pct','formation_ok',
    'paper_doi','process_notes',
    'ratio_order_was_ambiguous','composition_pct_was_renormalized',
}
status_cols = [c for c in data.columns if c.endswith('_lipid_status')]
# 2026-07-31新增：工艺相关的类别列（prep_method_std等），和status_cols一样是字符串，
# 不能直接喂给模型，要和status_cols一起做get_dummies。数值型工艺列（flow_ratio_imbalance等）
# 不需要特殊处理——它们不在EXCLUDE_COLS/status_cols/fp_cols里，会自动被feature_cols_numeric收进去。
process_cat_cols = ['prep_method_std', 'device_or_chip_std', 'measurement_instrument_std']
cat_cols_all = status_cols + process_cat_cols
fp_cols_all = [c for c in data.columns if '_fp_' in c]
fp_cols_keep = [c for c in fp_cols_all if int(c.rsplit('_',1)[1]) < 64]  # 每个角色只取前64位

feature_cols_numeric = [c for c in data.columns
                         if c not in EXCLUDE_COLS and c not in cat_cols_all
                         and (c not in fp_cols_all or c in fp_cols_keep)]
X_numeric = data[feature_cols_numeric].copy()
X_status = pd.get_dummies(data[cat_cols_all], prefix=cat_cols_all)
X = pd.concat([X_numeric, X_status], axis=1)
print(f'特征列数: {X.shape[1]}')

# HistGradientBoostingRegressor 原生支持NaN，不需要额外填充/插补——
# 这是对之前讨论的"零向量填充"方案的修正：树模型的缺失值路由比人为填0更合理，
# 填0会让"没数据"和"真实值恰好是0"混为一谈（比如NumHDonors=0是合法真实值，不该等同于"缺失"）

# =========================================================================
# 3) 5折交叉验证：旧方法（行级随机split） vs 新方法（按paper_doi分组）
#    背景：行级随机KFold会让同一篇论文/同一批实验的行同时出现在train和test里，
#    模型有可能记住"这篇论文的配方长这样、粒径大概这个数"而不是真学会组成→粒径的关系。
#    换成GroupKFold，保证同一paper_doi的所有行只出现在train或test其中一边，
#    这是对"整体R²=0.432能不能站得住"这个问题的直接回应，不是可选的加分项。
# =========================================================================
model = HistGradientBoostingRegressor(random_state=42)

# 分组key：按paper_doi。LNP_Atlas有5行没有paper_doi，各自给一个独立占位符单独成组，
# 不能给它们共享同一个占位符——那样等于凭空发明了一个它们本不属于的"同一篇论文"分组。
groups = data['paper_doi'].copy()
null_mask = groups.isna()
groups.loc[null_mask] = [f'__no_doi_row_{i}__' for i in data.index[null_mask]]
n_groups = groups.nunique()
print(f'分组CV用的分组数: {n_groups}（{null_mask.sum()} 行没有paper_doi，各自单独成组）')
print('各来源的唯一paper_doi/组数:', data.groupby('source_dataset').apply(lambda d: groups.loc[d.index].nunique()).to_dict())

kf = KFold(n_splits=5, shuffle=True, random_state=42)
y_pred_log_row = cross_val_predict(model, X, y, cv=kf)

gkf = GroupKFold(n_splits=5, shuffle=True, random_state=42)
y_pred_log_grp = cross_val_predict(model, X, y, cv=gkf, groups=groups)

def _report(y_true_log, y_pred_log, label):
    y_true_nm_, y_pred_nm_ = 10**y_true_log, 10**y_pred_log
    r2_ = r2_score(y_true_log, y_pred_log)
    rmse_ = np.sqrt(mean_squared_error(y_true_nm_, y_pred_nm_))
    mae_ = mean_absolute_error(y_true_nm_, y_pred_nm_)
    print(f'  [{label}] R²(log)={r2_:.3f}  RMSE={rmse_:.1f}nm  MAE={mae_:.1f}nm')
    return r2_, rmse_, mae_, y_pred_nm_

print()
print('=== 整体指标：旧（行级随机split，有跨论文泄漏风险） vs 新（按paper_doi分组，无泄漏） ===')
_, _, _, pred_nm_row = _report(y, y_pred_log_row, '旧-行级随机')
_, _, _, pred_nm_grp = _report(y, y_pred_log_grp, '新-按论文分组')

data['_true_nm'] = 10**y
data['_pred_nm_row'] = pred_nm_row
data['_pred_nm_grp'] = pred_nm_grp

print()
print('=== 按来源拆分：旧 vs 新（同一张表，cv_method列区分） ===')
per_source_rows = []
for src in data.source_dataset.unique():
    sub = data[data.source_dataset == src]
    for method, predcol in [('row_random', '_pred_nm_row'), ('group_by_paper', '_pred_nm_grp')]:
        r2_s = r2_score(np.log10(sub._true_nm), np.log10(sub[predcol]))
        rmse_s = np.sqrt(mean_squared_error(sub._true_nm, sub[predcol]))
        mae_s = mean_absolute_error(sub._true_nm, sub[predcol])
        per_source_rows.append({'source': src, 'cv_method': method, 'n': len(sub),
                                 'R2': r2_s, 'RMSE_nm': rmse_s, 'MAE_nm': mae_s})
        print(f'  [{method:15s}] {src} (n={len(sub)}): R²={r2_s:.3f}  RMSE={rmse_s:.1f}nm  MAE={mae_s:.1f}nm')
pd.DataFrame(per_source_rows).to_csv('m4_per_source_metrics.csv', index=False)

print()
print('=== 分组CV每一折的来源构成（用来暴露Luciani=单一论文这种极端集中情况） ===')
fold_composition = []
for i, (tr_idx, te_idx) in enumerate(gkf.split(X, y, groups=groups)):
    test_counts = data.iloc[te_idx].source_dataset.value_counts().to_dict()
    train_counts = data.iloc[tr_idx].source_dataset.value_counts().to_dict()
    print(f'  fold {i}: test={test_counts}  train={train_counts}')
    fold_composition.append({'fold': i, 'test_composition': test_counts, 'train_composition': train_counts})

# =========================================================================
# 4) 用全部筛选后数据重新训练最终模型（CV只是为了估计泛化能力，产出模型用全部数据训，
#    不受CV方法选择影响——不管CV用哪种分法，最终产出模型的训练方式不变）
# =========================================================================
final_model = HistGradientBoostingRegressor(random_state=42)
final_model.fit(X, y)
joblib.dump(final_model, 'm4_model.joblib')
joblib.dump(list(X.columns), 'm4_feature_columns.joblib')

data[['formulation_id', 'source_dataset', '_true_nm', '_pred_nm_row', '_pred_nm_grp']].to_csv(
    'm4_cv_predictions.csv', index=False)
print()
print('已保存 m4_model.joblib / m4_feature_columns.joblib / m4_cv_predictions.csv / m4_per_source_metrics.csv')
print('注意：m4_per_source_metrics.csv 现在有 cv_method 列区分旧/新方法，报告时以 group_by_paper 为准。')
