from signalroom.models import Match
from signalroom.setpieces import analyze_attacking_corners


def test_corner_sequence_stops_at_shot(event_factory):
    match = Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")
    events = [
        event_factory("corner", subtype="Corner", x=120, y=0, end_x=110, end_y=34),
        event_factory(
            "shot",
            index=2,
            event_type="Shot",
            x=108,
            end_x=None,
            xg=0.15,
            timestamp="00:01:05.000",
        ),
        event_factory("after", index=3, possession=2, timestamp="00:01:07.000"),
    ]
    groups, sequences = analyze_attacking_corners([match], events, "Example FC", minimum_group=1)
    assert sequences[0].source_event_ids == ("corner", "shot")
    assert sequences[0].termination_reason == "shot"
    assert groups[0].shots == 1
    assert groups[0].xg == 0.15


def test_small_delivery_group_is_suppressed(event_factory):
    match = Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")
    events = [event_factory("corner", subtype="Corner", x=120, y=80, end_x=112, end_y=48)]
    groups, _ = analyze_attacking_corners([match], events, "Example FC", minimum_group=4)
    assert groups[0].display_eligible is False
    assert "fewer than four" in groups[0].status


def test_shot_rate_counts_sequences_not_rebound_shots(event_factory):
    match = Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")
    events = [
        event_factory("corner", subtype="Corner", pass_length=30),
        event_factory("shot-1", index=2, event_type="Shot", xg=0.1, timestamp="00:01:03.000"),
        event_factory("shot-2", index=3, event_type="Shot", xg=0.2, timestamp="00:01:06.000"),
    ]
    groups, _ = analyze_attacking_corners([match], events, "Example FC", minimum_group=1)
    assert groups[0].shots == 1
    assert groups[0].corners_with_shot == 1
    assert groups[0].shot_rate == 1.0


def test_long_delivery_is_not_classified_as_short_from_end_x(event_factory):
    match = Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")
    corner = event_factory(
        "corner", subtype="Corner", x=120, y=0, end_x=105, end_y=37, pass_length=40
    )
    groups, _ = analyze_attacking_corners([match], [corner], "Example FC", minimum_group=1)
    assert groups[0].delivery_type == "direct"
