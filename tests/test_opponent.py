from signalroom.models import EvidenceSequence
from signalroom.opponent import classify_stability, compare_routines


def _sequence(index: int, match_id: int, label: str, shot: bool = False) -> EvidenceSequence:
    events = [{"event_id": f"c{index}", "type": "Pass", "team": "Team", "xg": None}]
    if shot:
        events.append({"event_id": f"s{index}", "type": "Shot", "team": "Team", "xg": 0.2})
    return EvidenceSequence(
        evidence_id=f"SP-{index}",
        match_id=match_id,
        match_date=f"2024-01-{match_id:02d}",
        opponent="Opponent",
        start_event_id=f"c{index}",
        source_event_ids=tuple(event["event_id"] for event in events),
        label=label,
        start_minute=1,
        events=tuple(events),
        quality={
            "corner_length_available": True,
            "locations_complete": True,
            "movement_endpoints_complete": True,
            "shot_xg_complete": True,
        },
    )


def test_routine_comparison_uses_window_corner_denominator_and_evidence():
    sequences = [_sequence(index, match_id, "left / direct / central") for index, match_id in enumerate(range(1, 5))]
    sequences += [_sequence(10 + index, match_id, "right / direct / far", shot=True) for index, match_id in enumerate(range(5, 9))]
    result = compare_routines(
        sequences,
        {match_id: f"2024-01-{match_id:02d}" for match_id in range(1, 9)},
        recent_matches=[5, 6, 7, 8],
        baseline_matches=[1, 2, 3, 4],
        minimum_sample=2,
        bootstrap_samples=200,
    )
    right = next(row for row in result if row.routine.startswith("right"))
    assert right.recent_share == 1.0
    assert right.baseline_share == 0.0
    assert right.sequence_conversion == 1.0
    assert right.evidence_ids == ("SP-10", "SP-11", "SP-12", "SP-13")


def test_small_samples_are_suppressed_with_explicit_reason():
    result = compare_routines(
        [_sequence(1, 1, "left / direct / central")],
        {1: "2024-01-01"},
        [1],
        [],
        minimum_sample=2,
        bootstrap_samples=100,
    )
    assert result[0].publish is False
    assert "sample too small" in result[0].suppression_reasons[0]


def test_stability_labels_are_understandable():
    assert classify_stability([0.1, 0.12, 0.08]) == "stable"
    assert classify_stability([0.1, -0.12]) == "sensitive to window selection"
    assert classify_stability([0.01, 0.02]) == "no material difference"
