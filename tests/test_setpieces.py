from signalroom.models import Match
from signalroom.setpieces import analyze_attacking_corners


def test_corner_sequence_stops_on_possession_change(event_factory):
    match = Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")
    events = [
        event_factory("corner", subtype="Corner", x=120, y=0, end_x=110, end_y=34),
        event_factory(
            "shot", index=2, event_type="Shot", x=108, end_x=None, xg=0.15, timestamp="00:01:05.000"
        ),
        event_factory("after", index=3, possession=2, timestamp="00:01:07.000"),
    ]
    routines, sequences = analyze_attacking_corners(
        [match], events, "Example FC", minimum_cluster=1
    )
    assert len(sequences) == 1
    assert sequences[0].source_event_ids == ("corner", "shot")
    assert routines[0].shots == 1
    assert routines[0].xg == 0.15


def test_small_routine_is_suppressed(event_factory):
    match = Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")
    events = [event_factory("corner", subtype="Corner", x=120, y=80, end_x=112, end_y=48)]
    routines, _ = analyze_attacking_corners([match], events, "Example FC", minimum_cluster=4)
    assert routines[0].publish is False
    assert "fewer than 4" in routines[0].reliability
