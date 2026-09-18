# Product specification

## Workflow

1. Select a built case or add a TOML configuration.
2. Ingest and validate the competition, season, match, and event records.
3. Calculate match metrics and corner routines.
4. Compare baseline and recent windows.
5. Apply magnitude, uncertainty, sensitivity, and evidence gates.
6. Review the briefing, suppressed comparisons, and evidence room.
7. Export or share the static historical report.

## Functional requirements

- Team switching requires configuration, not code edits.
- Every metric displays its exact definition, windows, sample sizes, and uncertainty.
- Every published finding contains at least three retrievable evidence sequences.
- A report may contain zero broad findings.
- Every corner routine with fewer than four examples is suppressed.
- Reports are deterministic by default.

## Non-goals

Current scouting advice, causal claims, live data, player evaluation, automated coaching recommendations, proprietary-provider emulation, and generic chat are outside the MVP.

