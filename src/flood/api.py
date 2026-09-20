from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from flood.repository import PredictionRepository
from flood.schemas import PredictionRequest, PredictionResponse
from flood.service import ForecastService

router = APIRouter()


def session(request: Request):
    with request.app.state.sessions() as db:
        yield db


@router.get("/health")
def health(request: Request, db: Session = Depends(session)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "model_ready": request.app.state.artifact is not None}


@router.post("/predictions", response_model=PredictionResponse, status_code=201)
def predict(body: PredictionRequest, request: Request, db: Session = Depends(session)):
    if request.app.state.artifact is None:
        raise HTTPException(503, "Model unavailable; run python -m flood.train --synthetic")
    return ForecastService(request.app.state.artifact, PredictionRepository(db)).predict(body)


@router.get("/predictions", response_model=list[PredictionResponse])
def history(
    station_id: str | None = Query(None, max_length=80),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(session),
):
    return PredictionRepository(db).list(station_id, limit, offset)
