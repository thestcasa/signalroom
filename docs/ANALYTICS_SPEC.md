# Analytics specification

Metric version: `1.0.0`. StatsBomb pitch coordinates are 120 by 80 and oriented in the attacking direction for each team.

| Metric | Exact rule |
| --- | --- |
| Shots | Count team `Shot` events, including penalties |
| Expected goals | Sum `shot.statsbomb_xg` |
| Final-third entries | Completed pass or carry crossing from x < 80 to x >= 80 |
| Box entries | Completed pass or carry entering x >= 102 and 18 <= y <= 62 from outside |
| Progressive actions | Completed pass or carry gaining at least 15 x units |
| Build-up exits | Completed pass or carry starting at x <= 40 and ending at x >= 60 |
| High regains | `Ball Recovery` or `Interception` recorded at x >= 80 |

An absent pass outcome means complete, consistent with the source schema. Carries are treated as complete recorded actions.

## Change gate

- Baseline and recent windows are chronological and non-overlapping.
- Resampling unit: match.
- Publish when absolute bias-corrected standardized effect is at least 0.5, bootstrap direction probability is at least 0.80, and at least two of three recent-window sensitivity checks agree.
- In addition, require Benjamini-Hochberg q <= 0.20, or a standardized effect of at least 0.8 with direction probability at least 0.90.
- Require at least three retrievable recent evidence sequences.

## Attacking final-third dead-ball domain

The supported domain starts with a recorded attacking restart in the final third and retains the same-period, same-possession sequence for at most 20 seconds and 17 subsequent events. Current categories are:

- `corner`: pass subtype `Corner`.
- `wide_free_kick`: pass subtype `Free Kick`, x >= 80, and y <= 18 or y >= 62.
- `indirect_free_kick`: pass subtype `Free Kick`, x >= 80, and not wide by the location rule.
- `direct_free_kick`: shot subtype `Free Kick`, x >= 80.

The free-kick split is an event-location bucket, not a referee-certified direct/indirect classification. The category summary reports count, rate per match, share with Wilson interval, first-contact zone, delivery target, second-phase rate, shots, xG, xG per restart, recurring players and combinations, repetition across matches, data completeness, suppression reasons, and evidence IDs.

First contact means the first recorded `Ball Receipt*`, `Duel`, `Clearance`, `Interception`, or `Shot` event after the restart. Second phase means later same-team pass, carry, or shot events after that contact. These are observable event definitions, not visual claims about aerial contact or tactical intent.

## SetPieceLab v1

An attacking corner begins with a team pass whose subtype is `Corner`. The sequence continues within the same period and possession for at most 20 seconds and 17 subsequent events. Routines are grouped by delivery side, short/direct choice, and target zone. A cluster needs at least four corners. Shares receive 95% Wilson intervals. Output is descriptive, not causal.

A short corner has a first-delivery length of at most 15 StatsBomb pitch units. Longer deliveries are direct. If length is unavailable, delivery type and target zone are `unknown`; no coordinate proxy is used. `shot_rate` is sequence conversion: the share of corners followed by at least one team shot inside the sequence window. `shots` remains the total shot count, so rebounds do not inflate conversion.

If pooled match variance is zero while window means differ, Hedges g is undefined. SignalRoom serializes the effect as `null` and suppresses the comparison rather than emitting a non-standard JSON infinity or treating it as decisive evidence.

## Opponent-preparation comparison

The current source bundle supports a selected-team recent window versus the selected team's previous chronological window. Routine shares use all attacking corners in each window as denominators. The comparison reports percentage-point difference, relative difference only when the baseline share is non-zero, and a deterministic binomial bootstrap interval. Routine-level publication requires a minimum recent sample and at least 90% completeness for the corner delivery-length field. Shot xG is independently suppressed when any supporting shot lacks xG. Stability is recomputed for nearby recent-window sizes and is labelled for analysts rather than presented as a binary truth claim.

The dead-ball summary uses within-team repetition and recent-window context. A peer prevalence baseline is intentionally absent when the bundle does not load complete comparable teams. No ML cluster or anomaly is promoted to the main briefing without a reproducible peer matrix, interpretable features, stability checks, and sequence evidence; current cases therefore show a suppressed exploratory profile.
