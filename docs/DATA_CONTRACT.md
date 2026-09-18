# Data contract

## Implemented source

StatsBomb Open Data repository snapshot inspected at commit `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb` on 18 September 2026.

The official repository documents:

- `competitions.json`
- `matches/{competition_id}/{season_id}.json`
- `events/{match_id}.json`
- `lineups/{match_id}.json`
- `three-sixty/{match_id}.json` for selected matches

SignalRoom currently consumes competitions, matches, and events. Lineups and 360 are inventoried but not required by implemented metrics.

## Internal event fields

Required: event ID, match ID, index, period, timestamp, team, event type, possession, possession team, and play pattern.

Nullable: player, start location, end location, outcome, subtype, pass length, and xG. Validation reports missing movement end locations, shot xG, and corner length explicitly. Missing corner length produces an `unknown` routine type rather than an inferred short/direct label.

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
