from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .models import DeadBallSequence, Event, EvidenceSequence, Match
from .rights import RightsManifest


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
        key=lambda event: (match_map[event.match_id].date, event.index),
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


def public_evidence_summary(
    sequence: DeadBallSequence,
    rights: RightsManifest,
    delivery_group: str | None = None,
) -> dict[str, object]:
    """Create a rights-safe, derived evidence card for public artifacts."""
    rights.require_public_artifact("derived_sequence_summary")
    predicates = [sequence.restart_type]
    if delivery_group:
        predicates.append(delivery_group)
    if int(sequence.shot_outcome.get("shot_count", 0)):
        predicates.append("shot-producing")
    else:
        predicates.append("no-shot")
    timeline = [
        {
            "team_role": event.get("team_role"),
            "type": event.get("type"),
            "subtype": event.get("subtype"),
            "outcome": event.get("outcome"),
            "body_part": event.get("body_part"),
            "xg": event.get("xg"),
        }
        for event in sequence.ordered_events
    ]
    return {
        "evidence_id": sequence.evidence_id,
        "match_id": sequence.match_id,
        "match_date": sequence.match_date,
        "opponent": sequence.opponent,
        "minute": _minute(sequence.timestamp),
        "restart_type": sequence.restart_type,
        "delivery_group": delivery_group,
        "predicate": delivery_group or sequence.restart_type,
        "supports_predicates": predicates,
        "delivery": {
            "side": sequence.delivery.get("side"),
            "delivery_type": (
                "unknown"
                if sequence.delivery.get("length") is None
                else "short"
                if float(sequence.delivery["length"]) <= 15.0
                else "direct"
            ),
            "target_lane": sequence.delivery.get("target_lane"),
            "height": sequence.delivery.get("height"),
            "body_part": sequence.delivery.get("body_part"),
            "technique": sequence.delivery.get("technique"),
        },
        "first_post_delivery": sequence.first_post_delivery,
        "player_roles": sequence.player_roles,
        "shot_outcome": sequence.shot_outcome,
        "termination_reason": sequence.termination_reason,
        "censoring_reason": sequence.censoring_reason,
        "data_quality": sequence.data_quality,
        "timeline": timeline,
        "evidence_status": "available-derived-summary",
        "rights_class": "derived-sequence-summary",
        "provenance": {
            "provider": rights.provider,
            "source_revision": sequence.source_revision,
            "publication_mode": rights.publication_mode,
        },
    }


def validate_bundle_evidence(bundle: dict[str, object]) -> list[str]:
    errors: list[str] = []
    evidence_rows = bundle.get("evidence", [])
    evidence = {str(row["evidence_id"]): row for row in evidence_rows}
    references: list[tuple[str, str | None, str]] = []
    for group in bundle.get("set_piece_lab", {}).get("delivery_groups", []):
        for evidence_id in group.get("evidence_ids", []):
            references.append((str(evidence_id), str(group["delivery_group"]), "delivery group"))
    for summary in bundle.get("dead_ball_lab", {}).get("summaries", []):
        for evidence_id in summary.get("evidence_ids", []):
            references.append((str(evidence_id), str(summary["restart_type"]), "restart summary"))
    for evidence_id, predicate, source in references:
        row = evidence.get(evidence_id)
        if row is None:
            errors.append(f"Missing evidence {evidence_id} referenced by {source}")
            continue
        if predicate and predicate not in row.get("supports_predicates", []):
            errors.append(
                f"Evidence {evidence_id} does not support {predicate!r} referenced by {source}"
            )
    return errors


def _minute(timestamp: str) -> int:
    hours, minutes, _ = timestamp.split(":")
    return int(hours) * 60 + int(minutes)


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
