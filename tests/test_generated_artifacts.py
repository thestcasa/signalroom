import json
from pathlib import Path

from signalroom.reporting import validate_grounded_bundle
from signalroom.rights import validate_public_payload

CASE_ROOT = Path("artifacts/cases")


def test_two_real_case_bundles_are_grounded_and_rights_safe():
    bundles = []
    for path in sorted(CASE_ROOT.glob("*/bundle.json")):
        bundle = json.loads(path.read_text(encoding="utf-8"))
        assert validate_grounded_bundle(bundle) == []
        assert validate_public_payload(bundle) == []
        assert bundle["schema_version"] == "2.0.0"
        assert bundle["case"]["historical_only"] is True
        assert bundle["capability"]["level"] == "event"
        assert bundle["set_piece_lab"]["corner_count"] > 0
        assert bundle["dead_ball_lab"]["sequence_count"] >= bundle["set_piece_lab"]["corner_count"]
        assert {row["restart_type"] for row in bundle["dead_ball_lab"]["summaries"]} == {
            "corner",
            "wide_final_third_free_kick_pass",
            "central_final_third_free_kick_pass",
            "direct_free_kick_shot",
        }
        assert (path.parent / "report.html").exists()
        assert (path.parent / "manual_review_sample.csv").exists()
        bundles.append(bundle)
    assert len(bundles) == 2


def test_brighton_has_complete_wsl_peer_population():
    path = CASE_ROOT / "brighton-wsl-2023-24" / "bundle.json"
    bundle = json.loads(path.read_text(encoding="utf-8"))
    assert bundle["data"]["coverage"]["received_fixtures"] == 132
    assert bundle["data"]["coverage"]["complete"] is True
    assert bundle["peer_baseline"]["status"] == "descriptive"
    assert bundle["peer_baseline"]["teams"] == 12
    assert bundle["peer_baseline"]["peer_teams"] == 11
