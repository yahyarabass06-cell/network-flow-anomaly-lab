"""Regression tests for chronological evaluation boundaries."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from flow_anomaly.models import FlowMeasurements, FlowSample
from flow_anomaly.splitting import validate_partitions


@pytest.fixture
def partitions():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return tuple(
        (
            FlowSample(
                sample_id=f"flow-{index}",
                group_id=f"session-{index}",
                scenario="ordinary",
                timestamp=start + timedelta(days=index),
                measurements=FlowMeasurements(
                    duration_seconds=2,
                    packet_count=10,
                    byte_count=800,
                    protocol="TCP",
                ),
                label=0,
            ),
        )
        for index in range(3)
    )


def test_valid_chronological_partitions(partitions):
    result = validate_partitions(*partitions)
    assert result.train == partitions[0]
    assert result.calibration == partitions[1]
    assert result.test == partitions[2]


@pytest.mark.parametrize("index", [0, 1, 2])
def test_empty_partition_is_rejected(partitions, index):
    changed = list(partitions)
    changed[index] = ()
    with pytest.raises(ValueError, match="non-empty"):
        validate_partitions(*changed)


def test_shared_session_is_rejected(partitions):
    train, calibration, test = partitions
    changed = replace(test[0], group_id=train[0].group_id)
    with pytest.raises(ValueError, match="groups"):
        validate_partitions(train, calibration, (changed,))


def test_repeated_sample_identifier_is_rejected(partitions):
    train, calibration, test = partitions
    changed = replace(test[0], sample_id=train[0].sample_id)
    with pytest.raises(ValueError, match="identifier"):
        validate_partitions(train, calibration, (changed,))


def test_duplicate_within_partition_is_rejected(partitions):
    train, calibration, test = partitions
    with pytest.raises(ValueError, match="identifier"):
        validate_partitions(train + train, calibration, test)


def test_suspicious_training_sample_is_rejected(partitions):
    train, calibration, test = partitions
    with pytest.raises(ValueError, match="benign"):
        validate_partitions((replace(train[0], label=1),), calibration, test)


@pytest.mark.parametrize("offset", [0, -1])
def test_overlapping_or_reversed_period_is_rejected(partitions, offset):
    train, calibration, test = partitions
    changed = replace(
        calibration[0],
        timestamp=train[0].timestamp + timedelta(seconds=offset),
    )
    with pytest.raises(ValueError, match="chronological"):
        validate_partitions(train, (changed,), test)


def test_multiple_records_from_same_session_are_allowed(partitions):
    train, calibration, test = partitions
    another = replace(
        train[0],
        sample_id="another-flow",
        timestamp=train[0].timestamp + timedelta(seconds=1),
    )
    result = validate_partitions(train + (another,), calibration, test)
    assert len(result.train) == 2
