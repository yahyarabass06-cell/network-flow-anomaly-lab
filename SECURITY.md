# Security Considerations

## Authorized Use

Use only synthetic records or data you are authorized to analyze.
This project performs offline analysis without active network operations.

## Data Handling

Real metadata can reveal infrastructure behavior and identities.
Do not commit private datasets, credentials or generated reports.

Input fingerprints identify bytes; they do not establish authenticity.
Keep input files stable during analysis.

## Model Trust

No serialized model artifact is loaded.
Do not add loading of untrusted pickle or joblib files: these formats
can execute code during deserialization.

## Configuration and Evaluation

Dataset labels, session identifiers and chronology are trusted evaluation
inputs. Incorrect or fabricated metadata can undermine evaluation.

Review dataset and feature changes before accepting new results.
A successful command means analysis completed, not that traffic is safe.

## Resource and Filesystem Boundaries

Inputs are loaded into memory and have no explicit size limits.
Run with ordinary user privileges and use appropriately sized datasets.

File export targets Linux filesystems supporting hard links.
Reports are created with owner-only permissions.
Use output directories controlled by the current user.

## Reporting Problems

Report reproducible issues without attaching private traffic data,
credentials or confidential infrastructure details.
Use minimized synthetic examples where possible.
