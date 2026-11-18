# Campaign Runway: duration, repetition and response

Prepared November 16, 2026. New exploration for a visual analytics product; the current Streamlit app has not been modified.

## The offering

**A campaign-planning simulator that helps a marketing manager decide how long to keep reaching new people and how often to keep contacting the same person.**

The proposed stakeholder is a marketing manager at a fictional online retailer. Their question is:

> How long should our campaign run, and how much repetition should each audience receive before we shift effort elsewhere?

The product ends with a proposed duration-and-frequency policy for a pilot. It combines an observed-history explorer with an explicitly synthetic planning model. It does not claim the source data contains randomized experiments on campaign duration or frequency caps.

## What changed about the concept

There are two clocks, and their difference makes the project interesting:

1. **Campaign age:** the campaign continues to encounter new people over time.
2. **Customer age:** time since a particular person's first recorded contact with that campaign.

A third time is **response delay:** conversion can occur after the final advertisement. Stopping ads and stopping measurement are different decisions.

The story is therefore not "most people respond quickly, so end the whole campaign quickly." It is "keep finding new people while controlling repeated contact with people already reached."

## Findings from the actual attribution data

### Reconstruction

All 16,468,027 impression rows were grouped by `(campaign, uid)`, producing 7,813,401 histories. For each history we calculated first and last observed impression, first recorded click, earliest valid recorded conversion timestamp, contact count before that first conversion, last pre-conversion contact time, initial context categories and daily pre-conversion contact counts.

We retained 4,941,310 histories whose first impression was at least fourteen days before the end of the impression log. These have the same available fourteen-day impression-follow-up window. Of these, 166,050 had an earliest recorded conversion within fourteen days.

The metric is **first recorded conversion-positive user-campaign history**, not distinct sales across all campaigns. The same person or conversion can be associated with more than one campaign.

### The response curve has a strong early rise and a meaningful tail

Among the fourteen-day responders:

| Days since first recorded contact | Response recorded by then | Last pre-conversion ad already recorded by then |
| --- | ---: | ---: |
| 1 | 43.10% | 63.48% |
| 3 | 56.95% | 73.50% |
| 5 | 67.41% | 81.15% |
| 7 | 76.60% | 87.62% |
| 10 | 87.57% | 94.43% |
| 14 | 100.00% | 100.00% |

This gives two useful curves instead of conflating when to advertise with when a conversion is observed.

**51.43% of these responding histories contain just one recorded impression before the first conversion.** The median pre-conversion count is one, the 75th percentile is three, the 90th percentile is five and the 95th percentile is seven. This motivates examining repetition. It does not establish that the first ad caused those conversions or that later ads were unnecessary.

Even among histories with only one recorded pre-conversion contact, conversion can be delayed: the 75th percentile of response delay is about 1.85 days and the 90th percentile about 6.28 days.

### The campaign can still be reaching new people

For 670 campaigns with a complete 28-day observable window after their first logged impression, the number of user-campaign histories first appearing by each day was:

| Campaign day | Share of the observed 28-day audience reached |
| --- | ---: |
| 1 | 6.64% |
| 7 | 34.68% |
| 14 | 59.45% |
| 21 | 80.16% |
| 28 | 100.00% |

This pooled curve weights histories rather than giving every campaign equal weight. It describes first appearances in the sampled log. The first observed impression is not necessarily the campaign's actual launch, and first logged appearance is not necessarily the customer's first real exposure. For the fictional scenario we can explicitly define that observed boundary as the simulated launch.

This is a strong visual contrast: new audience continues arriving even though many individual response histories have short contact sequences.

### Fourteen days is a modeling horizon, not the end of all response

The longer-follow-up scan also retained 1,189,569 histories with 28 days of observable impression follow-up. Of their 68,332 first recorded responses within 28 days, 54.77% appeared by day seven, 73.75% by day fourteen and 88.58% by day twenty-one.

These are different eligible cohorts, so do not interpret the difference from the fourteen-day curve as an isolated causal duration effect. The comparison demonstrates why a curve normalized to a fixed horizon must label that horizon. The proposed joined simulator uses fourteen days to align with the uplift benchmark's two-week label window; the historical explorer can show longer windows separately.

## How the two datasets are combined

There is no documented shared user key. The prototype creates a **synthetic segment-level bridge based on relative conversion propensity**. It does not pretend to recover shared identities.

### Step 1: Build the uplift audience table

Use the five feature-defined stages from the earlier raw-data exploration. Their audience shares are approximately 52.27%, 27.22%, 17.45%, 1.62% and 1.44%. Each row contains actual treatment/control counts and two-week conversion-rate differences for that feature-defined group.

The observed control conversion rates provide an ordering from low to high underlying conversion propensity. The stage names remain fictional customer language for those anonymous patterns.

### Step 2: Build a timing profile table

Fit a small first-contact propensity model to the attribution histories using seven categorical fields from the first recorded impression: cat1, cat2, cat4, cat5, cat6, cat8 and cat9. The target is whether an earliest recorded conversion appears within fourteen days. No future contact count, response time, conversion ID or observed response class enters the predictors.

The prototype fits on 1,000,000 histories from the discovery partition. A deterministic uid split keeps the same uid on one side across campaigns. It scores 987,306 held-out histories. Held-out AUC is approximately 0.799, sufficient evidence that these features distinguish relative observed conversion propensity in this exploratory setup. The model's role is making a common ranking, not becoming the presentation's main topic.

This is a user-held-out split within observed campaigns and time periods, not validation on unseen advertisers or future periods. Categories are first-observed context, not recovered demographics.

### Step 3: Match distributions, not IDs

Order the held-out attribution histories by predicted propensity. Divide that ordering into the same five population proportions as the uplift stages. Exact score ties are broken by a deterministic hash of uid and campaign. Assign the resulting bands `synthetic_segment_id = 0...4`.

The explicit assumption is:

> Lower- and higher-propensity profiles in the two releases provide plausible counterparts for constructing a fictional population.

Different sources have different sampling and rate levels, so relative rank is used rather than pretending their absolute probabilities are equal. This does not prove the populations are interchangeable. It creates a reproducible synthetic coupling.

### Step 4: Join aggregate tables on the generated segment key

| Table | Grain | Main fields |
| --- | --- | --- |
| `audience_segments` | One synthetic segment | segment ID, fictional label, audience share |
| `uplift_effects` | Segment and outcome | treatment/control rates, two-week difference, counts |
| `timing_profiles` | Segment and elapsed day | empirical response-time CDF and sample support |
| `contact_profiles` | Segment, elapsed day and cap | observed full-path coverage and contact load |
| `scenario_plans` | Segment, duration and cap | synthetic retained response and contact-load estimate |

These are logical tables represented by the CSV artifacts; no database server was introduced. The join is many timing rows to one uplift-summary row for each synthetic segment. We never directly join millions of unrelated individuals or multiply treatment/control rows by impression rows.

### Step 5: Add understandable metadata

The inherited five stages supply the initial labels. Timing descriptions are computed from the matched histories, such as day-one response share, days to 80% of fourteen-day responses, and pre-conversion contact distribution. Human or AI-generated prose can describe these profiles as quick-deciding, research-oriented or low-engagement, while retaining the synthetic origin.

For example, the matched high-intent profile has 56.3% of its fourteen-day responses by day one and 85.1% by day seven. The matched researcher profile has 39.0% by day one and 73.2% by day seven. These are actual held-out timing shapes assigned through the synthetic bridge; they are not directly observed timing results for Criteo's uplift users.

## The planning model

The prototype separates two calculations.

### Response observation curve

`two_week_uplift_difference × matched_share_of_responses_observed_by_day`

This estimates how a fixed two-week response amplitude could accumulate over observation time in a synthetic population. It answers when to expect to *see* response. It is not a stopping-policy model.

### Conservative contact-path replay

For each responding attribution history, examine all recorded contacts up to its earliest recorded conversion. A hypothetical plan retains that history only if:

- its last pre-conversion contact fits within the plan's customer follow-up window; and
- its total pre-conversion contact count fits within the cap.

Multiply the share of retained histories by the corresponding uplift group's two-week difference. Contact load is computed for all held-out histories by truncating their recorded pre-event contact sequence at the duration and cap. For nonresponders, the contact sequence is followed only within the available fourteen-day horizon.

This model assumes the full observed pre-conversion path is required to preserve the response. That is a deliberate conservative replay assumption. Extra recorded contacts might in reality be unnecessary, and an omitted contact might change both response and later contact timing. The prototype does not estimate these counterfactuals. It does not reschedule ads to replace removed contacts.

If published, the planner should expose the replay assumption and a sensitivity comparison against a weaker requirement. Observed converter timing is not proven to equal incremental-converter timing; transferring it to the uplift difference is another explicit scenario assumption.

## Does changing a setting change a decision?

Yes, in the prototype's synthetic scenario the controls generate a real tradeoff. These are uniform per-history policies for the matched population, relative to fourteen days without a binding cap:

| Follow-up window | Contact cap | Modeled response retained | Recorded contact load retained |
| --- | ---: | ---: | ---: |
| One contact only | 1 | 54.3% | 50.6% |
| 7 days | 5 | 85.6% | 79.3% |
| 10 days | 5 | 90.0% | 84.8% |
| 14 days | 8 | 97.5% | 95.9% |
| 14 days | No binding cap | 100.0% | 100.0% |

These are **scenario outputs**, not measured causal savings. A clear user task is "Find a policy preserving at least 90% of the modeled response with fewer contacts." In this scenario, ten days and a cap of five is one candidate with about 15% less recorded contact load. The website can compare it with alternatives instead of declaring a universal optimum.

Duration and frequency interact. A longer window with fewer contacts can compete with a shorter window allowing more repeats. Fast conversion alone does not determine the cheapest modeled policy. A user can inspect that frontier by audience.

The prototype also combines these windows with the 28-day audience-arrival curve. It distributes a fictional reachable population across observed arrival days, then gives each arrival only the contact window remaining before campaign end. It assumes the same arrival distribution across synthetic audiences and places arrivals at the start of each day. Response is counted within each entrant's two-week outcome horizon and can occur after campaign end. This is saved in `campaign_calendar_plans.csv`.

For a fictional population of 100,000 potential user-campaign histories, a fourteen-day uncapped campaign uses about 99,546 recorded-contact equivalents and models about 55.8 additional conversions. A twenty-eight-day single-contact campaign uses 100,000 contact equivalents and models about 57.2 additional conversions. The estimates are close; the useful point is that similar contact budgets can be distributed between new audience acquisition and repeated contact. They are scenario comparisons, not evidence that the second policy is truly superior.

When the permitted contact budget changes, the preferred duration/cap pair can change. For example, within this finite prototype grid, a 60,000-contact limit selects fourteen days with one contact per history; a 120,000-contact limit selects twenty-four days with a cap of two. These are illustrative outputs conditional on the matching and replay assumptions, not validated operational recommendations.

## Proposed website

### Opening view: where does the audience go over time?

Title: **How long should we keep advertising?**

Show two linked but clearly labeled views:

- **New audience reached over campaign age:** the observed first-appearance curve.
- **Response after first customer contact:** response-time and last-ad-time curves.

This introduces the discovery: campaign duration and repeated customer contact serve different purposes.

### Audience exploration

Show three prominent synthetic profile cards, expandable to five: discovery audience, researchers and purchase-ready audience. Selecting one updates response curves, contact distributions and the underlying sample support.

Useful questions include "Who responds quickly?", "Who has a long response tail?" and "How much repeated contact appears before response?" The profile description should reflect the computed shape, not dictate it.

### Policy comparison

Provide a per-customer follow-up slider and a contact-cap slider. Show the selected point on the response-versus-contact-load frontier, alongside two or three comparison plans. A target such as 80%, 90% or 95% of modeled response makes the task concrete.

Keep actual dollars optional and based on an entered CPM. The source monetary fields are transformed and cannot be treated as the advertiser's real spend.

### Final recommendation

Output a proposed pilot plan by audience: follow-up window, cap, modeled response retained, contact-load change and the replay assumption. Include the observed overall audience-arrival curve so a short individual follow-up window is not confused with ending the entire campaign.

The final pitch is:

> We help marketers decide how long to keep a campaign reaching new people, and how long to keep following up with each audience. Our visual explorer reveals response timing and repetition patterns, and our calibrated simulator compares policies before a pilot.

## What to emphasize in the presentation

1. A campaign can still be finding new people after many existing customers have responded.
2. Some response arrives after the last advertisement, so response delay is not the same as advertising duration.
3. Repetition and duration can be traded against each other.
4. Different synthetic profiles inherit different empirical timing patterns.
5. The final action is choosing a duration/cap policy for a pilot, with assumptions visible.

Avoid claiming "the first ad is best" from the contact counts. A defensible chart title is "How many recorded contacts precede response?" An explicitly hypothetical simulator can then explore the consequences of caps.

## Sensitivity and scope

`bridge_sensitivity.csv` compares aligned and reversed propensity mappings. The mapping affects audience-specific shapes and some reversed groups have only 32 or 54 responding histories. Such sparse profiles must be flagged rather than interpreted as strong findings. A production-quality class demo should also include a pooled-timing alternative, compare subgroup entry weeks/campaign mix, and expose the stopping-response assumption.

The model is useful as a visual planning simulation because the mechanisms, source counts and synthetic assumptions are inspectable. It should not claim to validate an optimal policy for a real advertiser.

## Deliverables and reproduction

`outputs/campaign_timing/` contains:

- `timing_foundation.png`: observed response/contact curves.
- `planning_scenario.png`: scenario heatmap and response/contact-load comparison.
- `matched_profile_shapes.png`: example timing differences between synthetic audiences.
- `histories.parquet`: reconstructed user-campaign histories, first-contact context and daily contact counts.
- `campaign_audience_reach.csv`, `duration_curves.csv`, `longer_followup.csv`: observed temporal summaries.
- `response_vs_contact_duration.csv`, `event_contact_curve.csv`, `duration_contact_surface.csv`: contact versus response evidence.
- `propensity_tier_profiles.csv`, `propensity_tier_curves.csv`: propensity-tier checks.
- `matched_segment_shapes.csv`, `synthetic_duration_scenario.csv`: response timing bridge.
- `synthetic_duration_frequency_plans.csv`, `uniform_plan_comparison.csv`, `shortlisted_plans.csv`: per-customer replay scenarios.
- `campaign_calendar_plans.csv`: 308 calendar-duration/cap scenarios integrating audience arrival and remaining contact windows.
- `bridge_example_20000.csv`: sample of concrete generated segment assignments.
- `timing_diagnostics.json`, `bridge_diagnostics.json`, `review_validation.json`, `bridge_sensitivity.csv`: provenance, reconciliation and sensitivity.

Run:

```powershell
.\.venv\Scripts\python.exe scripts/explore_campaign_timing.py
.\.venv\Scripts\python.exe scripts/explore_timing_bridge.py
.\.venv\Scripts\python.exe scripts/render_campaign_timing_review.py
```

The bridge also reads `outputs/metadata_exploration/readiness_summary.csv` from the earlier exploration. All existing raw data, app code and current app result tables remain unchanged.

## Source context

- [Criteo attribution documentation](https://ailab.criteo.com/criteo-attribution-modeling-bidding-dataset/): timestamps, uid/campaign grain, conversion labels and transformed prices.
- [Criteo benchmark paper](https://arxiv.org/html/2111.10106v1): two-week uplift label period, anonymous feature types and experimental structure.
- [Criteo uplift description](https://ailab.criteo.com/criteo-uplift-prediction-dataset/): anonymization and privacy subsampling.

Timestamp differences were treated as seconds, consistent with the documented seconds field and approximately 30.9-day observed span. The exact original campaign launch and complete exposure histories are unavailable. All numerical findings above were computed from the local processed releases.
