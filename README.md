# Campaign Runway

## Project Description

A visual analytics app that helps a retail campaign manager compare repeated advertising with wider audience reach. Explore customer groups, response timing and exposure patterns, then compare two campaigns through an animated simulation and a Gemini-assisted guided demo.

## App Deployment URL

[Open Campaign Runway](https://campaign-runway.streamlit.app/)

## Local Setup Instructions

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
git clone https://github.com/ChrisCoetzer/Segmentation-analysis.git
cd Segmentation-analysis
uv sync
uv run streamlit run app/streamlit_app.py
```

For Gemini chat, copy `.env.example` to `.env` and add your `GEMINI_API_KEY`. The charts, simulation and guided demo work without a key.

See the [project guide](docs/project-guide.md) for data sources, assumptions and development details.
