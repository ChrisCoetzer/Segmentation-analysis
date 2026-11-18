"""Explore feature-defined audience schemes; leave the application unchanged."""
from pathlib import Path
import sys, json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'outputs/metadata_exploration'
OUT.mkdir(exist_ok=True)
FEATURES=[f'f{i}' for i in range(12)]
CATS=['f8','f9','f4','f11','f3','f5','f1','f6']
CONT=['f0','f2','f7','f10']

def summarize(counts, keys):
    out=pd.DataFrame(counts,columns=['n','treated','visits','conversions','exposed','treated_visits','treated_conversions'])
    for k,v in keys.items():out[k]=v
    out['control']=out.n-out.treated
    for outcome,plural in [('visit','visits'),('conversion','conversions')]:
        a=out['treated_'+plural]; b=out[plural]-a
        out[outcome+'_rate']=out[plural]/out.n.replace(0,np.nan)
        out[outcome+'_treatment_rate']=a/out.treated.replace(0,np.nan)
        out[outcome+'_control_rate']=b/out.control.replace(0,np.nan)
        out[outcome+'_effect_per_10k']=10000*(out[outcome+'_treatment_rate']-out[outcome+'_control_rate'])
        out[outcome+'_se_per_10k']=10000*np.sqrt(out[outcome+'_treatment_rate']*(1-out[outcome+'_treatment_rate'])/out.treated.replace(0,np.nan)+out[outcome+'_control_rate']*(1-out[outcome+'_control_rate'])/out.control.replace(0,np.nan))
    return out

def main():
    split=np.load(ROOT/'outputs/mixed_clustering/split_rows.npz')
    partition=np.zeros(13979592,dtype=np.uint8)
    partition[split['estimation']]=1;partition[split['test']]=2
    rng=np.random.default_rng(20261116)
    sample_mask=np.zeros(len(partition),dtype=bool)
    for name in split.files:sample_mask[rng.choice(split[name],200000,replace=False)]=True
    pieces=[];offset=0
    for batch in pq.ParquetFile(ROOT/'data/processed/uplift.parquet').iter_batches(batch_size=250000):
        df=batch.to_pandas(); n=len(df); sel=sample_mask[offset:offset+n]
        part=df.loc[sel].copy();part['partition']=partition[offset:offset+n][sel];part['source_row_index']=np.flatnonzero(sel)+offset;pieces.append(part);offset+=n
    sample=pd.concat(pieces,ignore_index=True)
    train=sample[sample.partition==0]
    modes={f:float(train[f].mode().iloc[0]) for f in FEATURES}
    edges={f:np.unique(train.loc[train[f]!=modes[f],f].quantile([.25,.5,.75]).to_numpy()).tolist() for f in CONT}
    (OUT/'rules.json').write_text(json.dumps(dict(seed=20261116,modes=modes,off_mode_quantiles=edges,flags=CATS,partition_names=['train','estimation','evaluation'],sample_per_partition=200000),indent=2))
    counts=np.zeros((3*256,7));bins={f:np.zeros((3*5,7)) for f in CONT};offset=0
    for i,batch in enumerate(pq.ParquetFile(ROOT/'data/processed/uplift.parquet').iter_batches(batch_size=250000)):
        d=batch.to_pandas(); n=len(d); p=partition[offset:offset+n].astype(int);offset+=n
        pattern=np.zeros(n,dtype=int)
        for j,f in enumerate(CATS):pattern+=(d[f].to_numpy()!=modes[f]).astype(int)*(2**j)
        t=d.treatment.to_numpy(); v=d.visit.to_numpy(); c=d.conversion.to_numpy(); e=d.exposure.to_numpy()
        values=[np.ones(n),t,v,c,e,t*v,t*c]
        for j,val in enumerate(values):counts[:,j]+=np.bincount(p*256+pattern,weights=val,minlength=768)
        for f in CONT:
            x=d[f].to_numpy(); b=np.where(x==modes[f],0,1+np.searchsorted(edges[f],x,side='right'))
            for j,val in enumerate(values):bins[f][:,j]+=np.bincount(p*5+b,weights=val,minlength=15)
        if i%15==0:print('uplift rows',offset,flush=True)
    table=summarize(counts,dict(partition=np.repeat(['train','estimation','evaluation'],256),pattern=np.tile(np.arange(256),3)))
    for j,f in enumerate(CATS):table[f+'_active']=((table.pattern.to_numpy()>>j)&1)
    table.to_csv(OUT/'feature_patterns.csv',index=False)
    pd.concat([summarize(a,dict(feature=f,partition=np.repeat(['train','estimation','evaluation'],5),bin=np.tile(np.arange(5),3))) for f,a in bins.items()]).to_csv(OUT/'continuous_bins.csv',index=False)
    bundle=joblib.load(ROOT/'outputs/mixed_clustering/clustering.joblib')
    sample['cluster8']=bundle['model'].apply(sample[FEATURES].to_numpy(),depth=3)
    for f in CATS:sample[f+'_active']=(sample[f]!=modes[f]).astype(int)
    sample.groupby(['partition','cluster8']).agg(n=('conversion','size'),**{f+'_active':(f+'_active','mean') for f in CATS},**{f+'_median':(f,'median') for f in CONT}).to_csv(OUT/'cluster8_profiles.csv')
    sample.to_parquet(OUT/'feature_sample.parquet',index=False)
    print('Done: full release patterns and 600,000-row profile sample',flush=True)

if __name__=='__main__':main()
