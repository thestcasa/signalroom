from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from .models import Event, Match

METRIC_VERSION = "1.0.0"


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    label: str
    unit: str
    description: str
    predicate: Callable[[Event], bool]
    value: Callable[[Event], float]


def _completed_action(event: Event) -> bool:
    return event.event_type == "Carry" or (event.event_type == "Pass" and event.outcome is None)


def _crosses(event: Event, threshold: float) -> bool:
    return (
        _completed_action(event)
        and event.x is not None
        and event.end_x is not None
        and event.x < threshold <= event.end_x
    )


METRICS: tuple[MetricDefinition, ...] = (
    MetricDefinition(
        "shots",
        "Shots",
        "per match",
        "Team shot events, including penalties.",
        lambda e: e.event_type == "Shot",
        lambda e: 1.0,
    ),
    MetricDefinition(
        "xg",
        "Expected goals",
        "xG per match",
        "Sum of StatsBomb shot xG for the team.",
        lambda e: e.event_type == "Shot" and e.xg is not None,
        lambda e: float(e.xg or 0.0),
    ),
    MetricDefinition(
        "final_third_entries",
        "Final-third entries",
        "per match",
        "Completed passes or carries crossing from x < 80 to x >= 80.",
        lambda e: _crosses(e, 80.0),
        lambda e: 1.0,
    ),
    MetricDefinition(
        "box_entries",
        "Box entries",
        "per match",
        "Completed passes or carries entering x >= 102 and 18 <= y <= 62.",
        lambda e: (
            _completed_action(e)
            and e.x is not None
            and e.y is not None
            and e.end_x is not None
            and e.end_y is not None
            and not (e.x >= 102 and 18 <= e.y <= 62)
            and e.end_x >= 102
            and 18 <= e.end_y <= 62
        ),
        lambda e: 1.0,
    ),
    MetricDefinition(
        "progressive_actions",
        "Progressive actions",
        "per match",
        "Completed passes or carries gaining at least 15 metres in x.",
        lambda e: (
            _completed_action(e) and e.x is not None and e.end_x is not None and e.end_x - e.x >= 15
        ),
        lambda e: 1.0,
    ),
    MetricDefinition(
        "build_up_exits",
        "Build-up exits",
        "per match",
        "Completed passes or carries starting at x <= 40 and ending at x >= 60.",
        lambda e: (
            _completed_action(e)
            and e.x is not None
            and e.end_x is not None
            and e.x <= 40
            and e.end_x >= 60
        ),
        lambda e: 1.0,
    ),
    MetricDefinition(
        "high_regains",
        "High regains",
        "per match",
        "Ball Recovery or Interception events recorded at x >= 80.",
        lambda e: (
            e.event_type in {"Ball Recovery", "Interception"} and e.x is not None and e.x >= 80
        ),
        lambda e: 1.0,
    ),
)


def calculate_match_metrics(
    matches: list[Match], events: list[Event], team: str
) -> tuple[pd.DataFrame, dict[tuple[int, str], list[str]]]:
    own_events = [event for event in events if event.team == team]
    by_match: dict[int, list[Event]] = {match.match_id: [] for match in matches}
    for event in own_events:
        by_match[event.match_id].append(event)
    evidence: dict[tuple[int, str], list[str]] = {}
    rows: list[dict[str, object]] = []
    for match in matches:
        opponent = match.away_team if match.home_team == team else match.home_team
        row: dict[str, object] = {
            "match_id": match.match_id,
            "date": match.date,
            "opponent": opponent,
            "venue": "home" if match.home_team == team else "away",
        }
        for metric in METRICS:
            selected = [event for event in by_match[match.match_id] if metric.predicate(event)]
            row[metric.key] = sum(metric.value(event) for event in selected)
            evidence[(match.match_id, metric.key)] = [event.event_id for event in selected]
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["date", "match_id"]).reset_index(drop=True), evidence
