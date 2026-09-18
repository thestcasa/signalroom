# Audit changelog

## Analytical correctness

- Corrected corner conversion to count shot-producing sequences rather than total shots.
- Separated shot-producing corners, conversion, total shots, and xG.
- Removed the x-coordinate proxy that mislabeled long corners as short.
- Defined short corners as first deliveries at or below 15 pitch units.
- Suppressed undefined zero-variance standardized effects and serialized them as JSON `null`.
- Added validation diagnostics for missing movement endpoints, shot xG, and corner length.

## Reproducibility and reliability

- Removed runtime timestamps from analytical artifacts.
- Added corrupt-cache recovery and atomic cache writes.
- Enforced safe slugs, positive identifiers, window minima, and bootstrap minima.
- Added a deterministic end-to-end pipeline regression test.
- Added CI with locked dependency installation, lint, and tests.
- Changed the canonical Render Blueprint to install from `uv.lock`.
- Disabled Streamlit telemetry.

## Interface and reporting

- Replaced mixed-unit window bars with standardized effects plus original-value annotations.
- Improved contrast, heading semantics, responsive title behavior, and image alternative text.
- Updated SetPieceLab tables to distinguish conversion from total shots.
- Regenerated JSON, CSV, PNG, HTML, Markdown, claims, and the stakeholder PDF.

## Dependency health

- Upgraded optional `pypdf` and `pytest` dependencies to advisory-free versions.
- Verified the resolved environment with `pip-audit`.
