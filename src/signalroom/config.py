from __future__ import annotations

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

    @classmethod
    def from_toml(cls, path: str | Path) -> CaseConfig:
        with Path(path).open("rb") as handle:
            return cls(**tomllib.load(handle))
