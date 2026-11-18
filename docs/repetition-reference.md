# Current audience and repetition story

November 17, 2026. This supersedes the earlier page layout and 14-day scenario horizon. The original source allocation, mission definitions, opening client question and mandate remain unchanged.

## Page 2

Four tabs follow a deliberate sequence: an all-groups overview, shopping differences (mean annual purchases and typical basket value), conversion rates with/without advertising, and response timing. The overview ranks all groups from largest to smallest, encodes their shares as horizontal bars, marks the largest group, and places each mission and selection rule on the same row. It has no single-group selector or quote card; all groups can be understood at once. Conversion rates use percentages only. Timing retains the countable responder panels with a 30-day slider.

The declared clock is `scenario_day = 30 * (source_day / 14) ** mission_exponent`. Raw source histories are retained; this is not an observed 30-day follow-up study. The curve contains all 30 daily values and reaches 100% on day 30. The campaign simulation accepts up to 30 days and defaults to 30. Its 28-day source arrival shape continues for days 29–30 at the mean daily weight from the final source week, normalized to the declared arrivals total.

The rebuilt reference warehouse contains 164,286 customers, 832,724 historical orders, 75,000 contacts, 182,779 transitions and 4,217,743 daily states. There are 100,000 initial customers and 64,286 reachable arrivals.

## Page 3: what continued exposure adds

The earlier chart only divided eventual responders into exposure buckets. It omitted advertising delivered to nonresponders, so it could not describe the effort needed for later response.

The replacement is a fixed analytical reference, separate from configurable campaign playback. Every group starts with 100,000 customers. Its advertising-associated response potential equals its benchmark incremental conversion rate multiplied by population. The exposure curve allocates that potential across successive contacts, including the existing synthetic familiarity assumptions recorded in `allocation_spec.json`.

For N = 100,000 customers, L = group benchmark incremental conversion probability, and F(k) = cumulative modeled exposure coverage, with F(0) = 0:

- Cumulative responders after contact k: `N * L * F(k)`.
- Additional responders at contact k: `N * L * (F(k) - F(k-1))`.
- Contacts delivered at contact k: `N - cumulative_responders(k-1)`.

Every not-yet-responded customer receives the next exposure, including eventual nonresponders. Responders leave the ad pool. Stages are 1st, 2nd, 3rd–4th, 5th–8th and 9th–12th exposures. The reference excludes organic purchase simulation, arrivals, turnover, budget limits and scheduling. The full 30-day potential is held fixed to isolate exposure count. Exposures are not days.

Page 3 starts with a prominent reference strip: a 30-day response window, 100,000 starting customers in each group, and exposure counts rather than calendar days. Its first tab shows additional responders as dot clusters (one full dot represents two expected responders; partial dots preserve fractional area) and total contacts beneath each stage. Counts are fractional expectations, not sampled customer events. A highlight selector affects chart emphasis only, with an all-groups option. The separate first-versus-repeat comparison chart has been removed. The final tab presents the general conclusions.

There is no changing description or metric block beneath the charts. A final “What we learned” tab gives general conclusions across all five groups: front-loaded convenience/bargain response, later specialist response, the occasion-shopping reminder effect, and comparatively small household advertising uplift. These conclusions are computed from the prepared reference and remain independent of the highlight selection. They lead into Phase 2.

This is a synthetic reference expectation calibrated from source patterns, not an observed marginal causal effect or a promise about real retail customers. The benchmark rate supplies magnitude and constructed familiarity supplies the exposure distribution. The calculation does not estimate joint elapsed-time and exposure effects.

| Group | Potential captured by first two exposures | Responders per 100,000 ads: first exposure | Responders per 100,000 ads: 3rd–4th |
| --- | ---: | ---: | ---: |
| Household regulars | 65% | 18.4 | 5.5 |
| Bargain hunters | 75% | 78.2 | 12.0 |
| Occasion shoppers | 61% | 7.4 | 3.6 |
| Specialist enthusiasts | 11% | 6.7 | 25.1 |
| Convenience shoppers | 77% | 161.2 | 21.5 |

Specialists' 3rd–4th exposures add 50.2 responders across approximately 199,946 contacts: 25.1 per 100,000 ads, around 3.7 times their first-exposure yield. Convenience shoppers' first exposure adds 161.2 responders, but exposures 5–8 together add only 19.6 across approximately 398,898 contacts. Occasion shoppers have a stronger second exposure than first. Household regulars have a small overall benchmark increment despite frequent purchasing. These are findings about existing CRM groups, not new membership definitions.

## Phase 2 and reproducibility

Current organic setting (`selected-population-first-ad-v3-organic20`): `organic_rate_scale=0.20`, an 80% reduction from the original organic baseline, applied equally to both campaigns. This supersedes the 75% setting below.

Organic baseline tuning (`selected-population-first-ad-v2-organic75`): the live simulation now defaults to `organic_rate_scale=0.75`. It multiplies the benchmark-derived organic probabilities by 75% in both campaigns. Advertising response potential, group criteria and timing shapes are unchanged. The factor is included in exported scenario settings; 1.0 restores the previous baseline and 0.0 disables organic response for validation. In the saved 100,000-specialist, 75,000-contact comparison, each campaign's sampled organic total falls from 292 to 214. Actual advertising response counts can change because fewer organic buyers leave the eligible ad pool; the advertising-effect calibration itself is not multiplied by this factor.

Live simulation update (`selected-population-first-ad-v1`): the shared starting audience is drawn from all customer groups selected in either campaign. Their population shares are renormalized within that selection, and largest-remainder allocation preserves the mix to within one customer in each of the starting and arrival cohorts. Campaign eligibility is separate from membership of this shared pool. Both campaigns therefore receive the same identities, CRM profiles, arrivals and baseline organic-response thresholds.

Selecting specialists in both campaigns now means the full requested starting population consists of specialists. Selecting specialists and convenience shoppers gives approximately 42.893% specialists and 57.107% convenience shoppers. Arrivals use that same conditional mix. When the campaigns select different groups, the common pool includes both selections; each campaign only advertises to its own eligible groups.

Advertising response time starts on the first recorded ad, with contact day counted as response day 1. Repeat ads and returning from inactivity do not reset it. Untouched customers cannot produce advertising-associated responses; previously contacted customers can respond later without a new ad that day. Organic response time starts when the customer becomes available (day 1 for the initial audience, arrival day for newcomers) and does not depend on advertising. Organic responses remain in the animation and totals. Exported customer results include `first_contact_day`, `ad_response_day` and `organic_response_day`, using -1 when the event has not happened.

The run cache includes a simulation-version key, and old session results are cleared when the model version changes. The existing cell-level response-rate calibration is retained in this update; the previously identified rate-calibration difference from the group-level benchmark reference is a separate issue. Earlier exported warehouse snapshots and stress results describe the earlier model version and can be refreshed with the preparation scripts.

Page 3 has a fixed shared reference and no campaign-setting controls. Phase 2 lets the client choose eligible groups, budget, duration, caps, repeat preference, arrivals and turnover, and compare strategies with animated playback. The reference identifies contrasts worth testing; Phase 2 tests campaign tradeoffs.

`src/exposure_reference.py` owns the calculation; `scripts/prepare_exposure_reference.py` publishes detailed and staged Parquet/CSV outputs. Normal customer-data preparation rebuilds the same files. `app/repetition_visuals.py` renders the two views. The runtime bundle contains `exposure_reference_method.json`.

Validation checks include nonresponder contacts, cessation after response, stage/detail reconciliation, response bounds and normalization by every delivered contact. Additional simulation tests cover a pure 100,000-specialist population, conditional group proportions for starting customers and arrivals, identical shared profiles under different campaign eligibility, delayed first-ad anchoring, delayed response without new ads, non-resetting repeat contacts, and organic response independent of advertising. Streamlit checks cover moved tabs, removed conversion-unit toggle, group selection, 30-day timing/playback, shared identities/profiles/budget, selected specialist-only audiences and zero-budget behavior.

```powershell
.\.venv\Scripts\python.exe scripts/construct_retail_response_scenarios.py
.\.venv\Scripts\python.exe scripts/prepare_customer_lab.py
# Or rebuild only the analytical exposure reference:
.\.venv\Scripts\python.exe scripts/prepare_exposure_reference.py
.\.venv\Scripts\python.exe -m unittest tests.test_customer_lab tests.test_exposure_reference -q
.\.venv\Scripts\python.exe scripts/check_customer_app.py
```
