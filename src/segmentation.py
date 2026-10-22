"""Shallow response segmentation and paired held-out policy evaluation."""
import numpy as np
import pandas as pd


def responsive_audience_comparison(groups,outcome):
    """Prioritize using estimation data only; evaluate one whole group at each level."""
    data=groups[(groups.outcome==outcome)&(groups.evaluation=='All evaluation rows')]
    rows=[]
    for segments,frame in data.groupby('segments'):
        chosen=frame.sort_values('estimation_effect',ascending=False,kind='stable').iloc[0]
        share=float(chosen['share'])
        records=frame.to_dict('records')
        weights={r['node']:float(r['node']==chosen['node']) for r in records}
        rows.append(dict(outcome=outcome,segments=int(segments),reach=share*100,
                         selected_group=int(chosen['group']),
                         **evaluate_policy(records,weights,share)))
    return pd.DataFrame(rows).sort_values('segments')


def summarize_groups(leaves, treatment, outcome):
    records = []
    for leaf in np.unique(leaves):
        mask = leaves == leaf
        t, y = treatment[mask], outcome[mask]
        nt, nc = int(t.sum()), int(len(t) - t.sum())
        if min(nt, nc) < 2:
            raise ValueError('Every group needs at least two observations in each arm')
        st, sc = int(y[t == 1].sum()), int(y[t == 0].sum())
        pt, pc = st / nt, sc / nc
        variance = pt*(1-pt)/(nt-1) + pc*(1-pc)/(nc-1)
        records.append(dict(node=int(leaf), n=len(t), treated=nt, control=nc,
                            treated_positives=st, control_positives=sc,
                            treatment_rate=pt, control_rate=pc, effect=pt-pc,
                            se=float(np.sqrt(variance))))
    return records


def allocation(records, ranked_nodes, reach):
    """Allocate an exact fraction by features only; randomize within a boundary group.

    Weights are treatment probabilities, so fractional groups describe expected
    random allocation rather than claiming that a particular user must be treated.
    """
    if not 0 <= reach <= 1:
        raise ValueError('Reach must be between zero and one')
    sizes = {r['node']: r['n'] for r in records}
    remaining = reach * sum(sizes.values())
    weights = {}
    for node in ranked_nodes:
        weights[node] = float(np.clip(remaining / sizes[node], 0, 1))
        remaining = max(0.0, remaining - sizes[node])
    return weights


def evaluate_policy(records, weights, reach):
    """Difference in weighted outcomes by randomized arm, plus paired broad-policy gain.

    Outcomes for the counterfactual are identified by assignment. No realized
    exposure or economic assumptions enter. Uncertainty conditions on frozen
    groups, rankings, and allocation probabilities.
    """
    nt = sum(r['treated'] for r in records)
    nc = sum(r['control'] for r in records)

    def moments(offset):
        st = sum((weights[r['node']]-offset)*r['treated_positives'] for r in records)
        sc = sum((weights[r['node']]-offset)*r['control_positives'] for r in records)
        qt = sum((weights[r['node']]-offset)**2*r['treated_positives'] for r in records)
        qc = sum((weights[r['node']]-offset)**2*r['control_positives'] for r in records)
        variance = max(0.0, (qt-st*st/nt)/(nt-1)/nt + (qc-sc*sc/nc)/(nc-1)/nc)
        return st/nt-sc/nc, float(np.sqrt(variance))

    value, se = moments(0)
    gain, gain_se = moments(reach)
    baseline = reach * (sum(r['treated_positives'] for r in records)/nt
                        - sum(r['control_positives'] for r in records)/nc)
    return dict(value=value, se=se, broad_value=baseline, gain=gain, gain_se=gain_se,
                realized_expected_reach=sum(r['n']*weights[r['node']] for r in records)
                                         /sum(r['n'] for r in records))


def evaluate_standardized_policy(records,weights,reach):
    """Use common feature-stratum proportions in both randomized arms.

    Call with the same finest feature-only strata for every policy comparison.
    Variance conditions on fitted clusters, fixed rankings, and stratum counts.
    """
    total=sum(r['n'] for r in records)
    def moments(offset):
        value,variance=0.,0.
        for r in records:
            pt=r['treated_positives']/r['treated']
            pc=r['control_positives']/r['control']
            v=pt*(1-pt)/(r['treated']-1)+pc*(1-pc)/(r['control']-1)
            coefficient=r['n']/total*(weights[r['node']]-offset)
            value+=coefficient*(pt-pc)
            variance+=coefficient**2*v
        return value,float(np.sqrt(variance))
    value,se=moments(0)
    gain,gain_se=moments(reach)
    baseline=reach*sum(r['n']/total*(r['treated_positives']/r['treated']-r['control_positives']/r['control']) for r in records)
    return dict(value=value,se=se,broad_value=baseline,gain=gain,gain_se=gain_se,
                realized_expected_reach=sum(r['n']*weights[r['node']] for r in records)/total)


def cluster_average_comparison(groups,outcome):
    """Select by estimation response, report observed within-cluster average lift."""
    data=groups[(groups.outcome==outcome)&(groups.evaluation=='All evaluation rows')]
    broad=data[data.segments==1].iloc[0]
    rows=[]
    for count,frame in data.groupby('segments'):
        chosen=frame.sort_values(['estimation_effect','node'],ascending=[False,True]).iloc[0]
        def arm_variance(row,arm):
            n=row['treated' if arm=='treatment' else 'control']
            rate=row[f'{arm}_rate']
            return rate*(1-rate)/(n-1)
        covariance=sum(chosen[arm]/broad[arm]*arm_variance(chosen,label)
                       for arm,label in [('treated','treatment'),('control','control')])
        gain_variance=max(0.,chosen['se']**2+broad['se']**2-2*covariance)
        rows.append(dict(outcome=outcome,segments=int(count),selected_group=int(chosen['group']),
                         node=int(chosen['node']),reach=float(chosen['share'])*100,n=int(chosen['n']),
                         treatment_rate=float(chosen['treatment_rate']),control_rate=float(chosen['control_rate']),
                         value=float(chosen['effect']),se=float(chosen['se']),
                         gain=float(chosen['effect']-broad['effect']),gain_se=float(np.sqrt(gain_variance))))
    return pd.DataFrame(rows).sort_values('segments').reset_index(drop=True)
