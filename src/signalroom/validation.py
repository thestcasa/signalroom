from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .models import Event, Match


class ContractError(ValueError):
    """Raised when source data cannot satisfy the internal contract."""


@dataclass(frozen=True)
class ValidationSummary:
    matches: int
    events: int
    missing_locations: int
    missing_move_end_locations: int
    shots_missing_xg: int
    corners_missing_length: int
    duplicate_event_ids: int


def validate_dataset(matches: Iterable[Match], events: Iterable[Event]) -> ValidationSummary:
    match_list = list(matches)
    event_list = list(events)
    if not match_list:
        raise ContractError("No matches were loaded")
    if not event_list:
        raise ContractError("No events were loaded")
    known = {m.match_id for m in match_list}
    unknown = {e.match_id for e in event_list} - known
    if unknown:
        raise ContractError(f"Events reference unknown matches: {sorted(unknown)}")
    covered = {e.match_id for e in event_list}
    missing_matches = known - covered
    if missing_matches:
        raise ContractError(f"Matches have no events: {sorted(missing_matches)}")
    identifiers = [e.event_id for e in event_list]
    duplicates = len(identifiers) - len(set(identifiers))
    if duplicates:
        raise ContractError(f"Duplicate event IDs found: {duplicates}")
    ordered: dict[tuple[int, int], int] = {}
    for event in event_list:
        key = (event.match_id, event.period)
        if event.index < ordered.get(key, -1):
            raise ContractError(f"Non-monotonic event order in match {event.match_id}")
        ordered[key] = event.index
    return ValidationSummary(
        matches=len(match_list),
        events=len(event_list),
        missing_locations=sum(e.x is None for e in event_list),
        missing_move_end_locations=sum(
            e.event_type in {"Pass", "Carry"} and (e.end_x is None or e.end_y is None)
            for e in event_list
        ),
        shots_missing_xg=sum(e.event_type == "Shot" and e.xg is None for e in event_list),
        corners_missing_length=sum(
            e.event_type == "Pass"
            and e.subtype == "Corner"
            and (e.raw.get("pass") or {}).get("length") is None
            for e in event_list
        ),
        duplicate_event_ids=duplicates,
    )
