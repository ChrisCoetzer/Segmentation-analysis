"""Re-evaluate saved groups on a finer reach grid, without model retraining."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.segmentation import allocation,evaluate_policy


def refresh():
    folder=ROOT/'app/data'
    groups=pd.read_parquet(folder/'groups.parquet')
    groups=groups[groups.evaluation=='All evaluation rows']
    result=[]
    for (outcome,segments),frame in groups.groupby(['outcome','segments']):
        records=frame.to_dict('records')
        ranked=frame.sort_values('estimation_effect',ascending=False,kind='stable').node.tolist()
        for percent in np.arange(1,201)/2:
            reach=percent/100
            result.append(dict(outcome=outcome,segments=segments,reach=float(percent),
                               segment_limit=segments,
                               **evaluate_policy(records,allocation(records,ranked,reach),reach)))
    pd.DataFrame(result).to_parquet(folder/'policies.parquet',index=False)
    print('Policy grid refreshed: 0.5% to 100%, in 0.5 percentage-point steps.')


if __name__=='__main__':
    refresh()
