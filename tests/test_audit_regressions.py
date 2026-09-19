import json
from pathlib import Path

import pytest

from signalroom.capabilities import capability_notice
from signalroom.coordinates import canonical_point, validate_canonical_point
from signalroom.models import EvidenceSequence
from signalroom.opponent import compare_routines
from signalroom.rights import RightsError, default_rights_manifest, validate_public_payload


def test_f03_f23_coordinate_transform_preserves_zero_and_rotates_opponent():
    own = canonical_point(0.0, 0.0, "Selected", "Selected")
    opponent = canonical_point(10.0, 20.0, "Opponent", "Selected")
    assert own.canonical == (0.0, 0.0)
    assert own.status == "observed"
    assert opponent.canonical == (110.0, 60.0)
    assert validate_canonical_point(opponent.canonical)


def test_f18_snapshot_capability_does_not_claim_runs():
    snapshot = capability_notice("event_360")
    assert "event-linked position snapshots" in snapshot["supports"]
    assert "continuous runs" in snapshot["cannot_verify"]


def test_f24_rights_gate_blocks_source_records_and_ids():
    rights = default_rights_manifest()
    with pytest.raises(RightsError):
        rights.require_public_artifact("source_event_id")
    assert validate_public_payload({"evidence": [{"source_event_ids": ["abc"]}]})


def test_f16_missing_quality_never_defaults_to_complete():
    row = EvidenceSequence(
        evidence_id="DB-1",
        match_id=1,
        match_date="2024-01-01",
        opponent="Opponent",
        start_event_id="source",
        source_event_ids=("source",),
        label="left / direct / central box lane",
        start_minute=1,
        events=({"type": "Pass", "xg": None},),
        quality={},
    )
    comparison = compare_routines(
        [row],
        {1: "2024-01-01"},
        [1],
        [],
        minimum_sample=1,
        bootstrap_samples=100,
    )[0]
    assert comparison.completeness["delivery_group"] == 0.0
    assert comparison.review_eligible is False


def test_f01_f15_generated_evidence_resolves_and_exports_no_source_ids():
    for path in Path("artifacts/cases").glob("*/bundle.json"):
        bundle = json.loads(path.read_text(encoding="utf-8"))
        known = {row["evidence_id"] for row in bundle["evidence"]}
        referenced = {
            evidence_id
            for group in bundle["set_piece_lab"]["delivery_groups"]
            for evidence_id in group["evidence_ids"]
        }
        assert referenced <= known
        assert "source_event_ids" not in path.read_text(encoding="utf-8")


def test_f06_generated_roles_are_explicit_not_mixed_participant_sets():
    for path in Path("artifacts/cases").glob("*/bundle.json"):
        bundle = json.loads(path.read_text(encoding="utf-8"))
        for row in bundle["evidence"]:
            assert "participants" not in row
            assert set(row["player_roles"]) == {
                "taker",
                "intended_recipient",
                "first_post_delivery_actor",
                "first_post_delivery_actor_team",
                "shot_actors",
                "later_selected_team_participants",
            }

