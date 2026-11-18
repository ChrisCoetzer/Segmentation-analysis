# Retail customer construction and discovery audit

Built November 17, 2026. This supersedes the original response-stage customer labels.

The live site now uses the additional decision metadata and visuals in [visual-comparisons-v3.md](visual-comparisons-v3.md). That note supersedes the response shapes, stress results and transition count below; the base source allocation and CRM construction remain applicable.

## What the customer groups mean

The fictional client is a general online retailer promoting a featured collection. We constructed a retailer CRM layer so the audience can be introduced as customers with shopping purposes, interests and purchase histories. A response rate or browsing time does not define a segment.

| Group | Primary shopping mission | Typical products | Median prior-year orders | Median typical basket |
| --- | --- | --- | ---: | ---: |
| Household regulars | Restock the household | Kitchen basics, cleaning, pantry supplies | 9 | $42 |
| Bargain hunters | Find a deal | Fashion offers, home deals, discounted electronics | 2 | $55 |
| Occasion shoppers | Buy for a gift or occasion | Gifts, celebrations, seasonal purchases | 1 | $72 |
| Specialist enthusiasts | Buy specialist equipment | Hobbies, technology, outdoor gear | 3 | $185 |
| Convenience shoppers | Save time on everyday shopping | Personal care, essentials, easy reorders | 8 | $39 |

These CRM attributes are synthetic. The primary shopping mission is the deterministic membership rule. Generated fields include product category, prior-year orders, basket value, promotion affinity, delivery preference, preferred channel, customer relationship and tenure. Different fields describe the same coherent customer: for example, household regulars have at least four historical orders; bargain hunters have strong declared promotion preference; specialists concentrate on specialist categories.

The groups are primary missions within this campaign scenario, not immutable psychological classifications. Real people can shop for different reasons on different occasions.

## The discovery effort

The audit includes:

- All 13,979,592 uplift rows, assigned to synthetic missions through feature-only source-cell membership and a seeded allocation.
- Existing training, estimation and evaluation partitions, preserved throughout.
- Fourteen candidate allocation models: seven association strengths, each with two amounts of shared population overlap.
- A neutral allocation baseline, which produces essentially identical response rates across missions.
- A new temporal bridge based on 4,941,310 attribution histories with equal fourteen-day follow-up.
- 987,306 uid-held-out histories, containing 33,205 first recorded conversion-positive histories within fourteen days.
- Initial-context category checks, timing and frequency checks, and a reversed-subtype sensitivity case.
- Twenty-four policy probes, thirty-six initial mixed-focus policy runs, and forty-two final stress runs across three fixed seeds.

All candidate tables and the less successful initial policy choices are retained. The final model is not selected by claiming the focused campaign always wins.

## Why a simple relabel was rejected

The original five labels were ordered activity/readiness buckets. Assigning them retail names would leave each persona equivalent to a response bin. Instead, each new retail mission receives a mixture of anonymous source profiles. Every mission shares source profiles with the others; the mixture changes how prevalent those profiles are.

The source representation has fifteen cells: five feature-based activity bands crossed with three feature-presence subtypes. Source cells use f8/f9/f4/f11 and f3/f6 presence rules. They are internal anonymous strata, not recovered retail meanings.

We define a conditional probability table for synthetic shopping mission given source cell. The declared fictional population composition is 30% household regulars, 24% bargain hunters, 18% occasion shoppers, 12% specialists and 16% convenience shoppers. These proportions are scenario design inputs. They are not a claim about Criteo's actual customer mix.

Iterative proportional fitting balances the table to those priors on training records. Association strength changes the degree of connection to source cells; an additional shared component ensures overlap. Hash-based draws assign missions without reading an individual's treatment, conversion, visit or response delay.

The selected model is `s1_shared0.3`: strength 1.0 and a 30% common-population component. The declared selection rule chooses the lowest tested strength satisfying at least fivefold response contrast, a shared fraction of at least 30%, maximum cell-to-mission probability below 0.65 and at least three substantial source cells per mission. Its maximum conditional allocation probability is approximately 0.53. Stronger candidates are retained for inspection but are not used.

This is a documented synthetic association assumption, not evidence that the original anonymous features measured shopping missions.

## Full-data response audit

The chosen allocation was applied deterministically to all uplift records. Within the evaluation partition:

| Synthetic retail group | Assigned share | Control conversions / 10,000 | Treatment-minus-control / 10,000 |
| --- | ---: | ---: | ---: |
| Household regulars | 30.06% | 9.91 | 5.00 |
| Bargain hunters | 23.96% | 18.74 | 15.17 |
| Occasion shoppers | 18.00% | 8.30 | 2.98 |
| Specialist enthusiasts | 12.00% | 20.72 | 9.06 |
| Convenience shoppers | 15.98% | 48.23 | 29.14 |

The counts and outcomes are real source observations under constructed mission assignments. The retail identities and the association between retail missions and source profiles are synthetic.

Estimation/evaluation results are directionally similar for the broad contrasts, but fine rankings are not settled. For example, specialist increment is about 4.08 per 10,000 on estimation and 9.06 on evaluation; occasion shoppers are about 5.99 versus 2.98. Repeated exploration and privacy sampling mean these are not a new confirmatory experiment or client-population effects.

## Temporal connection between datasets

There is no shared identity key. The bridge works at source-cell and distribution level:

1. Fit a compact propensity model on 1,000,000 discovery attribution histories using first-impression categorical context only.
2. Rank records by predicted fourteen-day conversion propensity, with stable hashes breaking exact ties.
3. Form five propensity bands matching the uplift activity-band proportions.
4. Within each band, use a discovery-partition cat5 timing lookup to rank contexts. Split that ordering into subtypes matching the uplift subtype proportions in the corresponding band.
5. Apply the same synthetic mission allocation table to these cells.

The category-level lookup is learned on discovery uids, then applied to held-out uids. A customer's own future conversion time or contact count is not an input to their held-out mission assignment. The same uid remains on one side of the split across campaigns.

The subtype correspondence is an explicit synthetic transport assumption. It creates a plausible fictional joint population and cannot establish that two real source populations contain the same customer types.

Among held-out responding histories:

| Assigned retail mission | Responding histories | Median response delay | Day-one response share | One recorded pre-response contact |
| --- | ---: | ---: | ---: | ---: |
| Household regulars | 7,554 | 2.27 days | 39.2% | 48.8% |
| Bargain hunters | 7,888 | 1.09 days | 48.7% | 55.7% |
| Occasion shoppers | 3,880 | 2.12 days | 40.3% | 50.2% |
| Specialist enthusiasts | 5,709 | 3.19 days | 32.8% | 41.9% |
| Convenience shoppers | 8,174 | 0.95 days | 50.8% | 57.0% |

The largest discovery-versus-check difference in day-one share is about 0.70 percentage points. That supports consistency within this constructed bridge; it does not validate the fictional customer interpretation.

The reversal sensitivity materially changes the persona-specific timing ordering. For example, specialists' day-one share changes from 32.8% to 56.9% when subtype correspondence is reversed. This confirms that the retail-to-tempo connection is an assumption that must remain explicit, not a recovered demographic fact.

## Why the campaign comparison is now useful

The focused default targets convenience shoppers, with a cap of four and a 50% preferred repeat allocation. The wide-reach default includes all missions, caps at three and prefers 20% repeats. Both share the same starting 100,000 people, arrivals, turnover and available contact budget.

In the final stress check, across three fixed seeds:

| Available contacts per campaign | Focused modeled responses, mean | Wide-reach modeled responses, mean |
| --- | ---: | ---: |
| 30,000 | 25.7 | 11.3 |
| 75,000 | 44.0 | 32.0 |
| 150,000 | 48.7 | 65.3 |
| 250,000 | 49.7 | 83.7 |

This supplies a meaningful scenario tradeoff. With limited capacity, concentrating on the stronger-response mission can outperform broad reach. At larger budgets the focused pool saturates, leaving unused capacity; broader targeting can produce more total response. The model is not programmed to switch winners at a threshold: these are generated outcomes from audience availability, contact caps, source-cell response probabilities and seeded thresholds.

The default seed's 75,000-contact focused case produces 47 modeled additional responses and reaches 24,409 customers. All stress rows, seed ranges and competing policy probes are saved. At zero arrivals the strategies are nearly tied on average, making replenishment worth investigating rather than guaranteeing one conclusion.

## Live model and within-group variation

The simulator does not give everyone in a retail group the same response probability. Each synthetic customer retains their anonymous source `response_cell`. Control and incremental rates are calibrated at that cell, using estimation data with shrinkage toward the parent activity band. Small negative incremental estimates are clipped at zero for the positive-response probability model; raw estimates remain available.

Mission-specific held-out timing and frequency curves supply the time/contact terms. Synthetic customer order history and promotion affinity weight turnover, normalized around the user-chosen overall rate. These are disclosed scenario mechanisms.

Initial readiness follows the source response cell, not the retail mission ID. Retail identity and campaign lifecycle state remain separate.

Prior orders refer to the retailer's broader assortment. The advertised response refers to its promoted collection and is scaled from a privacy-subsampled benchmark. It would be inconsistent to treat the low benchmark response rate as a literal model of all historical purchases; the app does not make that claim.

New arrivals are newly reachable by the campaign, not necessarily new retail accounts. A household regular can therefore arrive in the ad audience with an existing purchase history.

## Actual linked synthetic warehouse

The reference build contains:

| Table | Rows | Relationship |
| --- | ---: | --- |
| customers.parquet | 160,000 | Unique synthetic customer_id; source-template lineage; retail CRM attributes |
| purchase_history.parquet | 810,927 | Unique order_id; customer_id foreign key; date, category and order value |
| contacts.parquet | 75,000 | Customer/day contact and cumulative contact number |
| transitions.parquet | 169,143 | Net customer state changes by day |
| customer_states.parquet | 3,877,251 | Entered-customer daily state and cumulative contacts |

Dates in the purchase history precede the fictional campaign start of November 17, 2026. They are generated, not recovered transaction dates. Order counts reconcile exactly to each customer's `orders_last_year`; order rows have valid customer keys. Channel and delivery preferences are constructed attributes, not observed channel effectiveness estimates.

## Files and reproduction

Core definitions: `src/retail_metadata.py`. Live model: `src/customer_lab.py`.

```powershell
.\.venv\Scripts\python.exe scripts/discover_retail_audiences.py
.\.venv\Scripts\python.exe scripts/build_retail_audience_data.py
.\.venv\Scripts\python.exe scripts/prepare_customer_lab.py
.\.venv\Scripts\python.exe scripts/audit_retail_campaigns.py
.\.venv\Scripts\python.exe scripts/render_retail_audience_review.py
```

The preparation reads the previous full-data exploration outputs. The runtime only reads the prepared bundle in `app/data/customer_lab/` and does not refit models or call external services.

The discovery audit in `outputs/retail_audiences/` retains allocation candidates and matrices, source-cell counts, actual group outcomes across all partitions, category timing lookup, held-out assignments, timing/contact curves, bridge sensitivity, profile bank, catalogue, policy probes and stress results. Figures show customer fingerprints, temporal patterns and budget tradeoffs. `previous_calibration/` preserves the replaced response-stage calibration.

The site remains one continuous scrolling story. Long sections scroll normally; the boundary controller hands off smoothly to the next section. All campaign settings remain on the main page. The sidebar remains an unconnected AI-chat placeholder.
