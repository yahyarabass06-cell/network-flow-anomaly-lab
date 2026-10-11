"""Strict JSONL loading for labeled flow samples."""

import json
from datetime import datetime
from pathlib import Path

from flow_anomaly.models import FlowMeasurements, FlowSample


class DatasetError(ValueError):
    """The dataset cannot be safely interpreted."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DatasetError("Duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise DatasetError("Non-standard JSON constant")


def parse_sample(line: str) -> FlowSample:
    """Parse exact fields without silently accepting schema mistakes."""
    data = json.loads(
        line,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )
    expected = {
        "sample_id",
        "group_id",
        "scenario",
        "timestamp",
        "measurements",
        "label",
    }
    if not isinstance(data, dict) or set(data) != expected:
        raise DatasetError("Unexpected sample fields")

    measurements = data["measurements"]
    measurement_fields = {
        "duration_seconds",
        "packet_count",
        "byte_count",
        "protocol",
    }
    if not isinstance(measurements, dict) or set(measurements) != measurement_fields:
        raise DatasetError("Unexpected measurement fields")

    if not isinstance(data["timestamp"], str):
        raise DatasetError("timestamp must be a string")

    return FlowSample(
        sample_id=data["sample_id"],
        group_id=data["group_id"],
        scenario=data["scenario"],
        timestamp=datetime.fromisoformat(data["timestamp"]),
        measurements=FlowMeasurements(**measurements),
        label=data["label"],
    )


def load_samples(path: Path) -> tuple[FlowSample, ...]:
    """Load records, rejecting invalid lines and duplicate sample identifiers."""
    samples = []
    identifiers = set()

    try:
        with path.open(encoding="utf-8") as source:
            for number, line in enumerate(source, start=1):
                try:
                    sample = parse_sample(line)
                    if sample.sample_id in identifiers:
                        raise DatasetError("Duplicate sample identifier")
                except ValueError:
                    raise DatasetError(
                        f"Invalid flow record at line {number}"
                    ) from None

                identifiers.add(sample.sample_id)
                samples.append(sample)
    except (OSError, UnicodeError):
        raise DatasetError("Dataset could not be read") from None

    if not samples:
        raise DatasetError("Dataset is empty")

    return tuple(samples)
