import pandas as pd

FEATURES = [
    "water_level",
    "discharge",
    "precipitation",
    "temperature",
    "rolling_mean_water_level",
    "rolling_max_discharge",
    "lagged_water_level",
    "day_of_year",
]


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Use only observations available on or before the forecast issue date."""
    result = frame.copy()
    result["date"] = pd.to_datetime(result["date"])
    previous = result["water_level"].shift(1)
    result["rolling_mean_water_level"] = previous.rolling(3).mean()
    result["rolling_max_discharge"] = result["discharge"].shift(1).rolling(3).max()
    result["lagged_water_level"] = previous
    result["day_of_year"] = result["date"].dt.dayofyear
    return result
