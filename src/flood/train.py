"""Run with --synthetic to build a reproducible demonstration, never an operational model."""

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, classification_report

from flood.features import FEATURES, build_features

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def synthetic_observations(rows: int = 720) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    days = np.arange(rows)
    rain = rng.gamma(1.3, 4, rows)
    water = np.maximum(
        0.1, 2.5 + 1.7 * np.sin(days / 19) + rain * 0.035 + rng.normal(0, 0.15, rows)
    )
    return pd.DataFrame(
        {
            "date": pd.date_range("2022-01-01", periods=rows),
            "water_level": water,
            "discharge": water * 40 + rng.uniform(0, 20, rows),
            "precipitation": rain,
            "temperature": 8 + 18 * np.sin(days / 58),
        }
    )


def train_demo(output: Path) -> dict:
    raw = synthetic_observations()
    frame = build_features(raw)
    # Illustrative thresholds in metres; labels describe the NEXT day's synthetic water level.
    next_water = raw["water_level"].shift(-1)
    frame["target"] = np.select([next_water < 2, next_water < 3.5], [0, 1], default=2)
    frame = frame.iloc[:-1].dropna().reset_index(drop=True)
    boundary = int(len(frame) * 0.8)
    # Purge one row so the final training target precedes the first held-out issue date.
    training, testing = frame.iloc[: boundary - 1], frame.iloc[boundary:]
    model = RandomForestClassifier(
        n_estimators=100, max_depth=8, min_samples_leaf=3, random_state=42, n_jobs=1
    )
    model.fit(training[FEATURES], training["target"])
    predictions = model.predict(testing[FEATURES])
    report = classification_report(
        testing["target"],
        predictions,
        labels=[0, 1, 2],
        target_names=["Low", "Medium", "High"],
        output_dict=True,
        zero_division=0,
    )
    version = hashlib.sha256(raw.to_csv(index=False).encode()).hexdigest()[:12]
    metadata = {
        "model_version": f"synthetic-rf-{version}",
        "synthetic_model": True,
        "forecast_horizon_days": 1,
        "features": FEATURES,
        "training_rows": len(training),
        "test_rows": len(testing),
        "last_training_issue_date": str(training["date"].iloc[-1].date()),
        "first_test_issue_date": str(testing["date"].iloc[0].date()),
        "accuracy": accuracy_score(testing["target"], predictions),
        "classification_report": report,
        "limitations": "Synthetic data and illustrative labels; no real-world validation.",
    }
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "metadata": metadata}, output / "model.joblib")
    (output / "metrics.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    raw.to_csv(output / "synthetic-observations.csv", index=False)
    ConfusionMatrixDisplay.from_predictions(
        testing["target"], predictions, labels=[0, 1, 2], display_labels=["Low", "Medium", "High"]
    )
    plt.title("Synthetic holdout only — next-day risk")
    plt.tight_layout()
    plt.savefig(output / "confusion-matrix.png")
    plt.close()
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic", action="store_true", required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    metadata = train_demo(args.output)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
