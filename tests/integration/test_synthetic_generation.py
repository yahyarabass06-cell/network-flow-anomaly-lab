"""Verify reproducibility and partition boundaries of generated data."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from flow_anomaly.reading import load_samples
from flow_anomaly.splitting import validate_partitions

ROOT = Path(__file__).resolve().parents[2]


def generate(path):
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/generate_synthetic_data.py"),
            "--output",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_generated_data_is_reproducible_and_validated(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    assert generate(first).returncode == 0
    assert generate(second).returncode == 0

    metadata = json.loads((first / "metadata.json").read_text())
    partitions = []
    for name in ("train", "calibration", "test"):
        path = first / f"{name}.jsonl"
        raw = path.read_bytes()
        assert raw == (second / path.name).read_bytes()
        assert (
            hashlib.sha256(raw).hexdigest() == (metadata["partitions"][name]["sha256"])
        )
        samples = load_samples(path)
        assert len(samples) == metadata["partitions"][name]["records"]
        partitions.append(samples)

    validated = validate_partitions(*partitions)
    assert {sample.label for sample in validated.train} == {0}
    assert {sample.label for sample in validated.calibration} == {0, 1}
    assert {sample.label for sample in validated.test} == {0, 1}
    assert any(
        sample.scenario == "legitimate_bulk" and sample.label == 0
        for sample in validated.test
    )


def test_existing_destination_is_preserved(tmp_path):
    destination = tmp_path / "existing"
    destination.mkdir()
    marker = destination / "marker.txt"
    marker.write_text("original")
    assert generate(destination).returncode != 0
    assert marker.read_text() == "original"
    assert list(destination.iterdir()) == [marker]
