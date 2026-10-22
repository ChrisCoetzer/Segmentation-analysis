"""Explicit client-assumption scenarios; no benchmark dollars or production forecast."""
import numpy as np
import pandas as pd


def investment_scenario(policies,eligible_audience,reach_percent,baseline_per_10k,
                        contribution_per_conversion,transfer_percent,costs):
    if eligible_audience<0 or not 0<reach_percent<=100 or not 0<=baseline_per_10k<=10000:
        raise ValueError('Use a nonnegative audience and valid reach/baseline rate.')
    if contribution_per_conversion<0 or not 0<=transfer_percent<=100 or any(c<0 for c in costs.values()):
        raise ValueError('Values and costs must be nonnegative; transfer must be between 0 and 100%.')
    selected=policies[(policies.outcome=='conversion')&np.isclose(policies.reach,reach_percent)].sort_values('segments')
    if selected.segments.duplicated().any() or set(selected.segments)!={1,*costs}:
        raise ValueError('No matching conversion comparison for this reach.')
    base=float(selected[selected.segments==1]['value'].iloc[0])
    if base<=0:
        raise ValueError('A positive benchmark baseline is required for relative-gain scenarios.')
    targeted=eligible_audience*reach_percent/100
    baseline_conversions=targeted*baseline_per_10k/10000
    records=[]
    for row in selected.itertuples():
        relative_gain=row.value/base-1
        assumed_gain=relative_gain*transfer_percent/100
        modeled_rate=baseline_per_10k/10000*(1+assumed_gain)
        if not 0<=modeled_rate<=1:
            raise ValueError('The implied incremental conversion rate is outside 0â€“100%; lower the baseline or transfer assumption.')
        extra_conversions=baseline_conversions*assumed_gain
        contribution=extra_conversions*contribution_per_conversion
        cost=0.0 if row.segments==1 else float(costs[int(row.segments)])
        records.append(dict(segments=int(row.segments),option='Broad targeting' if row.segments==1 else f'{row.segments} groups',
                            eligible_audience=eligible_audience,reach_percent=reach_percent,targeted_users=targeted,
                            client_baseline_per_10k=baseline_per_10k,contribution_per_conversion=contribution_per_conversion,
                            assumed_transfer_percent=transfer_percent,benchmark_relative_gain=relative_gain,
                            assumed_relative_gain=assumed_gain,baseline_incremental_conversions=baseline_conversions,
                            additional_conversions=extra_conversions,additional_contribution=contribution,
                            segmentation_cost=cost,net_value=contribution-cost))
    return pd.DataFrame(records)


def cluster_investment_scenario(averages,customers,baseline_per_10k,contribution_per_conversion):
    """Apply selected-cluster average lift ratios to an explicit client scenario."""
    selected=averages[averages.outcome=='conversion'].sort_values('segments')
    base=selected[selected.segments==1]['value']
    if len(base)!=1 or float(base.iloc[0])<=0:
        raise ValueError('A positive broad conversion baseline is required.')
    if customers<0 or not 0<=baseline_per_10k<=10000 or contribution_per_conversion<0:
        raise ValueError('Use a nonnegative campaign size, contribution and valid baseline rate.')
    records=[]
    for row in selected.itertuples():
        gain=row.value/float(base.iloc[0])-1
        rate=baseline_per_10k/10000*(1+gain)
        if not 0<=rate<=1:
            raise ValueError('Scenario implies a conversion lift outside 0–100%; lower the baseline assumption.')
        additional=customers*baseline_per_10k/10000*gain
        records.append(dict(segments=row.segments,option='Broad targeting' if row.segments==1 else f'{row.segments} groups',
                            selected_group=row.selected_group,benchmark_cluster_share_pct=row.reach,
                            benchmark_cluster_users=row.n,benchmark_average_lift=row.value,
                            campaign_customers=customers,client_baseline_per_10k=baseline_per_10k,
                            contribution_per_conversion=contribution_per_conversion,benchmark_relative_gain=gain,
                            additional_conversions=additional,break_even_cost=additional*contribution_per_conversion))
    return pd.DataFrame(records)


def population_investment_scenario(groups,population,reach_percent,baseline_per_10k,contribution_per_conversion):
    """Fill equal-size audiences from estimation-ranked clusters at each level."""
    from src.segmentation import allocation,evaluate_standardized_policy
    if population<0 or not 0<=reach_percent<=100 or not 0<=baseline_per_10k<=10000 or contribution_per_conversion<0:
        raise ValueError('Use nonnegative population/value and percentages between 0 and 100.')
    data=groups[(groups.outcome=='conversion')&(groups.evaluation=='All evaluation rows')]
    finest=int(data.segments.max())
    fine=data[data.segments==finest].to_dict('records')
    base=evaluate_standardized_policy(fine,{r['node']:1. for r in fine},1.)['value']
    if base<=0:
        raise ValueError('A positive broad conversion baseline is required.')
    q=reach_percent/100
    targeted=population*q
    rows=[]
    for count,frame in data.groupby('segments'):
        ranked=frame.sort_values(['estimation_effect','node'],ascending=[False,True]).node.tolist()
        records=frame.to_dict('records')
        w=allocation(records,ranked,q)
        lifted={r['node']:w[(r['node']+1)//(finest//count)-1] for r in fine}
        effect=evaluate_standardized_policy(fine,lifted,q)['value']/q if q>0 else 0.
        gain=effect/base-1 if q>0 else 0.
        if count==1 or reach_percent==100:
            gain=0.
        rate=baseline_per_10k/10000*(1+gain)
        if not 0<=rate<=1:
            raise ValueError('Scenario implies lift outside 0–100%; lower the baseline input.')
        extra=targeted*baseline_per_10k/10000*gain
        full=sum(v>=1-1e-12 for v in w.values())
        partial=[v for v in w.values() if 1e-12<v<1-1e-12]
        fraction=float(partial[0]) if partial else 0.
        description=f'{full} whole cluster'+('s' if full!=1 else '')
        if partial:
            description+=f' + {fraction:.2%} of the next'
        node_ids=frame.set_index('node')['group'].to_dict()
        ids=[str(node_ids[n]) for n in ranked if w[n]>0]
        rows.append(dict(segments=int(count),option='Broad targeting' if count==1 else f'{count} groups',
                         population=population,reach_percent=reach_percent,targeted_users=targeted,
                         whole_clusters=full,boundary_cluster_fraction=fraction,selection=description,
                         selected_cluster_ids=', '.join(ids),benchmark_lift_per_10k=effect*10000,
                         benchmark_relative_gain=gain,client_baseline_per_10k=baseline_per_10k,
                         contribution_per_conversion=contribution_per_conversion,
                         additional_conversions=extra,break_even_cost=extra*contribution_per_conversion))
    return pd.DataFrame(rows)
