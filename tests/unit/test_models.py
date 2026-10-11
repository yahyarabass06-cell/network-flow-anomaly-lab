"""Validate measurements and isolate evaluation metadata."""

from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timedelta, timezone

import pytest

from flow_anomaly.models import (
    MAX_EXACT_INTEGER,
    FlowMeasurements,
    FlowSample,
)


@pytest.fixture
def measurements():
    return FlowMeasurements(
        duration_seconds=2.0,
        packet_count=10,
        byte_count=800,
        protocol="TCP",
    )


@pytest.fixture
def sample(measurements):
    return FlowSample(
        sample_id="flow-001",
        group_id="session-001",
        scenario="ordinary",
        timestamp=datetime(2026, 10, 11, tzinfo=timezone.utc),
        measurements=measurements,
        label=0,
    )


def test_measurement_fields_exclude_evaluation_metadata():
    assert {field.name for field in fields(FlowMeasurements)} == {
        "duration_seconds",
        "packet_count",
        "byte_count",
        "protocol",
    }


def test_timestamp_is_normalized_to_utc(sample):
    offset = timezone(timedelta(hours=2))
    local = datetime(2026, 10, 11, 12, tzinfo=offset)
    changed = replace(sample, timestamp=local)
    assert changed.timestamp == datetime(2026, 10, 11, 10, tzinfo=timezone.utc)


def test_metadata_changes_do_not_change_measurements(sample):
    changed = replace(sample, label=1, scenario="suspicious", sample_id="flow-002")
    assert changed.measurements == sample.measurements


def test_measurements_are_immutable(measurements):
    with pytest.raises(FrozenInstanceError):
        measurements.packet_count = 20


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("duration_seconds", 0),
        ("duration_seconds", -1),
        ("duration_seconds", float("nan")),
        ("duration_seconds", float("inf")),
        ("duration_seconds", True),
        ("duration_seconds", "2"),
        ("packet_count", 0),
        ("packet_count", True),
        ("packet_count", 1.5),
        ("packet_count", MAX_EXACT_INTEGER + 1),
        ("byte_count", -1),
        ("byte_count", False),
        ("byte_count", MAX_EXACT_INTEGER + 1),
        ("protocol", "ICMP"),
        ("protocol", "tcp"),
        ("protocol", None),
    ],
)
def test_invalid_measurement_is_rejected(measurements, field, value):
    with pytest.raises(ValueError):
        replace(measurements, **{field: value})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sample_id", ""),
        ("group_id", " session-001"),
        ("scenario", None),
        ("timestamp", datetime(2026, 10, 11)),
        ("timestamp", "2026-10-11"),
        ("measurements", {}),
        ("label", True),
        ("label", -1),
        ("label", 2),
    ],
)
def test_invalid_sample_is_rejected(sample, field, value):
    with pytest.raises(ValueError):
        replace(sample, **{field: value})
