![Python](https://img.shields.io/badge/Python-3.14-blue)
![SQLite](https://img.shields.io/badge/SQLite-Database-blue)
![License](https://img.shields.io/badge/license-MIT-orange.svg?style=flat)
![GitHub last commit](https://img.shields.io/github/last-commit/Heenok93/watchtower)

# OpenAlex Search

Lightweight Streamlit application for searching scientific literature
through the OpenAlex API.

## Features

- Semantic literature search
- OQL structured search
- English/French filtering
- Publication year filtering
- Open Access filtering
- Abstract availability filtering
- Retracted article exclusion
- Optional OQL reranking
- DOI, OpenAlex and PDF links
- CSV export

## Install

```bash
uv sync
```

You need a OpenAlex mail address/API key in your environment (.env file at the root)

```text
OPENALEX_EMAIL=your.email@example.org
```

## How to run the app

```bash
uv run streamlit run app.py
```
## Search modes
Semantic -> Describe the literature you are looking for:
```text
infectious diseases modelling with machine learning methods
```

## Smart / OQL
Use OpenAlex Query Language:
```text
get works since 2022 about (cholera AND forecasting)
```

## To stop the app (in your IDE)
```text
CTRL + C
```
