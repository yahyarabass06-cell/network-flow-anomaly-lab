"""Command-line interface for fixed network anomaly experiments."""

import argparse
import json
import sys
from pathlib import Path

from flow_anomaly.experiment import run_experiment
from flow_anomaly.exporting import write_new_report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate network anomaly detectors on chronological data."
    )
    parser.add_argument(
        "--data-directory",
        required=True,
        type=Path,
        help="Directory containing train, calibration and test JSONL files.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target-fpr", type=float, default=0.05)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    try:
        report = run_experiment(
            args.data_directory,
            seed=args.seed,
            target_false_positive_rate=args.target_fpr,
        )
        content = json.dumps(report, indent=2, allow_nan=False) + "\n"

        if args.output is None:
            sys.stdout.write(content)
        else:
            write_new_report(args.output, content)
            print("Report saved.", file=sys.stderr)

    except (OSError, ValueError) as exc:
        print(
            f"Analysis failed ({type(exc).__name__}). "
            "Check datasets, parameters and output destination.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
