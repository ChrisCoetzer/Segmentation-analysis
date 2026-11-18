# Clustering seed stability — 2026-10-20

The original clustering and three new seeds use identical customer partitions, feature types, scaling rules, balanced hierarchy depth, estimation ranking protocol, and evaluation data. Only clustering randomness changes. These are not independent trials and do not test data outlier removal or variation from different train/evaluation samples.

|Clustering seed|16-group conversion lift|32-group conversion lift|Difference (32 − 16)|95% paired interval|
|---|---:|---:|---:|---|
|20261020|112.51|109.52|-2.99|-23.74 to 17.75|
|20261021|115.99|107.17|-8.82|-28.10 to 10.46|
|20261022|110.90|108.42|-2.48|-23.37 to 18.41|
|20261023|115.33|105.79|-9.54|-29.01 to 9.92|

Units are incremental conversions per 10,000 members of the cluster selected using estimation data. Paired intervals account for overlapping evaluation users when the selected 32-group cluster is a child of the selected 16-group cluster. They condition on the fitted model and stratum counts, exclude training/privacy-release uncertainty, and are not adjusted for repeated comparisons.

All three new conversion runs retain the dip, but every interval includes zero. This is not evidence that 32 is definitively worse, nor that the original point was simply an unlucky initialization. Visits vary more in their 16-vs-32 ranking across seeds; no universal segment-count optimum is established.

The app uses seed 20261021: the first new run, designated before examining its evaluation result. The other seeds are sensitivity checks, not a search for a favorable curve. Active artifacts are under outputs/clustering_stability/seed_20261021/; previous app summaries are under outputs/clustering_stability/before_rerun/. Reproduce with scripts/train_segmentation.py --cluster-seed 20261021 and inspect all runs with scripts/report_clustering_stability.py.
