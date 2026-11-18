"""Audit fixed balanced-tree policies without changing models or app results."""
from pathlib import Path
import sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.segmentation import allocation,evaluate_policy

g=pd.read_parquet(ROOT/'app/data/groups.parquet')
g=g[(g.outcome=='conversion')&(g.evaluation=='All evaluation rows')]
finest=int(g.segments.max())
fine=g[g.segments==finest].to_dict('records')
rows,paired=[],[]
for reach in [.25,.125,.0625,.03125,.015625]:
    previous=None
    weights_by_level={}
    for k,frame in g.groupby('segments'):
        k=int(k)
        records=frame.to_dict('records')
        ranked=frame.sort_values('estimation_effect',ascending=False).node.tolist()
        w=allocation(records,ranked,reach)
        lift=evaluate_policy(records,w,reach)['value']/reach*10000
        # Heap-indexed nodes: lift ancestor selection probabilities onto finest leaves.
        weights={r['node']:w[(r['node']+1)//(finest//k)-1] for r in fine}
        replaced=0 if previous is None else sum(r['n']*abs(weights[r['node']]-previous[r['node']]) for r in fine)/sum(r['n'] for r in fine)/reach/2
        rows.append(dict(reach_pct=reach*100,segments=k,lift_per_10k=lift,
                         selected_probability_mass_replaced_pct=replaced*100,
                         fully_selected_groups=sum(v==1 for v in w.values()),
                         fractional_groups=sum(0<v<1 for v in w.values()),
                         top_group_share_pct=frame.set_index('node').loc[ranked[0],'share']*100))
        weights_by_level[k]=weights
        previous=weights
    for lo,hi in zip([4,8,16,32],[8,16,32,64]):
        delta={n:weights_by_level[hi][n]-weights_by_level[lo][n] for n in weights_by_level[hi]}
        result=evaluate_policy(fine,delta,0)
        value,se=result['value']/reach*10000,result['se']/reach*10000
        paired.append(dict(reach_pct=reach*100,comparison=f'{lo} to {hi}',gain_per_10k=value,
                           lower=value-1.96*se,upper=value+1.96*se))
folder=ROOT/'outputs/balanced_segmentation'
pd.DataFrame(rows).to_csv(folder/'model_audit.csv',index=False)
pd.DataFrame(paired).to_csv(folder/'model_audit_paired.csv',index=False)
print(pd.DataFrame(rows).round(3).to_string(index=False))
print(pd.DataFrame(paired).round(3).to_string(index=False))
print('Control positives at finest level: zero=',sum(r['control_positives']==0 for r in fine),
      '; at most one=',sum(r['control_positives']<=1 for r in fine))
