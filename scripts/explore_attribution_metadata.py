"""Observed journey archetypes, aggregated without changing app data."""
from pathlib import Path
import pandas as pd
import numpy as np
import json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/metadata_exploration'
print('Reading attribution impressions',flush=True)
d=pd.read_parquet(ROOT/'data/processed/attribution.parquet',columns=['uid','campaign','click','conversion','timestamp'])
print('Aggregating user-campaign histories',flush=True)
p=d.groupby(['campaign','uid'],sort=False,observed=True).agg(impressions=('click','size'),clicks=('click','sum'),converted=('conversion','max'),first=('timestamp','min'),last=('timestamp','max')).reset_index()
del d
p['frequency']=pd.cut(p.impressions,[0,1,3,10,np.inf],labels=['1','2-3','4-10','11+']).astype(str)
p['clicked']=p.clicks.gt(0)
p['span']=p['last']-p['first']
summary=p.groupby(['clicked','frequency'],observed=True).agg(pairs=('uid','size'),positive_pairs=('converted','sum'),impressions=('impressions','sum'),clicks=('clicks','sum'),median_span=('span','median')).reset_index()
summary['positive_pair_rate']=summary.positive_pairs/summary.pairs
summary.to_csv(OUT/'journey_archetypes.csv',index=False)
campaigns=p.groupby(['campaign','clicked','frequency'],observed=True).agg(pairs=('uid','size'),positive_pairs=('converted','sum'),impressions=('impressions','sum')).reset_index()
campaigns.to_parquet(OUT/'journey_campaigns.parquet',index=False)
stats=dict(impressions=int(p.impressions.sum()),pairs=len(p),users=int(p.uid.nunique()),campaigns=int(p.campaign.nunique()),positive_pairs=int(p.converted.sum()),clicked_pairs=int(p.clicked.sum()),frequency_quantiles={str(k):float(v) for k,v in p.impressions.quantile([.5,.9,.95,.99,.999]).items()},max_recorded_impressions=int(p.impressions.max()))
(OUT/'journey_summary.json').write_text(json.dumps(stats,indent=2))
print(summary.to_string(index=False),flush=True)
print(json.dumps(stats,indent=2),flush=True)
