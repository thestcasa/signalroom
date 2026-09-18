from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np

from .deadballs import RESTART_TYPES
from .models import DeadBallSequence


def team_profile_features(sequences: list[DeadBallSequence], matches: int) -> dict[str, float]:
    total = len(sequences)
    shares = {f"share_{kind}": sum(row.restart_type == kind for row in sequences) / total if total else 0.0 for kind in RESTART_TYPES}
    lengths = [float(row.delivery["length"]) for row in sequences if row.delivery.get("length") is not None]
    second_phase = sum(bool(row.second_phase.get("observed")) for row in sequences) / total if total else 0.0
    shots = sum(int(row.shot_outcome.get("shot_count", 0)) > 0 for row in sequences) / total if total else 0.0
    routine_counts = Counter((row.restart_type, row.delivery.get("target_zone")) for row in sequences)
    hhi = sum((count / total) ** 2 for count in routine_counts.values()) if total else 0.0
    return {
        **shares,
        "mean_delivery_length": float(np.mean(lengths)) if lengths else 0.0,
        "second_phase_rate": second_phase,
        "shot_producing_rate": shots,
        "routine_concentration_hhi": hhi,
        "sequences_per_match": total / matches if matches else 0.0,
    }


def profile_publication(team_count: int, sequences: int, minimum_team_count: int = 5) -> dict[str, Any]:
    """Gate exploratory clustering until a real comparison sample exists."""
    if team_count < minimum_team_count:
        return {
            "status": "suppressed",
            "reason": f"coverage too small: {team_count} comparable teams, minimum {minimum_team_count}",
            "capability_level": "event",
            "interpretation": "No stable peer grouping is published.",
        }
    if sequences < 25:
        return {
            "status": "suppressed",
            "reason": "selected team has fewer than 25 supported sequences",
            "capability_level": "event",
            "interpretation": "No stable peer grouping is published.",
        }
    return {
        "status": "exploratory",
        "reason": "requires deterministic clustering and bootstrap stability review",
        "capability_level": "event",
        "interpretation": "Descriptive grouping only, pending peer feature matrix.",
    }
