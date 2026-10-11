# Evaluation

## Data and Protocol

The bundled dataset is generated with seed 42 and contains:

- Training: 600 designated benign records.
- Calibration: 300 records, including 234 designated benign records.
- Test: 400 records, including 297 benign and 103 suspicious records.

Partitions occupy separate chronological periods and have distinct
session identifiers. Scenario categories may appear in multiple periods.

Scenarios include ordinary traffic, legitimate bulk transfers,
unusual benign traffic and designated suspicious high-rate traffic.

Labels are assigned by the synthetic scenario definition before evaluation.
They are not independent expert judgments of real-world malicious activity.

Both detectors train on the same benign training features.
Thresholds use only benign calibration scores, with a preselected 0.05
false-positive target and strict score > threshold decisions.

Both observed calibration false-positive rates were 11/234,
approximately 0.0470.

## Observed Test Results

| Measurement | Robust deviation | Isolation Forest |
| --- | ---: | ---: |
| Threshold | 3.3163347557118126 | 0.5907408973867817 |
| True negatives | 286 | 289 |
| False positives | 11 | 8 |
| False negatives | 89 | 56 |
| True positives | 14 | 47 |
| Precision | 0.5600 | 0.8545 |
| Recall | 0.1359 | 0.4563 |
| F1 | 0.2188 | 0.5949 |
| False-positive rate | 0.0370 | 0.0269 |
| Average Precision | 0.5519 | 0.7642 |
| Trapezoidal PR-AUC | 0.5478 | 0.7600 |

The positive label is 1. Higher scores indicate greater anomaly.

Average Precision is a non-interpolated ranking summary.
Trapezoidal PR-AUC uses linear interpolation between precision-recall points.
They are reported separately.

Undefined metrics are null and listed explicitly. Ranking metrics are
reported only when both classes are present in the evaluated subset.

## Reproduction

Run from the repository root:

    network-flow-anomaly --data-directory data/synthetic/v1

Inspect the report's by_scenario sections to locate false positives,
including legitimate bulk transfers and unusual benign traffic.

A clean clone and non-editable Python 3.14 installation reproduced the
confusion matrices and F1 scores. The local suite passed 98 tests.

The observed environment included NumPy 2.5.4, scikit-learn 1.9.1 and
SciPy 1.18.1. The complete snapshot is in requirements-dev.lock.

## Interpretation

Isolation Forest performed better on this single synthetic experiment.
This does not establish superiority on real traffic or other datasets.

Low recall remains a material limitation. Scores and alerts need context
and do not prove compromise.

## Future Evaluation

Define datasets, labels, settings and success criteria before execution.
Use independently labeled data with reviewed licensing and provenance.

Report uncertainty across independent sessions and datasets.
Record class prevalence because precision depends on it.
Do not repeatedly tune against the already inspected test set.

Measure repeated timings and peak memory with hardware and scope recorded.
Current timings cover fit, calibration scoring and threshold selection,
and test scoring. They exclude feature extraction and complete CLI startup.
