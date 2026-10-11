"""Explicit feature extraction without evaluation metadata."""

import math

from flow_anomaly.models import FlowMeasurements

FEATURE_NAMES = (
    "log_duration",
    "log_packets",
    "log_bytes",
    "log_packet_rate",
    "log_bytes_per_packet",
    "is_tcp",
    "is_udp",
)


def extract_features(measurements: FlowMeasurements) -> tuple[float, ...]:
    """Return ordered features from validated measurements only."""
    if not isinstance(measurements, FlowMeasurements):
        raise ValueError("Expected validated measurements, not sample metadata")

    numeric = (
        measurements.duration_seconds,
        measurements.packet_count,
        measurements.byte_count,
        measurements.packet_count / measurements.duration_seconds,
        measurements.byte_count / measurements.packet_count,
    )

    if any(not math.isfinite(value) for value in numeric):
        raise ValueError("Derived features must be finite")

    return (
        *(math.log1p(value) for value in numeric),
        float(measurements.protocol == "TCP"),
        float(measurements.protocol == "UDP"),
    )
