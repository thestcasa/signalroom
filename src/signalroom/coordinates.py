from __future__ import annotations

from dataclasses import dataclass

from .models import Event

PITCH_LENGTH = 120.0
PITCH_WIDTH = 80.0
COORDINATE_VERSION = "statsbomb-selected-team-v1"


@dataclass(frozen=True)
class CoordinateObservation:
    source: tuple[float | None, float | None]
    canonical: tuple[float | None, float | None]
    orientation: str
    transform_version: str
    status: str


def canonical_point(
    x: float | None,
    y: float | None,
    actor_team: str,
    selected_team: str,
) -> CoordinateObservation:
    if x is None or y is None:
        return CoordinateObservation(
            source=(x, y),
            canonical=(None, None),
            orientation="selected-team-attacks-right",
            transform_version=COORDINATE_VERSION,
            status="missing",
        )
    if not 0.0 <= x <= PITCH_LENGTH or not 0.0 <= y <= PITCH_WIDTH:
        return CoordinateObservation(
            source=(x, y),
            canonical=(None, None),
            orientation="selected-team-attacks-right",
            transform_version=COORDINATE_VERSION,
            status="invalid",
        )
    canonical = (x, y) if actor_team == selected_team else (PITCH_LENGTH - x, PITCH_WIDTH - y)
    return CoordinateObservation(
        source=(x, y),
        canonical=canonical,
        orientation="selected-team-attacks-right",
        transform_version=COORDINATE_VERSION,
        status="observed",
    )


def event_coordinates(
    event: Event, selected_team: str, *, end: bool = False
) -> CoordinateObservation:
    return canonical_point(
        event.end_x if end else event.x,
        event.end_y if end else event.y,
        event.team,
        selected_team,
    )


def validate_canonical_point(point: tuple[float | None, float | None]) -> bool:
    x, y = point
    return (
        x is None
        and y is None
        or (
            x is not None and y is not None and 0.0 <= x <= PITCH_LENGTH and 0.0 <= y <= PITCH_WIDTH
        )
    )
