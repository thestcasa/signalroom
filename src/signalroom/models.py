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
    provider: str = "statsbomb-open-data"
    competition_id: int | None = None
    season_id: int | None = None
    home_team_id: int | None = None
    away_team_id: int | None = None

    @property
    def uid(self) -> str:
        return f"{self.provider}:match:{self.match_id}"


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
    player_id: int | None = None
    team_id: int | None = None
    recipient: str | None = None
    pass_length: float | None = None
    recipient_id: int | None = None
    body_part: str | None = None
    technique: str | None = None
    pass_height: str | None = None
    shot_outcome: str | None = None
    related_event_ids: tuple[str, ...] = ()
    source_payload_ref: str | None = None
    provider: str = "statsbomb-open-data"

    @property
    def uid(self) -> str:
        return f"{self.provider}:event:{self.event_id}"

    @property
    def player_uid(self) -> str | None:
        return f"{self.provider}:player:{self.player_id}" if self.player_id is not None else None

    @property
    def team_uid(self) -> str | None:
        return f"{self.provider}:team:{self.team_id}" if self.team_id is not None else None


@dataclass(frozen=True)
class LineupEntry:
    match_id: int
    team: str
    team_id: int
    player: str
    player_id: int
    positions: tuple[str, ...]
    started: bool
    recorded_minutes: float | None
    source_payload_ref: str
    provider: str = "statsbomb-open-data"

    @property
    def player_uid(self) -> str:
        return f"{self.provider}:player:{self.player_id}"


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
    evidence_status: str = "available"
    rights_class: str = "derived-sequence-summary"
    predicate: str | None = None
    termination_reason: str = "unknown"
    censoring_reason: str | None = None
    player_roles: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["source_event_ids"] = list(self.source_event_ids)
        value["events"] = list(self.events)
        return value


@dataclass(frozen=True)
class DeadBallSequence:
    """Provider-neutral evidence contract for a recorded attacking restart."""

    evidence_id: str
    match_id: int
    match_date: str
    opponent: str
    period: int
    timestamp: str
    restart_type: str
    start_event_id: str
    source_event_ids: tuple[str, ...]
    ordered_events: tuple[dict[str, Any], ...]
    delivery: dict[str, Any]
    first_post_delivery: dict[str, Any] | None
    player_roles: dict[str, Any]
    shot_outcome: dict[str, Any]
    termination_reason: str
    censoring_reason: str | None
    data_quality: dict[str, Any]
    source_revision: str
    capability_level: str = "event"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["source_event_ids"] = list(self.source_event_ids)
        value["ordered_events"] = list(self.ordered_events)
        return value
