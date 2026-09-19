from signalroom.models import EvidenceSequence
from signalroom.opponent import classify_stability, compare_routines


def _sequence(index: int, match_id: int, label: str, shot: bool = False) -> EvidenceSequence:
    events = [{"type": "Pass", "team_role": "selected_team", "xg": None}]
    if shot:
        events.append({"type": "Shot", "team_role": "selected_team", "xg": 0.2})
    return EvidenceSequence(
        evidence_id=f"DB-{index}",
        match_id=match_id,
        match_date=f"2024-01-{match_id:02d}",
        opponent="Opponent",
        start_event_id=f"source-{index}",
        source_event_ids=(f"source-{index}",),
        label=label,
        start_minute=1,
        events=tuple(events),
        quality={
            "delivery_length": "observed",
            "locations": "observed",
            "movement_endpoints": "observed",
            "shot_xg": "observed" if shot else "not_applicable",
        },
    )


def test_delivery_comparison_uses_corner_denominators_match_blocks_and_resolvable_evidence():
    sequences = [
        _sequence(index, match_id, "left / direct / central box lane")
        for index, match_id in enumerate(range(1, 5))
    ]
    sequences += [
        _sequence(10 + index, match_id, "right / direct / right box lane", shot=True)
        for index, match_id in enumerate(range(5, 9))
    ]
    result = compare_routines(
        sequences,
        {match_id: f"2024-01-{match_id:02d}" for match_id in range(1, 9)},
        recent_matches=[5, 6, 7, 8],
        baseline_matches=[1, 2, 3, 4],
        minimum_sample=2,
        bootstrap_samples=200,
    )
    right = next(row for row in result if row.delivery_group.startswith("right"))
    assert right.recent_share == 1.0
    assert right.reference_share == 0.0
    assert right.shot_producing_rate == 1.0
    assert right.resampling_unit == "match"
    assert len(right.evidence_ids) == 4


def test_small_samples_are_suppressed_with_explicit_reason():
    result = compare_routines(
        [_sequence(1, 1, "left / direct / central box lane")],
        {1: "2024-01-01"},
        [1],
        [],
        minimum_sample=2,
        bootstrap_samples=100,
    )
    assert result[0].review_eligible is False
    assert "below minimum" in result[0].suppression_reasons[0]


def test_window_sensitivity_labels_do_not_claim_stability():
    assert classify_stability([0.1, 0.12, 0.08]) == "consistent direction"
    assert classify_stability([0.1, -0.12]) == "mixed direction"
    assert classify_stability([0.01, 0.02]) == "no material signal"
