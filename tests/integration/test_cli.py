"""Exercise the CLI as a separate process."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/synthetic/v1"


def run_cli(*extra, data=DATA):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "flow_anomaly.cli",
            "--data-directory",
            str(data),
            *extra,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_stdout_contains_complete_report():
    result = run_cli()
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["analysis_status"] == "complete"
    assert set(report["detectors"]) == {"robust_deviation", "isolation_forest"}


def test_report_can_be_exported(tmp_path):
    path = tmp_path / "assessment.json"
    result = run_cli("--output", str(path))
    assert result.returncode == 0
    assert result.stdout == ""
    assert json.loads(path.read_text())["analysis_status"] == "complete"


def test_existing_output_is_preserved(tmp_path):
    path = tmp_path / "assessment.json"
    path.write_text("original")
    result = run_cli("--output", str(path))
    assert result.returncode == 2
    assert result.stdout == ""
    assert path.read_text() == "original"
    assert "Analysis failed" in result.stderr


def test_missing_dataset_returns_error(tmp_path):
    result = run_cli(data=tmp_path / "missing")
    assert result.returncode == 2
    assert result.stdout == ""


def test_invalid_target_rate_returns_error():
    result = run_cli("--target-fpr", "nan")
    assert result.returncode == 2
    assert result.stdout == ""


def test_invalid_seed_returns_error():
    result = run_cli("--seed", "-1")
    assert result.returncode == 2
    assert result.stdout == ""
