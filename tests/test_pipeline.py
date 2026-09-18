from __future__ import annotations

from signalroom.adapters.statsbomb import StatsBombOpenDataAdapter
from signalroom.config import CaseConfig
from signalroom.models import Match
from signalroom.pipeline import build_case


def test_pipeline_build_is_deterministic_and_grounded(tmp_path, monkeypatch, event_factory):
    matches = [
        Match(index, f"2024-01-{index:02d}", "Example FC", "Opponent", "Test", "2024")
        for index in range(1, 17)
    ]
    events = []
    for match in matches:
        events.extend(
            [
                event_factory(
                    f"corner-{match.match_id}",
                    match_id=match.match_id,
                    subtype="Corner",
                    pass_length=30,
                ),
                event_factory(
                    f"shot-{match.match_id}",
                    match_id=match.match_id,
                    index=2,
                    event_type="Shot",
                    xg=0.1,
                    timestamp="00:01:05.000",
                ),
            ]
        )

    monkeypatch.setattr(
        StatsBombOpenDataAdapter,
        "load_case",
        lambda self, config: (matches, events),
    )
    config = CaseConfig(
        slug="test-case",
        team="Example FC",
        competition_id=1,
        season_id=1,
        competition_label="Test",
        season_label="2024",
        baseline_matches=8,
        recent_matches=5,
        minimum_baseline_matches=8,
        minimum_recent_matches=5,
        bootstrap_samples=100,
    )

    output = build_case(config, output_root=tmp_path / "output", cache_dir=tmp_path / "cache")
    first_bundle = (output / "bundle.json").read_bytes()
    first_report = (output / "report.html").read_bytes()
    build_case(config, output_root=tmp_path / "output", cache_dir=tmp_path / "cache")

    assert (output / "bundle.json").read_bytes() == first_bundle
    assert (output / "report.html").read_bytes() == first_report
    assert (output / "assets" / "metric_comparison.png").exists()
    assert (output / "assets" / "routine_shares.png").exists()
