"""Run a fixed train/calibration/test anomaly detection experiment."""

import hashlib
import platform
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

from flow_anomaly.calibration import (
    calibrate_threshold,
    predict_anomalies,
)
from flow_anomaly.detectors import (
    IsolationForestDetector,
    RobustDeviationDetector,
)
from flow_anomaly.evaluation import evaluate_scores
from flow_anomaly.features import FEATURE_NAMES, extract_features
from flow_anomaly.reading import load_samples
from flow_anomaly.splitting import validate_partitions


def run_experiment(
    data_directory: Path,
    *,
    seed: int = 42,
    target_false_positive_rate: float = 0.05,
) -> dict:
    loaded = {}
    provenance = {}
    for name in ("train", "calibration", "test"):
        path = data_directory / f"{name}.jsonl"
        before = path.read_bytes()
        loaded[name] = load_samples(path)
        after = path.read_bytes()
        if before != after:
            raise ValueError("Dataset changed while being read.")
        provenance[name] = {
            "file": path.name,
            "sha256": hashlib.sha256(before).hexdigest(),
            "records": len(loaded[name]),
        }

    partitions = validate_partitions(
        loaded["train"], loaded["calibration"], loaded["test"]
    )
    training = [extract_features(sample.measurements) for sample in partitions.train]
    benign_calibration = [
        extract_features(sample.measurements)
        for sample in partitions.calibration
        if sample.label == 0
    ]
    if not benign_calibration:
        raise ValueError("Calibration requires designated benign records.")

    prepared = []
    detectors = (
        ("robust_deviation", RobustDeviationDetector()),
        ("isolation_forest", IsolationForestDetector(seed=seed)),
    )
    for name, detector in detectors:
        started = perf_counter()
        detector.fit(training)
        fit_seconds = perf_counter() - started

        started = perf_counter()
        calibration_scores = detector.score(benign_calibration)
        threshold = calibrate_threshold(
            calibration_scores,
            target_false_positive_rate=target_false_positive_rate,
        )
        calibration_seconds = perf_counter() - started
        prepared.append((name, detector, threshold, fit_seconds, calibration_seconds))

    # Test features are consumed only after both thresholds are fixed.
    test_features = [
        extract_features(sample.measurements) for sample in partitions.test
    ]
    labels = [sample.label for sample in partitions.test]
    results = {}
    for name, detector, threshold, fit_seconds, calibration_seconds in prepared:
        started = perf_counter()
        scores = detector.score(test_features)
        inference_seconds = perf_counter() - started
        predicted = predict_anomalies(scores, threshold=threshold.value)

        scenarios = {}
        for scenario in sorted({sample.scenario for sample in partitions.test}):
            indices = [
                index
                for index, sample in enumerate(partitions.test)
                if sample.scenario == scenario
            ]
            scenarios[scenario] = evaluate_scores(
                [labels[index] for index in indices],
                scores[indices],
                threshold=threshold.value,
            )

        results[name] = {
            "threshold": asdict(threshold),
            "metrics": evaluate_scores(labels, scores, threshold=threshold.value),
            "by_scenario": scenarios,
            "timings_seconds": {
                "fit": fit_seconds,
                "benign_calibration_scoring_and_threshold": calibration_seconds,
                "test_scoring": inference_seconds,
            },
            "test_predictions": [
                {
                    "sample_id": sample.sample_id,
                    "scenario": sample.scenario,
                    "label": sample.label,
                    "anomaly_score": float(scores[index]),
                    "flagged": bool(predicted[index]),
                }
                for index, sample in enumerate(partitions.test)
            ],
        }

    return {
        "schema_version": 1,
        "analysis_status": "complete",
        "seed": seed,
        "features": list(FEATURE_NAMES),
        "inputs": provenance,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": version("numpy"),
            "scipy": version("scipy"),
            "scikit_learn": version("scikit-learn"),
        },
        "protocol": {
            "training": "designated benign training records only",
            "threshold_selection": "benign calibration scores only",
            "target_false_positive_rate": target_false_positive_rate,
            "decision": "anomaly_score > threshold",
            "score_orientation": "higher means more anomalous",
            "isolation_forest": {
                "n_estimators": 100,
                "max_samples": min(256, len(training)),
                "n_jobs": 1,
                "contamination": "auto; built-in threshold not used",
            },
            "robust_deviation": (
                "maximum absolute deviation; median center; "
                "1.4826*MAD scale, then IQR/1.349, then unit fallback"
            ),
        },
        "limitations": [
            "Synthetic scenarios do not establish real-world attack detection.",
            "Session separation cannot prove independence of real traffic.",
            "Input files must remain stable during analysis.",
            "Timings are single-run measurements excluding feature extraction.",
            "Do not retune settings using these final test results.",
        ],
        "detectors": results,
    }
