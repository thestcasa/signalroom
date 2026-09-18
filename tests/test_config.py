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
