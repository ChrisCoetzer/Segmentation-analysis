"""Full-population feature sensitivity checks, separate from app results."""
from pathlib import Path
import sys,time,json
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data import load_dataset,UPLIFT_FEATURES
from src.balanced_clustering import BalancedClustering
from src.segmentation import summarize_groups
out=ROOT/'outputs/feature_exploration';out.mkdir(exist_ok=True)
df=load_dataset('uplift',UPLIFT_FEATURES+['treatment','conversion'])
splits=np.load(ROOT/'outputs/balanced_clustering/split_rows.npz')
train,est,test=[splits[k] for k in ['train','estimation','test']]
profile=pd.read_csv(out/'feature_profile.csv').set_index('feature')
# Shared repeated-value indicators are a redundancy diagnostic, not proof of
# interchangeable numeric features or a reason to discard either feature.
# Read mode values at full binary precision, avoiding CSV floating-point rounding.
flags={name:df[name].to_numpy()==df[name].value_counts().index[0] for name in UPLIFT_FEATURES}
flagrows=[]
for i,a in enumerate(UPLIFT_FEATURES):
 for b in UPLIFT_FEATURES[i+1:]:
  agreement=float(np.mean(flags[a]==flags[b]))
  if agreement>.9999:
   flagrows.append(dict(a=a,b=b,matching_mode_indicator_pct=agreement*100))
pd.DataFrame(flagrows).to_csv(out/'shared_mode_indicators.csv',index=False)
print('Shared repeated-value patterns:',flagrows,flush=True)
del flags
base=joblib.load(ROOT/'outputs/balanced_clustering/clustering.joblib')['model']
base_labels=base.apply(df.iloc[test][UPLIFT_FEATURES].to_numpy(dtype=np.float32))
rows,agreements,failures=[],[],[]
t=df.treatment.to_numpy(dtype=np.int8);y=df.conversion.to_numpy(dtype=np.int8)
variants=[('all_features',[]),('without_f8',['f8']),('without_f2_f8',['f2','f8']),('without_f2_f8_f9',['f2','f8','f9']),('clip_0.1_99.9_pct',[])]
for name,drop in variants:
 tick=time.perf_counter()
 features=[f for f in UPLIFT_FEATURES if f not in drop]
 x=df[features].to_numpy(dtype=np.float32)
 if name.startswith('clip'):
  bounds=np.quantile(x[train],[.001,.999],axis=0).astype(np.float32)
  x=np.clip(x,bounds[0],bounds[1])
  np.savez(out/'clip_bounds.npz',lower=bounds[0],upper=bounds[1])
 if name=='all_features':
  model=base
 elif (out/f'{name}.joblib').exists():
  model=joblib.load(out/f'{name}.joblib')['model']
 else:
  import re
  depth=6
  while True:
   try:
    model=BalancedClustering(max_depth=depth).fit(x[train],features)
    break
   except ValueError as error:
    failures.append(dict(variant=name,attempt_depth=depth,error=str(error)))
    match=re.search(r'node (\d+)',str(error))
    depth=int(np.log2(int(match.group(1))+1)) if match else depth-1
    if depth<0:
     raise
  (out/'balance_limitations.json').write_text(json.dumps(failures,indent=2))
 le=model.apply(x[est]);lv=base_labels if name=='all_features' else model.apply(x[test])
 for count in [k for k in [2,4,8,16,32,64] if k<=2**model.max_depth]:
  e=(le+1)//(2**model.max_depth//count)-1;v=(lv+1)//(2**model.max_depth//count)-1
  # Select one cluster with highest ESTIMATION conversion rate, not eval rate.
  est_counts=np.bincount(e);est_positives=np.bincount(e,weights=y[est])
  eligible=np.flatnonzero(est_counts)
  top=int(eligible[np.argmax(est_positives[eligible]/est_counts[eligible])])
  rec=summarize_groups(v,t[test],y[test])
  r=next(r for r in rec if r['node']==top)
  rows.append(dict(variant=name,clusters=count,selected_node=top,customer_share_pct=r['n']/len(test)*100,
       treatment_conversion_capture_pct=r['treated_positives']/int(y[test][t[test]==1].sum())*100,
       control_conversion_capture_pct=r['control_positives']/int(y[test][t[test]==0].sum())*100,
       treatment_rate_pct=r['treatment_rate']*100,control_rate_pct=r['control_rate']*100))
  # Evaluate coassignment on 100k fixed evaluation-feature rows; no labels involved.
  reference=(base_labels[:100000]+1)//(64//count)-1
  agreements.append(dict(variant=name,clusters=count,adjusted_rand_vs_baseline=adjusted_rand_score(reference,v[:100000])))
 joblib.dump(dict(model=model,features=features,removed=drop),out/f'{name}.joblib')
 del x
 print(name,'actual max clusters',2**model.max_depth,'done',round(time.perf_counter()-tick,1),'s',flush=True)
 pd.DataFrame(rows).to_csv(out/'conversion_concentration_ablations.csv',index=False)
 pd.DataFrame(agreements).to_csv(out/'cluster_assignment_sensitivity.csv',index=False)
print(pd.DataFrame(rows).round(3).to_string(index=False))
