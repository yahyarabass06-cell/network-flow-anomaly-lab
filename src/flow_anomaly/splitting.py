"""Validate chronological partitions before detector training."""

from dataclasses import dataclass

from flow_anomaly.models import FlowSample


@dataclass(frozen=True)
class DatasetPartitions:
    train: tuple[FlowSample, ...]
    calibration: tuple[FlowSample, ...]
    test: tuple[FlowSample, ...]


def validate_partitions(
    train: tuple[FlowSample, ...],
    calibration: tuple[FlowSample, ...],
    test: tuple[FlowSample, ...],
) -> DatasetPartitions:
    """Reject empty partitions, shared sessions and overlapping periods."""
    partitions = (train, calibration, test)
    seen_samples: set[str] = set()
    previous_groups: set[str] = set()

    for partition in partitions:
        if not isinstance(partition, tuple) or not partition:
            raise ValueError("Each partition must be a non-empty tuple.")

        partition_groups: set[str] = set()
        for sample in partition:
            if not isinstance(sample, FlowSample):
                raise ValueError("Partitions require validated flow samples.")
            if sample.sample_id in seen_samples:
                raise ValueError("Repeated sample identifier across partitions.")
            seen_samples.add(sample.sample_id)
            partition_groups.add(sample.group_id)

        if previous_groups & partition_groups:
            raise ValueError("Session groups must not cross partitions.")
        previous_groups.update(partition_groups)

    if any(sample.label != 0 for sample in train):
        raise ValueError("Training must contain only designated benign samples.")

    for earlier, later in zip(partitions, partitions[1:]):
        if max(sample.timestamp for sample in earlier) >= min(
            sample.timestamp for sample in later
        ):
            raise ValueError("Partition periods must be strictly chronological.")

    return DatasetPartitions(train, calibration, test)
