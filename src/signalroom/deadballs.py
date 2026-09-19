from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from .coordinates import event_coordinates
from .models import DeadBallSequence, Event, Match

FINAL_THIRD_X = 80.0
RESTART_TYPES = (
    "corner",
    "wide_final_third_free_kick_pass",
    "central_final_third_free_kick_pass",
    "direct_free_kick_shot",
)
STOPPAGE_EVENTS = {"Half End", "Injury Stoppage", "Offside", "Referee Ball-Drop"}


@dataclass(frozen=True)
class DeadBallSummary:
    restart_type: str
    count: int
    matches: int
    rate_per_match: float
    share: float
    share_ci_low: float
    share_ci_high: float
    total_shots: int
    shot_producing_sequences: int
    shot_producing_rate: float | None
    total_xg: float | None
    xg_per_restart: float | None
    xg_per_shot: float | None
    first_post_delivery_events: dict[str, int]
    delivery_target_lanes: dict[str, int]
    player_roles: dict[str, list[dict[str, Any]]]
    repetition_matches: int
    evidence_ids: tuple[str, ...]
    data_quality: dict[str, float]
    publication: str
    suppression_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["evidence_ids"] = list(self.evidence_ids)
        value["suppression_reasons"] = list(self.suppression_reasons)
        return value


def analyze_attacking_final_third_dead_balls(
    matches: list[Match],
    events: list[Event],
    team: str,
    source_revision: str,
    minimum_sample: int = 4,
) -> tuple[list[DeadBallSummary], list[DeadBallSequence]]:
    """Build event-bounded attacking restart observations, not inferred phases."""
    match_map = {match.match_id: match for match in matches}
    by_match: dict[int, list[Event]] = defaultdict(list)
    for event in events:
        by_match[event.match_id].append(event)
    sequences: list[DeadBallSequence] = []
    for match_id, match_events in by_match.items():
        ordered = sorted(match_events, key=lambda event: event.index)
        for position, start in enumerate(ordered):
            restart_type = classify_restart(start, team)
            if restart_type is None:
                continue
            context, termination, censoring = _sequence_window(start, ordered, position, team)
            match = match_map[match_id]
            opponent = match.away_team if match.home_team == team else match.home_team
            after = context[1] if len(context) > 1 else None
            shots = [
                event for event in context if event.team == team and event.event_type == "Shot"
            ]
            sequences.append(
                DeadBallSequence(
                    evidence_id=f"DB-{match_id}-{start.index}",
                    match_id=match_id,
                    match_date=match.date,
                    opponent=opponent,
                    period=start.period,
                    timestamp=start.timestamp,
                    restart_type=restart_type,
                    start_event_id=start.event_id,
                    source_event_ids=tuple(event.event_id for event in context),
                    ordered_events=tuple(_summary(event, team) for event in context),
                    delivery=_delivery(start, restart_type, team),
                    first_post_delivery=_post_delivery_summary(after, team) if after else None,
                    player_roles=_player_roles(start, context, team),
                    shot_outcome={
                        "shot_count": len(shots),
                        "total_xg": _sum_xg(shots),
                        "goals": sum(event.shot_outcome == "Goal" for event in shots),
                        "status": "observed" if shots else "not_applicable",
                    },
                    termination_reason=termination,
                    censoring_reason=censoring,
                    data_quality=_quality(start, context, after, censoring),
                    source_revision=source_revision,
                    capability_level="event",
                )
            )
    return _summaries(sequences, matches, minimum_sample), sequences


def classify_restart(event: Event, team: str) -> str | None:
    if event.team != team:
        return None
    in_final_third = event.x is not None and event.x >= FINAL_THIRD_X
    if event.event_type == "Pass" and event.subtype == "Corner":
        return "corner"
    if event.event_type == "Pass" and event.subtype == "Free Kick" and in_final_third:
        return (
            "wide_final_third_free_kick_pass"
            if _is_wide(event.y)
            else "central_final_third_free_kick_pass"
        )
    if event.event_type == "Shot" and event.subtype == "Free Kick" and in_final_third:
        return "direct_free_kick_shot"
    return None


def _is_wide(y: float | None) -> bool:
    return y is not None and (y <= 18 or y >= 62)


def _sequence_window(
    start: Event, events: list[Event], position: int, team: str
) -> tuple[list[Event], str, str | None]:
    if start.event_type == "Shot":
        return [start], "shot", None
    result = [start]
    start_seconds = _timestamp_seconds(start.timestamp)
    candidates = events[position + 1 : position + 18]
    termination = "source_end"
    censoring: str | None = None
    for event in candidates:
        if event.period != start.period:
            termination = "stoppage"
            break
        if _timestamp_seconds(event.timestamp) - start_seconds > 20:
            termination = "time_limit"
            censoring = "time_limit"
            break
        if event.possession != start.possession:
            termination = "loss" if event.team != team else "reset"
            break
        result.append(event)
        if event.event_type == "Shot" and event.team == team:
            termination = "shot"
            break
        if event.event_type in STOPPAGE_EVENTS:
            termination = "stoppage"
            break
    else:
        if len(candidates) == 17:
            termination = "event_limit"
            censoring = "event_limit"
    return result, termination, censoring


def _delivery(start: Event, restart_type: str, team: str) -> dict[str, Any]:
    start_point = event_coordinates(start, team)
    end_point = event_coordinates(start, team, end=True)
    end_x, end_y = end_point.canonical
    pass_detail = start.raw.get("pass") or {}
    technique = (pass_detail.get("technique") or {}).get("name")
    return {
        "side": "left" if start.y is not None and start.y < 40 else "right",
        "length": start.pass_length,
        "height": start.pass_height,
        "body_part": start.body_part,
        "technique": start.technique,
        "inswinging": technique == "Inswinging",
        "outswinging": technique == "Outswinging",
        "source_location_status": start_point.status,
        "canonical_location_status": end_point.status,
        "target_lane": _target_lane(end_x, end_y, start.pass_length),
        "recorded_action": "shot" if restart_type == "direct_free_kick_shot" else "pass",
    }


def _target_lane(x: float | None, y: float | None, length: float | None) -> str:
    if length is not None and length <= 15:
        return "short option"
    if x is None or y is None:
        return "unknown"
    if x >= 114 and 30 <= y <= 50:
        return "central six-yard lane"
    if x >= 102 and 18 <= y <= 62:
        if y < 30:
            return "left box lane"
        if y > 50:
            return "right box lane"
        return "central box lane"
    if x >= FINAL_THIRD_X:
        return "outer final-third lane"
    return "short or recycled lane"


def _post_delivery_summary(event: Event, team: str) -> dict[str, Any]:
    point = event_coordinates(event, team)
    return {
        "type": event.event_type,
        "team_role": "selected_team" if event.team == team else "opponent",
        "player": event.player,
        "body_part": event.body_part,
        "outcome": event.outcome,
        "location_status": point.status,
        "lane": _target_lane(*point.canonical, None),
    }


def _player_roles(start: Event, events: list[Event], team: str) -> dict[str, Any]:
    later_team_events = [event for event in events[1:] if event.team == team]
    shots = [event for event in later_team_events if event.event_type == "Shot"]
    first = events[1] if len(events) > 1 else None
    return {
        "taker": start.player,
        "intended_recipient": start.recipient,
        "first_post_delivery_actor": first.player if first else None,
        "first_post_delivery_actor_team": (
            "selected_team" if first and first.team == team else "opponent" if first else None
        ),
        "shot_actors": sorted({event.player for event in shots if event.player}),
        "later_selected_team_participants": sorted(
            {event.player for event in later_team_events if event.player}
        ),
    }


def _summary(event: Event, team: str) -> dict[str, Any]:
    point = event_coordinates(event, team)
    end_point = event_coordinates(event, team, end=True)
    return {
        "index": event.index,
        "elapsed_minute": event.minute,
        "elapsed_second": event.second,
        "team_role": "selected_team" if event.team == team else "opponent",
        "player": event.player,
        "type": event.event_type,
        "subtype": event.subtype,
        "outcome": event.outcome,
        "body_part": event.body_part,
        "location_status": point.status,
        "canonical_location": list(point.canonical),
        "canonical_end_location": list(end_point.canonical),
        "coordinate_transform": point.transform_version,
        "xg": event.xg,
    }


def _quality(
    start: Event,
    events: list[Event],
    first_post_delivery: Event | None,
    censoring: str | None,
) -> dict[str, Any]:
    shots = [event for event in events if event.event_type == "Shot"]
    moves = [event for event in events if event.event_type in {"Pass", "Carry"}]
    return {
        "delivery_location": (
            "observed"
            if all(value is not None for value in (start.x, start.y, start.end_x, start.end_y))
            else "missing"
        ),
        "delivery_length": "observed" if start.pass_length is not None else "unavailable",
        "first_post_delivery_event": "observed" if first_post_delivery else "unavailable",
        "event_locations": (
            "observed"
            if all(event.x is not None and event.y is not None for event in events)
            else "missing"
        ),
        "movement_endpoints": (
            "observed"
            if all(event.end_x is not None and event.end_y is not None for event in moves)
            else "missing"
        ),
        "shot_xg": (
            "not_applicable"
            if not shots
            else "observed"
            if all(event.xg is not None for event in shots)
            else "missing"
        ),
        "sequence": "censored" if censoring else "observed",
    }


def _sum_xg(shots: list[Event]) -> float | None:
    if not shots:
        return 0.0
    return (
        sum(float(event.xg) for event in shots)
        if all(event.xg is not None for event in shots)
        else None
    )


def _summaries(
    sequences: list[DeadBallSequence], matches: list[Match], minimum_sample: int
) -> list[DeadBallSummary]:
    total = len(sequences)
    total_matches = len(matches)
    output: list[DeadBallSummary] = []
    for restart_type in RESTART_TYPES:
        rows = [row for row in sequences if row.restart_type == restart_type]
        shot_rows = [row for row in rows if int(row.shot_outcome["shot_count"]) > 0]
        shot_count = sum(int(row.shot_outcome["shot_count"]) for row in rows)
        xg_values = [row.shot_outcome["total_xg"] for row in rows]
        total_xg = (
            sum(float(value) for value in xg_values)
            if all(value is not None for value in xg_values)
            else None
        )
        match_ids = {row.match_id for row in rows}
        first_events = Counter(
            (row.first_post_delivery or {}).get("type", "unavailable") for row in rows
        )
        targets = Counter(row.delivery.get("target_lane", "unknown") for row in rows)
        roles = {
            role: Counter(
                value for row in rows for value in _role_values(row.player_roles.get(role)) if value
            )
            for role in ("taker", "intended_recipient", "first_post_delivery_actor", "shot_actors")
        }
        quality = _quality_rates(rows)
        reasons: list[str] = []
        if len(rows) < minimum_sample:
            reasons.append(f"sample too small: {len(rows)} sequences, minimum {minimum_sample}")
        if quality.get("delivery_location", 0.0) < 0.90:
            reasons.append("delivery location completeness below 90%")
        publication = "descriptive" if not reasons else "suppressed"
        low, high = _wilson_interval(len(rows), total)
        is_direct_shot = restart_type == "direct_free_kick_shot"
        output.append(
            DeadBallSummary(
                restart_type=restart_type,
                count=len(rows),
                matches=len(match_ids),
                rate_per_match=len(rows) / total_matches if total_matches else 0.0,
                share=len(rows) / total if total else 0.0,
                share_ci_low=low,
                share_ci_high=high,
                total_shots=shot_count,
                shot_producing_sequences=len(shot_rows),
                shot_producing_rate=(
                    None if is_direct_shot else len(shot_rows) / len(rows) if rows else 0.0
                ),
                total_xg=total_xg,
                xg_per_restart=total_xg / len(rows) if total_xg is not None and rows else None,
                xg_per_shot=total_xg / shot_count if total_xg is not None and shot_count else None,
                first_post_delivery_events=dict(first_events),
                delivery_target_lanes=dict(targets),
                player_roles={
                    role: [
                        {"player": player, "count": count}
                        for player, count in counter.most_common(5)
                    ]
                    for role, counter in roles.items()
                },
                repetition_matches=len(match_ids),
                evidence_ids=tuple(_diverse_evidence_ids(rows, 5)),
                data_quality=quality,
                publication=publication,
                suppression_reasons=tuple(reasons),
            )
        )
    return output


def _role_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _diverse_evidence_ids(rows: list[DeadBallSequence], limit: int) -> list[str]:
    selected: list[str] = []
    seen_matches: set[int] = set()
    for row in sorted(rows, key=lambda item: (item.match_date, item.evidence_id), reverse=True):
        if row.match_id in seen_matches:
            continue
        selected.append(row.evidence_id)
        seen_matches.add(row.match_id)
        if len(selected) >= limit:
            break
    return selected


def _quality_rates(rows: list[DeadBallSequence]) -> dict[str, float]:
    keys = (
        "delivery_location",
        "delivery_length",
        "first_post_delivery_event",
        "event_locations",
        "movement_endpoints",
        "shot_xg",
        "sequence",
    )
    if not rows:
        return {key: 0.0 for key in keys}
    return {
        key: sum(row.data_quality.get(key) in {"observed", "not_applicable"} for row in rows)
        / len(rows)
        for key in keys
    }


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
