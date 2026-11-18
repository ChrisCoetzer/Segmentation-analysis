# First coarse segmentation run

Historical record only. This approach has been replaced by the balanced, nested models described in `segmentation-model.md` and is not used by the current app.

Run date: October 20, 2026. Exploratory results from the released Criteo Uplift benchmark, not production advertiser estimates.

## Method

Run `.\.venv\Scripts\python.exe scripts/run_coarse_models.py` from the project root.

A seeded random permutation partitions all 13,979,592 rows into 1,000,000 discovery rows, 2,000,000 effect-estimation rows, and 10,979,592 test rows. Both outcomes use the same partition. Seed: 20261020. Row positions are saved in `outputs/coarse_models/split_rows.npz`.

For each outcome, fit ordinary shallow regression trees with 2, 4, and 8 leaves to the randomized transformed outcome:

`Z = Y * (T/e - (1-T)/(1-e))`

Here `e` is the discovery-set treatment proportion. This targets differences in response to treatment rather than conversion probability alone. These are transformed-outcome regression trees, not an implementation of a specialized causal-tree splitting criterion. Maximum depth is 4; minimum discovery leaf size is 20,000 rows. Inputs are only `f0`–`f11`; neither exposure nor either outcome is an input feature.

Within each fitted group, use the separate estimation set to estimate treatment-minus-control response and order the groups. Freeze the rules and order before evaluating test outcomes. Test group effects are differences in outcome proportions, with pointwise normal 95% confidence intervals. High-versus-low comparison p-values receive Holm adjustment across the six models. Saved prediction-gain statistics compare calibrated segment estimates with a single calibrated average using paired transformed-outcome squared loss; they are statistical prediction metrics, not incremental conversions delivered by a targeting policy.

## Results

Total runtime, including loading and fitting/evaluation: 26.94 seconds, excluding chart export. Both outcomes show substantial held-out response variation.

Estimated incremental outcomes per 10,000 eligible users in the test set:

| Outcome | Population average (95% CI) | Lowest group in 4-group tree | Highest group in 4-group tree |
| --- | --- | --- | --- |
| Visit | 102.7 (99.4, 105.9) | 24.6 (22.7, 26.5) | 1,211.5 (1,151.8, 1,271.3) |
| Conversion | 11.6 (10.8, 12.4) | 1.7 (1.3, 2.0) | 232.9 (207.3, 258.5) |

The high-response groups are small: approximately 2.1% of test users for visits and 2.2% for conversions. Group rates are not population-wide gains. Visit and conversion trees discover their own groups; matching group numbers do not identify matching users across outcomes.

For both outcomes, the group ordering in the 4-group model also holds in each of two test halves. This checks evaluation consistency for fixed trees. It does not establish that retraining with different seeds would discover the same groups.

## Saved outputs

Under `outputs/coarse_models/`:

- `visit_groups.html`, `conversion_groups.html`: Altair charts, with held-out group effects, intervals, group counts, and a population-baseline reference. HTML rendering uses CDN-hosted chart libraries.
- `group_effects.parquet`: all models and test-half results.
- `model_comparison.csv`, `baselines.csv`: summary metrics and rates.
- `tree_rules.txt`, six `.joblib` models: rules and calibrated effects.
- `run.json`, `split_rows.npz`: configuration, runtime, and partitions.

## Limits and next interpretation

This first pass supports investigating treatment-response heterogeneity. It has not demonstrated an economic return, a targeting-policy gain, or an optimal segmentation depth. More groups do not increase the population average treatment effect. The release's anonymization and non-uniform sampling still limit interpretation and transfer to a real advertiser.

Intervals condition on learned rules and do not include model-discovery uncertainty or release-sampling distortion. Test halves are not independent replications of model training. Further model decisions informed by these results make this test set exploratory; a confirmatory final protocol should be agreed before further tuning.

Reference for the regression-tree implementation: [scikit-learn DecisionTreeRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeRegressor.html). Dataset background: [Criteo benchmark paper](https://arxiv.org/abs/2111.10106).
