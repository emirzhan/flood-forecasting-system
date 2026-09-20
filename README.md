# Flood Forecasting System Based on Meteorological Data and Hydrological Models

## Overview

An educational prototype supporting Emirzhan Smagulov's Software Engineering diploma topic at Astana IT University. The goal is to investigate how meteorological and hydrological observations can support flood-risk forecasts.

The runnable MVP predicts a **next-day risk class for one station** from daily observations. It uses a reproducible synthetic dataset and illustrative thresholds, not a calibrated hydrological model or an operational warning system. No claim of real-world predictive accuracy is made.

## Features

**Implemented**

- Daily observation validation, ordered dates and rejection of missing daily intervals.
- Water level, discharge, precipitation and temperature inputs.
- Lagged water level, previous-three-day mean level, previous-three-day maximum discharge and day-of-year features.
- Random Forest classification: **0 — Low, 1 — Medium, 2 — High**.
- Chronological holdout evaluation with Accuracy, Precision, Recall and F1-score.
- FastAPI prediction and history endpoints, bounded pagination and station filtering.
- SQLAlchemy persistence with SQLite by default and an optional PostgreSQL connection.
- A saved confusion-matrix plot and reproducible training metadata.

**Planned / Future Improvements**

Real observation adapters, basin-specific hydrological modelling, PostGIS spatial features, MongoDB raw-document storage, dashboards and alert delivery.

## Architecture

Implemented flow:

```mermaid
flowchart LR
    A[Daily observations] --> B[Validation]
    B --> C[Causal feature builder]
    C --> D[Random Forest]
    D --> E[Prediction repository]
    E --> F[(SQLite or PostgreSQL)]
    E --> G[REST response]
    H[Synthetic training CLI] --> I[Local model artifact]
    I --> D
```

Target research architecture — components below are **planned**, except the feature/ML/API prototype:

```mermaid
flowchart TD
    A[Meteorological data] --> B[Meteo processor]
    B --> C[Hydrological engine]
    C --> D[Feature preparation and ML]
    D --> E[(PostgreSQL / PostGIS)]
    B -. Raw source documents .-> M[(MongoDB)]
    E --> F[REST API]
    F --> G[Web interface / alerts]
```

See [model card](docs/model-card.md) for feature timing, units and evaluation limits.

## Tech Stack

Python 3.12+ · FastAPI · Uvicorn · Pydantic · SQLAlchemy 2 · Pandas · NumPy · scikit-learn · Matplotlib · SQLite / PostgreSQL.

PostGIS and MongoDB are design candidates, not runtime dependencies.

## Project Structure

```text
src/flood/
  api.py             HTTP routes and session dependency
  core/config.py     Environment settings
  schemas.py         Request and response contracts
  features.py        Shared training/inference features
  train.py           Synthetic data, training and evaluation
  service.py         Forecast use case
  repository.py      Persistence queries
  db.py              ORM model and connection setup
  main.py            Application lifecycle
tests/               Feature and API tests
examples/            Valid prediction request
docs/                Model card
requirements*.txt    Pinned direct dependencies
```

## Installation

Run commands from this repository's root. Use Python 3.12 or newer; Python 3.13 was used for local verification.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
```

On Linux/macOS, activate with `source .venv/bin/activate`. If PowerShell activation is disabled, use `.\.venv\Scripts\python.exe` in place of `python`.

## Configuration

Copy `.env.example` to `.env`. Defaults are sufficient for the local SQLite demo.

| Variable | Default | Purpose |
| --- | --- | --- |
| `FLOOD_DATABASE_URL` | `sqlite:///./flood.db` | Persistence connection |
| `FLOOD_MODEL_PATH` | `artifacts/model.joblib` | Operator-controlled local model path |

For PostgreSQL, supply a private `postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE` URL. Create an empty database first. Never commit the URL or point this prototype at an existing production database.

Tables are created for a fresh database on startup; versioned schema migrations are planned.

## Running the Application

```powershell
python -m flood.train --synthetic
python -m uvicorn flood.main:app --host 127.0.0.1 --port 8001
```

Training creates `artifacts/model.joblib`, `metrics.json`, `synthetic-observations.csv` and `confusion-matrix.png`. Retrain and restart the API to load a new artifact. Without a model, `/health` reports `model_ready: false` and prediction returns **503**.

Model files use joblib/pickle: load only artifacts produced locally by trusted code. There is no model-upload endpoint.

## API Documentation

Open [Swagger UI](http://127.0.0.1:8001/docs) or [OpenAPI JSON](http://127.0.0.1:8001/openapi.json) after starting the API.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Database health and model readiness |
| POST | `/predictions` | Validate observations, predict and persist |
| GET | `/predictions` | Filtered, paginated prediction history |

This local demonstration has no authentication and binds to loopback in the documented command.

## Example API Requests

```powershell
curl.exe http://127.0.0.1:8001/health
curl.exe -X POST http://127.0.0.1:8001/predictions -H "Content-Type: application/json" --data-binary "@examples/prediction.json"
curl.exe "http://127.0.0.1:8001/predictions?station_id=DEMO-001&limit=10&offset=0"
```

On Linux/macOS use `curl`. The response includes the forecast date, risk code, label, model version and `synthetic_model: true`. Four consecutive daily observations are the minimum; the forecast date is the day after the final input.

## Testing

```powershell
python -m pytest -q
python -m ruff check src tests
```

Tests cover causal features, prediction persistence, input validation, pagination, OpenAPI and a missing model. For PostgreSQL verification, set `FLOOD_TEST_DATABASE_URL` to a disposable database named `portfolio_flood_test`; that database must be empty before the test run. The prediction persistence test uses it; the missing-model test still uses SQLite.

## Current Status

**Implemented:** a tested local ML/API MVP with synthetic data.

An actual run of the included synthetic training command is preserved in
[synthetic-evaluation.json](docs/synthetic-evaluation.json). This is a reproducibility example,
not evidence of real-world flood forecasting accuracy.

![Confusion matrix for the synthetic holdout only](docs/synthetic-confusion-matrix.png)

**Not implemented:** an independently validated real-data forecast, hydrological simulation, GIS storage, live collection or warning delivery. Metrics generated by the CLI describe only the synthetic holdout. The supplied prototype does not establish completion of the wider diploma research.

## Future Improvements

1. Document data provenance, station identifiers, units and missing-data policies.
2. Introduce real labels and basin-specific flood thresholds with domain review.
3. Compare a persistence baseline and a hydrological baseline using rolling-origin evaluation.
4. Evaluate rare-event recall, calibration, per-station generalisation and uncertainty.
5. Add migrations, authentication, PostGIS queries, a web interface and alert delivery.

## License

[MIT](LICENSE).
