from sqlalchemy import select
from sqlalchemy.orm import Session

from flood.db import Prediction


class PredictionRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, prediction: Prediction) -> Prediction:
        self.session.add(prediction)
        self.session.commit()
        return prediction

    def list(self, station_id: str | None, limit: int, offset: int) -> list[Prediction]:
        query = select(Prediction).order_by(Prediction.id.desc()).limit(limit).offset(offset)
        if station_id:
            query = query.where(Prediction.station_id == station_id)
        return list(self.session.scalars(query))
