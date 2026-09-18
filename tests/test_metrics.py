from signalroom.metrics import calculate_match_metrics
from signalroom.models import Match


def test_metric_boundaries_and_completion(event_factory):
    match = Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")
    events = [
        event_factory("progress", x=60, end_x=80),
        event_factory("incomplete", index=2, x=60, end_x=90, outcome="Incomplete"),
        event_factory("box", index=3, x=90, y=10, end_x=103, end_y=30),
        event_factory("shot", index=4, event_type="Shot", x=105, end_x=None, xg=0.2),
        event_factory("regain", index=5, event_type="Ball Recovery", x=81, end_x=None),
    ]
    frame, evidence = calculate_match_metrics([match], events, "Example FC")
    row = frame.iloc[0]
    assert row["final_third_entries"] == 1
    assert row["progressive_actions"] == 1
    assert row["box_entries"] == 1
    assert row["shots"] == 1
    assert row["xg"] == 0.2
    assert row["high_regains"] == 1
    assert "incomplete" not in evidence[(1, "progressive_actions")]


def test_other_team_is_excluded(event_factory):
    match = Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")
    events = [event_factory("own"), event_factory("other", index=2, team="Opponent")]
    frame, _ = calculate_match_metrics([match], events, "Example FC")
    assert frame.iloc[0]["progressive_actions"] == 1
