from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CaseConfig:
    slug: str
    team: str
    competition_id: int
    season_id: int
    competition_label: str
    season_label: str
    baseline_matches: int = 10
    recent_matches: int = 6
    minimum_baseline_matches: int = 8
    minimum_recent_matches: int = 5
    minimum_evidence_sequences: int = 3
    bootstrap_samples: int = 2000
    random_seed: int = 42

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", self.slug):
            raise ValueError("slug must contain lowercase letters, numbers, and single hyphens")
        if not self.team.strip() or not self.competition_label.strip() or not self.season_label.strip():
            raise ValueError("team, competition_label, and season_label must be non-empty")
        if self.competition_id <= 0 or self.season_id <= 0:
            raise ValueError("competition_id and season_id must be positive")
        if self.minimum_baseline_matches < 2 or self.minimum_recent_matches < 2:
            raise ValueError("minimum window sizes must be at least two matches")
        if self.baseline_matches < self.minimum_baseline_matches:
            raise ValueError("baseline_matches is below minimum_baseline_matches")
        if self.recent_matches < self.minimum_recent_matches:
            raise ValueError("recent_matches is below minimum_recent_matches")
        if self.minimum_evidence_sequences < 1:
            raise ValueError("minimum_evidence_sequences must be positive")
        if self.bootstrap_samples < 100:
            raise ValueError("bootstrap_samples must be at least 100")

    @classmethod
    def from_toml(cls, path: str | Path) -> CaseConfig:
        with Path(path).open("rb") as handle:
            return cls(**tomllib.load(handle))
