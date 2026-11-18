"""Export fitted tree structure and correct segment labels to actual leaf counts."""
import json
from pathlib import Path
import sys

import joblib
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def export():
    data=ROOT/'app/data'
    groups=pd.read_parquet(data/'groups.parquet')
    policies=pd.read_parquet(data/'policies.parquet')
    old_rules=json.loads((data/'rules.json').read_text())
    trees,rules,counts={},{},{}
    for outcome in ['conversion','visit']:
        counts[outcome]=[]
        for cap in json.loads((data/'run.json').read_text())['segments']:
            bundle=joblib.load(ROOT/f'outputs/balanced_segmentation/{outcome}_{cap}_segments.joblib')
            model=bundle['model']
            depth=bundle['depth']
            nodes=model.view_nodes(depth)
            actual=sum(r['left']<0 for r in nodes)
            counts[outcome].append(actual)
            key=f'{outcome}_{actual}'
            rules[key]=old_rules.get(f'{outcome}_{cap}',old_rules.get(key))
            trees[key]=dict(nodes=nodes,segment_limit=cap,actual_segments=actual)
            for frame in [groups,policies]:
                if 'segment_limit' not in frame:
                    frame['segment_limit']=frame.segments
                mask=(frame.outcome==outcome)&(frame.segment_limit==cap)
                frame.loc[mask,'segments']=actual
    groups.to_parquet(data/'groups.parquet',index=False)
    policies.to_parquet(data/'policies.parquet',index=False)
    (data/'trees.json').write_text(json.dumps(trees,indent=2),encoding='utf-8')
    (data/'rules.json').write_text(json.dumps(rules,indent=2),encoding='utf-8')
    meta=json.loads((data/'run.json').read_text())
    meta['actual_segments_by_outcome']=counts
    (data/'run.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print('Actual segment counts:',counts)


if __name__=='__main__':
    export()
