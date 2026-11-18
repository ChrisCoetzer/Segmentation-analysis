"""Full-data audit and held-out temporal calibration for synthetic retail missions."""
from pathlib import Path
import sys,json,time
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.retail_metadata import GROUPS,MISSIONS,PRIOR,DESCRIPTIONS,QUOTES,EXAMPLES,latent_cells,assign_missions,metadata
OUT=ROOT/'outputs/retail_audiences';OUT.mkdir(exist_ok=True)
COLS=['n','treated','conversions','treated_conversions','visits','treated_visits']

def main():
    start=time.perf_counter();matrix=np.load(OUT/'s1_shared0.3.npy')
    rules=json.loads((ROOT/'outputs/metadata_exploration/rules.json').read_text());modes=rules['modes']
    source=pd.read_csv(OUT/'source_cells.csv')
    train=source.query('partition=="train"').set_index('response_cell').reindex(range(15),fill_value=0)
    split=np.load(ROOT/'outputs/mixed_clustering/split_rows.npz')
    part=np.zeros(13979592,dtype=np.int8);part[split['estimation']]=1;part[split['test']]=2
    aggregate=np.zeros((3*5,6));offset=0
    print('Auditing mission assignments across all uplift records',flush=True)
    for batch in pq.ParquetFile(ROOT/'data/processed/uplift.parquet').iter_batches(batch_size=250000):
        d=batch.to_pandas();ids=np.arange(offset,offset+len(d));cell=latent_cells(d,modes);group=assign_missions(cell,ids,matrix)
        code=part[offset:offset+len(d)]*5+group;offset+=len(d)
        t=d.treatment.to_numpy();c=d.conversion.to_numpy();v=d.visit.to_numpy()
        for j,a in enumerate([np.ones(len(d)),t,c,t*c,v,t*v]):aggregate[:,j]+=np.bincount(code,weights=a,minlength=15)
    records=[]
    for partition in range(3):
        for group in range(5):
            a=dict(zip(COLS,aggregate[partition*5+group]));nt=a['treated'];nc=a['n']-nt
            b=(a['conversions']-a['treated_conversions'])/nc;rate=a['treated_conversions']/nt
            records.append(dict(partition=['train','estimation','evaluation'][partition],segment_id=group,profile=GROUPS[group],share=a['n']/aggregate[partition*5:partition*5+5,0].sum(),baseline_rate=b,incremental_rate=rate-b,se=np.sqrt(rate*(1-rate)/nt+b*(1-b)/nc),**a))
    groups=pd.DataFrame(records);groups.to_csv(OUT/'actual_group_outcomes.csv',index=False)
    assert int(groups.n.sum())==13979592
    print(groups.query('partition=="evaluation"')[['profile','share','baseline_rate','incremental_rate','se']].round(6).to_string(index=False),flush=True)
    print('Scoring first-contact attribution contexts',flush=True)
    cols=['uid','campaign','cat1','cat2','cat4','cat5','cat6','cat8','cat9','eligible14','event14','event_days','event_contact_number']
    q=pd.read_parquet(ROOT/'outputs/campaign_timing/histories.parquet',columns=cols).query('eligible14').reset_index(drop=True)
    discovery=q.uid.mod(5).ne(0).to_numpy();features=[c for c in q if c.startswith('cat')]
    fit=q.loc[discovery].sample(1000000,random_state=20261116)
    enc=OneHotEncoder(handle_unknown='ignore',dtype=np.float32);x=enc.fit_transform(fit[features]);model=LogisticRegression(max_iter=150,C=.1)
    with threadpool_limits(limits=1):model.fit(x,fit.event14)
    score=np.empty(len(q))
    for i in range(0,len(q),250000):
        with threadpool_limits(limits=1):score[i:i+250000]=model.predict_proba(enc.transform(q.iloc[i:i+250000][features]))[:,1]
    q['purchase_propensity']=score
    pair_hash=pd.util.hash_pandas_object(q[['uid','campaign']],index=False).to_numpy()
    q['response_cell']=np.int8(0)
    shares=train.groupby(train.index//3).n.sum().to_numpy()/train.n.sum()
    # Discover category-level timing on one partition; apply category lookup
    # to unseen uids. No individual's future timing enters their assignment.
    ev=q.loc[discovery&q.event14.to_numpy()].copy();ev['early']=ev.event_days.le(1).astype(int)
    tempo=ev.groupby('cat5').agg(events=('early','size'),early=('early','sum'))
    global_early=ev.early.mean();tempo['tempo_score']=(tempo.early+200*global_early)/(tempo.events+200)
    context_tempo=q.cat5.map(tempo.tempo_score).fillna(global_early).to_numpy()
    tempo.to_csv(OUT/'discovery_context_timing.csv')
    for mask in [discovery,~discovery]:
        rows=np.flatnonzero(mask);ordered=rows[np.lexsort((pair_hash[rows],score[rows]))]
        ranks=(np.arange(len(rows))+.5)/len(rows)
        band=np.searchsorted(np.cumsum(shares)[:-1],ranks,side='right')
        for r in range(5):
            members=ordered[band==r];members=members[np.lexsort((pair_hash[members],context_tempo[members]))]
            weight=train.loc[range(r*3,r*3+3),'n'].to_numpy();weight=weight/max(1,weight.sum())
            subtype=np.searchsorted(np.cumsum(weight)[:-1],(np.arange(len(members))+.5)/max(1,len(members)),side='right')
            q.loc[members,'response_cell']=(r*3+subtype).astype(np.int8)
    q['segment_id']=assign_missions(q.response_cell.to_numpy(),pair_hash,matrix)
    q['partition']=np.where(discovery,'discovery','check')
    summaries=[];curves=[];frequency=[]
    for (partition,gid),a in q.groupby(['partition','segment_id']):
        e=a[a.event14]
        summaries.append(dict(partition=partition,segment_id=int(gid),profile=GROUPS[gid],n=len(a),events14=len(e),event_rate=len(e)/len(a),day1_share=float(e.event_days.le(1).mean()),day7_share=float(e.event_days.le(7).mean()),median_days=float(e.event_days.median()),one_contact=float(e.event_contact_number.eq(1).mean())))
        for day in range(1,15):curves.append(dict(partition=partition,segment_id=int(gid),day=day,response_share=float(e.event_days.le(day).mean()),n_histories=len(a),events14=len(e)))
        for cap in [1,2,3,4,5,6,8,10,12,15,20,400]:frequency.append(dict(partition=partition,segment_id=int(gid),contact_cap=cap,coverage=float(e.event_contact_number.le(cap).mean()),events14=len(e)))
    summary=pd.DataFrame(summaries);summary.to_csv(OUT/'mission_timing_checks.csv',index=False)
    pd.DataFrame(curves).to_csv(OUT/'mission_timing_curves.csv',index=False)
    pd.DataFrame(frequency).to_csv(OUT/'mission_contact_curves.csv',index=False)
    q.loc[~discovery,['uid','campaign','response_cell','segment_id','purchase_propensity','event14','event_days','event_contact_number']].to_parquet(OUT/'heldout_timing_missions.parquet',index=False)
    # Timing dependence is explicitly a synthetic bridge assumption. Record a
    # reversal and pooled alternative so the effect is inspectable.
    sensitivity=[]
    for name,cells in [('aligned',q.response_cell.to_numpy()),('reversed_subtype',(q.response_cell.to_numpy()//3)*3+2-q.response_cell.to_numpy()%3)]:
        missions=assign_missions(cells,pair_hash,matrix)
        for gid in range(5):
            e=q[(~discovery)&(missions==gid)&q.event14]
            sensitivity.append(dict(mapping=name,segment_id=gid,events=len(e),day1_share=float(e.event_days.le(1).mean()),one_contact=float(e.event_contact_number.eq(1).mean())))
    pd.DataFrame(sensitivity).to_csv(OUT/'bridge_sensitivity.csv',index=False)
    bank=pd.read_parquet(ROOT/'outputs/metadata_exploration/feature_sample.parquet').sample(200000,random_state=171126)
    bank=metadata(bank,matrix,modes)
    bank.to_parquet(OUT/'retail_profile_bank.parquet',index=False)
    catalogue=[dict(segment_id=i,profile=GROUPS[i],mission=MISSIONS[i],description=DESCRIPTIONS[i],quote=QUOTES[i],product_examples=EXAMPLES[i],orders_median=float(a.orders_last_year.median()),basket_median=float(a.typical_basket.median()),promotion_affinity=float(a.promotion_affinity.mean()),existing_customer_share=float(a.orders_last_year.gt(0).mean()),channels=a.preferred_channel.value_counts(normalize=True).round(3).to_dict()) for i,a in bank.groupby('segment_id')]
    (OUT/'catalogue.json').write_text(json.dumps(catalogue,indent=2))
    (OUT/'allocation_spec.json').write_text(json.dumps(dict(candidate='s1_shared0.3',strength=1.,common_fraction=.3,fictional_population_prior=PRIOR.tolist(),matrix=matrix.tolist(),selection_rule='Lowest tested strength with at least 5x response contrast, >=30% shared population component, maximum cell allocation below .65 and >=3 substantial source cells per mission.',seed=171127,synthetic_matching='Purchase-propensity rank plus discovery-context timing rank; subtype correspondence is an explicit scenario assumption.'),indent=2))
    print('\nHeld-out timing:');print(summary.query('partition=="check"').round(4).to_string(index=False))
    print('Elapsed seconds',round(time.perf_counter()-start,2),flush=True)

if __name__=='__main__':main()
