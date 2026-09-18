from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import asdict, dataclass

from .models import Event, EvidenceSequence, Match


@dataclass(frozen=True)
class CornerRoutine:
    routine: str
    delivery_side: str
    delivery_type: str
    target_zone: str
    count: int
    share: float
    share_ci_low: float
    share_ci_high: float
    shots: int
    corners_with_shot: int
    xg: float
    shot_rate: float
    evidence_ids: tuple[str, ...]
    publish: bool
    reliability: str

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["evidence_ids"] = list(self.evidence_ids)
        return value


def analyze_attacking_corners(
    matches: list[Match], events: list[Event], team: str, minimum_cluster: int = 4
) -> tuple[list[CornerRoutine], list[EvidenceSequence]]:
    match_map = {match.match_id: match for match in matches}
    by_match: dict[int, list[Event]] = defaultdict(list)
    for event in events:
        by_match[event.match_id].append(event)
    sequences: list[EvidenceSequence] = []
    records: list[dict[str, object]] = []
    for match_id, match_events in by_match.items():
        match_events.sort(key=lambda event: event.index)
        positions = {event.event_id: index for index, event in enumerate(match_events)}
        for corner in match_events:
            if not _is_attacking_corner(corner, team):
                continue
            following = _corner_sequence(corner, match_events, positions[corner.event_id])
            delivery_side = "left" if (corner.y or 0) < 40 else "right"
            length = (corner.raw.get("pass") or {}).get("length")
            if length is None:
                delivery_type = "unknown"
            else:
                delivery_type = "short" if float(length) <= 15.0 else "direct"
            target_zone = _target_zone(corner, delivery_side, delivery_type)
            routine = f"{delivery_side} / {delivery_type} / {target_zone}"
            shots = [
                event for event in following if event.team == team and event.event_type == "Shot"
            ]
            match = match_map[match_id]
            opponent = match.away_team if match.home_team == team else match.home_team
            evidence_id = f"SP-{match_id}-{corner.index}"
            sequences.append(
                EvidenceSequence(
                    evidence_id=evidence_id,
                    match_id=match_id,
                    match_date=match.date,
                    opponent=opponent,
                    start_event_id=corner.event_id,
                    source_event_ids=tuple(event.event_id for event in following),
                    label=routine,
                    start_minute=corner.minute,
                    events=tuple(_summary(event) for event in following),
                    quality=_sequence_quality(corner, following),
                )
            )
            records.append(
                {
                    "routine": routine,
                    "delivery_side": delivery_side,
                    "delivery_type": delivery_type,
                    "target_zone": target_zone,
                    "shots": len(shots),
                    "has_shot": bool(shots),
                    "xg": sum(float(shot.xg or 0) for shot in shots),
                    "evidence_id": evidence_id,
                }
            )
    total = len(records)
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        grouped[str(record["routine"])].append(record)
    routines: list[CornerRoutine] = []
    for routine, group in grouped.items():
        count = len(group)
        ci_low, ci_high = _wilson_interval(count, total)
        shots = sum(int(row["shots"]) for row in group)
        corners_with_shot = sum(bool(row["has_shot"]) for row in group)
        publish = count >= minimum_cluster
        routines.append(
            CornerRoutine(
                routine=routine,
                delivery_side=str(group[0]["delivery_side"]),
                delivery_type=str(group[0]["delivery_type"]),
                target_zone=str(group[0]["target_zone"]),
                count=count,
                share=count / total if total else 0.0,
                share_ci_low=ci_low,
                share_ci_high=ci_high,
                shots=shots,
                corners_with_shot=corners_with_shot,
                xg=sum(float(row["xg"]) for row in group),
                shot_rate=corners_with_shot / count if count else 0.0,
                evidence_ids=tuple(str(row["evidence_id"]) for row in group[:1]),
                publish=publish,
                reliability="descriptive" if publish else "suppressed: fewer than 4 corners",
            )
        )
    routines.sort(key=lambda row: (row.publish, row.count, row.xg), reverse=True)
    return routines, sequences


def _is_attacking_corner(event: Event, team: str) -> bool:
    return event.team == team and event.event_type == "Pass" and event.subtype == "Corner"


def _corner_sequence(corner: Event, events: list[Event], position: int) -> list[Event]:
    sequence = [corner]
    start_seconds = _timestamp_seconds(corner.timestamp)
    for event in events[position + 1 : position + 18]:
        if event.period != corner.period:
            break
        elapsed = _timestamp_seconds(event.timestamp) - start_seconds
        if elapsed > 20:
            break
        if event.possession != corner.possession:
            break
        sequence.append(event)
    return sequence


def _target_zone(corner: Event, side: str, delivery_type: str) -> str:
    if delivery_type == "short":
        return "short option"
    if delivery_type == "unknown":
        return "unknown"
    if corner.end_y is None:
        return "unknown"
    if 32 <= corner.end_y <= 48:
        return "central goalmouth"
    same_side = (side == "left" and corner.end_y < 40) or (side == "right" and corner.end_y > 40)
    return "near-side channel" if same_side else "far-side channel"


def _timestamp_seconds(timestamp: str) -> float:
    hours, minutes, seconds = timestamp.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    proportion = successes / total
    denominator = 1 + z**2 / total
    centre = proportion + z**2 / (2 * total)
    spread = z * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2))
    return (centre - spread) / denominator, (centre + spread) / denominator


def _summary(event: Event) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "index": event.index,
        "minute": event.minute,
        "second": event.second,
        "team": event.team,
        "player": event.player,
        "type": event.event_type,
        "outcome": event.outcome,
        "location": [event.x, event.y],
        "end_location": [event.end_x, event.end_y],
        "xg": event.xg,
    }


def _sequence_quality(corner: Event, events: list[Event]) -> dict[str, object]:
    moves = [event for event in events if event.event_type in {"Pass", "Carry"}]
    shots = [event for event in events if event.event_type == "Shot"]
    return {
        "corner_length_available": (corner.raw.get("pass") or {}).get("length") is not None,
        "locations_complete": all(event.x is not None and event.y is not None for event in events),
        "movement_endpoints_complete": all(
            event.end_x is not None and event.end_y is not None for event in moves
        ),
        "shot_xg_complete": all(event.xg is not None for event in shots),
        "sequence_complete": True,
        "event_count": len(events),
    }
