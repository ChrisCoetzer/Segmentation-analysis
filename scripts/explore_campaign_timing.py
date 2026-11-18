"""Reconstruct recorded timelines and equal-follow-up duration/frequency curves."""
from pathlib import Path
import json, time
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/campaign_timing'
OUT.mkdir(exist_ok=True)
DAY=86400
HORIZON=14

def main():
    start=time.perf_counter()
    columns=['uid','campaign','timestamp','conversion_timestamp','conversion_id','click','conversion','cat1','cat2','cat4','cat5','cat6','cat8','cat9']
    print('Reading attribution timestamps and initial-context categories',flush=True)
    d=pd.read_parquet(ROOT/'data/processed/attribution.parquet',columns=columns)
    end=int(d.timestamp.max())
    valid=d.conversion.eq(1)&d.conversion_timestamp.ge(d.timestamp)
    sentinel=np.iinfo(np.int64).max//2
    d['event_time']=d.conversion_timestamp.where(valid,sentinel)
    d['click_time']=d.timestamp.where(d.click.eq(1),sentinel)
    g=d.groupby(['campaign','uid'],sort=False,observed=True)
    print('Aggregating histories',flush=True)
    p=g.agg(first=('timestamp','min'),last=('timestamp','max'),impressions=('timestamp','size'),clicks=('click','sum'),event_time=('event_time','min'),first_click=('click_time','min'),**{c:(c,'first') for c in columns if c.startswith('cat')}).reset_index()
    code=g.ngroup().to_numpy()
    first=p['first'].to_numpy();event=p.event_time.to_numpy()
    elapsed=(d.timestamp.to_numpy()-first[code])/DAY
    pre=d.timestamp.to_numpy()<=event[code]
    lastpre=np.zeros(len(p),dtype=np.int64)
    np.maximum.at(lastpre,code[pre],d.timestamp.to_numpy()[pre])
    before=np.bincount(code,weights=pre,minlength=len(p)).astype(int)
    early=np.bincount(code,weights=(elapsed<=1),minlength=len(p)).astype(int)
    p['impressions_before_first_event']=before;p['impressions_first_day']=early
    p['event_days']=(p.event_time-p['first'])/DAY
    p['click_days']=(p.first_click-p['first'])/DAY
    p['has_event']=p.event_time.lt(sentinel)
    p['eligible14']=p['first'].le(end-HORIZON*DAY)
    p['event14']=p.has_event&p.event_days.le(HORIZON)
    # Fixed 14-day follow-up avoids treating late-arriving histories as slow failures.
    p['event_contact_number']=np.where(p.has_event,before,0)
    p['last_pre_event_contact_days']=(lastpre-p['first'].to_numpy())/DAY
    # Observed contact load by elapsed day, ending at the first recorded event.
    # 0 means within the first 24h; bin 13 ends at day 14.
    timing_bin=np.ceil(elapsed).astype(np.int16)-1
    timing_bin=np.maximum(timing_bin,0)
    day_counts=[]
    for day in range(14):
        nday=np.bincount(code,weights=(pre&(timing_bin==day)),minlength=len(p)).astype(np.int16)
        p[f'contacts_day_{day+1}']=nday
    p.to_parquet(OUT/'histories.parquet',index=False)
    # Operational history profiles: no event outcome enters these definitions.
    q=p[p.eligible14].copy()
    q['early_click']=q.click_days.le(1)
    q['initial_pace']=pd.cut(q.impressions_first_day,[0,1,3,np.inf],labels=['One first-day contact','2-3 first-day contacts','4+ first-day contacts']).astype(str)
    q['entry_week']=(q['first']//(7*DAY)).astype(int)
    curves=[]
    for profile,groups in [('All',[("All",q)]),('initial_pace',q.groupby('initial_pace')),('early_click',q.groupby('early_click')),('campaign',q.groupby('campaign'))]:
        for label,a in groups:
            ne=int(a.event14.sum())
            if profile=='campaign' and (len(a)<5000 or ne<100):continue
            for day in range(15):
                n=int((a.event14&a.event_days.le(day)).sum())
                curves.append(dict(profile=profile,group=str(label),day=day,n=len(a),events14=ne,events_by_day=n,events_per_10000=10000*n/len(a),share_of_14d_events=n/ne if ne else np.nan))
    pd.DataFrame(curves).to_csv(OUT/'duration_curves.csv',index=False)
    freq=[]
    ev=q[q.event14]
    for k in [1,2,3,4,5,6,8,10,15,20,30,50,100,400]:
        freq.append(dict(contacts=k,event_pairs=int(ev.event_contact_number.le(k).sum()),share_of_events=float(ev.event_contact_number.le(k).mean())))
    pd.DataFrame(freq).to_csv(OUT/'event_contact_curve.csv',index=False)
    # A joint description of recorded events, not an intervention on impressions.
    surface=[]
    for day in range(1,15):
        for k in [1,2,3,4,5,6,8,10,15,20,30]:
            n=int((ev.event_days.le(day)&ev.event_contact_number.le(k)).sum())
            surface.append(dict(day=day,contacts=k,events=n,share_of_14d_events=n/len(ev)))
    pd.DataFrame(surface).to_csv(OUT/'duration_contact_surface.csv',index=False)
    checks=dict(impressions=len(d),pairs=len(p),distinct_conversion_ids=int(d.loc[d.conversion_id.ge(0),'conversion_id'].nunique()),max_impression_timestamp=end,recorded_days=end/DAY,positive_impression_rows=int(d.conversion.sum()),positive_rows_with_conversion_before_impression=int((d.conversion.eq(1)&d.conversion_timestamp.lt(d.timestamp)).sum()),conversion_timestamp_max=int(d.conversion_timestamp.max()),eligible_pairs14=len(q),events14=int(q.event14.sum()),has_recorded_event_pairs=int(p.has_event.sum()),event_delay_quantiles={str(k):float(v) for k,v in ev.event_days.quantile([.1,.25,.5,.75,.9,.95]).items()},event_contact_quantiles={str(k):float(v) for k,v in ev.event_contact_number.quantile([.1,.25,.5,.75,.9,.95]).items()},last_pre_event_contact_quantiles={str(k):float(v) for k,v in ev.last_pre_event_contact_days.quantile([.5,.75,.9,.95]).items()},first_day_event_share=float(ev.event_days.le(1).mean()),first_contact_event_share=float(ev.event_contact_number.eq(1).mean()),elapsed_seconds=round(time.perf_counter()-start,2),timestamp_unit='Seconds assumed consistently with approximately 30-day log span and documented seconds for time_since_last_click')
    (OUT/'timing_diagnostics.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2),flush=True)
    print(pd.DataFrame(curves).query('profile=="All"').to_string(index=False),flush=True)
    print(q.groupby(['initial_pace','early_click']).agg(n=('uid','size'),events14=('event14','sum')).to_string(),flush=True)

if __name__=='__main__':main()
