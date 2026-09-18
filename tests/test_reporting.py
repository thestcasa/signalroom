from signalroom.reporting import deterministic_finding_text, validate_grounded_bundle


def test_grounded_report_accepts_exact_structured_narrative():
    finding = {
        "metric": "shots",
        "label": "Shots",
        "absolute_change": 2.0,
        "baseline_value": 8.0,
        "recent_value": 10.0,
        "unit": "per match",
        "ci_low": 0.2,
        "ci_high": 3.8,
        "reliability": "moderate",
        "publish": True,
        "evidence_ids": ["EV-1", "EV-2", "EV-3"],
    }
    finding["narrative"] = deterministic_finding_text(finding)
    bundle = {
        "method": {"minimum_evidence_sequences": 3},
        "findings": [finding],
        "evidence": [{"evidence_id": value} for value in finding["evidence_ids"]],
        "set_piece_lab": {"published_routines": []},
    }
    assert validate_grounded_bundle(bundle) == []


def test_grounded_report_rejects_changed_number():
    finding = {
        "metric": "shots",
        "label": "Shots",
        "absolute_change": 2.0,
        "baseline_value": 8.0,
        "recent_value": 10.0,
        "unit": "per match",
        "ci_low": 0.2,
        "ci_high": 3.8,
        "reliability": "moderate",
        "publish": True,
        "evidence_ids": ["EV-1", "EV-2", "EV-3"],
        "narrative": "Shots increased from 8 to 99.",
    }
    bundle = {
        "method": {"minimum_evidence_sequences": 3},
        "findings": [finding],
        "evidence": [{"evidence_id": value} for value in finding["evidence_ids"]],
        "set_piece_lab": {"published_routines": []},
    }
    assert any("Narrative mismatch" in error for error in validate_grounded_bundle(bundle))
