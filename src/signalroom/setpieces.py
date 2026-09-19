from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import asdict, dataclass

from .adapters.statsbomb import SOURCE_REVISION
from .deadballs import analyze_attacking_final_third_dead_balls
from .models import Event, EvidenceSequence, Match


@dataclass(frozen=True)
class CornerDeliveryGroup:
    delivery_group: str
    delivery_side: str
    delivery_type: str
    target_lane: str
    count: int
    matches: int
    share: float
    share_ci_low: float
    share_ci_high: float
    shots: int
    corners_with_shot: int
    xg: float | None
    shot_rate: float
    evidence_ids: tuple[str, ...]
    display_eligible: bool
    status: str

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["evidence_ids"] = list(self.evidence_ids)
        return value


def analyze_attacking_corners(
    matches: list[Match], events: list[Event], team: str, minimum_group: int = 4
) -> tuple[list[CornerDeliveryGroup], list[EvidenceSequence]]:
    """Group recorded corner deliveries without claiming analyst-confirmed routines."""
    _, dead_balls = analyze_attacking_final_third_dead_balls(
        matches, events, team, SOURCE_REVISION, minimum_sample=minimum_group
    )
    corners = [row for row in dead_balls if row.restart_type == "corner"]
    sequences: list[EvidenceSequence] = []
    for row in corners:
        length = row.delivery.get("length")
        delivery_type = (
            "unknown" if length is None else "short" if float(length) <= 15.0 else "direct"
        )
        label = (
            f"{row.delivery.get('side', 'unknown')} / {delivery_type} / "
            f"{row.delivery.get('target_lane', 'unknown')}"
        )
        sequences.append(
            EvidenceSequence(
                evidence_id=row.evidence_id,
                match_id=row.match_id,
                match_date=row.match_date,
                opponent=row.opponent,
                start_event_id=row.start_event_id,
                source_event_ids=row.source_event_ids,
                label=label,
                start_minute=_elapsed_minute(row.timestamp),
                events=row.ordered_events,
                quality={
                    "delivery_length": row.data_quality.get("delivery_length", "unknown"),
                    "locations": row.data_quality.get("event_locations", "unknown"),
                    "movement_endpoints": row.data_quality.get("movement_endpoints", "unknown"),
                    "shot_xg": row.data_quality.get("shot_xg", "unknown"),
                    "sequence": row.data_quality.get("sequence", "unknown"),
                },
                predicate=label,
                termination_reason=row.termination_reason,
                censoring_reason=row.censoring_reason,
                player_roles=row.player_roles,
            )
        )
    grouped: dict[str, list[EvidenceSequence]] = defaultdict(list)
    for sequence in sequences:
        grouped[sequence.label].append(sequence)
    total = len(sequences)
    output: list[CornerDeliveryGroup] = []
    for label, rows in grouped.items():
        side, delivery_type, target_lane = label.split(" / ", 2)
        shots = [event for row in rows for event in row.events if event.get("type") == "Shot"]
        shot_rows = [
            row for row in rows if any(event.get("type") == "Shot" for event in row.events)
        ]
        xg_values = [event.get("xg") for event in shots]
        xg = (
            sum(float(value) for value in xg_values)
            if all(value is not None for value in xg_values)
            else None
        )
        low, high = _wilson_interval(len(rows), total)
        eligible = len(rows) >= minimum_group
        output.append(
            CornerDeliveryGroup(
                delivery_group=label,
                delivery_side=side,
                delivery_type=delivery_type,
                target_lane=target_lane,
                count=len(rows),
                matches=len({row.match_id for row in rows}),
                share=len(rows) / total if total else 0.0,
                share_ci_low=low,
                share_ci_high=high,
                shots=len(shots),
                corners_with_shot=len(shot_rows),
                xg=xg,
                shot_rate=len(shot_rows) / len(rows) if rows else 0.0,
                evidence_ids=tuple(_diverse_ids(rows, 5)),
                display_eligible=eligible,
                status="descriptive" if eligible else "suppressed: fewer than four corners",
            )
        )
    output.sort(key=lambda row: (row.display_eligible, row.count), reverse=True)
    return output, sequences


def _elapsed_minute(timestamp: str) -> int:
    hours, minutes, _ = timestamp.split(":")
    return int(hours) * 60 + int(minutes)


def _diverse_ids(rows: list[EvidenceSequence], limit: int) -> list[str]:
    output: list[str] = []
    seen: set[int] = set()
    for row in sorted(rows, key=lambda item: (item.match_date, item.evidence_id), reverse=True):
        if row.match_id in seen:
            continue
        output.append(row.evidence_id)
        seen.add(row.match_id)
        if len(output) == limit:
            break
    return output


def _wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    proportion = successes / total
    denominator = 1 + z**2 / total
    centre = proportion + z**2 / (2 * total)
    spread = z * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2))
    return (centre - spread) / denominator, (centre + spread) / denominator
