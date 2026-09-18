import pytest

from signalroom.adapters.statsbomb import BASE_URL, SOURCE_REVISION
from signalroom.config import CaseConfig


def test_two_cases_are_configuration_only():
    brighton = CaseConfig.from_toml("configs/brighton_wsl_2023_24.toml")
    leverkusen = CaseConfig.from_toml("configs/leverkusen_bundesliga_2023_24.toml")
    assert brighton.team != leverkusen.team
    assert brighton.competition_id != leverkusen.competition_id
    assert brighton.__class__ is leverkusen.__class__


def test_data_acquisition_is_pinned_to_reviewed_revision():
    assert SOURCE_REVISION in BASE_URL
    assert "/master/" not in BASE_URL


def test_config_rejects_path_like_slug():
    with pytest.raises(ValueError, match="slug"):
        CaseConfig(
            slug="../../outside",
            team="Example FC",
            competition_id=1,
            season_id=1,
            competition_label="Test",
            season_label="2024",
        )


def test_config_enforces_declared_minimum_windows():
    with pytest.raises(ValueError, match="minimum_baseline"):
        CaseConfig(
            slug="test",
            team="Example FC",
            competition_id=1,
            season_id=1,
            competition_label="Test",
            season_label="2024",
            baseline_matches=4,
            minimum_baseline_matches=8,
        )
