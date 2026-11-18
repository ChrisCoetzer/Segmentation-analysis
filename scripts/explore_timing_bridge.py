"""Prototype a documented synthetic segment-level bridge, not identity linkage."""
from pathlib import Path
import sys, json
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/campaign_timing'
DAY=86400

def main():
    p=pd.read_parquet(OUT/'histories.parquet')
    q=p[p.eligible14].copy()
    features=[c for c in q if c.startswith('cat')]
    # Same uid stays on one side of the split across campaigns.
    train=q.uid.mod(5).ne(0)
    fit=q[train].sample(min(1000000,int(train.sum())),random_state=20261116)
    print('Fitting compact initial-context propensity score',flush=True)
    enc=OneHotEncoder(handle_unknown='ignore',dtype=np.float32)
    x=enc.fit_transform(fit[features])
    model=LogisticRegression(max_iter=150,C=.1)
    with threadpool_limits(limits=1):model.fit(x,fit.event14)
    scores=[]
    for i in range(0,len(q),250000):
        with threadpool_limits(limits=1):scores.append(model.predict_proba(enc.transform(q.iloc[i:i+250000][features]))[:,1])
    q['initial_propensity']=np.concatenate(scores)
    thresholds=np.quantile(q.loc[train,'initial_propensity'],[.2,.4,.6,.8])
    q['risk_tier']=np.searchsorted(thresholds,q.initial_propensity,side='right')
    q['split']=np.where(train,'discovery','check')
    print('Scoring complete',flush=True)
    # Held-out histories for chart shape exploration.
    v=q[~train].copy()
    curves=[];profiles=[]
    for tier,g in v.groupby('risk_tier'):
        ev=g[g.event14]
        profiles.append(dict(risk_tier=int(tier),n=len(g),events14=len(ev),event_rate=len(ev)/len(g),median_response_days=float(ev.event_days.median()),first_contact_share=float(ev.event_contact_number.eq(1).mean()),mean_propensity=float(g.initial_propensity.mean())))
        for day in range(1,15):
            n=int(ev.event_days.le(day).sum())
            curves.append(dict(risk_tier=int(tier),day=day,n=len(g),events14=len(ev),events=n,event_share=n/len(ev),events_per_10000=10000*n/len(g)))
    pd.DataFrame(profiles).to_csv(OUT/'propensity_tier_profiles.csv',index=False)
    pd.DataFrame(curves).to_csv(OUT/'propensity_tier_curves.csv',index=False)
    # Match uplift stage proportions to ranks within the attribution source.
    u=pd.read_csv(ROOT/'outputs/metadata_exploration/readiness_summary.csv').query('partition=="evaluation"').sort_values('readiness')
    shares=u.share_pct.to_numpy()/100
    # A seeded uid-campaign hash breaks exact risk-score ties, without outcomes.
    h=pd.util.hash_pandas_object(v[['uid','campaign']],index=False).to_numpy()
    order=np.lexsort((h,v.initial_propensity.to_numpy()))
    ranks=np.empty(len(v));ranks[order]=(np.arange(len(v))+.5)/len(v)
    v['synthetic_segment_id']=np.searchsorted(np.cumsum(shares)[:-1],ranks,side='right')
    bridge=[];shapes=[]
    for stage,g in v.groupby('synthetic_segment_id'):
        row=u[u.readiness.eq(stage)].iloc[0];ev=g[g.event14]
        for day in range(1,15):
            f=float(ev.event_days.le(day).mean())
            shapes.append(dict(synthetic_segment_id=int(stage),day=day,response_share=f,n_histories=len(g),events14=len(ev)))
            bridge.append(dict(synthetic_segment_id=int(stage),synthetic_label=row.synthetic_label,day=day,audience_share=float(row.share_pct/100),uplift_conversion_effect_14d_per_10000=float(row.conversions_effect_per_10k),attribution_response_share=f,synthetic_incremental_conversions_per_10000=float(row.conversions_effect_per_10k*f),synthetic_cumulative_reach='not estimated; contactable audience is a user assumption'))
    pd.DataFrame(bridge).to_csv(OUT/'synthetic_duration_scenario.csv',index=False)
    pd.DataFrame(shapes).to_csv(OUT/'matched_segment_shapes.csv',index=False)
    plans=[]
    for stage,g in v.groupby('synthetic_segment_id'):
        row=u[u.readiness.eq(stage)].iloc[0];ev=g[g.event14]
        contacts=np.cumsum(g[[f'contacts_day_{day}' for day in range(1,15)]].to_numpy(dtype=np.int32),axis=1)
        for day in range(1,15):
            for cap in [1,2,3,4,5,6,8,10,15,20,400]:
                # Explicit conservative replay assumption: retain a historical
                # response only when its entire recorded pre-event path fits.
                retained=float((ev.last_pre_event_contact_days.le(day)&ev.event_contact_number.le(cap)).mean())
                meancontacts=float(np.minimum(contacts[:,day-1],cap).mean())
                plans.append(dict(synthetic_segment_id=int(stage),synthetic_label=row.synthetic_label,day=day,contact_cap=cap,historical_path_coverage=retained,mean_recorded_contacts=meancontacts,uplift_conversion_effect_14d_per_10000=float(row.conversions_effect_per_10k),synthetic_incremental_conversions_per_10000=float(row.conversions_effect_per_10k*retained),audience_share=float(row.share_pct/100),assumption='Full recorded pre-conversion contact path required; synthetic policy replay, not measured stopping effect'))
    pd.DataFrame(plans).to_csv(OUT/'synthetic_duration_frequency_plans.csv',index=False)
    # Alternative mapping is a sensitivity check: reverse the rank relationship.
    rev=[]
    for direction in ['aligned','reversed']:
        segment=np.searchsorted(np.cumsum(shares)[:-1],ranks if direction=='aligned' else 1-ranks,side='right')
        for stage in range(5):
            a=v[(segment==stage)&v.event14]
            rev.append(dict(mapping=direction,segment=stage,n_events=len(a),day1_share=float(a.event_days.le(1).mean()),day7_share=float(a.event_days.le(7).mean()),day10_share=float(a.event_days.le(10).mean())))
    pd.DataFrame(rev).to_csv(OUT/'bridge_sensitivity.csv',index=False)
    # Longer duration uses its own consistently followed cohort.
    longer=[]
    end=2671199
    for horizon in [14,21,28]:
        a=p[p['first'].le(end-horizon*DAY)];e=a[a.has_event&a.event_days.le(horizon)]
        for day in range(1,horizon+1):
            longer.append(dict(horizon=horizon,day=day,n=len(a),events_horizon=len(e),events_by_day=int(e.event_days.le(day).sum()),event_share=float(e.event_days.le(day).mean())))
    pd.DataFrame(longer).to_csv(OUT/'longer_followup.csv',index=False)
    v.sample(20000,random_state=20261116)[['campaign','uid','cat1','cat2','cat4','cat5','cat6','cat8','cat9','initial_propensity','synthetic_segment_id','event_days','event_contact_number','event14']].to_csv(OUT/'bridge_example_20000.csv',index=False)
    diagnostics=dict(features=features,fit_histories=len(fit),heldout_histories=len(v),heldout_auc=float(roc_auc_score(v.event14,v.initial_propensity)),thresholds=thresholds.tolist(),heldout_events=int(v.event14.sum()),interpretation='Propensity-rank statistical matching is an explicit synthetic transport assumption; no cross-dataset identity linkage exists.',equation='scenario_incremental_response_s(d) = uplift_release_effect_s(14) * attribution_matched_event_time_CDF_s(d)',day14_consistency=True)
    scenario=pd.DataFrame(bridge)
    assert np.allclose(scenario.query('day==14').synthetic_incremental_conversions_per_10000,u.conversions_effect_per_10k)
    assert len(v)==v.groupby('synthetic_segment_id').size().sum()
    (OUT/'bridge_diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
    print(json.dumps(diagnostics,indent=2),flush=True)
    print(pd.DataFrame(profiles).round(4).to_string(index=False),flush=True)
    print(pd.DataFrame(rev).round(4).to_string(index=False),flush=True)

if __name__=='__main__':main()
