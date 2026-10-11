"""Train and calibrate without consuming final test feature values."""

from pathlib import Path

import numpy as np

from flow_anomaly.calibration import calibrate_threshold
from flow_anomaly.detectors import (
    IsolationForestDetector,
    RobustDeviationDetector,
)
from flow_anomaly.features import extract_features
from flow_anomaly.reading import load_samples
from flow_anomaly.splitting import validate_partitions

DATA = Path(__file__).resolve().parents[2] / "data/synthetic/v1"


def test_both_detectors_train_and_calibrate_on_separate_periods():
    partitions = validate_partitions(
        load_samples(DATA / "train.jsonl"),
        load_samples(DATA / "calibration.jsonl"),
        load_samples(DATA / "test.jsonl"),
    )
    training = [extract_features(sample.measurements) for sample in partitions.train]
    benign_calibration = [
        extract_features(sample.measurements)
        for sample in partitions.calibration
        if sample.label == 0
    ]

    for detector in (
        RobustDeviationDetector(),
        IsolationForestDetector(seed=42),
    ):
        detector.fit(training)
        scores = detector.score(benign_calibration)
        threshold = calibrate_threshold(scores)
        assert np.isfinite(threshold.value)
        assert threshold.benign_count == len(benign_calibration)
        assert threshold.observed_false_positive_rate <= 0.05
