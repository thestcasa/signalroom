# Opponent-preparation workflow

## Product story

1. Choose the opponent case.
2. Identify repeated, distinctive, or changing attacking final-third dead-ball behaviours.
3. Choose one pattern worth review rather than prescribing a solution.
4. Open the supporting event sequences and formulate a deterministic review question.

SignalRoom is an evidence browser for analyst review. It does not infer intent, establish effectiveness, predict outcomes, or replace video analysis.

## Baseline decision

The current open-data case bundles contain all selected-team matches, not every competition match. The strongest valid defaults are therefore: recent selected-team window vs previous selected-team window for change, and repetition across matches for recurrence. A competition-wide or peer prevalence baseline must not be shown until every relevant comparison match is acquired, validated, and included.

## Routine comparison

Routines are grouped by selected dimensions from delivery side, delivery type, and target zone. SignalRoom reports recent count, previous count, shares, percentage-point difference, relative difference when defined, bootstrap interval, shot-producing sequences, sequence conversion, total shots, xG when complete, sample sizes, stability, completeness, suppression reasons, and evidence IDs.

Shares are descriptive. They do not prove tactical intent or causal effectiveness. Conversion means the share of supported dead-ball sequences containing at least one team shot within the retained-possession sequence window. Free-kick categories are location buckets, not referee-certified direct/indirect labels.

The fully implemented first domain includes corners, wide attacking free kicks, indirect attacking free kicks near the penalty area, and direct free-kick shots. First contact means the first recorded contact-like event. Second phase means later same-team recorded actions after that contact. Attacking throw-ins, goal kicks, kick-offs, penalties, defensive restarts, tracking, and video remain planned or gated.

## Quality gates

The dead-ball contract checks delivery locations, delivery length where available, first-contact observation, event locations, movement endpoints, shot xG, sequence completeness, and sample size. Category publication requires at least four sequences and adequate delivery completeness. Missing shot xG suppresses xG-derived values while allowing valid count and share metrics to remain visible. The UI identifies the affected capability and field.

## Stability

The system repeats the comparison over nearby recent-window sizes. It reports `stable` when the direction is consistent across all tested windows, `directionally consistent` when most are consistent, `sensitive to window selection` when the direction changes, and `sample too small` when the routine does not meet its minimum.

## Evidence room and export

Every dead-ball category stores representative evidence IDs. The Evidence room filters by restart or routine, opponent, and shot outcome, then exposes event identifiers, ordered event rows, capability level, missing fields, and a pitch view. Video is intentionally not claimed because no synchronized footage is distributed with the legitimate source data. The briefing download is self-contained deterministic HTML containing the selected state, observations, sample sizes, uncertainty, stability, evidence references, definitions, warnings, source revision, and non-affiliation language.
