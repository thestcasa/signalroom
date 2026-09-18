import json
from pathlib import Path

from signalroom.reporting import validate_grounded_bundle

CASE_ROOT = Path("artifacts/cases")


def test_two_real_case_bundles_are_grounded_and_portable():
    bundles = []
    for path in sorted(CASE_ROOT.glob("*/bundle.json")):
        bundle = json.loads(path.read_text(encoding="utf-8"))
        assert validate_grounded_bundle(bundle) == []
        assert bundle["set_piece_lab"]["corner_count"] > 0
        assert bundle["case"]["historical_only"] is True
        assert (path.parent / "report.html").exists()
        assert (path.parent / "assets" / "statsbomb-open-data-logo.png").exists()
        bundles.append(bundle)
    assert len(bundles) == 2
    assert len({bundle["data"]["competition_id"] for bundle in bundles}) == 2


def test_brighton_abstention_and_set_piece_output_are_preserved():
    path = CASE_ROOT / "brighton-wsl-2023-24" / "bundle.json"
    bundle = json.loads(path.read_text(encoding="utf-8"))
    assert bundle["case"]["matches"] == 22
    assert bundle["set_piece_lab"]["corner_count"] == 92
    assert bundle["findings"] == []
    assert len(bundle["set_piece_lab"]["published_routines"]) == 4
