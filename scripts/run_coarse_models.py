"""Exploratory honest shallow-tree segmentation for visit and conversion.

Trees regress the randomized transformed outcome, not raw conversion probability.
Discovery, effect-estimation, and test rows are disjoint. No targeting policy is fitted.
"""
from pathlib import Path
import argparse
import json
import sys
import time

import altair as alt
import joblib
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.tree import DecisionTreeRegressor, export_text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data import UPLIFT_FEATURES, load_dataset


def effect(t, y):
    n1, n0 = int(t.sum()), int(len(t) - t.sum())
    s1, s0 = int(y[t == 1].sum()), int(y[t == 0].sum())
    p1, p0 = s1 / n1, s0 / n0
    estimate = p1 - p0
    se = np.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    return dict(n=len(t), treated=n1, control=n0, treated_positives=s1,
                control_positives=s0, treatment_rate=p1, control_rate=p0,
                effect=estimate, se=se, low=estimate - 1.96 * se, high=estimate + 1.96 * se)


def main(discovery_rows, estimation_rows, seed):
    started = time.perf_counter()
    out = ROOT / 'outputs' / 'coarse_models'
    out.mkdir(parents=True, exist_ok=True)
    print('Loading full uplift dataset...', flush=True)
    df = load_dataset('uplift', columns=UPLIFT_FEATURES + ['treatment', 'visit', 'conversion'])
    if discovery_rows + estimation_rows >= len(df):
        raise ValueError('Discovery and estimation sets must leave test rows')
    order = np.random.default_rng(seed).permutation(len(df))
    discovery = order[:discovery_rows]
    estimation = order[discovery_rows:discovery_rows + estimation_rows]
    test = order[discovery_rows + estimation_rows:]
    np.savez_compressed(out / 'split_rows.npz', discovery=discovery, estimation=estimation, test=test)
    x = df[UPLIFT_FEATURES].to_numpy(dtype=np.float32)
    t = df.treatment.to_numpy(dtype=np.int8)
    xd, xe, xt = x[discovery], x[estimation], x[test]
    td, te, tt = t[discovery], t[estimation], t[test]
    del x
    propensity = float(td.mean())
    groups, summaries, baselines, rules = [], [], [], []
    for outcome in ('visit', 'conversion'):
        y = df[outcome].to_numpy(dtype=np.int8)
        yd, ye, yt = y[discovery], y[estimation], y[test]
        z_discovery = yd * (td / propensity - (1 - td) / (1 - propensity))
        z_test = yt * (tt / propensity - (1 - tt) / (1 - propensity))
        calibration_baseline = effect(te, ye)['effect']
        baseline = effect(tt, yt)
        baselines.append(dict(outcome=outcome, split='test', **baseline))
        baselines.append(dict(outcome=outcome, split='full_release', **effect(t, y)))
        for count in (2, 4, 8):
            tick = time.perf_counter()
            model = DecisionTreeRegressor(max_leaf_nodes=count, max_depth=4,
                                          min_samples_leaf=max(1000, discovery_rows // 50),
                                          random_state=seed)
            model.fit(xd, z_discovery)
            le, lt = model.apply(xe), model.apply(xt)
            leaves = sorted(np.unique(le))
            estimated = {int(leaf): effect(te[le == leaf], ye[le == leaf])['effect'] for leaf in leaves}
            ranked = sorted(leaves, key=lambda leaf: estimated[int(leaf)])
            prediction = np.empty(len(test))
            leaf_test = {}
            for rank, leaf in enumerate(ranked, start=1):
                mask = lt == leaf
                record = effect(tt[mask], yt[mask])
                leaf_test[int(leaf)] = record
                prediction[mask] = estimated[int(leaf)]
                for half, indexes in [('test_first_half', np.arange(len(test)//2)),
                                      ('test_second_half', np.arange(len(test)//2, len(test)))]:
                    subset = indexes[lt[indexes] == leaf]
                    groups.append(dict(outcome=outcome, groups=count, group=rank, node=int(leaf),
                                       split=half, estimated_effect=estimated[int(leaf)],
                                       **effect(tt[subset], yt[subset])))
                groups.append(dict(outcome=outcome, groups=count, group=rank, node=int(leaf),
                                   split='test', estimated_effect=estimated[int(leaf)], **record))
            low_group, high_group = leaf_test[int(ranked[0])], leaf_test[int(ranked[-1])]
            gap = high_group['effect'] - low_group['effect']
            gap_se = np.sqrt(high_group['se']**2 + low_group['se']**2)
            # Paired squared-loss reduction on randomized transformed outcomes.
            # Positive values favor the calibrated segment effects over one constant effect.
            improvement = (2 * z_test * (prediction - calibration_baseline)
                           + calibration_baseline**2 - prediction**2)
            gain = float(improvement.mean())
            gain_se = float(improvement.std(ddof=1) / np.sqrt(len(test)))
            summaries.append(dict(outcome=outcome, groups=count, actual_groups=len(leaves),
                                  high_minus_low=gap, gap_low=gap-1.96*gap_se, gap_high=gap+1.96*gap_se,
                                  gap_p=float(2*norm.sf(abs(gap/gap_se))),
                                  prediction_gain=gain, gain_low=gain-1.96*gain_se,
                                  gain_high=gain+1.96*gain_se,
                                  fit_seconds=round(time.perf_counter()-tick, 2)))
            joblib.dump({'model': model, 'calibrated_effects': estimated, 'features': UPLIFT_FEATURES},
                        out / f'{outcome}_{count}_groups.joblib')
            rules.append(f'## {outcome}, {count} groups\n\n' + export_text(model, feature_names=UPLIFT_FEATURES, decimals=5))
            print(f'{outcome}, {count} groups: {summaries[-1]}', flush=True)
    group_frame = pd.DataFrame(groups)
    summary_frame = pd.DataFrame(summaries)
    # Holm adjustment across all six predeclared high-versus-low comparisons.
    p = summary_frame.gap_p.to_numpy()
    ix = np.argsort(p)
    adjusted = np.empty(len(p))
    adjusted[ix] = np.minimum(1, np.maximum.accumulate(p[ix] * np.arange(len(p), 0, -1)))
    summary_frame['gap_p_holm'] = adjusted
    group_frame.to_parquet(out / 'group_effects.parquet', index=False)
    summary_frame.to_csv(out / 'model_comparison.csv', index=False)
    pd.DataFrame(baselines).to_csv(out / 'baselines.csv', index=False)
    (out / 'tree_rules.txt').write_text('\n\n'.join(rules), encoding='utf-8')
    meta = dict(seed=seed, total_rows=len(df), discovery_rows=len(discovery),
                estimation_rows=len(estimation), test_rows=len(test),
                discovery_treatment_share=propensity, features=UPLIFT_FEATURES,
                outcomes=['visit', 'conversion'], requested_groups=[2,4,8],
                max_depth=4, min_leaf_rows=max(1000, discovery_rows//50),
                elapsed_seconds=round(time.perf_counter()-started, 2),
                note='Exploratory transformed-outcome regression trees; not a custom causal-tree splitting algorithm. '
                     'Pointwise normal intervals conditional on fitted groups; no allowance for release sampling bias. '
                     'Split halves check evaluation consistency, not model retraining stability. '
                     'No monetary assumptions, targeting policy, or flexible model.')
    (out / 'run.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    render(out, group_frame, baselines)
    print(f'Done in {meta["elapsed_seconds"]} seconds. Results: {out}', flush=True)


def render(out, group_frame, baselines):
    for outcome in ('visit', 'conversion'):
        chart_data = group_frame[(group_frame.outcome == outcome) & (group_frame.split == 'test')].copy()
        for c in ('effect', 'low', 'high', 'estimated_effect'):
            chart_data[c] *= 10_000
        chart_data['model'] = chart_data.groups.astype(str) + ' groups'
        base = alt.Chart(chart_data).encode(
            x=alt.X('group:O', title='Group ordered by separate estimation-set effect'),
            tooltip=['group:O','n:Q','treated_positives:Q','control_positives:Q',
                     alt.Tooltip('effect:Q', format='.2f'),alt.Tooltip('low:Q',format='.2f'),
                     alt.Tooltip('high:Q',format='.2f')])
        points = base.mark_point(filled=True, size=90, color='#087f8c').encode(
            y=alt.Y('effect:Q', title=f'Incremental {outcome}s per 10,000 users'))
        bars = base.mark_rule(color='#087f8c').encode(y='low:Q', y2='high:Q')
        baseline_value = next(b['effect']*10000 for b in baselines if b['outcome']==outcome and b['split']=='test')
        ref = base.mark_rule(strokeDash=[5,5], color='#737373').encode(y=alt.datum(baseline_value))
        chart = (bars + points + ref).properties(width=300,height=300).facet(column='model:N').properties(
            title=f'{outcome.title()}: held-out treatment differences (95% pointwise intervals)')
        chart.save(out / f'{outcome}_groups.html')
        chart.save(out / f'{outcome}_groups.vl.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--discovery-rows', type=int, default=1_000_000)
    parser.add_argument('--estimation-rows', type=int, default=2_000_000)
    parser.add_argument('--seed', type=int, default=20261020)
    parser.add_argument('--render-only', action='store_true')
    args = parser.parse_args()
    if args.render_only:
        out = ROOT / 'outputs' / 'coarse_models'
        render(out, pd.read_parquet(out / 'group_effects.parquet'),
               pd.read_csv(out / 'baselines.csv').to_dict('records'))
    else:
        main(args.discovery_rows, args.estimation_rows, args.seed)
