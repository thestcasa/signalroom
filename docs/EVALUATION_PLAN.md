# Evaluation plan

## Automated acceptance

- All expected fixtures are present or explained.
- Public bundles contain no raw provider record, source event ID, or exact source excerpt.
- Every displayed evidence reference resolves and supports its predicate.
- Coordinates transform into the selected-team frame and remain on the pitch.
- Zero-valued coordinates are retained.
- Player roles exclude opponent players unless the role explicitly identifies an opponent actor.
- Direct free-kick shots do not enter conversion rankings.
- Missing completeness metadata does not default to true.
- Sequence termination and censoring are explicit.
- Change intervals resample matches.
- The application, evidence view, and export share one analysis state.
- WSL fixture totals reconcile to 132 and 12 teams.
- Leverkusen peer comparison is suppressed.

## Manual corpus

Each build produces `manual_review_sample.csv`, targeting 80 stratified sequences across teams, restart types, shot outcomes, and boundary states. Judgment-heavy fields require two reviewers and adjudication. Blank reviewer columns mean review is pending, not passed.

## External analyst validation

The protocol in `docs/ANALYST_VALIDATION_PROTOCOL.md` must be completed before any external-validation or club-readiness claim.
