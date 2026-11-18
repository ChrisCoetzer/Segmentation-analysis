# Presentation question sheet

## Purpose

**What are we investigating?** Whether finer customer segmentation identifies audiences with enough additional advertising response to justify further effort.

**How does this represent market research?** Segmentation represents one part of understanding differences within a customer base. More clusters mean more analytical detail. They do not directly measure research effort, personalization or financial cost.

## Model

**What model do we use?** Unsupervised, balanced hierarchical clustering: a modified bisecting k-means approach that repeatedly divides each group into two roughly equal groups. We compare 1, 2, 4, 8, 16 and 32 groups.

**Why balanced groups?** To compare progressively finer audience subdivisions while preventing the analysis from mainly isolating tiny groups. This is a deliberate constraint and can compromise the most natural similarity grouping.

**Which inputs construct the groups?** Only the 12 anonymous features f0–f11. Treatment assignment, visits and conversions do not construct the clusters.

**How are feature types handled?** Continuous features f0, f2, f7 and f10 are standardized using training data. The other eight are treated as nominal categories using one-hot encoding. A larger category code does not imply a larger quantity. In the chosen distance, each categorical mismatch contributes one, and each squared standardized continuous difference contributes half its value.

**Are these customer personas?** No. They are groups of similar anonymous records. We cannot identify them as age groups, income levels or named marketing audiences.

**Why are the clusters the same for visits and conversions?** Outcomes do not define membership. We measure and rank the same clusters separately for each outcome, so the selected cluster can differ.

## Data and evaluation

**How much data?** All 13,979,592 uplift users enter the analysis, divided into disjoint partitions:

| Partition | Users | Role |
| --- | ---: | --- |
| Training, 60% | 8,387,755 | Fit preprocessing and cluster boundaries |
| Estimation, 20% | 2,795,918 | Rank clusters by advertising response |
| Evaluation, 20% | 2,795,919 | Measure displayed performance |

**Is clustering fitted to only a small sample?** Each split uses up to 20,000 training users to estimate its direction efficiently. All training members of that parent determine the final median boundary. The saved run records about 40 seconds for the pipeline on this machine; timing depends on hardware and settings.

**Why separate estimation and evaluation?** Choosing a cluster and reporting its performance on the same outcomes would favor chance winners. Separate partitions reduce that selection bias. We have inspected this evaluation release during development, so the results remain exploratory rather than a fresh confirmatory test.

## First chart

**What does each point represent?** At each group count, select the cluster with the highest treatment-minus-control response in the estimation partition. Then report its average response on evaluation users.

**What is incremental response?** Treatment outcome rate minus control outcome rate. For display, multiply by 10,000. An estimate of 22.1 means a rate difference equivalent to 22.1 additional outcomes per 10,000 cluster members, not 22.1 total observed conversions.

**What does gain mean?** The cluster's incremental response minus the broad-audience incremental response. The plotted gain and the summary's raw cluster average are different quantities.

| Groups | Selected-cluster conversion lift per 10,000 | Selected share |
| --- | ---: | ---: |
| 1 | 11.6 | 100% |
| 2 | 22.1 | 49.95% |
| 4 | 41.3 | 25.01% |
| 8 | 68.7 | 12.52% |
| 16 | 116.0 | 6.26% |
| 32 | 107.2 | 3.13% |

**Why do averages rise so much?** Finer clusters can concentrate responsive customers into a smaller audience. A higher per-member average does not establish more total campaign conversions.

**Why does 32 dip?** Feature similarity does not guarantee greater advertising response. Rankings come from estimation data, while performance comes from different evaluation users. Smaller clusters also have less precise estimates. Overlapping intervals do not prove equality, and the point estimates alone do not establish a reliable decline.

**What do the vertical bars mean?** Approximate 95% confidence intervals around each estimate. They condition on the fitted clusters and rankings; they do not include uncertainty from retraining or the source's privacy sampling.

## Simulator

**How is it different?** Every option advertises to the same number of customers, combining estimation-ranked clusters until it fills the chosen population percentage. It takes a random fraction of the last cluster in expectation when necessary.

**How does it compare treatment and control?** It uses the same finest 32-cluster strata and common population weights in both arms. That standardization means its broad reference can differ from the first chart's raw broad average.

**Where do dollars come from?** Client-entered baseline lift and contribution, scaled by the benchmark relative improvement:

Additional conversions = selected customers × baseline lift per 10,000 ÷ 10,000 × relative gain.

Break-even spending = additional conversions × contribution per conversion.

**What is the presentation example?** Population 100,000; advertised share 10%; selected audience 10,000; baseline lift 10 per 10,000; contribution $100. Break-even value is about $5,854 at 8 groups, $6,921 at 16 and $6,984 at 32. The last doubling adds approximately $63. The 8-versus-32 comparison adds approximately $1,130.

**Does this prove an optimal group count?** No. Returns depend on reach, fitted clusters and client assumptions. There is no measured segmentation-cost curve or independent financial validation. Selecting everyone produces no targeting advantage.

## Repeated exposure

**What data supports it?** A separate attribution release with 16,468,027 impressions, aggregated into 7,813,401 user–campaign pairs across 675 campaign IDs.

**What is its conversion rate?** Pairs with at least one positive conversion label divided by all pairs in the selected bin. The pooled view has 336,748 positive pairs, approximately 4.31%. These are not distinct conversion-event counts. One person can appear in multiple campaign pairs.

**Does more exposure cause conversion?** This chart cannot establish that. Customer intent, campaign differences, sampling and timing can explain the association. We do not infer a frequency cap or join these users to the uplift dataset.

## AI and practical limits

**Is the AI working?** The sidebar currently uses scripted responses. The planned bot wrapper supplies definitions, selected filters and Python result rows. Python will verify numerical claims, with a fallback for unsupported answers.

**What can we recommend now?** Use the app to explore segmentation resolution and scenarios, then validate a proposed strategy in a client pilot. We cannot supply real customer personas, actual implementation costs, guaranteed client ROI or proof of transfer to another customer base. The uplift release's non-uniform privacy sampling further limits interpretation of benchmark effects as original-population causal effects.

**What is built with machine learning, and what is calculated?** The feature-based clustering is the machine-learning component. Response comparisons and simulator values are statistical calculations. The AI assistant is a separate planned language-model feature.

Source of implementation details: src/mixed_clustering.py, src/segmentation.py, src/investment.py, app/data/run.json and app/data/frequency_run.json. Values match the presentation's saved model run.
