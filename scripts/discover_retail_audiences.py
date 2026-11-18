"""Compare soft retail-mission allocations before choosing a demo ontology."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.retail_metadata import allocation_matrix,GROUPS,PRIOR
OUT=ROOT/'outputs/retail_audiences';OUT.mkdir(exist_ok=True)
COUNTS=['n','treated','conversions','treated_conversions','visits','treated_visits']

def main():
    p=pd.read_csv(ROOT/'outputs/metadata_exploration/feature_patterns.csv')
    r=np.select([p.f8_active.eq(0),p.f9_active.eq(0),p.f4_active.eq(0),p.f11_active.eq(0)],[0,1,2,3],default=4)
    t=np.select([p.f3_active.eq(0)&p.f6_active.eq(0),p.f3_active.eq(0)],[0,1],default=2)
    p['response_cell']=r*3+t
    cells=p.groupby(['partition','response_cell'])[COUNTS].sum().reset_index()
    cells.to_csv(OUT/'source_cells.csv',index=False)
    train=cells[cells.partition=='train'].set_index('response_cell').reindex(range(15),fill_value=0)
    rows=[];summaries=[]
    for strength in [0,.6,1.,1.2,1.5,1.8,2.2]:
        for common in [.15,.30]:
            matrix=allocation_matrix(train.n.to_numpy(),strength,common)
            key=f's{strength:g}_shared{common:g}'
            for partition in ['train','estimation','evaluation']:
                c=cells[cells.partition==partition].set_index('response_cell').reindex(range(15),fill_value=0)
                counts=matrix.T@c[COUNTS].to_numpy()
                for group,a in enumerate(counts):
                    d=dict(zip(COUNTS,a));nt=d['treated'];nc=d['n']-nt
                    b=(d['conversions']-d['treated_conversions'])/nc
                    rate=d['treated_conversions']/nt
                    se=np.sqrt(rate*(1-rate)/nt+b*(1-b)/nc)
                    rows.append(dict(candidate=key,strength=strength,common=common,partition=partition,segment_id=group,profile=GROUPS[group],share=d['n']/c.n.sum(),baseline_per_10000=b*10000,increment_per_10000=(rate-b)*10000,se_per_10000=se*10000,source_cells_over_5pct=int(((matrix[:,group]*c.n)/(matrix[:,group]*c.n).sum()).gt(.05).sum()),**d))
            a=pd.DataFrame(rows);a=a[(a.candidate==key)&(a.partition=='evaluation')]
            summaries.append(dict(candidate=key,strength=strength,common=common,effect_ratio=a.increment_per_10000.max()/max(.001,a.increment_per_10000.min()),min_group_share=a.share.min(),min_control_events=float((a.conversions-a.treated_conversions).min()),max_cell_mission_probability=float(matrix.max()),min_cells=int(a.source_cells_over_5pct.min())))
            np.save(OUT/(key+'.npy'),matrix)
    pd.DataFrame(rows).to_csv(OUT/'allocation_candidates.csv',index=False)
    summary=pd.DataFrame(summaries);summary.to_csv(OUT/'candidate_summary.csv',index=False)
    print(summary.round(3).to_string(index=False))
    chosen=pd.DataFrame(rows);chosen=chosen[(chosen.candidate=='s1.5_shared0.15')&(chosen.partition=='evaluation')]
    print('\nCandidate profile contrast:');print(chosen[['profile','share','baseline_per_10000','increment_per_10000','se_per_10000','source_cells_over_5pct']].round(3).to_string(index=False))

if __name__=='__main__':main()
