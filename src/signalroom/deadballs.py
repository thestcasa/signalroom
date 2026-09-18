from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from .models import DeadBallSequence, Event, Match

FINAL_THIRD_X = 80.0
RESTART_TYPES = (
    "corner",
    "wide_free_kick",
    "indirect_free_kick",
    "direct_free_kick",
)
ARCHITECTURE_ONLY_TYPES = (
    "attacking_throw_in",
    "goal_kick",
    "kick_off",
    "penalty",
    "defensive_dead_ball",
)
CONTACT_EVENTS = {"Ball Receipt*", "Duel", "Clearance", "Interception", "Shot"}


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
    shot_producing_rate: float
    total_xg: float | None
    xg_per_restart: float | None
    xg_per_shot: float | None
    second_phase_rate: float
    first_contact_zones: dict[str, int]
    delivery_targets: dict[str, int]
    recurring_players: list[dict[str, Any]]
    recurring_combinations: list[dict[str, Any]]
    repetition_matches: int
    evidence_ids: tuple[str, ...]
    review_questions: tuple[str, ...]
    data_quality: dict[str, float]
    publication: str
    suppression_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["evidence_ids"] = list(self.evidence_ids)
        value["review_questions"] = list(self.review_questions)
        value["suppression_reasons"] = list(self.suppression_reasons)
        return value


def analyze_attacking_final_third_dead_balls(
    matches: list[Match],
    events: list[Event],
    team: str,
    source_revision: str,
    minimum_sample: int = 4,
) -> tuple[list[DeadBallSummary], list[DeadBallSequence]]:
    """Build deterministic, event-only sequences for the supported first domain.

    Free-kick categories are location buckets. StatsBomb Open Data does not expose a
    referee-certified direct/indirect flag on the restart pass, so the distinction is
    deliberately descriptive and is shown as such in the product copy.
    """
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
            context = _sequence_window(start, ordered, position)
            opponent = match_map[match_id].away_team if match_map[match_id].home_team == team else match_map[match_id].home_team
            first_contact = _first_contact(context[1:])
            second_phase = _second_phase(context, first_contact, team)
            shots = [event for event in context if event.team == team and event.event_type == "Shot"]
            participants = tuple(sorted({event.player for event in context if event.player}))
            sequence = DeadBallSequence(
                evidence_id=f"DB-{match_id}-{start.index}",
                match_id=match_id,
                match_date=match_map[match_id].date,
                opponent=opponent,
                period=start.period,
                timestamp=start.timestamp,
                restart_type=restart_type,
                start_event_id=start.event_id,
                source_event_ids=tuple(event.event_id for event in context),
                ordered_events=tuple(_summary(event) for event in context),
                participants=participants,
                delivery=_delivery(start, restart_type),
                first_contact=_contact_summary(first_contact) if first_contact else None,
                second_phase=second_phase,
                shot_outcome={
                    "shot_count": len(shots),
                    "total_xg": _sum_xg(shots),
                    "goals": sum(event.outcome == "Goal" for event in shots),
                },
                data_quality=_quality(start, context, first_contact),
                source_revision=source_revision,
                capability_level="event",
            )
            sequences.append(sequence)
    return _summaries(sequences, matches, team, minimum_sample), sequences


def classify_restart(event: Event, team: str) -> str | None:
    if event.team != team:
        return None
    if event.event_type == "Pass" and event.subtype == "Corner":
        return "corner"
    if event.event_type == "Pass" and event.subtype == "Free Kick" and (event.x or 0) >= FINAL_THIRD_X:
        return "wide_free_kick" if _is_wide(event.y) else "indirect_free_kick"
    if event.event_type == "Shot" and event.subtype == "Free Kick" and (event.x or 0) >= FINAL_THIRD_X:
        return "direct_free_kick"
    return None


def _is_wide(y: float | None) -> bool:
    return y is not None and (y <= 18 or y >= 62)


def _sequence_window(start: Event, events: list[Event], position: int) -> list[Event]:
    if start.event_type == "Shot":
        return [start]
    result = [start]
    start_seconds = _timestamp_seconds(start.timestamp)
    for event in events[position + 1 : position + 18]:
        if event.period != start.period or event.possession != start.possession:
            break
        if _timestamp_seconds(event.timestamp) - start_seconds > 20:
            break
        result.append(event)
    return result


def _first_contact(events: list[Event]) -> Event | None:
    return next((event for event in events if event.event_type in CONTACT_EVENTS), None)


def _second_phase(events: list[Event], first_contact: Event | None, team: str) -> dict[str, Any]:
    if first_contact is None:
        return {"observed": False, "event_count": 0, "recycle_count": 0, "shot_count": 0}
    later = [event for event in events if event.index > first_contact.index and event.team == team]
    return {
        "observed": bool(later),
        "event_count": len(later),
        "recycle_count": sum(event.event_type in {"Pass", "Carry"} for event in later),
        "shot_count": sum(event.event_type == "Shot" for event in later),
    }


def _delivery(start: Event, restart_type: str) -> dict[str, Any]:
    side = "left" if (start.y or 40) < 40 else "right"
    target = _zone(start.end_x, start.end_y)
    return {
        "side": side,
        "length": start.pass_length if start.pass_length is not None else (start.raw.get("pass") or {}).get("length"),
        "start_location": [start.x, start.y],
        "end_location": [start.end_x, start.end_y],
        "target_zone": target,
        "action": "direct shot" if restart_type == "direct_free_kick" else "first recorded restart action",
    }


def _zone(x: float | None, y: float | None) -> str:
    if x is None or y is None:
        return "unknown"
    if x >= 105:
        return "goalmouth"
    if y < 28:
        return "near-side wide"
    if y > 52:
        return "far-side wide"
    return "central box"


def _contact_summary(event: Event) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "type": event.event_type,
        "team": event.team,
        "player": event.player,
        "location": [event.x, event.y],
        "zone": _zone(event.x, event.y),
    }


def _summary(event: Event) -> dict[str, Any]:
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


def _quality(start: Event, events: list[Event], first_contact: Event | None) -> dict[str, Any]:
    shots = [event for event in events if event.event_type == "Shot"]
    moves = [event for event in events if event.event_type in {"Pass", "Carry"}]
    return {
        "delivery_location_complete": start.x is not None and start.y is not None and start.end_x is not None and start.end_y is not None,
        "delivery_length_available": start.pass_length is not None or (start.raw.get("pass") or {}).get("length") is not None,
        "first_contact_observed": first_contact is not None,
        "first_contact_location_complete": first_contact is not None and first_contact.x is not None and first_contact.y is not None,
        "event_locations_complete": all(event.x is not None and event.y is not None for event in events),
        "movement_endpoints_complete": all(event.end_x is not None and event.end_y is not None for event in moves),
        "shot_xg_complete": all(event.xg is not None for event in shots),
    }


def _sum_xg(shots: list[Event]) -> float | None:
    return sum(float(event.xg) for event in shots) if all(event.xg is not None for event in shots) else None


def _summaries(sequences: list[DeadBallSequence], matches: list[Match], team: str, minimum_sample: int) -> list[DeadBallSummary]:
    total = len(sequences)
    total_matches = len(matches)
    output: list[DeadBallSummary] = []
    for restart_type in RESTART_TYPES:
        rows = [row for row in sequences if row.restart_type == restart_type]
        shots = [row for row in rows if int(row.shot_outcome["shot_count"]) > 0]
        xg_values = [row.shot_outcome["total_xg"] for row in rows]
        total_xg = sum(float(value) for value in xg_values) if all(value is not None for value in xg_values) else None
        match_ids = {row.match_id for row in rows}
        contacts = Counter((row.first_contact or {}).get("zone", "not observed") for row in rows)
        targets = Counter(row.delivery.get("target_zone", "unknown") for row in rows)
        players = Counter(player for row in rows for player in row.participants)
        combos = Counter(tuple(row.participants) for row in rows if len(row.participants) >= 2)
        quality = _quality_rates(rows)
        reasons: list[str] = []
        if len(rows) < minimum_sample:
            reasons.append(f"sample too small: {len(rows)} sequences, minimum {minimum_sample}")
        if total == 0:
            reasons.append("no supported attacking final-third dead balls")
        if quality["delivery_location_complete"] < 0.90:
            reasons.append("delivery location completeness below 90%")
        publication = "published descriptive" if not reasons else "suppressed"
        low, high = _wilson_interval(len(rows), total)
        output.append(DeadBallSummary(
            restart_type=restart_type,
            count=len(rows),
            matches=len(match_ids),
            rate_per_match=len(rows) / total_matches if total_matches else 0.0,
            share=len(rows) / total if total else 0.0,
            share_ci_low=low,
            share_ci_high=high,
            total_shots=sum(int(row.shot_outcome["shot_count"]) for row in rows),
            shot_producing_sequences=len(shots),
            shot_producing_rate=len(shots) / len(rows) if rows else 0.0,
            total_xg=total_xg,
            xg_per_restart=total_xg / len(rows) if total_xg is not None and rows else None,
            xg_per_shot=total_xg / sum(int(row.shot_outcome["shot_count"]) for row in rows) if total_xg is not None and sum(int(row.shot_outcome["shot_count"]) for row in rows) else None,
            second_phase_rate=sum(bool(row.second_phase["observed"]) for row in rows) / len(rows) if rows else 0.0,
            first_contact_zones=dict(contacts),
            delivery_targets=dict(targets),
            recurring_players=[{"player": name, "count": count} for name, count in players.most_common(5)],
            recurring_combinations=[{"players": list(names), "count": count} for names, count in combos.most_common(5)],
            repetition_matches=len(match_ids),
            evidence_ids=tuple(row.evidence_id for row in rows[:5]),
            review_questions=_review_questions(restart_type, rows, contacts, players),
            data_quality=quality,
            publication=publication,
            suppression_reasons=tuple(reasons),
        ))
    return output


def _quality_rates(rows: list[DeadBallSequence]) -> dict[str, float]:
    if not rows:
        return {key: 0.0 for key in ("delivery_location_complete", "delivery_length_available", "first_contact_observed", "first_contact_location_complete", "event_locations_complete", "movement_endpoints_complete", "shot_xg_complete")}
    keys = rows[0].data_quality.keys()
    return {key: sum(bool(row.data_quality.get(key)) for row in rows) / len(rows) for key in keys}


def _review_questions(
    restart_type: str,
    rows: list[DeadBallSequence],
    contacts: Counter[str],
    players: Counter[str],
) -> tuple[str, ...]:
    if not rows:
        return ()
    evidence = ", ".join(row.evidence_id for row in rows[:3])
    questions = [
        f"Does the repeated {restart_type.replace('_', ' ')} pattern create an assignment question? Supporting evidence: {evidence}.",
    ]
    common_zone, common_count = contacts.most_common(1)[0] if contacts else ("not observed", 0)
    if common_count >= 2 and common_zone != "not observed":
        questions.append(
            f"Is the recorded first-contact concentration in {common_zone} visible enough to review? Supporting evidence: {evidence}."
        )
    common_player, player_count = players.most_common(1)[0] if players else ("", 0)
    if player_count >= 2:
        questions.append(
            f"Who should review the recurring recorded involvement of {common_player}? Supporting evidence: {evidence}."
        )
    return tuple(questions[:3])


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
