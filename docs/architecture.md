# Architecture

## Modules

| Module | Responsibility |
| --- | --- |
| models | Immutable validated measurements and labeled flow samples |
| reading | Strict JSONL parsing and duplicate identifier rejection |
| splitting | Chronological and session boundary validation |
| features | Numeric features without evaluation metadata |
| detectors | Training and scoring of both detectors |
| calibration | Benign-only threshold selection |
| evaluation | Binary and ranking metrics |
| experiment | Fixed experiment orchestration and provenance |
| exporting | Exclusive publication of complete reports |
| cli | Arguments, JSON output and exit codes |

## Feature Contract

Both detectors receive the same seven features:

1. log1p(duration_seconds)
2. log1p(packet_count)
3. log1p(byte_count)
4. log1p(packet_count / duration_seconds)
5. log1p(byte_count / packet_count)
6. TCP indicator
7. UDP indicator

Labels, identifiers, IP addresses, timestamps and scenario names are
not predictive features. Timestamps enforce partition chronology.

Logarithms reduce magnitude differences; they do not guarantee improved
detection. The feature definition must be reviewed before new experiments.

## Training and Calibration

Isolation Forest uses 100 trees, at most 256 samples per tree, seed 42
and one training worker by default. Its score_samples output is negated
so that larger values mean more anomalous.

The statistical baseline uses training medians and scaled median
absolute deviations. Zero dispersion falls back to scaled interquartile
range, then a unit scale. The score is the maximum absolute deviation.

Each threshold is the higher-method 95th percentile of its own benign
calibration scores. A record is flagged only when its score exceeds
the threshold. Calibration ties can reduce the observed alert rate.

The calibration target is empirical. It is not a guarantee about
the false-positive rate on new traffic.

## Evaluation Boundary

Both detectors and thresholds are prepared before test scoring.
Tests verify deterministic behavior under the same environment.

Once final results have been inspected, changing settings requires
a new independently defined evaluation protocol and held-out dataset.

## Reports and Filesystem

Reports include dependency versions, data fingerprints, configuration,
scores, decisions and scenario metrics.

Input hashes are checked against bytes read before and after parsing.
Inputs must remain stable; this is not a transactional filesystem snapshot
or proof of authenticity.

Exports use an owner-only temporary file and exclusive hard-link
publication. Existing files and symbolic links are preserved.
