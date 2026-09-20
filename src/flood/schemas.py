import re
from datetime import date
from itertools import pairwise
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NonNegative = Annotated[float, Field(ge=0, le=1_000_000, allow_inf_nan=False)]


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: date
    water_level: NonNegative
    discharge: NonNegative
    precipitation: Annotated[float, Field(ge=0, le=3000, allow_inf_nan=False)]
    temperature: Annotated[float, Field(ge=-90, le=65, allow_inf_nan=False)]

    @field_validator("date", mode="before")
    @classmethod
    def iso_date(cls, value: object) -> object:
        if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value
        if isinstance(value, date):
            return value
        raise ValueError("Use a date in YYYY-MM-DD format")


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    station_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    observations: list[Observation] = Field(min_length=4, max_length=366)

    @model_validator(mode="after")
    def consecutive_days(self) -> "PredictionRequest":
        dates = [row.date for row in self.observations]
        if any((b - a).days != 1 for a, b in pairwise(dates)):
            raise ValueError("Observations must be ordered, unique and exactly one day apart")
        return self


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    station_id: str
    forecast_date: date
    risk: int
    label: str
    model_version: str
    synthetic_model: bool
