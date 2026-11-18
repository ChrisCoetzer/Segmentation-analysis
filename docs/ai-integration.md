# AI assistance: defined strategy and current mockup

## Role

Help a client interpret the charts, compare segmentation options, understand uncertainty, and choose useful follow-up analyses. The assistant explains computed evidence; it does not train clusters, choose clusters from evaluation outcomes, execute campaigns, or decide an optimal marketing budget.

The left sidebar is a working UI mockup with three scripted example responses filled from current app values. It makes no model/API calls and is labeled accordingly. Suggested-question buttons, a scrollable user/assistant chat box, and a message composer demonstrate chart summary, the 32-group conversion dip, and 8-vs-32 simulator comparisons. Typed supported questions route to the same scripted templates; unsupported questions receive an explicit mockup limitation. Chart/scenario changes update the displayed explanation.

## Inputs to the planned AI

A free-form client question plus a versioned, compact JSON snapshot assembled by the application:

- Current outcome, selected segmentation level, chart measure, cluster ID/share/count, treatment/control rates, estimate, gain, uncertainty interval, and broad reference.
- The comparison rows for 1/2/4/8/16/32 groups, keeping selected-cluster averages separate from fixed-population targeting policies.
- Frequency chart campaign, selected frequency bins, pair counts, converted-pair counts, rates, reference rate, and counting definitions.
- Scenario population, audience percentage/count, baseline lift, contribution, cluster allocation, relative gains, and break-even amounts for each option.
- Method/source facts: f0–f11 mixed-type clustering, separate training/estimation/evaluation roles, anonymous feature meanings, privacy subsampling, and observational frequency data.

Each record carries a stable source identifier and current filter fingerprint. No raw user-level dataset, inferred demographics, or invented feature names are sent. Financial assumptions are tagged as client inputs rather than dataset observations.

## Output contract

A short plain-language answer, quantitative claims identified by source-row IDs, assumptions/limitations relevant to the question, and optionally one suggested next analysis. The UI should link claims to the relevant chart/row. Questions outside the provided data receive a clear statement of what is unknown. The assistant must not infer age, income, campaign meaning, real advertiser ROI, or causality from the frequency chart.

## Validation against data

Python remains the numerical authority. The model receives computed values and may request only allowlisted read-only comparison/calculation functions. Proposed numeric claims are returned in a structured schema with source IDs, measure, units, value, and filter fingerprint. The server verifies each claim against the current result table or recalculates it, allowing only declared display-rounding tolerance. Unsupported numbers or stale filters are rejected and the answer is regenerated once; persistent failures show a deterministic summary instead. Displayed numbers are inserted from validated claims, not copied unchecked from prose.

Checks also distinguish conversion rate from incremental lift, per-member averages from campaign totals, the single-cluster chart from the combined-cluster simulator, estimation-based choice from evaluation performance, conditional intervals from guaranteed effects, and illustrative money from observed financial returns. Do not declare that 32 is definitively worse than 16 from a small point-estimate difference.

## Evaluation plan

Use fixed regression questions covering point explanation, conversion/visit switching, 16-vs-32 comparisons, uncertainty, campaign filtering, frequency-bin changes, zero/100% audience selection, zero population/baseline, changed contribution, and requests for undisclosed feature meanings. Assert that every numerical claim matches the source within rounding, carries the right units and filters, and does not invent client ROI or frequency causality. Human review checks clarity and whether the answer actually addresses the question.

## Sprint to final

Connect a selected LLM through a server-side API, add free-form question entry, implement the context snapshot and structured-output validator, add source navigation and failure handling, and run the regression evaluation. Choose and document the provider/model at implementation time; no model was used to generate the current mock responses. Keep API keys outside the repository and browser. Deploy the existing precomputed-data app, configure its server-side secret, verify hosted interactions and response latency, and polish responsive sidebar behavior. Final deck, client critique, response document, and submission zip remain separate deliverables.
