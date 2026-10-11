"""Generate a reproducible synthetic flow evaluation dataset."""

import argparse
import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flow_anomaly.reading import load_samples
from flow_anomaly.splitting import validate_partitions

SEED = 42


def make_record(
    rng: random.Random,
    partition: str,
    index: int,
    start: datetime,
    scenario: str,
) -> dict:
    if scenario == "ordinary":
        duration = rng.uniform(2, 60)
        packets = rng.randint(20, 600)
        bytes_per_packet = rng.randint(80, 1000)
        protocol = rng.choice(("TCP", "UDP"))
        label = 0
    elif scenario == "legitimate_bulk":
        duration = rng.uniform(30, 180)
        packets = rng.randint(2000, 12000)
        bytes_per_packet = rng.randint(900, 1400)
        protocol = "TCP"
        label = 0
    elif scenario == "unusual_benign":
        duration = rng.uniform(0.5, 5)
        packets = rng.randint(100, 1500)
        bytes_per_packet = rng.randint(60, 1200)
        protocol = rng.choice(("TCP", "UDP"))
        label = 0
    elif scenario == "suspicious_high_rate":
        duration = rng.uniform(0.2, 3)
        packets = rng.randint(800, 6000)
        bytes_per_packet = rng.randint(60, 900)
        protocol = rng.choice(("TCP", "UDP"))
        label = 1
    else:
        raise ValueError("Unknown synthetic scenario.")

    return {
        "sample_id": f"{partition}-flow-{index:05d}",
        "group_id": f"{partition}-session-{index // 5:05d}",
        "scenario": scenario,
        "timestamp": (start + timedelta(seconds=index)).isoformat(),
        "measurements": {
            "duration_seconds": duration,
            "packet_count": packets,
            "byte_count": packets * bytes_per_packet,
            "protocol": protocol,
        },
        "label": label,
    }


def generate(destination: Path) -> None:
    # Refuse reuse to preserve previous experiment inputs.
    destination.mkdir(parents=True, exist_ok=False)
    rng = random.Random(SEED)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    specifications = (
        ("train", 600, 0),
        ("calibration", 300, 1),
        ("test", 400, 2),
    )
    metadata = {
        "schema_version": 1,
        "seed": SEED,
        "data_kind": "synthetic",
        "label_definition": {
            "0": "Designated benign synthetic scenario",
            "1": "Designated suspicious high-rate synthetic scenario",
        },
        "partitions": {},
    }
    loaded = {}

    for name, count, day_offset in specifications:
        scenarios = ["ordinary", "legitimate_bulk", "unusual_benign"]
        if name != "train":
            scenarios.append("suspicious_high_rate")

        records = [
            make_record(
                rng,
                name,
                index,
                start + timedelta(days=day_offset),
                rng.choice(scenarios),
            )
            for index in range(count)
        ]
        content = "".join(
            json.dumps(record, allow_nan=False) + "\n" for record in records
        ).encode("utf-8")
        path = destination / f"{name}.jsonl"
        with path.open("xb") as output:
            output.write(content)

        loaded[name] = load_samples(path)
        metadata["partitions"][name] = {
            "file": path.name,
            "records": count,
            "sha256": hashlib.sha256(content).hexdigest(),
            "scenario_counts": {
                scenario: sum(record["scenario"] == scenario for record in records)
                for scenario in scenarios
            },
        }

    validate_partitions(loaded["train"], loaded["calibration"], loaded["test"])
    with (destination / "metadata.json").open("x", encoding="utf-8") as output:
        json.dump(metadata, output, indent=2)
        output.write("\n")
    print(f"Validated synthetic dataset written to {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/synthetic/v1"),
    )
    args = parser.parse_args()
    generate(args.output)


if __name__ == "__main__":
    main()
