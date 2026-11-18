# Audience metadata directions: evidence and website concepts

Prepared November 16, 2026. This is a design exploration, not a change to the existing application.

## Recommendation

Build an **Audience Strategy Studio** for a fictional online retailer. Use five synthetic audience stages to introduce the customer base, and seven campaign roles for deeper comparisons. End with a user-created campaign brief. The stakeholder question is:

> We can support three audience-specific campaigns this month. Which audiences should we prioritize, for which objective, and with which proposed message?

The dataset contains enough real differences to make the exploration interesting without inventing response numbers. The fabricated layer supplies understandable customer language, motivations and proposed content. The website can say: **Real advertising benchmark; synthetic audience profiles.**

## What was explored

- Scanned all 13,979,592 processed uplift records, using all twelve anonymous features and the treatment, exposure, visit and conversion fields.
- Counted all 256 combinations of whether eight categorical features equal their most frequent training-sample value. Category codes were treated as nominal, never as numerical ranks.
- Summarized four continuous features using a separate mode bin and quartiles among non-mode values. Bin boundaries and exact mode tokens came from a reproducible 200,000-record training sample.
- Preserved the existing training/estimation/evaluation partitions. The principal tables below use all 2,795,919 evaluation records; comparisons across the other partitions are saved.
- Examined a 600,000-record feature sample, 200,000 from each partition. Inspected the saved mixed-clustering profiles, but built the proposed groups directly from raw feature rules so results do not depend on interpreting saved cluster IDs as personas.
- Independently aggregated all 16,468,027 attribution impressions into 7,813,401 user-campaign histories, covering 6,142,256 distinct recorded users and 675 campaigns.

No real outcome was replaced, and no application code or current result table was changed. Proposed groups were developed after looking at the data; the partition comparisons are exploratory checks, not a new blind validation.

## Option 1: Shopping readiness — clearest presentation

**Client:** retail campaign manager.

**Question:** How should we balance broad discovery audiences against a small audience closer to purchase?

The labels below are fictional shopping-stage interpretations assigned to actual feature-defined groups. They do not identify actual browsing histories, carts or customer lifecycle transitions.

| Synthetic stage | Audience share | Observed visit rate | Observed conversion rate | Share of observed conversions |
| --- | ---: | ---: | ---: | ---: |
| Unengaged prospects | 52.27% | 0.144% | 0.009% | 1.57% |
| Light browsers | 27.22% | 1.811% | 0.081% | 7.64% |
| Active researchers | 17.45% | 16.174% | 0.332% | 20.04% |
| Decision-stage shoppers | 1.62% | 40.699% | 3.565% | 19.97% |
| High-intent shoppers | 1.44% | 44.768% | 10.161% | 50.77% |

**Strong opening:** about 3.06% of the evaluation audience accounts for 70.74% of observed conversions. Meanwhile, the largest two groups make up almost 80% of the audience. The manager must consider both audience scale and conversion concentration.

### Metadata that fits

- `synthetic_audience_stage`: the five stages above, assigned deterministically.
- `proposed_campaign_objective`: introduce, engage, inform, reassure, remind.
- `fictional_motivation`: a short narrative such as learning about the brand, exploring options, comparing benefits or seeking reassurance.
- `proposed_message_theme`: an introduction, product overview, comparison, trust/reassurance or purchase reminder.
- Optional fictional purchase horizon, such as exploring / considering / near-term. This would be an explicitly invented scenario attribute, not a recovered timestamp.

AI can generate consistent descriptions and example creative briefs from a small approved catalogue. The numerical charts continue to use computed outcomes. Message recommendations are proposals; the experiment did not compare those messages.

### Website story and visuals

1. **Who is in the audience?** Sorted audience-size bars linked to a profile description.
2. **Where do outcomes concentrate?** An audience-share versus conversion-share comparison. Selecting a group highlights both measures.
3. **What does advertising add?** Treatment/control dumbbells with an optional difference-and-interval view. Keep this separate from the raw conversion-rate chart.
4. **Which campaign do we build?** Choose up to three stages and export a short brief with objectives and proposed messages.

Use a stage matrix or small multiples rather than a funnel that implies observed movement between these groups. They are a cross-sectional segmentation.

**Tradeoff:** extremely easy to explain, but the ordering is so strong that the app may become a simple ranking. It becomes richer when combined with the engagement-style lens described below.

## Option 2: Campaign roles — strongest visual analytics concept

**Client:** marketing manager deciding which audiences need paid advertising support.

**Question:** Which audiences already engage, and where is advertising associated with additional response in the experimental comparison?

This scheme splits the middle stages using two additional feature-presence indicators and merges the two highest stages before that split. All memberships use features only, not a user's observed conversion or treatment assignment.

| Synthetic campaign role | Audience share | Control visit rate | Treatment visit rate | Conversion difference per 10,000 |
| --- | ---: | ---: | ---: | ---: |
| Quiet prospects | 52.27% | 0.096% | 0.153% | +0.3 |
| Independent light browsers | 16.18% | 0.861% | 0.934% | -0.2 |
| Engageable light browsers | 11.04% | 2.234% | 3.265% | +8.4 |
| Self-directed researchers | 9.29% | 10.084% | 10.057% | +5.6 |
| Engageable researchers | 8.17% | 17.907% | 23.969% | +24.9 |
| Self-directed buyers | 0.89% | 36.050% | 36.381% | +58.4 |
| Responsive buyers | 2.17% | 39.367% | 46.098% | +260.8 |

The role names are narrative interpretations. For example, "self-directed" is not a measured psychological trait. Negative or small estimates do not establish harm or no effect.

### Why this is more interesting

- **Self-directed researchers** have roughly a 10% visit rate in both arms. A high observed visit rate alone does not identify additional visits from treatment.
- **Engageable researchers** show an approximately 6.06 percentage-point visit difference, equivalent to 606 additional visits per 10,000 group members in this release's comparison.
- **Responsive buyers** are much smaller, but show a much larger conversion difference per member.
- **Quiet prospects** have enormous scale and very low near-term activity. A user can explore the tension between reach and response, rather than simply choose the largest rate.

There is a useful second explanation to surface: the role groups also differ sharply in actual ad delivery. Only about 1.23% of treatment-assigned self-directed researchers were effectively exposed, compared with 16.44% of engageable researchers. Do not frame every difference as intrinsic persuasion or customer preference. A "delivery" lens would help explain the comparison.

### Website story and interactions

1. **Start with the decision:** choose visits or conversions as the campaign objective.
2. **Compare audiences:** a scatterplot with control outcome rate on one axis and treatment-minus-control difference on the other; bubble area represents audience share. A linked table makes small or overlapping points selectable.
3. **Inspect the contrast:** click a group to reveal treatment/control dumbbells, counts, effective exposure, a synthetic profile and proposed message.
4. **Assemble a campaign:** add up to three mutually exclusive audiences to a selection tray. Show selected reach and proposed creative variants. Avoid presenting invented costs as measured spending.
5. **Produce a brief:** summarize the chosen audiences, objective, evidence, proposed messages and questions for a pilot.

The best interaction is a change in objective or audience selection that forces the user to compare scale, baseline behavior and additional response. The website should remain useful even if no ranking changes between visits and conversions.

### Metadata that fits

- `synthetic_campaign_role`: the seven labels above.
- `synthetic_engagement_style`: self-directed, low-engagement or ad-receptive; these can be a simpler three-way feature-based lens.
- `fictional_customer_need`: comparison help, reassurance, discovery or convenience.
- `proposed_message_theme`: a proposed creative approach, not a measured winning message.
- `campaign_priority`: computed from the selected objective and audience constraints, rather than fixed by the fictional persona.

**Tradeoff:** a stronger decision-support product, but seven groups are too many for the opening screen. Introduce the five readiness stages first, then enable this deeper comparison.

## Option 3: Engagement journeys — strongest timeline visuals

**Client:** media planner reviewing contact patterns.

**Question:** Which recorded engagement histories deserve different follow-up experiments?

Use the attribution dataset as a separate workspace. These users cannot be joined to the uplift audience by a documented shared key.

| Recorded history | User-campaign pairs | Conversion-positive pair rate |
| --- | ---: | ---: |
| One impression, no recorded click | 3,567,362 | 0.00% |
| 2–3 impressions, no recorded click | 875,690 | 0.00% |
| 4–10 impressions, no recorded click | 159,144 | 0.00% |
| 11+ impressions, no recorded click | 5,518 | 0.00% |
| One impression, recorded click | 1,332,716 | 5.96% |
| 2–3 impressions, at least one click | 1,051,035 | 9.61% |
| 4–10 impressions, at least one click | 686,494 | 16.66% |
| 11+ impressions, at least one click | 135,442 | 31.01% |

The denominator is user-campaign pairs; a person can appear in several campaigns. A positive pair has at least one positive conversion label. These are not distinct conversion-event counts.

### Synthetic names and metadata

Possible archetypes include first-contact audience, repeated non-clickers, early engagers, repeat engagers and heavily contacted engagers. Derived metadata can describe recorded contact depth, whether a click appears, active span and campaign. Fictional fields can add proposed next action or a creative brief.

### Website story and visuals

- An exposure-depth by click-status heatmap.
- A campaign selector that updates pair counts, contact distribution and observed outcomes.
- Selected real user-campaign timelines, with impressions and clicks; these require additional timeline extraction beyond the aggregated artifacts produced here.
- An investigation shortlist: audiences to consider for a creative test, cadence test or follow-up review.

### Why I rank this third

The visuals can be compelling, but every conversion-positive pair here has a recorded click. That is a structural feature of this release, not evidence that non-clickers can never convert. The groups also use the complete observed history and can include activity after conversion. They should support retrospective exploration, not a claim that eleven impressions cause more conversions or that a particular cap is optimal.

If the original uplift dataset remains a required primary source, this is a supporting page rather than the whole project.

## Optional lens: three engagement styles

Across the evaluation release, two feature-presence indicators yield three nonempty groups:

| Synthetic style | Audience share | Control visit rate | Treatment visit rate | Effectively exposed among treatment |
| --- | ---: | ---: | ---: | ---: |
| Self-directed | 26.50% | 5.291% | 5.311% | 0.70% |
| Low-engagement | 55.38% | 1.646% | 1.885% | 0.88% |
| Ad-receptive | 18.12% | 8.788% | 13.100% | 15.94% |

This is a useful heatmap column or profile attribute alongside readiness. It should not be presented as established psychology: effective delivery differs, as does the outcome comparison. The labels are deliberately fictional business language for anonymous feature patterns.

## Group construction details

Let `active(f)` mean the feature value differs from its most frequent exact value in the fixed training sample. This is a repeated-value distinction, not evidence that the user performed an activity.

Readiness uses the first matching rule:

1. f8 not active → unengaged prospects.
2. f8 active, f9 not active → light browsers.
3. f8/f9 active, f4 not active → active researchers.
4. f8/f9/f4 active, f11 not active → decision-stage shoppers.
5. Remaining records → high-intent shoppers.

Within the light-browser and researcher stages, `f3 not active AND f6 not active` defines the self-directed branch. The same split is applied after combining the two highest stages. Quiet prospects remain one group. The three-style lens uses self-directed first, then f3 not active as low-engagement, then ad-receptive.

Exact tokens are in `outputs/metadata_exploration/rules.json`. The categorical tokens themselves have no interpretable units. We are assigning a scenario ontology to these patterns, not decoding what Criteo originally measured.

## Stability and limits that matter for the design

- Five-stage audience proportions differ by less than 0.06 percentage points between estimation and evaluation partitions. The large structural story is consistent.
- The largest stage has about 0.14% observed visits and the highest stage about 45%, making a linear "more detail" curve unnecessary for the opening story.
- The highest stage's conversion difference is about 173 per 10,000 on estimation and 301 on evaluation. Do not sell an exact fine-grained ranking or precise ROI as settled. The top two stage estimates have substantial uncertainty.
- The self-directed researcher visit difference is approximately +47 per 10,000 on estimation and -3 on evaluation. It is safer to describe it as smaller and less stable than the engageable researcher difference, not a proven zero.
- These are treatment-assignment comparisons in a privacy-subsampled benchmark. They do not recover the original advertiser's population effect or predict a fictional retailer's real financial return.
- If fictional product interests, channels or motivations are added later, label them synthetic and give them consistent generation rules. They can enrich a demo; they cannot establish which channel or message actually works.

## Practical build scope

For a strong class project, build three main views:

1. **Audience overview:** five-stage composition, outcome concentration and selected profile.
2. **Campaign comparison:** seven roles, linked selection, objective switch and treatment/control detail.
3. **Campaign brief:** up to three selected audiences, reach, proposed content and source-linked evidence.

Use a fictional retailer identity and restrained audience imagery if desired. Keep the main presentation on the stakeholder decision. Put anonymous feature rules, partition details and benchmark limitations behind an evidence drawer.

The opening pitch can be:

> Our retailer can create only three audience-specific campaigns this month. We built a visual workspace to understand who is in the audience, compare where advertising adds response, and assemble an evidence-backed campaign brief.

The strongest demo compares self-directed researchers with engageable researchers, then asks the manager to select audiences for either a traffic or conversion campaign. The final deliverable is a campaign plan the user can explain.

## Review artifacts and reproduction

All new analysis artifacts are in `outputs/metadata_exploration/`:

- `option_1_readiness.png`, `option_2_missions.png`, `option_3_journeys.png`: charts for comparing directions.
- `readiness_summary.csv`, `mission_summary.csv`, `style_summary.csv`: exact counts, rates, treatment/control differences, standard errors and shares across all partitions.
- `feature_patterns.csv`, `continuous_bins.csv`: full-release descriptive scans.
- `readiness_style_cells.csv`: counts for the two-dimensional audience lens.
- `journey_archetypes.csv`, `journey_campaigns.parquet`, `journey_summary.json`: independent attribution exploration.
- `metadata_example_20000.csv`: concrete metadata example attached to real sampled feature rows. `source_row_index` is a zero-based position in the local processed parquet, not a real user identifier. The file explicitly labels synthetic metadata and includes real outcomes for inspection.
- `feature_sample.parquet`: reproducible 600,000-row profile sample.
- `rules.json`, `metadata_catalogue.json`, `validation.json`: assignment tokens, approved scenario vocabulary and reconciliation checks.

Reproduce from the project root using the project Python environment:

```powershell
.\.venv\Scripts\python.exe scripts/explore_metadata_options.py
.\.venv\Scripts\python.exe scripts/explore_attribution_metadata.py
.\.venv\Scripts\python.exe scripts/build_metadata_review.py
```

## Primary source context

- [Criteo uplift publisher description](https://ailab.criteo.com/criteo-uplift-prediction-dataset/): anonymization and nonuniform privacy subsampling.
- [Criteo benchmark paper](https://arxiv.org/html/2111.10106v1): feature types, experiment structure and benchmark interpretation.
- [Criteo attribution publisher description](https://ailab.criteo.com/criteo-attribution-modeling-bidding-dataset/): impression grain, forward conversion labels and transformed monetary fields.
- [Attribution paper](https://arxiv.org/html/1707.06409): sampling and distinction between public offline logs and online experiments.

The numerical findings in this review were computed from the local processed releases, rather than copied from those sources.
