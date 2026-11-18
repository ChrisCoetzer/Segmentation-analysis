# Criteo dataset reference

Documentation reviewed October 20, 2026. The source-based notes below distinguish published figures from local checks. Both full datasets were subsequently downloaded, checksum-verified, and scanned during setup; exact row/column counts matched, with no null or nonfinite numeric values. See the README and `outputs/validation/` for setup results, and `docs/coarse-models.md` for the subsequent exploratory modeling run.

## Uplift Prediction

### Origin and versions

Rows represent user observations from pooled advertising incrementality experiments, with randomly selected controls withheld from advertising.

The original release had 25,309,483 rows. An erratum describes an advertiser-related leak that could artificially improve uplift prediction. The replacement has 13,979,592 rows. The official repository links `criteo-research-uplift-v2.1.csv.gz` under CRITEO-UPLIFTv2. [Publisher page](https://ailab.criteo.com/criteo-uplift-prediction-dataset/), [official repository](https://github.com/criteo-research/large-scale-ITE-UM-benchmark).

### Fields

| Field | Documented meaning / interpretation |
| --- | --- |
| `f0`–`f11` | Twelve dense numeric features, anonymized and randomly projected. Original labels and units unavailable. |
| `treatment` | Binary experimental treatment-group indicator. |
| `exposure` | Binary effective-exposure indicator; distinct from assignment. Despite ambiguous source wording, this is not an estimated treatment-effect magnitude. |
| `visit` | Whether a visit occurred. |
| `conversion` | Whether a conversion occurred; the field description does not identify the business action. |

The Hugging Face viewer lists 16 columns: float64 features and int64 indicators. The card publishes treatment share 0.85, visit rate 0.046992, and conversion rate 0.00292. These are aggregate rates, not treatment effects. Its introductory “11 features” and “25M rows” text conflicts with the field list and updated figures. [Criteo dataset card and viewer](https://huggingface.co/datasets/criteo/criteo-uplift).

Criteo states that non-uniform subsampling hides the original incrementality level. The documentation does not establish that every subgroup effect or ranking remains unchanged. Original advertiser population rates cannot be recovered simply by reading the public rates. [Privacy description](https://ailab.criteo.com/criteo-uplift-prediction-dataset/).

Schema-based observation: no explicit user ID, campaign ID, experiment ID, timestamp, spend, revenue, or targeting-budget field is listed. This does not establish what the anonymous features originally encoded.

## Attribution Modeling for Bidding

### Origin and grain

Each row is one displayed banner impression from sampled, anonymized traffic covering 30 days. Hugging Face reports 16,468,027 rows. The publisher gives approximately 16.5 million impressions, 45,000 conversions, and 700 campaigns. The field list totals 22 columns. [Publisher page](https://ailab.criteo.com/criteo-attribution-modeling-bidding-dataset/), [Criteo dataset card](https://huggingface.co/datasets/criteo/criteo-attribution-dataset).

### Fields

| Field | Documented meaning |
| --- | --- |
| `timestamp` | Impression time, starting at zero; rows ordered by time. |
| `uid` | User identifier. |
| `campaign` | Campaign identifier. |
| `conversion` | Conversion within 30 days after the impression, regardless of last-click status. |
| `conversion_timestamp` | Conversion time; `-1` if none observed. |
| `conversion_id` | Conversion identifier; `-1` if none observed. |
| `attribution` | Whether the conversion was credited to Criteo. |
| `click` | Whether the impression was clicked. |
| `click_pos` | Position of click before conversion, indexed from zero. |
| `click_nb` | Number of clicks before conversion. |
| `cost` | Transformed price paid by Criteo for the display. |
| `cpo` | Transformed cost-per-order associated with attributed conversion. |
| `time_since_last_click` | Seconds since the previous click for the impression. |
| `cat1`–`cat9` | Contextual categorical features with undisclosed meanings. |

Definitions: [publisher documentation](https://ailab.criteo.com/criteo-attribution-modeling-bidding-dataset/), [Criteo dataset card](https://huggingface.co/datasets/criteo/criteo-attribution-dataset).

### Reading the records

Inference from the grain and forward-looking label: positive impression rows need not equal distinct conversions. Inspect repeated `conversion_id` values before counting conversions. Likewise, impression counts differ from user counts. Numeric category codes do not establish a continuous scale.

The paper distinguishes public logs used offline from separate online experiments. Its online results are not experimental outcomes attached to these public rows. [Original paper, Sections 4.1 and 4.4](https://arxiv.org/html/1707.06409).

The monetary transformations are unspecified in the field descriptions. These fields alone do not establish actual dollar spend, profit, or a campaign budget. Crediting Criteo with a conversion does not establish that an impression caused it.

## Relationship between releases

Schema-based conclusion: no shared join key is documented. `uid` appears only in attribution; no crosswalk to the uplift features is provided. We have not established shared users, campaigns, or time periods. How these datasets might complement each other remains open.

## Unresolved checks

- Uplift: observation windows, precise effective-exposure definition, sampling mechanism, and retained experimental metadata.
- Attribution: meanings of undocumented sentinel values; click fields when inapplicable; journey completeness after sampling; timestamp units beyond the explicitly documented seconds field; and interpretation of `cpo` on non-converting rows. The viewer shows such rows with populated `cpo`, so the short field description needs further investigation.
- Both: duplicates, detailed distributions, and identifier consistency remain to be investigated. Setup has now checked missing/nonfinite values and agreement with published row/column counts.

These are questions, not asserted defects. This reference selects no model, segmentation method, budget scenario, or application design.
