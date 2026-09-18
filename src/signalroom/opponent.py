from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import asdict, dataclass, replace
from typing import Any

import numpy as np

from .models import EvidenceSequence


@dataclass(frozen=True)
class RoutineComparison:
    routine: str
    count: int
    baseline_count: int
    recent_share: float
    baseline_share: float
    absolute_share_difference: float
    relative_difference_pct: float | None
    ci_low: float
    ci_high: float
    total_shots: int
    shot_producing_sequences: int
    sequence_conversion: float | None
    total_xg: float | None
    sample_size: int
    baseline_sample_size: int
    completeness: dict[str, Any]
    stability: str
    publish: bool
    suppression_reasons: tuple[str, ...]
    evidence_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["suppression_reasons"] = list(self.suppression_reasons)
        value["evidence_ids"] = list(self.evidence_ids)
        return value


def routine_label(sequence: EvidenceSequence, dimensions: Iterable[str]) -> str:
    parts = sequence.label.split(" / ")
    names = {"side": 0, "type": 1, "zone": 2}
    selected = [parts[names[item]] for item in dimensions if item in names]
    return " / ".join(selected) if selected else "all attacking corners"


def compare_routines(
    sequences: list[EvidenceSequence],
    match_dates: dict[int, str],
    recent_matches: list[int],
    baseline_matches: list[int],
    dimensions: tuple[str, ...] = ("side", "type", "zone"),
    minimum_sample: int = 4,
    minimum_completeness: float = 0.90,
    seed: int = 42,
    bootstrap_samples: int = 1000,
) -> list[RoutineComparison]:
    recent = [row for row in sequences if row.match_id in recent_matches]
    baseline = [row for row in sequences if row.match_id in baseline_matches]
    groups = sorted({routine_label(row, dimensions) for row in recent + baseline})
    output: list[RoutineComparison] = []
    for index, group in enumerate(groups):
        current = [row for row in recent if routine_label(row, dimensions) == group]
        before = [row for row in baseline if routine_label(row, dimensions) == group]
        comparison = _compare_group(
            group,
            current,
            before,
            len(recent),
            len(baseline),
            len(recent),
            len(baseline),
            minimum_sample,
            minimum_completeness,
            seed + index,
            bootstrap_samples,
        )
        checks: list[float] = []
        ordered_ids = sorted(match_dates, key=lambda match_id: (match_dates[match_id], match_id))
        recent_end = max((ordered_ids.index(match_id) for match_id in recent_matches), default=-1) + 1
        for window in sorted({max(2, len(recent_matches) - 1), len(recent_matches), len(recent_matches) + 1}):
            if recent_end < window:
                continue
            alt_recent = ordered_ids[recent_end - window : recent_end]
            alt_baseline = ordered_ids[max(0, recent_end - window - len(baseline_matches)) : recent_end - window]
            current_alt = [row for row in sequences if row.match_id in alt_recent and routine_label(row, dimensions) == group]
            before_alt = [row for row in sequences if row.match_id in alt_baseline and routine_label(row, dimensions) == group]
            total_alt = len([row for row in sequences if row.match_id in alt_recent])
            total_before_alt = len([row for row in sequences if row.match_id in alt_baseline])
            checks.append((len(current_alt) / total_alt if total_alt else 0.0) - (len(before_alt) / total_before_alt if total_before_alt else 0.0))
        comparison = replace(comparison, stability=classify_stability(checks))
        output.append(comparison)
    return sorted(output, key=lambda row: (row.publish, abs(row.absolute_share_difference), row.count), reverse=True)


def _compare_group(
    group: str,
    current: list[EvidenceSequence],
    before: list[EvidenceSequence],
    recent_match_count: int,
    baseline_match_count: int,
    recent_corner_total: int,
    baseline_corner_total: int,
    minimum_sample: int,
    minimum_completeness: float,
    seed: int,
    bootstrap_samples: int,
) -> RoutineComparison:
    recent_total = recent_corner_total
    before_total = baseline_corner_total
    recent_share = len(current) / recent_total if recent_total else 0.0
    baseline_share = len(before) / before_total if before_total else 0.0
    difference = recent_share - baseline_share
    rng = np.random.default_rng(seed)
    bootstrap = _bootstrap_share_difference(len(current), recent_total, len(before), before_total, bootstrap_samples, rng)
    ci_low, ci_high = np.quantile(bootstrap, [0.025, 0.975]) if len(bootstrap) else (difference, difference)
    completeness = _completeness(current, before)
    total_shots = sum(_sequence_stats(row)[0] for row in current)
    shot_sequences = sum(_sequence_stats(row)[1] for row in current)
    xg_values = [_sequence_stats(row)[2] for row in current]
    total_xg = sum(xg_values) if all(value is not None for value in xg_values) else None
    reasons: list[str] = []
    if len(current) < minimum_sample:
        reasons.append(f"sample too small: {len(current)} recent corners, minimum {minimum_sample}")
    if completeness["routine_share"] < minimum_completeness:
        reasons.append("routine share completeness below threshold")
    if completeness["shot_xg"] < minimum_completeness:
        reasons.append("shot xG incomplete, so xG is suppressed")
    if recent_total == 0 or before_total == 0:
        reasons.append("insufficient window corners")
    publish = not any(reason for reason in reasons if "xG" not in reason)
    stability = "sample too small" if len(current) < minimum_sample else "directionally consistent"
    relative = None if abs(baseline_share) < 1e-12 else difference / baseline_share * 100
    return RoutineComparison(
        routine=group,
        count=len(current),
        baseline_count=len(before),
        recent_share=recent_share,
        baseline_share=baseline_share,
        absolute_share_difference=difference,
        relative_difference_pct=relative,
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        total_shots=total_shots,
        shot_producing_sequences=shot_sequences,
        sequence_conversion=shot_sequences / len(current) if current else None,
        total_xg=total_xg,
        sample_size=len(current),
        baseline_sample_size=len(before),
        completeness=completeness,
        stability=stability,
        publish=publish,
        suppression_reasons=tuple(reasons),
        evidence_ids=tuple(row.evidence_id for row in current[:5]),
    )


def _bootstrap_share_difference(group_recent: int, total_recent: int, group_before: int, total_before: int, samples: int, rng: np.random.Generator) -> np.ndarray:
    if not total_recent or not total_before:
        return np.array([], dtype=float)
    recent = rng.binomial(total_recent, group_recent / total_recent, size=samples) / total_recent
    before = rng.binomial(total_before, group_before / total_before, size=samples) / total_before
    return recent - before


def _sequence_stats(sequence: EvidenceSequence) -> tuple[int, int, float | None]:
    shots = [event for event in sequence.events if event.get("type") == "Shot"]
    xg = [event.get("xg") for event in shots]
    return len(shots), int(bool(shots)), sum(float(value) for value in xg) if all(value is not None for value in xg) else None


def _completeness(current: list[EvidenceSequence], before: list[EvidenceSequence]) -> dict[str, Any]:
    rows = current + before
    if not rows:
        return {"routine_share": 0.0, "shot_xg": 0.0, "locations": 0.0, "movement_endpoints": 0.0}
    def rate(key: str, default: bool = False) -> float:
        return sum(bool(row.quality.get(key, default)) for row in rows) / len(rows)
    return {
        "routine_share": rate("corner_length_available", True),
        "shot_xg": rate("shot_xg_complete", True),
        "locations": rate("locations_complete", True),
        "movement_endpoints": rate("movement_endpoints_complete", True),
    }


def classify_stability(values: list[float], minimum: float = 0.05) -> str:
    if len(values) < 2:
        return "sample too small"
    signs = [math.copysign(1, value) for value in values if abs(value) >= minimum]
    if not signs:
        return "no material difference"
    if len(set(signs)) == 1:
        return "stable" if len(signs) == len(values) else "directionally consistent"
    return "sensitive to window selection"
