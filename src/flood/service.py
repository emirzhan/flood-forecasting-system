from datetime import timedelta

import pandas as pd

from flood.db import Prediction
from flood.features import FEATURES, build_features
from flood.repository import PredictionRepository
from flood.schemas import PredictionRequest


class ForecastService:
    def __init__(self, artifact: dict, repository: PredictionRepository):
        self.artifact = artifact
        self.repository = repository

    def predict(self, request: PredictionRequest) -> Prediction:
        frame = pd.DataFrame([row.model_dump() for row in request.observations])
        latest = build_features(frame).iloc[[-1]][FEATURES]
        risk = int(self.artifact["model"].predict(latest)[0])
        metadata = self.artifact["metadata"]
        return self.repository.add(
            Prediction(
                station_id=request.station_id,
                forecast_date=request.observations[-1].date + timedelta(days=1),
                risk=risk,
                label={0: "Low", 1: "Medium", 2: "High"}[risk],
                model_version=metadata["model_version"],
                synthetic_model=metadata["synthetic_model"],
            )
        )
