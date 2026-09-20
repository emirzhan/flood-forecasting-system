from datetime import date

from sqlalchemy import Date, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[str] = mapped_column(String(80), index=True)
    forecast_date: Mapped[date] = mapped_column(Date)
    risk: Mapped[int]
    label: Mapped[str] = mapped_column(String(10))
    model_version: Mapped[str] = mapped_column(String(80))
    synthetic_model: Mapped[bool]


def create_database(url: str):
    engine = create_engine(
        url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {}
    )
    return engine, sessionmaker(engine, expire_on_commit=False)
