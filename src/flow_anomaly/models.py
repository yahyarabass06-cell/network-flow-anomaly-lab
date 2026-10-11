"""Validated flow measurements and separate evaluation metadata."""

import math
from dataclasses import dataclass
from datetime import datetime, timezone

MAX_EXACT_INTEGER = 2**53 - 1


@dataclass(frozen=True)
class FlowMeasurements:
    """Predictive inputs, excluding labels and scenario identifiers."""

    duration_seconds: float
    packet_count: int
    byte_count: int
    protocol: str

    def __post_init__(self) -> None:
        if type(self.duration_seconds) not in (int, float):
            raise ValueError("duration_seconds must be numeric")
        try:
            duration = float(self.duration_seconds)
        except OverflowError:
            raise ValueError("duration_seconds is too large") from None

        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("duration_seconds must be finite and positive")
        object.__setattr__(self, "duration_seconds", duration)

        for name, minimum in (("packet_count", 1), ("byte_count", 0)):
            value = getattr(self, name)
            if type(value) is not int or not minimum <= value <= MAX_EXACT_INTEGER:
                raise ValueError(f"{name} is outside the supported integer range")

        if not isinstance(self.protocol, str) or self.protocol not in {"TCP", "UDP"}:
            raise ValueError("Supported protocols are TCP and UDP")


@dataclass(frozen=True)
class FlowSample:
    """A measured flow with metadata used for splitting and evaluation."""

    sample_id: str
    group_id: str
    scenario: str
    timestamp: datetime
    measurements: FlowMeasurements
    label: int

    def __post_init__(self) -> None:
        for name in ("sample_id", "group_id", "scenario"):
            value = getattr(self, name)
            if (
                not isinstance(value, str)
                or not value.strip()
                or value != value.strip()
            ):
                raise ValueError(f"{name} must be a non-empty trimmed string")

        if not isinstance(self.timestamp, datetime):
            raise ValueError("timestamp must be a datetime")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(timezone.utc))

        if not isinstance(self.measurements, FlowMeasurements):
            raise ValueError("Expected validated flow measurements")

        if type(self.label) is not int or self.label not in (0, 1):
            raise ValueError("label must be 0 or 1")
