from __future__ import annotations

from signalroom.deadballs import analyze_attacking_final_third_dead_balls, classify_restart
from signalroom.models import Event, Match


def _event(
    event_id: str,
    index: int,
    event_type: str,
    subtype: str | None,
    team: str = "Example FC",
    x: float = 90.0,
    y: float = 40.0,
    end_x: float | None = 108.0,
    end_y: float | None = 40.0,
    possession: int = 1,
    xg: float | None = None,
    outcome: str | None = None,
) -> Event:
    raw: dict = {
        "id": event_id,
        "pass": {"length": 24.0, "end_location": [end_x, end_y]} if event_type == "Pass" else {},
    }
    return Event(
        event_id=event_id,
        match_id=1,
        index=index,
        period=1,
        timestamp=f"00:01:{index:02d}.000",
        minute=1,
        second=index,
        team=team,
        player=f"Player {index}",
        event_type=event_type,
        possession=possession,
        possession_team=team,
        play_pattern="From Free Kick" if subtype == "Free Kick" else "From Corner",
        x=x,
        y=y,
        end_x=end_x,
        end_y=end_y,
        outcome=outcome,
        subtype=subtype,
        xg=xg,
        raw=raw,
        pass_length=24.0 if event_type == "Pass" else None,
    )


def test_restart_taxonomy_is_explicit_about_location_buckets():
    wide = _event("wide", 1, "Pass", "Free Kick", y=10.0)
    indirect = _event("indirect", 2, "Pass", "Free Kick", y=40.0)
    direct = _event("direct", 3, "Shot", "Free Kick", x=96.0, xg=0.04)
    assert classify_restart(wide, "Example FC") == "wide_free_kick"
    assert classify_restart(indirect, "Example FC") == "indirect_free_kick"
    assert classify_restart(direct, "Example FC") == "direct_free_kick"


def test_sequence_links_first_contact_second_phase_and_shot():
    matches = [Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")]
    events = [
        _event("restart", 1, "Pass", "Corner", x=120.0, y=5.0),
        _event("contact", 2, "Ball Receipt*", None, x=106.0, y=28.0),
        _event("recycle", 3, "Pass", None, x=105.0, y=35.0),
        _event("shot", 4, "Shot", "Open Play", x=110.0, y=38.0, xg=0.08),
    ]
    summaries, sequences = analyze_attacking_final_third_dead_balls(matches, events, "Example FC", "rev")
    assert len(sequences) == 1
    assert sequences[0].first_contact["zone"] == "goalmouth"
    assert sequences[0].second_phase["recycle_count"] == 1
    assert sequences[0].shot_outcome["total_xg"] == 0.08
    assert summaries[0].restart_type == "corner"
    assert summaries[0].shot_producing_sequences == 1
    assert summaries[0].repetition_matches == 1
