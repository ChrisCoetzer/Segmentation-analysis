"""Correctly nominal f8 association and clustering-removal sensitivity."""
import sys,json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import roc_auc_score
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.data import load_dataset,UPLIFT_FEATURES
from src.mixed_clustering import MixedBalancedClustering
from src.segmentation import summarize_groups
out=ROOT/'outputs/feature_exploration';out.mkdir(exist_ok=True)
df=load_dataset('uplift',UPLIFT_FEATURES+['treatment','conversion'])
s=np.load(ROOT/'outputs/mixed_clustering/split_rows.npz');train,est,test=[s[k] for k in ['train','estimation','test']]
x=df.f8.to_numpy();y=df.conversion.to_numpy(dtype=np.int8);t=df.treatment.to_numpy(dtype=np.int8)
categories,codes=np.unique(x[train],return_inverse=True)
rates=np.bincount(codes,weights=y[train])/np.bincount(codes)
lookup=pd.Series(rates,index=categories)
score=lookup.reindex(x[est]).fillna(float(y[train].mean())).to_numpy()
auc=float(roc_auc_score(y[est],score))
print('Nominal f8-only prediction AUC on estimation users:',auc,flush=True)
features=[f for f in UPLIFT_FEATURES if f!='f8']
x=df[features].to_numpy(dtype=np.float64)
model=MixedBalancedClustering(max_depth=5).fit(x[train],features)
le=model.apply(x[est]);lv=model.apply(x[test])
rows=[]
for count in [1,2,4,8,16,32]:
 e=(le+1)//(32//count)-1;v=(lv+1)//(32//count)-1
 cal=summarize_groups(e,t[est],y[est]);ranked=sorted(cal,key=lambda r:(-r['effect'],r['node']))
 rec=summarize_groups(v,t[test],y[test]);chosen=next(r for r in rec if r['node']==ranked[0]['node'])
 rows.append(dict(segments=count,average_lift_per_10k=chosen['effect']*10000,
                  share=chosen['n']/len(test),estimation_effect=ranked[0]['effect']))
report=dict(nominal_f8_conversion_auc=auc,without_f8=rows,notes='Outcome-free mixed clustering fit; rank by estimation uplift; evaluate all users. Removal sensitivity is not causal feature attribution.')
(out/'mixed_f8_check.json').write_text(json.dumps(report,indent=2))
joblib.dump(dict(model=model,features=features),out/'mixed_without_f8.joblib')
print(pd.DataFrame(rows).to_string(index=False))
