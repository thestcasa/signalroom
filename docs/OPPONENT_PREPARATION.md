# Opponent-preparation workflow

## Product story

1. Choose the opponent case.
2. Identify unusual or changing attacking-corner routines.
3. Open the supporting event sequences.

SignalRoom is an evidence browser for analyst review. It does not infer intent, establish effectiveness, predict outcomes, or replace video analysis.

## Baseline decision

The current open-data case bundles contain all selected-team matches, not every competition match. The strongest valid default is therefore: `recent selected-team window vs previous selected-team window`. The windows are chronological, non-overlapping, and user-configurable within the available case. A competition-wide routine baseline must not be shown until every relevant competition match is acquired, validated, and included.

## Routine comparison

Routines are grouped by selected dimensions from delivery side, delivery type, and target zone. SignalRoom reports recent count, previous count, shares, percentage-point difference, relative difference when defined, bootstrap interval, shot-producing sequences, sequence conversion, total shots, xG when complete, sample sizes, stability, completeness, suppression reasons, and evidence IDs.

Shares are descriptive. They do not prove tactical intent or causal effectiveness. Conversion means the share of corner sequences containing at least one team shot within the retained-possession sequence window.

## Quality gates

The set-piece contract checks corner delivery length, event locations, movement endpoints, shot xG, sequence completeness, and sample size. Routine share publication requires at least 90% corner-length completeness and the configured minimum recent routine sample. Missing shot xG suppresses the xG value while allowing valid share and conversion metrics to remain visible. The UI identifies which metric is affected.

## Stability

The system repeats the comparison over nearby recent-window sizes. It reports `stable` when the direction is consistent across all tested windows, `directionally consistent` when most are consistent, `sensitive to window selection` when the direction changes, and `sample too small` when the routine does not meet its minimum.

## Evidence room and export

Every routine comparison stores representative evidence IDs. The Evidence room filters by routine, opponent, and shot outcome, then exposes event identifiers, ordered event rows, and a pitch view. Video is intentionally not claimed because no synchronized footage is distributed with the legitimate source data. The briefing download is self-contained deterministic HTML containing the selected state, observations, sample sizes, uncertainty, stability, evidence references, definitions, warnings, source revision, and non-affiliation language.
