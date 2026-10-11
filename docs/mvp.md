# Network Flow Anomaly Lab — MVP

## Goal

Evaluate anomaly detection on authorized network-flow data.
Compare a trained Isolation Forest with a simple statistical baseline.

An anomaly score is not a probability of attack.
The first dataset is synthetic and does not establish real-world accuracy.

## Inputs

Use validated JSONL flow records with timestamps, scenario groups,
duration, packet count, byte count and protocol.

Evaluation labels and scenario identifiers remain separate from model features.
IP addresses, record identifiers and split membership are not predictive inputs.

Include ordinary traffic, unusual legitimate traffic and suspicious scenarios.
Do not define every large transfer as malicious.

## Evaluation Protocol

1. Define scenario labels before evaluating detectors.
2. Generate separate chronological training, calibration and test periods.
3. Keep scenario groups separate across periods.
4. Fit preprocessing and models using training data only.
5. Train Isolation Forest on the designated benign training subset.
6. Select thresholds using the calibration set, never the test set.
7. Freeze settings before the final test evaluation.
8. Compare detectors on the same test records.

Record seeds, feature definitions, split sizes and data fingerprints.
Repeated tuning on the test set invalidates its held-out role.

## Outputs

- Anomaly scores and explicit threshold decisions.
- Precision, recall, F1 and false-positive rate.
- Confusion matrix with clearly defined positive labels.
- PR-AUC using anomaly scores oriented toward the positive class.
- Results by scenario, including unusual benign traffic.
- Training and inference timings with measurement scope documented.

Report undefined metrics explicitly when a denominator is zero.

## Engineering

Provide validated inputs, deterministic runs, unit and integration tests,
a CLI, documented experiments and CI.

Never load an untrusted pickle or joblib artifact.
Model persistence will receive an explicit trust and compatibility design.

## Boundaries

No active scanning, traffic interception or automatic blocking.
No cloud infrastructure is required.
Real datasets require license and provenance review before use.
