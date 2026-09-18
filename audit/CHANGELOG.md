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
- Added opponent-preparation controls, routine-share comparisons, uncertainty, stability labels, filtered evidence review, event-ID export, and deterministic briefing HTML.
- Added sequence-level completeness fields for corner length, locations, movement endpoints, shot xG, and sequence retention.

## Dependency health

- Upgraded optional `pypdf` and `pytest` dependencies to advisory-free versions.
- Verified the resolved environment with `pip-audit`.

## Opponent-preparation extension

- Implemented the strongest valid current baseline: recent selected-team window versus previous selected-team window.
- Added regression coverage for denominator correctness, suppression reasons, stability labels, and briefing determinism.
- Prepared `docs/ANALYST_VALIDATION_PACKAGE.md`; no external analyst validation is claimed yet.

## Dead-ball intelligence extension

- Added a provider-neutral `DeadBallSequence` contract and capability registry.
- Implemented attacking final-third corners, wide free kicks, indirect near-box free kicks, and direct free-kick shots from event data.
- Added first recorded contact, second-phase continuation, delivery target, player recurrence, shot/xG outcomes, quality fields, evidence IDs, and explicit suppression reasons.
- Added an interpretable team profile feature vector with a conservative ML gate; current cases suppress clustering because no complete peer matrix is loaded.
- Added a dedicated Dead-ball Lab, capability warnings, broader evidence filters, data-source research, and schema `1.2.0` compatibility handling.
- Independently recomputed category counts and verified strict JSON, evidence resolution, deterministic builds, 29 tests, and 90% total coverage.
