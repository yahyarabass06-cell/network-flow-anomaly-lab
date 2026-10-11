"""Choose thresholds using designated benign calibration scores only."""

from dataclasses import dataclass

import numpy as np


def validate_scores(values) -> np.ndarray:
    try:
        scores = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Scores must be numeric.") from exc
    if scores.ndim != 1 or scores.size == 0:
        raise ValueError("Scores must be a non-empty vector.")
    if not np.isfinite(scores).all():
        raise ValueError("Scores must be finite.")
    return scores


@dataclass(frozen=True)
class CalibratedThreshold:
    value: float
    target_false_positive_rate: float
    observed_false_positive_rate: float
    benign_count: int


def calibrate_threshold(
    benign_scores,
    *,
    target_false_positive_rate: float = 0.05,
) -> CalibratedThreshold:
    if (
        type(target_false_positive_rate) not in (int, float)
        or not 0 < target_false_positive_rate < 1
    ):
        raise ValueError("Target false-positive rate must be between 0 and 1.")

    scores = validate_scores(benign_scores)
    value = float(
        np.quantile(
            scores,
            1 - target_false_positive_rate,
            method="higher",
        )
    )
    observed = float(np.mean(scores > value))
    return CalibratedThreshold(
        value=value,
        target_false_positive_rate=float(target_false_positive_rate),
        observed_false_positive_rate=observed,
        benign_count=len(scores),
    )


def predict_anomalies(scores, *, threshold: float) -> np.ndarray:
    if type(threshold) not in (int, float) or not np.isfinite(threshold):
        raise ValueError("Threshold must be finite.")
    return validate_scores(scores) > threshold
