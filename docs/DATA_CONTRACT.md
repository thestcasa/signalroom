# Data contract

## Implemented source

StatsBomb Open Data repository snapshot inspected at commit `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb` on 18 September 2026.

The official repository documents:

- `competitions.json`
- `matches/{competition_id}/{season_id}.json`
- `events/{match_id}.json`
- `lineups/{match_id}.json`
- `three-sixty/{match_id}.json` for selected matches

SignalRoom currently consumes competitions, matches, and events. Lineups and 360 are inventoried but not required by implemented metrics. The internal contract is provider-neutral beyond the adapter boundary and carries a capability level with every dead-ball sequence.

## Internal event fields

Required: event ID, match ID, index, period, timestamp, team, event type, possession, possession team, and play pattern.

Nullable: player, start location, end location, outcome, subtype, pass length, and xG. Validation reports missing movement end locations, shot xG, and corner length explicitly. Missing corner length produces an `unknown` routine type rather than an inferred short/direct label.

## Dead-ball sequence contract

`DeadBallSequence` contains a stable evidence ID, match and opponent context, period and timestamp, restart type, source event IDs, ordered event summaries, participants, delivery metadata, first recorded contact, second-phase summary, shot and xG outcome, data-quality fields, source revision, and capability level. It is implemented for attacking final-third corners, wide free kicks, indirect near-box free kicks, and direct free-kick shots. Free-kick categories are location buckets because the open event contract does not provide a referee-certified direct/indirect flag.

Architecture-only domains use the same planned contract: attacking throw-ins, goal kicks, kick-offs, penalties, defensive dead balls, and synchronized video references.

## Bundle compatibility

Bundles written before schema `1.2.0` remain readable because the UI treats `dead_ball_lab`, `capability`, and `ordered_events` as optional legacy fields. New builds write `1.2.0` and include the dead-ball domain. No raw provider data is migrated into the bundle.

## Verified availability

| Case | Competition / season | Matches for team | 360 |
| --- | --- | ---: | --- |
| Brighton & Hove Albion WFC | FA WSL 2023/24, IDs 37 / 281 | 22 | Not available |
| Bayer Leverkusen | Bundesliga 2023/24, IDs 9 / 281 | 34 | Repository metadata indicates availability, not used by MVP |

## Known source limitations

- Event data captures recorded on-ball and selected defensive actions, not complete off-ball shape.
- Coordinates and event labels are provider-specific before adapter normalization.
- Open-data availability is a selected sample, not a complete current competition feed.
- The public data agreement controls use of source data and requires attribution.
