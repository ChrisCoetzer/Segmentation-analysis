"""Descriptive frequency aggregation at the user-within-campaign grain."""
import numpy as np
import pandas as pd

FREQUENCY_ORDER=['1','2–3','4–6','7–10','11+']


def aggregate_frequency(impressions):
    """Count impressions once, and count each converting user-campaign pair once."""
    pairs=impressions.groupby(['campaign','uid'],sort=False,observed=True).agg(
        impressions=('conversion','size'),converted=('conversion','max')).reset_index()
    pairs['frequency']=pd.cut(pairs.impressions,bins=[0,1,3,6,10,np.inf],
                              labels=FREQUENCY_ORDER,ordered=True)
    result=pairs.groupby(['campaign','frequency'],observed=True,sort=False).agg(
        pairs=('uid','size'),converted_pairs=('converted','sum'),
        impressions=('impressions','sum')).reset_index()
    result['campaign']=result.campaign.astype(str)
    result['frequency']=result.frequency.astype(str)
    return result


def interval_table(counts,z=1.959963984540054):
    """Wilson intervals as descriptive binomial reference intervals for pair rates."""
    data=counts.copy()
    n=data.pairs.to_numpy(dtype=float)
    p=data.converted_pairs.to_numpy(dtype=float)/n
    denom=1+z*z/n
    center=(p+z*z/(2*n))/denom
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    data['rate']=p
    data['lower']=np.clip(center-half,0,1)
    data['upper']=np.clip(center+half,0,1)
    data['share']=n/n.sum()
    return data
