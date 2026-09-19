from signalroom.reporting import preparation_brief_html


def test_briefing_export_is_deterministic_and_matches_selected_state():
    bundle = {
        "case": {
            "team": "Example FC",
            "competition": "Test League",
            "season": "2024",
            "historical_cutoff": "2024-05-01",
        },
        "data": {"limitations": ["Historical only"]},
    }
    comparison = {
        "delivery_group": "left / direct / central box lane",
        "review_eligible": True,
        "recent_count": 6,
        "recent_total": 10,
        "reference_count": 2,
        "reference_total": 10,
        "share_difference": 0.4,
        "ci_low": 0.1,
        "ci_high": 0.7,
        "recent_match_support": 4,
        "reference_match_support": 2,
        "evidence_ids": ["DB-1-2"],
    }
    first = preparation_brief_html(bundle, [comparison], "preceding window", 6, 5, "Check video")
    second = preparation_brief_html(bundle, [comparison], "preceding window", 6, 5, "Check video")
    assert first == second
    assert "DB-1-2" in first
    assert "Check video" in first
    assert "match-block" in first
