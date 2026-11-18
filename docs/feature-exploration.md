# Historical feature exploration — 2026-10-20

These diagnostics predate the mixed-type correction. The ablation clustering treated category codes as continuous numbers and is superseded. In particular, single-feature directional AUC of an arbitrarily ordered category code is not a reliable measure of meaningful ordered association. The repeated-value counts remain descriptive facts. Current clustering respects Criteo’s four continuous and eight categorical features; see segmentation-model.md.

## What was tested

All 13,979,592 users were retained. Distribution/mode/missing-value summaries cover the full release. Single-feature conversion AUC is measured on the 2,795,918 estimation users, with the direction chosen to make AUC at least 0.5. It is discrimination, not classification accuracy or advertising uplift. Pearson correlations use a fixed 200,000-user training-feature sample. Outcomes do not enter any clustering fit.

Sensitivity runs use the same 60/20/20 data partitions and balanced feature-only clustering. The 8,387,755 training users set feature scaling and split medians. At most 20,000 users per parent initialize/iterate cluster centers. Evaluation assignments cover all 2,795,919 evaluation users. For this diagnostic, one cluster at each level is chosen by the highest overall conversion rate in the separate estimation set, then conversion concentration is measured in evaluation. This descriptive ranking differs from the app's advertising-response ranking. It is designed to investigate conversion concentration, not choose a targeting policy or validate investment returns.

## Main finding

f8 is strongly predictive of conversion on its own: estimation AUC 0.932. f9 reaches 0.911, f4 0.857, and f10 0.840. This supports checking f8's influence, but does not establish label leakage or invalid data. Feature meanings/timing are not recoverable from the anonymized columns alone.

For f8, 52.24% of all users have one repeated value. On estimation users, conversion rates are about 0.0073% at that value and 0.6156% elsewhere: about an 84-fold difference. This is a large repeated-value population difference, not just a handful of extreme observations.

## Full-data feature-removal checks

|Feature setup|Conversions captured by one half-sized cluster, treatment/control|Captured by one quarter-sized cluster, treatment/control|Maximum balanced hierarchy fitted|
|---|---:|---:|---:|
|All features|98.4% / 98.4%|95.6% / 94.6%|64|
|Remove f8|63.4% / 58.4%|62.8% / 57.7%|64|
|Remove f2 and f8|92.0% / 89.5%|90.6% / 88.6%|4|
|Remove f2, f8, f9|85.1% / 80.6%|83.2% / 78.7%|4|
|Clip feature tails at training 0.1%/99.9% quantiles|98.4% / 98.4%|95.7% / 94.6%|64|

Removing f8 materially changes the early geometry. Removing additional features can bring concentration back through a different geometry; this is not a monotone feature-importance experiment. A sequential constrained clustering algorithm can find different local solutions after feature removal. The remaining features still encode substantial conversion-associated structure.

The feature-removal runs without f2/f8 cannot form a full balanced hierarchy: at a later parent, tied profiles produce a 62.2% split when a roughly half-sized split is required. The script records the failure and reports the deepest feasible complete hierarchy rather than arbitrarily separating tied users. These variants are not comparable at 8–64 clusters because those models were not fitted.

## Repeated-value and tail structure

No missing or infinite values were found in any f0–f11 feature. Some sparse features have extreme values far from the median relative to standard deviation (f1 about 60 standard deviations, f11 about 53), but clipping the extreme 0.1% tails does not remove the conversion-concentration pattern.

Across all rows, these pairs have exactly matching indicators for being at their own most common value: f0/f6, f2/f8, f4/f10, f5/f7. This does not mean their numeric values are identical, nor that they can safely replace each other. No sampled Pearson correlation exceeds an absolute 0.9; repeated-value redundancy is not captured by that linear-correlation test.

## Interpretation

The concern about f8 dominating the result has direct support. The concern that a few numerical outliers explain everything does not have support from this clipping test. Multiple anonymous features carry conversion-associated information, and removing features until gains disappear would select the result rather than validate it.

Keep the current app unchanged while deciding whether the project should show the full feature set, an explicitly simplified feature subset, or both. The useful next comparison is all features versus without f8, labeled as sensitivity, with feature profiles available for explanation. Do not call f8 leakage without evidence about feature provenance/timing. New feature selection and repeated evaluation make these exploratory diagnostics, not a fresh confirmatory assessment.

## Artifacts

`outputs/feature_exploration/` contains feature_profile.csv, feature_correlations.csv, shared_mode_indicators.csv, conversion_concentration_ablations.csv, cluster_assignment_sensitivity.csv, balance_limitations.json, feature_sensitivity.png, and the separate diagnostic model bundles. Clipped bundles require the stored clip_bounds.npz preprocessing. App data and its clustering model are unchanged.

Reproduce with scripts/explore_features.py, scripts/check_feature_ablations.py, and scripts/render_feature_exploration.py, using the project virtual environment. The balance-constrained fitting procedure may stop at fewer groups after features are removed; failures are recorded explicitly.
