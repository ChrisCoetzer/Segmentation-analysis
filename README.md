# Segmentation Analysis

A Streamlit and Altair app exploring customer segmentation and advertising response using precomputed Criteo results.

## Run locally

Use Python 3.13. Create and activate a virtual environment, then run:

```sh
python -m pip install -r requirements-app.txt
python -m streamlit run app/streamlit_app.py
```

The app reads the small result tables included in `app/data/`. Raw datasets and model training are not required to run it.

## App features

- **Segmentation:** switch between conversions and visits, compare incremental response or gain over broad targeting, and click points to inspect 1–32 groups.
- **Repeated exposure:** filter campaigns and frequency groups, then compare observed conversion rates or audience distribution.
- **Investment scenario:** compare equally sized advertised audiences and illustrative break-even segmentation spending using editable population, audience percentage, baseline lift and contribution.
- **Assistant mockup:** scripted, context-aware example answers demonstrate the planned chatbot. No model API is connected and no API key is required.

## Reading the results

The segmentation chart shows one selected cluster at each level. Its average response is expressed per 10,000 cluster members, and cluster sizes change across levels. Group construction uses anonymous features f0–f11 only; separate estimation data ranks groups by advertising response, and evaluation data supplies the displayed estimates.

The simulator combines ranked clusters to fill the same audience size for every option. Its financial values depend on user assumptions and are not guaranteed profit or measured segmentation costs. The repeated-exposure chart shows observational associations rather than causal advertising lift.

Only application code and aggregate result tables are included here. Raw customer records, local environments, presentation files and submission documents are excluded.

## Structure

```text
app/                 Streamlit interface and precomputed results
src/                 Chart, frequency and scenario calculations
.streamlit/          App theme configuration
requirements-app.txt Runtime dependencies
```
