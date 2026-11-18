"""Compare fixed-data clustering seeds without selecting by evaluation performance."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.segmentation import cluster_average_comparison
folder=ROOT/'outputs/clustering_stability'
rows=[]
for seed,path in [(20261020,folder/'before_rerun')]+[(s,folder/f'seed_{s}/app_results') for s in [20261021,20261022,20261023]]:
 g=pd.read_parquet(path/'groups.parquet')
 for outcome in ['conversion','visit']:
  averages=cluster_average_comparison(g,outcome)
  a=averages[averages.segments==16].iloc[0];b=averages[averages.segments==32].iloc[0]
  data=g[(g.outcome==outcome)&(g.evaluation=='All evaluation rows')]
  r16=data[(data.segments==16)&(data.node==a.node)].iloc[0]
  r32=data[(data.segments==32)&(data.node==b.node)].iloc[0]
  variance=0.
  for size,rate in [('treated','treatment_rate'),('control','control_rate')]:
   v16=r16[rate]*(1-r16[rate])/(r16[size]-1)
   v32=r32[rate]*(1-r32[rate])/(r32[size]-1)
   covariance=r32[size]/r16[size]*v32 if (int(b.node)-1)//2==int(a.node) else 0.
   variance+=v16+v32-2*covariance
  delta=(b['value']-a['value'])*10000;se=np.sqrt(max(0.,variance))*10000
  rows.append(dict(cluster_seed=seed,outcome=outcome,lift_16=a['value']*10000,lift_32=b['value']*10000,
                   difference_32_minus_16=delta,lower=delta-1.96*se,upper=delta+1.96*se,
                   users_16=int(a['n']),users_32=int(b['n'])))
result=pd.DataFrame(rows)
result.to_csv(folder/'comparison.csv',index=False)
print(result.round(2).to_string(index=False))
