# Model card: synthetic next-day flood-risk prototype

## Purpose and data

Demonstrate a reproducible software pipeline. The training CLI generates 720 daily observations for one artificial station with a fixed random seed. No real meteorological records, river measurements or validated flood events are included.

Input units: water level in metres, discharge in m³/s, daily precipitation in millimetres and temperature in °C. Values and ranges are illustrative; real stations need datum and unit reconciliation.

## Target and prediction time

At the end of day **t**, the model predicts the risk associated with the synthetic water level on **t+1**. Training labels use:

| Next-day water level | Label |
| --- | --- |
| Below 2 m | 0 / Low |
| At least 2 m and below 3.5 m | 1 / Medium |
| At least 3.5 m | 2 / High |

These are demonstration thresholds, not public-safety thresholds. No physical rainfall-runoff or hydraulic model is implemented.

## Feature availability

Current-day water level, discharge, precipitation and temperature are assumed available by issue time. Rolling features use days **t−3 through t−1**; the lag uses **t−1**. Day of year describes the issue date. The API rejects non-consecutive input dates rather than silently treating an irregular sample as a daily lag.

The same feature function serves training and inference. A test changes future observations and verifies that earlier feature rows remain unchanged. This follows the principle of keeping unavailable future information out of model inputs; see [scikit-learn's guidance on data leakage](https://scikit-learn.org/stable/common_pitfalls.html).

## Evaluation

The earliest 80% defines the training boundary. One boundary row is purged because its next-day label would reach the held-out period. The final 20% is used once for evaluation. No random train/test shuffle or hyperparameter search is used.

The CLI writes actual Accuracy and per-class / macro / weighted Precision, Recall and F1 values to `artifacts/metrics.json`, plus a confusion matrix. There is no promised target score. The synthetic generator, threshold rules and temporal dependence make these results unsuitable for estimating operational performance.

## Reproducibility and limits

Direct dependencies are pinned. The model identifier combines the synthetic dataset digest with the model family; it is not a full model registry. Algorithm/configuration changes should introduce a new versioning scheme before model comparison.

The serving model remains trained only on the training interval. No confidence probability is presented as calibrated flood likelihood. Station identity is persisted but the synthetic model has no station-specific calibration.

Before real use: acquire licensed observations, validate labels, compare baselines, evaluate out-of-time and held-out-station performance, quantify missed-event costs and add operational safeguards.

