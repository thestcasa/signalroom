import json

from signalroom.reporting import preparation_brief_html


def test_briefing_export_is_deterministic_and_grounded():
    bundle = {
        "case": {"team": "Example FC", "competition": "Test League", "season": "2024"},
        "data": {"source_revision": "abc", "limitations": ["Historical only"]},
    }
    comparison = {
        "routine": "left / direct",
        "publish": True,
        "recent_share": 0.6,
        "baseline_share": 0.2,
        "absolute_share_difference": 0.4,
        "sample_size": 6,
        "baseline_sample_size": 5,
        "stability": "stable",
        "evidence_ids": ["SP-1-2"],
    }
    first = preparation_brief_html(bundle, [comparison], "previous team window", 6, 5)
    second = preparation_brief_html(bundle, [comparison], "previous team window", 6, 5)
    assert first == second
    assert "SP-1-2" in first
    json.loads(json.dumps(bundle, allow_nan=False))
