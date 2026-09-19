# Data contract

## Source manifest

The pinned StatsBomb source manifest records provider, revision, competition scope, expected and received fixtures, modality list, aggregate event-file and lineup-file hashes, licence reference, and publication mode.

## Identity

Internal `Match`, `Event`, and `LineupEntry` objects retain provider-scoped identifiers. Public artifacts use SignalRoom evidence IDs and do not expose provider event IDs.

## Event fields

The adapter preserves:

- time, period, team, player, recipient, event type and subtype
- source and end coordinates
- body part, technique, pass height, and outcome
- possession and linked event references
- shot outcome and xG
- local source-payload reference

Nullable values remain nullable. Generated quality reports distinguish observed from missing or unavailable values. Sequence-specific fields also support not-applicable and censored states.

## Lineups and exposure

Lineups are loaded for every declared fixture. Player position intervals, start status, recorded minutes where calculable, and match exposure are retained. Public role tables scope players to the selected team.

## Coordinates

Both provider-source and selected-team canonical coordinates exist during processing. Opponent events are rotated by `(120 - x, 80 - y)`. Coordinates are validated against a 120 by 80 pitch. Public evidence publishes lanes and status, not exact source coordinates.

## Restart and sequence

Restart type, recorded action, spatial category, legal-status availability, termination reason, censoring reason, event membership, roles, quality state, and provenance remain separate.

Event, lineup, shot freeze frame, 360 snapshot, continuous tracking, video, and human annotation are distinct modalities. Availability of one does not imply another.

## Rights classes

The public build permits attributed derived aggregates and derived sequence summaries. It rejects raw records, source event identifiers, and source event excerpts. Rights validation runs before bundle generation succeeds.
