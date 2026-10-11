"""Validate the complete fixed evaluation protocol."""

import json
from pathlib import Path

from flow_anomaly.experiment import run_experiment

DATA = Path(__file__).resolve().parents[2] / "data/synthetic/v1"


def test_experiment_is_reproducible_except_timings():
    first = run_experiment(DATA)
    second = run_experiment(DATA)
    assert first["analysis_status"] == "complete"
    assert first["inputs"]["test"]["records"] == 400

    for name in first["detectors"]:
        result = first["detectors"][name]
        assert result["threshold"]["benign_count"] == 234
        matrix = result["metrics"]["confusion_matrix"]
        assert sum(matrix.values()) == 400
        assert len(result["test_predictions"]) == 400
        assert "legitimate_bulk" in result["by_scenario"]
        first["detectors"][name].pop("timings_seconds")
        second["detectors"][name].pop("timings_seconds")

    assert first == second
    assert json.loads(json.dumps(first, allow_nan=False)) == first
