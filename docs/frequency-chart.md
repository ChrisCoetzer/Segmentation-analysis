# Advertising-frequency chart

The second deck visual is implemented as the **Advertising frequency** view in Streamlit. It uses the complete attribution release independently of the uplift models.

## Data preparation

Run `.\.venv\Scripts\python.exe scripts/prepare_frequency.py`. The script reads `uid`, `campaign`, and `conversion` from all 16,468,027 recorded impressions. For each `(campaign, uid)` pair, it counts impressions and takes the maximum binary conversion label. Thus multiple positive impression labels do not inflate the number of converting pairs.

The release produces 7,813,401 user–campaign pairs across 675 distinct campaign identifiers. Of these pairs, 336,748 have at least one positive conversion label. These are **not counts of distinct conversion events or distinct users**. A user or conversion can be associated with multiple pairs. The raw positive-impression label count is 806,196, which illustrates why summing positive impressions would answer a different question.

Pair frequencies are grouped as 1, 2–3, 4–6, 7–10, and 11+ recorded impressions, matching the proposed deck bins. Each bar's rate is converting pairs divided by all pairs in that bin. With all campaigns pooled, users occurring in several campaigns appear in several pairs. The dashed reference uses all bins in the selected campaign scope, before bin/support filters. Displayed metrics and audience shares use only the displayed bins after filters.

Precomputed counts and source-checksum metadata are stored in `app/data/frequency.parquet` and `app/data/frequency_run.json`. No raw impressions or identifiers are sent to the browser; it receives only aggregate counts and rates.

## Interactions and visual grammar

Campaign filtering supports all 675 opaque campaign IDs or the pooled view. Frequency-bin selection and minimum pair count control which bars appear. The measure toggle shows conversion rate or audience distribution; tooltips and the table supply numerator, denominator, and recorded impression count. CSV export saves the current comparison.

Bars use ordered horizontal positions for frequency categories and height for the selected measure. Bars start at zero. A line was rejected because interval widths differ and 11+ is open-ended. A single teal color avoids implying campaign semantics or extra categories. The dashed reference supplies context without adding an unsupported causal comparison.

## Uncertainty and limits

95% Wilson binomial reference intervals assume independent pairs. They remain in downloaded data but are not drawn on the chart. In the pooled view, a user can occur in several campaigns, so these intervals are not cluster-adjusted inference.

Frequency covers the entire released impression period. Conversion labels look forward 30 days from each impression. This is not a prospective exposure-before-first-conversion analysis: some counted impressions can follow a conversion, and the original sampling can omit parts of a journey. Customer intent, campaign mix, and reverse timing can explain the association. The graph does not estimate the causal effect of extra impressions, identify an optimal frequency cap, or establish which campaign would benefit from segmentation.

The local campaign count is 675; earlier publisher summaries round to approximately 700. No semantic campaign types are inferred from IDs, and no join to the uplift data is performed.
