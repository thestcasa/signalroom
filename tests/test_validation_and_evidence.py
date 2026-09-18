import pytest

from signalroom.evidence import build_metric_evidence, validate_evidence_references
from signalroom.models import Match
from signalroom.validation import ContractError, validate_dataset


def test_duplicate_event_ids_fail_contract(event_factory):
    match = Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")
    with pytest.raises(ContractError, match="Duplicate"):
        validate_dataset([match], [event_factory("same"), event_factory("same", index=2)])


def test_empty_event_dataset_fails_contract():
    match = Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")
    with pytest.raises(ContractError, match="No events"):
        validate_dataset([match], [])


def test_validation_reports_optional_metric_fields(event_factory):
    match = Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")
    shot = event_factory("shot", event_type="Shot", xg=None)
    move = event_factory("move", index=2, end_x=None, end_y=None)
    corner = event_factory("corner", index=3, subtype="Corner", pass_length=None)
    summary = validate_dataset([match], [shot, move, corner])
    assert summary.shots_missing_xg == 1
    assert summary.missing_move_end_locations == 1
    assert summary.corners_missing_length == 1


def test_evidence_is_traceable(event_factory):
    match = Match(1, "2024-01-01", "Example FC", "Opponent", "Test", "2024")
    events = [event_factory("a"), event_factory("b", index=2), event_factory("c", index=3)]
    sequences = build_metric_evidence(["b"], events, [match], "Example FC", "Test")
    assert sequences[0].start_event_id == "b"
    assert validate_evidence_references(sequences, events) == []
