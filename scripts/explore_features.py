"""Feature audit; does not alter app data or fitted production clusters."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data import load_dataset,UPLIFT_FEATURES
out=ROOT/'outputs/feature_exploration';out.mkdir(exist_ok=True)
df=load_dataset('uplift',UPLIFT_FEATURES+['treatment','conversion','visit'])
split=np.load(ROOT/'outputs/balanced_clustering/split_rows.npz')
train=split['train'];est=split['estimation']
sample=df.iloc[train[:200000]][UPLIFT_FEATURES]
corr=sample.corr();corr.to_csv(out/'feature_correlations.csv')
rows=[]
# Distribution summaries use all rows. Outcome association uses only estimation
# rows so evaluation labels do not choose ablations.
for name in UPLIFT_FEATURES:
    s=df[name]
    freq=s.value_counts(dropna=False)
    q=s.quantile([0,.001,.01,.25,.5,.75,.99,.999,1])
    score=df.iloc[est][name].to_numpy()
    target=df.iloc[est].conversion.to_numpy()
    auc=roc_auc_score(target,score)
    mode=freq.index[0]
    mask=df.iloc[est][name].to_numpy()==mode
    rows.append(dict(feature=name,unique_values=len(freq),mode=float(mode),mode_pct=float(freq.iloc[0]/len(df)*100),
                     min=q.loc[0],p001=q.loc[.001],p01=q.loc[.01],q25=q.loc[.25],median=q.loc[.5],q75=q.loc[.75],p99=q.loc[.99],p999=q.loc[.999],max=q.loc[1],
                     std=s.std(),missing=int(s.isna().sum()),infinite=int(np.isinf(s.to_numpy()).sum()),
                     directional_conversion_auc=max(auc,1-auc),auc_direction='increasing' if auc>=.5 else 'decreasing',
                     conversion_rate_at_mode=float(target[mask].mean()),conversion_rate_off_mode=float(target[~mask].mean())))
    print(name,'mode%',round(rows[-1]['mode_pct'],2),'conversion AUC',round(rows[-1]['directional_conversion_auc'],4),flush=True)
p=pd.DataFrame(rows).sort_values('directional_conversion_auc',ascending=False)
p.to_csv(out/'feature_profile.csv',index=False)
pairs=[dict(a=a,b=b,correlation=float(corr.loc[a,b])) for i,a in enumerate(UPLIFT_FEATURES) for b in UPLIFT_FEATURES[i+1:] if abs(corr.loc[a,b])>=.9]
(out/'correlated_pairs.json').write_text(json.dumps(pairs,indent=2))
print(p[['feature','mode_pct','directional_conversion_auc','auc_direction','conversion_rate_at_mode','conversion_rate_off_mode']].to_string(index=False))
print('High correlations',pairs)
