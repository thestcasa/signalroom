import pandas as pd

from signalroom.config import CaseConfig
from signalroom.statistics import compare_windows


def _config() -> CaseConfig:
    return CaseConfig(
        slug="test",
        team="Example FC",
        competition_id=1,
        season_id=1,
        competition_label="Test",
        season_label="2024",
        baseline_matches=10,
        recent_matches=6,
        minimum_baseline_matches=8,
        minimum_recent_matches=5,
        bootstrap_samples=400,
        random_seed=9,
    )


def test_temporal_windows_do_not_use_future_rows():
    rows = []
    for index in range(20):
        value = 2 if index < 14 else 12
        rows.append(
            {
                "date": f"2024-01-{index + 1:02d}",
                "match_id": index,
                "shots": value,
                "xg": value,
                "final_third_entries": value,
                "box_entries": value,
                "progressive_actions": value,
                "build_up_exits": value,
                "high_regains": value,
            }
        )
    comparisons = compare_windows(pd.DataFrame(rows), _config())
    assert all(item.baseline_value == 2 for item in comparisons)
    assert all(item.recent_value == 12 for item in comparisons)


def test_negligible_changes_are_suppressed():
    rows = []
    for index in range(20):
        rows.append(
            {
                "date": f"2024-01-{index + 1:02d}",
                "match_id": index,
                **{
                    key: 5 + (index % 2)
                    for key in [
                        "shots",
                        "xg",
                        "final_third_entries",
                        "box_entries",
                        "progressive_actions",
                        "build_up_exits",
                        "high_regains",
                    ]
                },
            }
        )
    comparisons = compare_windows(pd.DataFrame(rows), _config())
    assert not any(item.publish for item in comparisons)
