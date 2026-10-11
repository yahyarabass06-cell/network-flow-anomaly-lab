"""Test schema rejection, dataset loading and feature isolation."""

import json
import math

import pytest

from flow_anomaly.features import FEATURE_NAMES, extract_features
from flow_anomaly.reading import DatasetError, load_samples, parse_sample


@pytest.fixture
def record():
    return {
        "sample_id": "flow-001",
        "group_id": "session-001",
        "scenario": "ordinary",
        "timestamp": "2026-10-11T10:00:00+00:00",
        "measurements": {
            "duration_seconds": 2.0,
            "packet_count": 10,
            "byte_count": 800,
            "protocol": "TCP",
        },
        "label": 0,
    }


def test_expected_feature_values(record):
    sample = parse_sample(json.dumps(record))
    features = extract_features(sample.measurements)
    assert len(features) == len(FEATURE_NAMES)
    assert features == pytest.approx(
        (math.log(3), math.log(11), math.log(801), math.log(6), math.log(81), 1.0, 0.0)
    )


def test_metadata_does_not_change_features(record):
    first = parse_sample(json.dumps(record))
    record.update(
        sample_id="another-id",
        group_id="another-group",
        scenario="suspicious",
        label=1,
    )
    second = parse_sample(json.dumps(record))
    assert extract_features(first.measurements) == extract_features(second.measurements)


def test_sample_cannot_be_used_as_feature_input(record):
    with pytest.raises(ValueError):
        extract_features(parse_sample(json.dumps(record)))


def test_non_finite_derived_rate_is_rejected(record):
    record["measurements"]["duration_seconds"] = 1e-320
    sample = parse_sample(json.dumps(record))
    with pytest.raises(ValueError, match="finite"):
        extract_features(sample.measurements)


def test_jsonl_loads_valid_records(tmp_path, record):
    path = tmp_path / "flows.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    samples = load_samples(path)
    assert len(samples) == 1
    assert samples[0].sample_id == "flow-001"


def test_duplicate_sample_id_is_rejected(tmp_path, record):
    path = tmp_path / "flows.jsonl"
    path.write_text((json.dumps(record) + "\n") * 2, encoding="utf-8")
    with pytest.raises(DatasetError, match="line 2"):
        load_samples(path)


@pytest.mark.parametrize("content", ["", "\n", "{\n"])
def test_empty_or_invalid_dataset_is_rejected(tmp_path, content):
    path = tmp_path / "flows.jsonl"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(DatasetError):
        load_samples(path)


@pytest.mark.parametrize(
    "content",
    [
        '{"label": 0, "label": 1}',
        '{"label": NaN}',
        "[]",
    ],
)
def test_invalid_json_structure_is_rejected(content):
    with pytest.raises(ValueError):
        parse_sample(content)


def test_unknown_field_is_rejected(record):
    record["prediction"] = 1
    with pytest.raises(DatasetError):
        parse_sample(json.dumps(record))


def test_missing_measurement_is_rejected(record):
    record["measurements"].pop("packet_count")
    with pytest.raises(DatasetError):
        parse_sample(json.dumps(record))
