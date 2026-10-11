"""Validate detector contracts and calibration boundary behavior."""

import numpy as np
import pytest

from flow_anomaly.calibration import (
    calibrate_threshold,
    predict_anomalies,
)
from flow_anomaly.detectors import (
    IsolationForestDetector,
    RobustDeviationDetector,
)


@pytest.fixture
def matrix():
    rng = np.random.default_rng(42)
    return rng.normal(size=(60, 7))


@pytest.mark.parametrize("factory", [RobustDeviationDetector, IsolationForestDetector])
def test_scoring_requires_training(factory, matrix):
    with pytest.raises(ValueError, match="fitted"):
        factory().score(matrix)


@pytest.mark.parametrize("factory", [RobustDeviationDetector, IsolationForestDetector])
def test_fitted_detector_returns_finite_scores(factory, matrix):
    scores = factory().fit(matrix).score(matrix[:5])
    assert scores.shape == (5,)
    assert np.isfinite(scores).all()


def test_seeded_isolation_forest_is_reproducible(matrix):
    first = IsolationForestDetector(seed=42).fit(matrix)
    second = IsolationForestDetector(seed=42).fit(matrix)
    np.testing.assert_array_equal(first.score(matrix), second.score(matrix))


def test_constant_training_columns_are_supported():
    matrix = np.ones((20, 7))
    detector = RobustDeviationDetector().fit(matrix)
    np.testing.assert_array_equal(detector.score(matrix), np.zeros(20))
    assert detector.score(np.full((1, 7), 3))[0] > 0


@pytest.mark.parametrize(
    "values",
    [
        [],
        [1, 2, 3],
        [[1, 2]],
        [[float("nan")] * 7],
        [[float("inf")] * 7],
        [[1e100] * 7],
    ],
)
def test_invalid_training_matrix_is_rejected(values):
    with pytest.raises(ValueError):
        IsolationForestDetector().fit(values)


def test_calibration_respects_empirical_budget():
    scores = np.arange(100, dtype=float)
    result = calibrate_threshold(scores, target_false_positive_rate=0.05)
    assert result.benign_count == 100
    assert result.observed_false_positive_rate <= 0.05
    assert result.observed_false_positive_rate == np.mean(scores > result.value)


def test_threshold_ties_are_not_flagged():
    result = calibrate_threshold([2, 2, 2, 2])
    assert result.value == 2
    assert result.observed_false_positive_rate == 0
    assert predict_anomalies([2, 3], threshold=result.value).tolist() == [False, True]


@pytest.mark.parametrize("rate", [0, 1, -0.1, True, float("nan")])
def test_invalid_calibration_rate_is_rejected(rate):
    with pytest.raises(ValueError):
        calibrate_threshold([1, 2], target_false_positive_rate=rate)


@pytest.mark.parametrize("scores", [[], [[1]], [float("nan")]])
def test_invalid_calibration_scores_are_rejected(scores):
    with pytest.raises(ValueError):
        calibrate_threshold(scores)
