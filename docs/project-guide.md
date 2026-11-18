# Campaign Runway

A continuous scrolling Streamlit story about balancing repeated advertising with new audience reach. Retail customer groups are defined by synthetic shopping missions and CRM attributes, with advertising behavior calibrated separately. Campaign settings are on the main page; the sidebar contains the Gemini analyst and guided demonstration.

The presentation uses a dark charcoal palette with teal and warm copper accents. Page 1 combines the original client question with a repeat-versus-reach illustration, client/problem cards and the two-stage story. Native controls use `.streamlit/config.toml`; page styles and the opening SVG live in `app/theme.py`. Chart labels and customer SVGs share the dark palette and consistent customer-group colours.

## Run

Python 3.13 and the pinned packages in `requirements-app.txt`:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/streamlit_app.py
```

The runtime reads the portable calibration bundle in `app/data/customer_lab/` without downloading raw data or training a model. Charts, simulations and the guided demonstration work without an API key. Conversational answers require the server-side Gemini key described below.

## The live-demo story

1. **The question:** who the site is for, the business pain, the base mandate and the Phase 2 opportunity.
2. **Meet the audience:** customer mix, shopping habits, group criteria, conversion rates with/without advertising, and 30-day response timing. No customer table.
3. **Continued exposure:** compare additional response and total ad contacts at successive exposure stages for fixed customer populations. Select customer rows and review the findings with their supporting evidence.
4. **Campaign simulation:** configure focused and wide-reach campaigns, then watch their customer traces and cumulative response curves advance together.
5. **Our answer:** compare modeled response, reach and contact usage, then propose a client pilot.

Campaigns have independently selectable customer groups, contact caps and repeat preference. They share the same population, duration, contact budget, arrivals and turnover. All settings are on the main page. Playback includes pause/resume, next day, replay, final-day jump and speed. Settings collapse after submitting a run. Technical explanations live in the About popover and source/assumption expander.

The starting population contains the groups selected in either campaign, preserving their relative shares within that selection. Two specialists-only campaigns therefore share the full requested population of specialists. Mixed audiences and arrivals preserve the selected group proportions. Advertising response timing starts at each customer's first ad; organic buying follows time since entering the audience and remains included in the comparison.

All sections are rendered together. Ordinary scrolling remains available within long sections, with a smooth boundary handoff into the next. The optional sidebar tour uses Back/Next to scroll to sections and select the relevant views.

Customers who respond leave the advertising pool. At most one ad is delivered per person per day. Unused daily capacity expires and is shown explicitly. Animated traces intentionally emphasize responders; numeric results use the full customer population.

## The larger linked synthetic sample

`data/synthetic/customer_lab/` contains the reproducible default sample:

| Table | Default rows | Key |
| --- | ---: | --- |
| customers.parquet | 164,286 | customer_id |
| purchase_history.parquet | 832,724 | order_id; customer_id foreign key |
| contacts.parquet | 75,000 | customer_id + day |
| transitions.parquet | 182,779 | customer_id + day |
| customer_states.parquet | 4,217,743 | customer_id + day |

There are 100,000 starting customers and 64,286 arrivals over 30 days. Customer rows carry source-template lineage, anonymous features, shopping mission, prior orders, basket, product interests, promotion preference, channel/delivery preferences, cohort and outcomes. Historical orders reconcile to each customer's prior-order count. Counts and parameters are in `manifest.json`; local warehouse tables remain excluded from Git.

## Evidence and assumptions

The discovery compared fourteen mission-allocation models, audited all 13,979,592 uplift rows, checked 987,306 held-out timing histories and ran policy probes plus three-seed stress scenarios. Retail metadata and the declared customer mix are constructed assumptions, not recovered Criteo feature meanings. Every shopping mission contains mixed source response cells. The timing bridge is synthetic and does not identify shared users. Recommendations are scenario comparisons, not validated real advertiser policy effects.

See `docs/repetition-reference.md` for the current layout, 30-day scenario, exposure calculation and denominator audit. `docs/visual-comparisons-v3.md` and `docs/retail-customer-construction.md` retain the earlier design and base discovery audit.

## Rebuild and check

With the earlier exploration outputs available locally, rebuild the retail allocation and runtime bundle:

```powershell
.\.venv\Scripts\python.exe scripts/discover_retail_audiences.py
.\.venv\Scripts\python.exe scripts/build_retail_audience_data.py
.\.venv\Scripts\python.exe scripts/construct_retail_response_scenarios.py
.\.venv\Scripts\python.exe scripts/prepare_customer_lab.py
.\.venv\Scripts\python.exe -m unittest tests.test_customer_lab tests.test_exposure_reference -v
.\.venv\Scripts\python.exe scripts/check_customer_app.py
```

The last command uses Streamlit's AppTest and needs local event-loop sockets. It checks all chapters render together, the AI-only sidebar, eligibility, shared budget, playback, linked results, empty-group validation and the zero-budget case.

## Gemini sidebar chat

### Streamlit Community Cloud

Deploy `ChrisCoetzer/Segmentation-analysis`, branch `main`, entrypoint `app/streamlit_app.py`, with Python 3.13. `app/requirements.txt` selects the pinned runtime packages in `requirements-app.txt`; the root requirements are for development and data preparation. The prepared runtime data is included in the repository.

Add `GEMINI_API_KEY` and `GEMINI_MODEL` to the app's private Streamlit secrets using TOML syntax. Keep `.env` out of Git. The model for this project is `gemini-3.8-flash`. Chat is enabled when a server-side key is configured; the rest of the demonstration also works without it.

Put your Agent Platform / Vertex express-mode API key in the root `.env` file:

```dotenv
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-3.8-flash
```

The local `.env` is ignored by Git; `.env.example` is the shareable template. Install the app requirements after updating. For deployment, set `GEMINI_API_KEY` and optionally `GEMINI_MODEL` in the host's environment or Streamlit secrets; do not commit the key file. Environment variables take priority, then Streamlit secrets, then `.env`. Restart the app after changing deployment settings.

Visitors share the server's Gemini credentials and quota, but conversation history is separate for each Streamlit session. Requests use the [Agent Platform express-mode REST endpoint](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start?usertype=apikey): `https://aiplatform.googleapis.com/v1/publishers/google/models/{model}:generateContent`. This selects the backend corresponding to `genai.Client(vertexai=True, api_key=...)` in the class notes. The app uses REST directly, so SDK/ADK environment flags do not affect it. A key for the Gemini Developer API is a different backend and will not be routed there automatically.

The analyst's version-controlled knowledge base is `app/knowledge/site_guide.md`. Each message includes that guide, actual aggregate audience/timing/exposure figures, the current control selections and saved campaign totals when present. Only allowlisted aggregate state is sent; raw customer records, credentials and unrelated session state are excluded. The small guide is included directly rather than searched through embeddings, so all chart definitions and caveats remain available. The latest 20 conversation messages provide dialogue context.

Gemini function calls can open a section/tab, highlight a group, select a response checkpoint, fill draft campaign controls or start the guided demo. Every argument is checked against actual controls and valid ranges. A complete tool request validates before it stages any state changes; staged changes commit only after the model finishes its reply. Unknown tools, arbitrary selectors/code and invalid settings are rejected. The client preserves Gemini's thought signatures and returns validated tool outcomes to the model. Navigation uses fixed section selectors, smooth scrolling and a brief outline. Changes are recorded beneath the assistant reply. Campaign edits never run or replace saved results: press Run comparison to apply. There are no download, file-access, deployment or simulation-run tools.

Say **give me a demo** or use the starter button for the 35-step guided walkthrough. It introduces all five CRM shopping missions and moves between page 2 tabs to compare membership, shopping habits, conversion and timing. It explains the exposure-stage chart, then justifies all four conclusion cards by revisiting their evidence. It uses existing group highlights and subtle card emphasis, without outlining whole sections. The worked example loads 100,000 starting customers, 250,000 contacts and 30 days: specialists only with cap 8 and 90% repeat preference versus all groups with cap 1 and 0% repeats. Both share the same population and available budget. This contrasts repeated follow-up in a small eligible group with fresh reach across the full audience. The fixed sample gives 12 versus 52 ad-driven responses; the guide reads actual run totals rather than hardcoding them. An explicit Run example button uses the normal simulation; matching saved results are required before Next advances to day-7 and day-30 checkpoints. Current-step narration, previous/next titles, actual selected group, checkpoints and example status are included in Gemini context so questions about the demo do not restart it. Back/Next/End remain available. Run python scripts/check_guided_demo.py to check the full route, questions in context and example handoff.

Entire customer rows in Meet the audience and What each stage adds are clickable and keyboard accessible. Names are plain labels; the row itself is the selection target. Selected rows are highlighted; selecting again or Show all groups clears the emphasis. Both views share `repetition_profile`, independently of campaign eligibility. The former exposure highlight dropdown is removed.

The sidebar fills the viewport: its header stays above a flexible scrolling message history, with the composer anchored at the bottom. Extra capability text and the unsent-message preview are removed. Request failures and Retry message remain inside the history area.

Run client and wrapper checks with `python -m unittest tests.test_gemini_chat tests.test_site_analyst -v` and UI checks with `python scripts/check_analyst_app.py`. The UI test mocks Gemini; live replies require a configured key. Grounding reduces unsupported answers but is not a guarantee that every generated statement is correct.

The previous segmentation application is preserved at `app/legacy_app.py` and can be run directly with Streamlit.
