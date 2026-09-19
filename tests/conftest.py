from __future__ import annotations

from copy import deepcopy

import pytest

from signalroom.models import Event, Match


@pytest.fixture
def matches() -> list[Match]:
    return [
        Match(index, f"2024-01-{index:02d}", "Example FC", "Opponent", "Test", "2024")
        for index in range(1, 21)
    ]


def make_event(
    event_id: str,
    match_id: int = 1,
    index: int = 1,
    event_type: str = "Pass",
    team: str = "Example FC",
    possession: int = 1,
    x: float | None = 30,
    y: float | None = 40,
    end_x: float | None = 60,
    end_y: float | None = 40,
    outcome: str | None = None,
    subtype: str | None = None,
    xg: float | None = None,
    pass_length: float | None = 30.0,
    timestamp: str = "00:01:00.000",
) -> Event:
    raw = {
        "id": event_id,
        "index": index,
        "period": 1,
        "timestamp": timestamp,
        "minute": 1,
        "second": index,
        "type": {"name": event_type},
        "team": {"name": team},
        "possession": possession,
        "possession_team": {"name": team},
        "play_pattern": {"name": "Regular Play"},
    }
    if event_type == "Pass":
        raw["pass"] = {"end_location": [end_x, end_y], "length": pass_length}
        if subtype:
            raw["pass"]["type"] = {"name": subtype}
    return Event(
        event_id=event_id,
        match_id=match_id,
        index=index,
        period=1,
        timestamp=timestamp,
        minute=1,
        second=index,
        team=team,
        player="Player",
        event_type=event_type,
        possession=possession,
        possession_team=team,
        play_pattern="Regular Play",
        x=x,
        y=y,
        end_x=end_x,
        end_y=end_y,
        outcome=outcome,
        subtype=subtype,
        xg=xg,
        raw=deepcopy(raw),
        pass_length=pass_length if event_type == "Pass" else None,
        shot_outcome=outcome if event_type == "Shot" else None,
    )


@pytest.fixture
def event_factory():
    return make_event
