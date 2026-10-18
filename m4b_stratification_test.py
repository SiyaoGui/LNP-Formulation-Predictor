import pandas as pd, numpy as np, warnings, re, sys
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import r2_score, mean_absolute_error
from scipy.stats import spearmanr
warnings.filterwarnings('ignore')
B='/sessions/charming-focused-tesla/mnt/Liposome AI algorithm-圣草酚/'
f = pd.read_parquet(B+'feature_matrix.parquet')
m = pd.read_parquet(B+'merged_formulations.parquet')
assert (f['formulation_id'].values == m['formulation_id'].values).all(), 'row order mismatch'
f = f.copy(); f['formation_ok'] = m['formation_ok'].values
print('rows', len(f), '| formation_ok==0:', (f.formation_ok==0).sum())

TARGETS=['particle_size_nm','pdi','encapsulation_efficiency_pct']
def keep(c):
    mm=re.match(r'(.*)_fp_(\d+)$',c)
    if mm:
        return mm.group(1)!='payload' and int(mm.group(2))<64
    return True
FEATS=[c for c in f.columns if keep(c) and c not in TARGETS+['source_row_id','formulation_id','paper_doi','formation_ok']]

def run(df,target,label,log=True):
    d=df[df[target].notna()].copy(); g=d['paper_doi'].fillna('__na__')
    if len(d)<60 or g.nunique()<5:
        print(f'{label:38s} SKIP n={len(d)} papers={g.nunique()}'); sys.stdout.flush(); return
    X=pd.get_dummies(d[FEATS],dummy_na=False).select_dtypes(include=[np.number,bool]).astype(np.float32)
    y=np.log(d[target].values) if log else d[target].values
    mo=HistGradientBoostingRegressor(random_state=42,max_iter=200,early_stopping=False)
    pred=cross_val_predict(mo,X,y,cv=GroupKFold(n_splits=min(5,g.nunique())),groups=g)
    r2=r2_score(y,pred); yy=np.exp(y) if log else y; pp=np.exp(pred) if log else pred
    rhos=[];gv=g.values
    for doi in pd.unique(gv):
        ii=np.where(gv==doi)[0]
        if len(ii)>=6 and np.std(y[ii])>1e-6:
            r,_=spearmanr(y[ii],pred[ii])
            if not np.isnan(r): rhos.append(r)
    print(f'{label:38s} n={len(d):5d} papers={g.nunique():3d} groupedR2={r2:7.3f} MAE={mean_absolute_error(yy,pp):6.1f} rho_med={np.median(rhos) if rhos else float("nan"):6.3f}')
    sys.stdout.flush()

clean = f[(f.formation_ok!=0)]
win   = clean[(clean.particle_size_nm.isna())|((clean.particle_size_nm>=20)&(clean.particle_size_nm<=500))]

print('\n=== A. PARTICLE SIZE: effect of removing failed formations ===')
run(f,'particle_size_nm','A1 raw (current model)')
run(clean,'particle_size_nm','A2 drop formation_ok==0')
run(win,'particle_size_nm','A3 + window 20-500nm')

print('\n=== B. payload stratification ON CLEAN DATA ===')
run(win[win.payload_type_mRNA==1],'particle_size_nm','B1 mRNA only')
run(win[win.payload_type_siRNA==1],'particle_size_nm','B2 siRNA only')
run(win[(win.payload_type_mRNA==1)|(win.payload_type_siRNA==1)|(win.payload_type_ASO==1)|(win.payload_type_DNA==1)],'particle_size_nm','B3 nucleic acid')
run(win[win.payload_type_empty==1],'particle_size_nm','B4 empty (Luciani)')

print('\n=== C. EE and PDI on clean data ===')
run(clean,'encapsulation_efficiency_pct','C1 EE all',log=False)
run(clean[clean.payload_type_mRNA==1],'encapsulation_efficiency_pct','C2 EE mRNA',log=False)
run(clean,'pdi','C3 PDI all',log=False)
run(win,'pdi','C4 PDI windowed',log=False)
