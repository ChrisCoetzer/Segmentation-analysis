# Feature-only balanced clustering

## Cluster construction

One unsupervised hierarchy is fitted using only f0–f11. No treatment, exposure, visit, conversion, or transformed outcome enters clustering. The previous response-driven trees are historical.

Criteo's feature types are respected:

- Continuous: f0, f2, f7, f10. Training-only mean/standard-deviation scaling.
- Categorical: f1, f3, f4, f5, f6, f8, f9, f11. Nominal one-hot membership, never numerical ordering or numerical differences between codes. Raw float64 values are retained so casting cannot merge distinct category tokens.

The distance is half the sum of squared standardized continuous differences, plus one for each categorical mismatch. The weighting gives each continuous variable an expected pairwise contribution near one, while each categorical mismatch contributes one regardless of code magnitude. This is an explicit modeling choice, not a unique correct weighting.

Each parent is split by approximate, balanced two-means in that encoded geometry:

1. Sample at most 20,000 training members and initialize two centers using KMeans (three starts).
2. Order squared-distance differences, assign roughly half to each center, and update centers up to 12 times.
3. Freeze the distance-difference direction and median threshold from all training members of the parent.
4. Repeat for five levels: 1/2/4/8/16/32 clusters. Ties that prevent balance fail explicitly.

The implementation uses sparse one-hot sample matrices and category-index lookups for full-data scoring, avoiding a giant dense dummy matrix. Held-out categories not observed in training use a reserved unknown token. No labels enter vocabulary fitting, scaling, or clustering.

New users follow the frozen distance-difference boundaries. Evaluation sizes are measured, not forcibly rebalanced. Anonymous features support numeric similarity, not named demographics or marketing personas. Standardization is a modeling choice, not proof that all features have equal business importance.

## Data roles

The release has 13,979,592 users. Seed 20261020 creates disjoint partitions:

- 8,387,755 training users fit scaling and clusters.
- 2,795,918 estimation users measure treatment-minus-control response in each cluster and freeze the ranking.
- 2,795,919 evaluation users measure the selected policy.

Membership depends only on features. Post-clustering response rankings may differ between outcomes. A response ranking does not alter the cluster boundaries or membership.

## Selection and evaluation

For each cluster count, select the single cluster with highest treatment-minus-control response in the separate estimation data (node ID breaks exact ties). Evaluate its mean treatment outcome minus its mean control outcome using every evaluation user in that cluster. These are selected-cluster averages, not fixed-reach targeting policies. No sample is drawn and there is no reach control. Group sizes differ across levels and are shown explicitly.

Multiply the average by 10,000 for the display. The broad reference is the treatment-minus-control average over all evaluation users. Gain subtracts this reference. Group-effect variance sums treatment/control rate variances; paired group-minus-broad variance subtracts covariance from overlapping users within each arm. Intervals condition on frozen clustering and estimation rankings and exclude training and privacy-release uncertainty.

The break-even simulator separately combines estimation-ranked clusters to fill a chosen percentage of the client's total customer population. Its selected-customer count updates with population and ratio. Every model uses the same audience share; its fixed-reach evaluation uses common 32-cluster strata and population weights in both arms. It therefore differs from the main single-cluster-average chart, as explained in the UI.

The offline pipeline still retains the earlier standardized fixed-reach policy grid for historical analysis, but the current app does not read it. Current chart averages are computed from groups.parquet via cluster_average_comparison.

## Current artifacts and checks

Current artifacts are in `outputs/mixed_clustering/`. `previous_app_results/` preserves the replaced, incorrectly all-numeric clustering summaries. Older response-driven models and all-numeric models are historical and are not loaded by the app.

Rebuild with `.\.venv\Scripts\python.exe scripts/train_segmentation.py`. Tests verify that arbitrary category-code recoding preserves geometry and cluster assignment, continuous features retain scaled geometry, unknown categories are handled, float64 category identity is preserved, training groups are balanced and nested, prediction boundaries are frozen, outcome inputs are excluded, both arms use common stratum weights, and the chart/simulator use the same selected-cluster averages.

Fit counts, balance, vocabulary sizes, and current measured values are recorded in run.json and the exported tables. The previous all-numeric results do not apply to this corrected geometry.

## Scope

The curve measures how useful these feature-based clusters are for selecting a campaign audience. Cluster count is not measured marketing effort or monetary cost. Criteo's non-uniform privacy subsampling prevents interpreting these benchmark effects as original-advertiser or client-population causal effects. The financial simulator applies explicit client assumptions to the same evidence; it does not provide independent validation.


Feature types and pre-treatment collection are documented by Criteo in Section 3, Table 2, and Appendix C: https://arxiv.org/html/2111.10106v1#S3 .


The segmentation chart supports direct point selection. Clicking a point highlights that level and updates the selected-cluster summary below it. The separate segment slider has been removed. The outcome and chart-measure controls remain above the plot.
