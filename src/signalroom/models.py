from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Match:
    match_id: int
    date: str
    home_team: str
    away_team: str
    competition: str
    season: str


@dataclass(frozen=True)
class Event:
    event_id: str
    match_id: int
    index: int
    period: int
    timestamp: str
    minute: int
    second: int
    team: str
    player: str | None
    event_type: str
    possession: int
    possession_team: str
    play_pattern: str
    x: float | None
    y: float | None
    end_x: float | None
    end_y: float | None
    outcome: str | None
    subtype: str | None
    xg: float | None
    raw: dict[str, Any] = field(repr=False, compare=False)


@dataclass(frozen=True)
class EvidenceSequence:
    evidence_id: str
    match_id: int
    match_date: str
    opponent: str
    start_event_id: str
    source_event_ids: tuple[str, ...]
    label: str
    start_minute: int
    events: tuple[dict[str, Any], ...]
    quality: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["source_event_ids"] = list(self.source_event_ids)
        value["events"] = list(self.events)
        return value
