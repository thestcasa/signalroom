# Analytics specification

## Population and context

Every output declares team, competition, season, historical cutoff, recent matches, preceding reference matches, fixture coverage, modalities, and source revision. The shortlist, evidence review, and export use the same context.

The Brighton case loads all 132 FA Women's Super League 2023/24 fixtures. The Leverkusen case loads the 34 released Leverkusen fixtures and suppresses Bundesliga peer claims.

## Restart taxonomy

| Category | Exact recorded rule |
| --- | --- |
| `corner` | Selected-team pass subtype `Corner` |
| `wide_final_third_free_kick_pass` | Selected-team pass subtype `Free Kick`, x >= 80, y <= 18 or y >= 62 |
| `central_final_third_free_kick_pass` | Selected-team pass subtype `Free Kick`, x >= 80, not wide |
| `direct_free_kick_shot` | Selected-team shot subtype `Free Kick`, x >= 80 |

The pass categories do not assert referee-certified direct or indirect status.

## Sequence boundary

A sequence starts at the restart anchor and remains in the same period and provider possession for at most 20 seconds and 17 later events. It terminates as `shot`, `loss`, `reset`, `stoppage`, or `source_end`. A time or event limit is explicitly censored.

The first recorded event after the delivery is reported with its type, team role, body part, outcome, and availability. It is not called physical first contact. There is no football second-phase label.

## Coordinates and delivery groups

StatsBomb source coordinates are stored only in the ignored cache. Internal event summaries transform opponent actions into a selected-team-attacks-right frame. Public evidence exposes validated lanes rather than exact coordinates.

Corner delivery groups combine:

- delivery side
- short, direct, or unknown pass length
- two-dimensional target lane

These are algorithmic groups, not analyst-confirmed routines.

## Change comparison

Recent and preceding shares use all corners in each window as denominators. Uncertainty resamples complete matches. A change is review-eligible only when all gates pass:

- minimum recent group sample
- at least two supporting recent matches
- at least a five percentage-point difference
- 95% match-block interval excluding zero
- consistent material direction across nearby windows
- at least three retrievable examples
- at least 90% delivery-group completeness

Rows failing a gate remain descriptive and show the exact suppression reasons.

## Outcomes

Pass restarts may report the share of sequences producing a shot within the declared window. Direct free-kick shots do not report shot-producing conversion because the category is selected by the presence of a shot. xG is provider shot xG within the bounded sequence and is descriptive, not causal effectiveness.

## Peer context

The WSL peer view is a complete competition-season descriptive baseline with 11 leave-target-out peers. It reports exposure, corner rate, shot-producing rate, delivery-group shares, and percentiles. It does not support clustering, archetypes, causal claims, or cross-competition generalization.

## Broad metrics

Seven older team metrics remain optional descriptive context in generated bundles. They are not the core preparation workflow. Progressive actions are expressed in provider pitch units, not metres.
