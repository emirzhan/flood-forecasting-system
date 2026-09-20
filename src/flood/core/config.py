from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="FLOOD_", extra="ignore")
    database_url: str = "sqlite:///./flood.db"
    model_path: Path = Path("artifacts/model.joblib")
