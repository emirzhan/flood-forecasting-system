import os
from datetime import date, timedelta

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from flood.core.config import Settings
from flood.features import FEATURES, build_features
from flood.main import create_app
from flood.schemas import PredictionRequest
from flood.train import synthetic_observations, train_demo


def test_dates_reject_timestamp_coercion():
    for value in ["20240101", "1704067200", 1704067200]:
        body = payload()
        body["observations"][0]["date"] = value
        with pytest.raises(ValueError, match="YYYY-MM-DD"):
            PredictionRequest.model_validate(body)


@pytest.fixture(scope="module")
def artifact_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("model")
    train_demo(path)
    return path


def payload():
    return {
        "station_id": "DEMO-001",
        "observations": [
            {
                "date": str(date(2024, 1, 1) + timedelta(days=i)),
                "water_level": 2 + i * 0.1,
                "discharge": 85,
                "precipitation": 4,
                "temperature": 10,
            }
            for i in range(4)
        ],
    }


def test_features_do_not_read_future():
    original = synthetic_observations(30)
    changed = original.copy()
    changed.loc[15:, "water_level"] = 900
    pd.testing.assert_frame_equal(
        build_features(original).loc[:14, FEATURES], build_features(changed).loc[:14, FEATURES]
    )
    assert build_features(original).iloc[3]["lagged_water_level"] == original.iloc[2]["water_level"]


def test_prediction_persistence_validation_and_pagination(tmp_path, artifact_dir):
    database_url = os.getenv("FLOOD_TEST_DATABASE_URL", f"sqlite:///{tmp_path / 'db.sqlite'}")
    if database_url.startswith("postgresql") and not database_url.endswith("/portfolio_flood_test"):
        raise ValueError("Use a disposable database named portfolio_flood_test")
    app = create_app(Settings(database_url=database_url, model_path=artifact_dir / "model.joblib"))
    with TestClient(app) as client:
        result = client.post("/predictions", json=payload())
        assert result.status_code == 201
        assert result.json()["forecast_date"] == "2024-01-05"
        assert result.json()["synthetic_model"] is True
        assert result.json()["risk"] in [0, 1, 2]
        assert len(client.get("/predictions?station_id=DEMO-001").json()) == 1
        assert client.get("/predictions?station_id=unknown").json() == []
        assert client.get("/predictions?offset=1").json() == []
        assert client.get("/predictions?limit=101").status_code == 422
        body = payload()
        body["observations"][1]["date"] = "2024-01-01"
        assert client.post("/predictions", json=body).status_code == 422
        body = payload()
        body["observations"][0]["precipitation"] = -1
        assert client.post("/predictions", json=body).status_code == 422


def test_missing_model_returns_actionable_503(tmp_path):
    app = create_app(
        Settings(
            database_url=f"sqlite:///{tmp_path / 'db.sqlite'}",
            model_path=tmp_path / "missing.joblib",
        )
    )
    with TestClient(app) as client:
        assert client.get("/health").json()["model_ready"] is False
        assert client.post("/predictions", json=payload()).status_code == 503
        assert client.get("/openapi.json").status_code == 200
