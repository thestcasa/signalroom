# Product specification

## Workflow

1. Select a built case or add a TOML configuration.
2. Ingest and validate the competition, season, match, and event records.
3. Calculate match metrics and attacking final-third dead-ball sequences.
4. Compare recent versus previous team windows, with peer prevalence only when coverage is complete.
5. Apply sample, uncertainty, repetition, data-quality, stability, and evidence gates.
6. Review ranked dead-ball observations and the supporting evidence room.
7. Export or share the deterministic historical preparation briefing.

## Functional requirements

- Team switching requires configuration, not code edits.
- Every metric displays its exact definition, windows, sample sizes, and uncertainty.
- Every published finding contains at least three retrievable evidence sequences.
- A report may contain zero broad findings.
- Every corner routine with fewer than four examples is suppressed.
- Reports are deterministic by default.
- Every dead-ball observation states its data capability level.
- ML grouping is suppressed unless a reproducible peer feature matrix and stability check pass.

## Non-goals

Current scouting advice, causal claims, live data, player evaluation, automated coaching recommendations, proprietary-provider emulation, video integration without licensed synchronized video, and generic chat are outside the MVP.
