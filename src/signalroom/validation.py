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
    duplicate_event_ids: int


def validate_dataset(matches: Iterable[Match], events: Iterable[Event]) -> ValidationSummary:
    match_list = list(matches)
    event_list = list(events)
    if not match_list:
        raise ContractError("No matches were loaded")
    known = {m.match_id for m in match_list}
    unknown = {e.match_id for e in event_list} - known
    if unknown:
        raise ContractError(f"Events reference unknown matches: {sorted(unknown)}")
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
        duplicate_event_ids=duplicates,
    )
