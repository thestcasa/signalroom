from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .models import Event, EvidenceSequence, Match


def build_metric_evidence(
    event_ids: Iterable[str],
    events: list[Event],
    matches: list[Match],
    team: str,
    label: str,
    limit: int = 5,
) -> list[EvidenceSequence]:
    requested = set(event_ids)
    match_map = {match.match_id: match for match in matches}
    by_match: dict[int, list[Event]] = defaultdict(list)
    for event in events:
        by_match[event.match_id].append(event)
    selected: list[EvidenceSequence] = []
    used_possessions: set[tuple[int, int]] = set()
    candidate_events = sorted(
        (event for event in events if event.event_id in requested),
        key=lambda event: (event.match_id, event.index),
        reverse=True,
    )
    for anchor in candidate_events:
        key = (anchor.match_id, anchor.possession)
        if key in used_possessions:
            continue
        context = [
            event
            for event in by_match[anchor.match_id]
            if event.period == anchor.period
            and event.possession == anchor.possession
            and abs(event.index - anchor.index) <= 10
        ]
        context.sort(key=lambda event: event.index)
        match = match_map[anchor.match_id]
        opponent = match.away_team if match.home_team == team else match.home_team
        selected.append(
            EvidenceSequence(
                evidence_id=f"EV-{anchor.match_id}-{anchor.index}",
                match_id=anchor.match_id,
                match_date=match.date,
                opponent=opponent,
                start_event_id=anchor.event_id,
                source_event_ids=tuple(event.event_id for event in context),
                label=label,
                start_minute=anchor.minute,
                events=tuple(_event_summary(event) for event in context),
            )
        )
        used_possessions.add(key)
        if len(selected) >= limit:
            break
    return selected


def validate_evidence_references(
    sequences: Iterable[EvidenceSequence], events: Iterable[Event]
) -> list[str]:
    known = {event.event_id for event in events}
    errors = []
    for sequence in sequences:
        missing = set(sequence.source_event_ids) - known
        if missing:
            errors.append(f"{sequence.evidence_id}: missing {sorted(missing)}")
        if sequence.start_event_id not in sequence.source_event_ids:
            errors.append(f"{sequence.evidence_id}: anchor absent from sequence")
    return errors


def _event_summary(event: Event) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "index": event.index,
        "minute": event.minute,
        "second": event.second,
        "team": event.team,
        "player": event.player,
        "type": event.event_type,
        "subtype": event.subtype,
        "outcome": event.outcome,
        "location": [event.x, event.y],
        "end_location": [event.end_x, event.end_y],
        "xg": event.xg,
    }
