"""Detectors operating exclusively on numeric feature matrices."""

import numpy as np
from sklearn.ensemble import IsolationForest

from flow_anomaly.features import FEATURE_NAMES


def validate_matrix(values) -> np.ndarray:
    """Require a non-empty finite matrix with the documented feature width."""
    try:
        matrix = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Features must form a numeric matrix.") from exc

    if (
        matrix.ndim != 2
        or matrix.shape[0] == 0
        or matrix.shape[1] != len(FEATURE_NAMES)
    ):
        raise ValueError("Invalid feature matrix dimensions.")
    if not np.isfinite(matrix).all():
        raise ValueError("Feature values must be finite.")
    # Isolation Forest converts input to float32 internally.
    if np.abs(matrix).max() > np.finfo(np.float32).max:
        raise ValueError("Feature values exceed supported numeric bounds.")
    return matrix


class RobustDeviationDetector:
    """Maximum absolute deviation using training medians and robust scales."""

    def __init__(self):
        self._center = None
        self._scale = None

    def fit(self, values):
        matrix = validate_matrix(values)
        center = np.median(matrix, axis=0)
        mad = np.median(np.abs(matrix - center), axis=0)
        quartiles = np.quantile(matrix, [0.25, 0.75], axis=0)
        iqr = quartiles[1] - quartiles[0]

        # A unit scale handles constant or discrete columns explicitly.
        scale = np.where(
            mad > 0,
            1.4826 * mad,
            np.where(iqr > 0, iqr / 1.349, 1.0),
        )
        self._center = center
        self._scale = scale
        return self

    def score(self, values) -> np.ndarray:
        if self._center is None:
            raise ValueError("Detector must be fitted before scoring.")
        matrix = validate_matrix(values)
        scores = np.max(
            np.abs(matrix - self._center) / self._scale,
            axis=1,
        )
        if not np.isfinite(scores).all():
            raise ValueError("Computed scores must be finite.")
        return scores


class IsolationForestDetector:
    """Seeded Isolation Forest with higher scores meaning more anomalous."""

    def __init__(self, *, seed: int = 42):
        if type(seed) is not int or not 0 <= seed < 2**32:
            raise ValueError("Seed must be an integer in [0, 2**32).")
        self.seed = seed
        self._model = None

    def fit(self, values):
        matrix = validate_matrix(values)
        model = IsolationForest(
            n_estimators=100,
            max_samples=min(256, len(matrix)),
            contamination="auto",
            random_state=self.seed,
            n_jobs=1,
        )
        model.fit(matrix)
        self._model = model
        return self

    def score(self, values) -> np.ndarray:
        if self._model is None:
            raise ValueError("Detector must be fitted before scoring.")
        matrix = validate_matrix(values)
        scores = -self._model.score_samples(matrix)
        if not np.isfinite(scores).all():
            raise ValueError("Computed scores must be finite.")
        return scores
