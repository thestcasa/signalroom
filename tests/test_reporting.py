from signalroom.reporting import validate_grounded_bundle


def _bundle():
    return {
        "schema_version": "2.0.0",
        "case": {"historical_only": True},
        "data": {"coverage": {"complete": True}},
        "peer_baseline": {"status": "suppressed"},
        "set_piece_lab": {"delivery_groups": []},
        "dead_ball_lab": {"summaries": []},
        "evidence": [{"evidence_id": "DB-1", "evidence_status": "available-derived-summary"}],
    }


def test_grounded_report_accepts_rights_safe_schema():
    assert validate_grounded_bundle(_bundle()) == []


def test_grounded_report_rejects_source_event_ids():
    bundle = _bundle()
    bundle["evidence"][0]["source_event_ids"] = ["provider-id"]
    assert any("source event IDs" in error for error in validate_grounded_bundle(bundle))
