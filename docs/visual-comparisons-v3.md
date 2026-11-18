# Customer comparisons and retail decision layerCurrent layout and 30-day reference: [repetition-reference.md](repetition-reference.md). Conversion/timing now sit in page 2; page 3 compares additional response against all advertising contacts. This note retains the earlier design history.

Current version: `retail-decisions-v3`, November 17, 2026. The [original construction audit](retail-customer-construction.md) describes the unchanged source allocation and CRM warehouse. This note supersedes its timing, contact-shape and campaign-result sections for the live site.

## The customer groups

Membership can be recomputed from row-level CRM fields with `identify_missions` in `src/retail_metadata.py`. It does not use response time, contact count or conversion. Rules run in this order:

1. Promotion preference ≥75% → Bargain hunters.
2. Hobby equipment, technology or outdoor interest plus careful delivery → Specialist enthusiasts.
3. Gift, seasonal or occasion interest plus occasion-date delivery → Occasion shoppers.
4. Everyday essentials, pantry or personal care plus fast delivery and ≥2 annual orders → Convenience shoppers.
5. Household interest plus scheduled delivery and ≥4 annual orders → Household regulars.

The generator first samples a shopping mission using the existing soft source-cell allocation, then constructs compatible CRM attributes. These rules recover that membership exactly. This is a reproducible synthetic segmentation, not an unsupervised discovery of retail identities from Criteo. The site states the rules in the customer cards and a dedicated tab; construction details remain in fine print and expandable notes.

## Why change the response metadata?

The original matched-history differences were modest: first-day shares ranged from 32.8% to 50.8%, and three-contact coverage from 75.8% to 86.1%. They made poor demonstration material. The source does not contain recoverable retail missions, so stronger behavioral differences must be explicit scenario assumptions.

The new layer represents two plausible decision mechanisms:

- **Deliberation:** easy reorder decisions and offer-led purchases move faster; occasion purchases and specialist evaluation take longer.
- **Familiarity:** a fraction of each audience requires additional exposures before a response path is available.

Raw source histories and the previous curves remain unchanged in the research folder. The script writes separate scenario histories and curves, which now feed both the charts and campaign simulation.

## Reproducible transformations

For a source response time `t` between 0 and 14 days, the scenario time is `14 * (t / 14) ** exponent`. This monotone transformation preserves ordering within each mission, both endpoints and the number of 14-day responses. It changes the decision clock, not the total response magnitude. Benchmark increment and baseline rates remain calibrated to the existing uplift source cells.

| Mission | Time exponent | Probability of extra familiarity contacts | Extra contacts when required |
| --- | ---: | ---: | ---: |
| Household | 1.00 | 25% | 1 |
| Bargain | 1.55 | 8% | 1 |
| Occasion | 0.70 | 50% | 1 |
| Specialist | 0.52 | 82% | 2 |
| Convenience | 2.20 | 3% | 1 |

Familiarity assignment uses a stable hash, never a person's future outcome. Scenario pre-response contacts equal source contacts plus this requirement. The CRM profile bank and exported customers retain `decision_pace_exponent` and `familiarity_extra_contacts` as lineage fields. Simulation uses group marginal timing and contact distributions, not these fields as a separate second multiplier.

Strengths 0, .5, .75 and 1 were evaluated. Strength interpolates exponents from 1 and scales familiarity probability. Strength 1 is the first tested version with a ≥40 percentage-point spread in first-day response and ≥25 percentage-point spread in three-contact coverage. This is a presentation scenario design criterion, not model selection for real-world predictive accuracy.

| Group | Response by day 1 | Response by day 3 | Median decision time | One-contact coverage | Three-contact coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Household | 39.2% | 54.0% | 2.27 days | 36.8% | 78.8% |
| Bargain | 58.5% | 71.9% | 0.27 days | 51.5% | 84.7% |
| Occasion | 33.3% | 45.7% | 3.73 days | 24.7% | 76.1% |
| Specialist | 22.7% | 29.6% | 6.49 days | 7.4% | 48.2% |
| Convenience | 69.1% | 79.5% | 0.04 days | 55.3% | 85.7% |

These percentages describe eventual 14-day responders, not conversion rates across all customers. Contact coverage is not evidence that an extra ad causes a conversion. Timing and contact distributions are separable marginals in the current simulation, not a fitted joint causal process.

## New presentation views

Section 2 has three tabs: a countable 100-person population with customer cards; separate horizontal bar charts for mean annual purchases and mean typical basket value; and the explicit CRM grouping criteria. The example customer table is removed.

Section 3 remains audience exploration with three tabs. A paired-dot comparison shows treatment/control buying rates for each group, switchable between conversion percent and buyers per 10,000. Grey dots show without-ad rates, group-colored dots show with-ad rates and the connecting gap shows the benchmark difference. A second tab retains filling 100-responder panels with a day checkpoint. A third splits 100 responder dots per group across 1, 2, 3–4 and 5+ pre-response exposures, with a selectable bucket highlight. Disjoint contact buckets come from differencing cumulative coverage at contacts 1, 2 and 4; the remaining share includes all histories above four contacts. Largest-remainder rounding keeps every displayed row at exactly 100 dots. Underlying labels use unrounded shares.

All groups appear together in consistent order and color. This section describes audience differences; budget choices, contact caps and campaign-policy comparisons remain in Phase 2. The previous opportunity bubble chart, contact-cap coverage bars and next-contact gain bars are no longer used on page 3.

## Decision checks

The same 42-run audit (seven environments, three seeds, two policies) was rerun after replacing the shapes. Both campaigns share customers, environments and budgets. No winning policy is hardcoded.

| Contact budget | Focused mean responses | Wide-reach mean responses |
| --- | ---: | ---: |
| 30,000 | 24.0 | 12.7 |
| 75,000 | 47.0 | 29.0 |
| 150,000 | 50.0 | 51.3 |
| 250,000 | 50.3 | 78.0 |

At 150,000 contacts the result is close; at 250,000 the wider campaign leads across all three seeds. With no new arrivals the average result ties. This retains a decision-sensitive campaign story instead of making one strategy win universally.

The CRM warehouse still contains 160,000 customers, 810,927 historical orders and 75,000 reference contacts. The rebuilt reference has 169,406 state transitions and 3,877,251 state snapshots.

## Rebuild and validate

After the original base discovery scripts, run:

```powershell
.\.venv\Scripts\python.exe scripts/construct_retail_response_scenarios.py
.\.venv\Scripts\python.exe scripts/prepare_customer_lab.py
.\.venv\Scripts\python.exe scripts/audit_retail_campaigns.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_customer_lab.py -q
.\.venv\Scripts\python.exe scripts/check_customer_app.py
```

The scenario candidates, raw and transformed held-out histories, resulting curves and revised campaign results are retained under `outputs/retail_audiences/`. The allocation specification records the transformation parameters. Validation checks CRM membership, mixed source-cell support, monotone bounded curves, endpoint preservation, material scenario contrasts, budget and contact-cap constraints, identity conservation, repeatability and the page interactions.
