# Segmentation model review — 2026-10-20

## Finding

The current model measures a constrained targeting policy, not the business return to segmentation effort in general. Reciprocal alignment between reach and segment count is partly structural, but the magnitude and persistence of benefits are empirical. A plateau is neither guaranteed nor automatically meaningless.

## What the code actually does

- Learns separate conversion/visit depth-six trees from f0–f11 using training-only transformed randomized outcomes. It optimizes squared-error separation, not directly the campaign policy value at a chosen reach.
- Forces every node to split 45–55% at each level. It searches five near-median thresholds per feature. There is no minimum benefit or validation-based stopping rule: weak splits still happen.
- Ranks group effects on a separate estimation partition. Selects groups in that order until the audience is filled; the last group is selected at random in expectation.
- Evaluates the frozen selection using randomized treatment/control outcomes in a third partition. Selection sizes use evaluation features/counts, not outcomes. Repeated inspection makes these exploratory evaluation results, not a fresh confirmation.

## Why the reach-dependent knee appears

If reach is smaller than the top-ranked group, the model randomly selects within that group. Its expected response per selected person is essentially constant as reach changes within that range. Further splitting can isolate a smaller responsive pocket. Once reach spans several groups, many subsequent splits occur inside areas that remain fully selected or fully excluded. Splitting those areas without changing their selection leaves policy value exactly unchanged. Only changed priorities and boundary allocation affect value. Refining groups can still improve or worsen selection at every level; there is no mathematical guarantee of monotonic improvement or a knee exactly at 1/reach.

## Measured evidence: conversion lift per 10,000 selected users

| Reach | 4 groups | 8 | 16 | 32 | 64 |
|---|---:|---:|---:|---:|---:|
|25%|43.35|43.44|44.41|44.73|43.84|
|12.5%|48.91|76.28|79.09|81.33|82.52|
|3.125%|48.91|92.97|174.82|214.75|209.07|

At 12.5% reach, the paired gain from 32 to 64 groups is +1.20 per 10,000, with a pointwise 95% interval of -1.93 to +4.33. At 25% reach it is -0.89 (-2.16 to +0.37); at 3.125% it is -5.68 (-16.37 to +5.02). These intervals condition on the frozen model and rankings, exclude model-training variability, and do not correct for searching multiple reaches or model levels.

The 64-group evaluation contains 24 groups with zero control conversions and 39 with at most one. Overall sample size is large, but many individual group effects have sparse outcome support. This is not proof that the selected high-response groups are unreliable; it is a reason to check event counts and ranking stability rather than trust group count alone.

## Implications and recommended next step

The existing equal-volume targeting comparison is internally coherent. Its limitation is the claim we attach to it: analytical resolution is not measured marketing effort, monetary cost, or a universal optimal group count. The financial simulator rescales the same policy evidence and supplies no independent validation.

Keep this tree as a transparent baseline. Assess marginal gain across a small set of campaign reaches and repeated train/estimate/evaluate splits before recommending model complexity. Use paired differences and ranking/selection stability to identify the simplest model whose additional refinements have little supported benefit at a specified reach. A more flexible uplift method would provide a useful comparator for how much the forced median splits restrict results, but is not implemented or selected in this review. Changing to equal-sized score bins alone would retain the same within-bin selection ceiling and would not resolve the conceptual issue.

The app and fitted models were not changed during this review. Reproduce the numerical audit with `python scripts/audit_segmentation.py` using the project virtual environment.


## Follow-up: independent raw-count and normalization reassessment

Reconstructed the 64-leaf assignments from the original processed evaluation rows and saved model. Every leaf's row count, treatment/control count, and positive counts exactly matched the exported summaries. Feature inputs remain f0–f11 only. No evaluation label is used to rank groups.

The large gains have a concrete source: the top 47.7% group contains 98.45% of treatment conversions and 98.25% of control conversions. The top 22.0% group contains 93.35% and 93.49% respectively. The first splits use f8. Thus simple feature thresholds separate a large near-zero-conversion region from a concentrated conversion region. Both arms concentrate together; the tree's gains cannot be described exclusively as discovering unique advertising susceptibility rather than baseline conversion likelihood.

There is also a material estimator sensitivity. The current app subtracts weighted outcome means using the overall arm denominators, then divides by the pooled selected fraction. This is an inverse-propensity-style policy estimator under constant random assignment; finite imbalance and any release-induced differences in feature composition can affect it. It is not the same as comparing treatment and control rates standardized to the same segment proportions. Neither post-hoc calculation alone establishes an unbiased original-population causal effect in this privacy-subsampled release.

At 12.5% reach, applying the SAME frozen rankings and allocations but averaging within-group treatment-minus-control rates with common population-share weights gives:

|Groups|Current app / 10,000 selected|Common-group-weight estimate|
|---|---:|---:|
|1|11.56|11.56|
|2|23.92|23.63|
|4|48.91|45.70|
|8|76.28|67.14|
|16|79.09|62.04|
|32|81.33|61.07|
|64|82.52|63.11|

This is not merely a cosmetic change: the common-group-weight comparison does not show the same continuing improvement beyond eight groups. The previous review's paired intervals assess the current app estimator only and do not resolve this sensitivity. The simulator inherits the same issue through its benchmark gain ratio.

The earlier recommendation to assess only repeated partitions was incomplete. Before recommending any group count, settle the policy estimand and group standardization, examine treatment proportions within groups, and compare uplift-based ranking against a conversion-propensity baseline. Do not yet interpret the current displayed financial amounts as validated investment guidance. Models and UI remain unchanged during this reassessment.

Source context: Criteo explicitly states that the release was non-uniformly subsampled to prevent recovering original incrementality: https://huggingface.co/datasets/criteo/criteo-uplift . This prevents validating the original advertiser's effect from these rates alone.
