from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import asdict, dataclass, replace
from typing import Any

import numpy as np

from .models import EvidenceSequence


@dataclass(frozen=True)
class DeliveryGroupComparison:
    delivery_group: str
    recent_count: int
    reference_count: int
    recent_share: float
    reference_share: float
    share_difference: float
    relative_difference_pct: float | None
    ci_low: float
    ci_high: float
    resampling_unit: str
    recent_total: int
    reference_total: int
    recent_match_support: int
    reference_match_support: int
    total_shots: int
    shot_producing_sequences: int
    shot_producing_rate: float | None
    total_xg: float | None
    completeness: dict[str, Any]
    window_sensitivity: str
    review_eligible: bool
    suppression_reasons: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    reference_evidence_ids: tuple[str, ...]
    counterexample_evidence_ids: tuple[str, ...]

    @property
    def publish(self) -> bool:
        """Compatibility alias. UI language uses review eligibility, not publication."""
        return self.review_eligible

    @property
    def routine(self) -> str:
        return self.delivery_group

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for key in (
            "suppression_reasons",
            "evidence_ids",
            "reference_evidence_ids",
            "counterexample_evidence_ids",
        ):
            value[key] = list(value[key])
        return value


RoutineComparison = DeliveryGroupComparison


def delivery_group_label(sequence: EvidenceSequence, dimensions: Iterable[str]) -> str:
    parts = sequence.label.split(" / ")
    names = {"side": 0, "type": 1, "lane": 2, "zone": 2}
    selected = [
        parts[names[item]] for item in dimensions if item in names and len(parts) > names[item]
    ]
    return " / ".join(selected) if selected else "all recorded attacking corners"


routine_label = delivery_group_label


def compare_routines(
    sequences: list[EvidenceSequence],
    match_dates: dict[int, str],
    recent_matches: list[int],
    baseline_matches: list[int],
    dimensions: tuple[str, ...] = ("side", "type", "lane"),
    minimum_sample: int = 4,
    minimum_completeness: float = 0.90,
    minimum_effect: float = 0.05,
    seed: int = 42,
    bootstrap_samples: int = 1000,
) -> list[DeliveryGroupComparison]:
    recent = [row for row in sequences if row.match_id in recent_matches]
    reference = [row for row in sequences if row.match_id in baseline_matches]
    groups = sorted({delivery_group_label(row, dimensions) for row in recent + reference})
    output: list[DeliveryGroupComparison] = []
    for index, group in enumerate(groups):
        current = [row for row in recent if delivery_group_label(row, dimensions) == group]
        before = [row for row in reference if delivery_group_label(row, dimensions) == group]
        counterexamples = [row for row in recent if delivery_group_label(row, dimensions) != group]
        comparison = _compare_group(
            group=group,
            current=current,
            before=before,
            recent_all=recent,
            reference_all=reference,
            recent_matches=recent_matches,
            reference_matches=baseline_matches,
            counterexamples=counterexamples,
            minimum_sample=minimum_sample,
            minimum_completeness=minimum_completeness,
            minimum_effect=minimum_effect,
            seed=seed + index,
            bootstrap_samples=bootstrap_samples,
        )
        checks = _window_checks(
            sequences,
            match_dates,
            recent_matches,
            baseline_matches,
            dimensions,
            group,
        )
        sensitivity = classify_stability(checks, minimum_effect)
        reasons = list(comparison.suppression_reasons)
        if sensitivity in {"mixed direction", "insufficient nearby windows"}:
            reasons.append(f"window sensitivity: {sensitivity}")
        eligible = comparison.review_eligible and sensitivity == "consistent direction"
        output.append(
            replace(
                comparison,
                window_sensitivity=sensitivity,
                review_eligible=eligible,
                suppression_reasons=tuple(dict.fromkeys(reasons)),
            )
        )
    return sorted(
        output,
        key=lambda row: (row.review_eligible, abs(row.share_difference), row.recent_count),
        reverse=True,
    )


def _compare_group(
    *,
    group: str,
    current: list[EvidenceSequence],
    before: list[EvidenceSequence],
    recent_all: list[EvidenceSequence],
    reference_all: list[EvidenceSequence],
    recent_matches: list[int],
    reference_matches: list[int],
    counterexamples: list[EvidenceSequence],
    minimum_sample: int,
    minimum_completeness: float,
    minimum_effect: float,
    seed: int,
    bootstrap_samples: int,
) -> DeliveryGroupComparison:
    recent_total = len(recent_all)
    reference_total = len(reference_all)
    recent_share = len(current) / recent_total if recent_total else 0.0
    reference_share = len(before) / reference_total if reference_total else 0.0
    difference = recent_share - reference_share
    rng = np.random.default_rng(seed)
    bootstrap = _match_block_share_difference(
        recent_all,
        reference_all,
        current,
        before,
        recent_matches,
        reference_matches,
        bootstrap_samples,
        rng,
    )
    ci_low, ci_high = (
        np.quantile(bootstrap, [0.025, 0.975]) if len(bootstrap) else (difference, difference)
    )
    completeness = _completeness(current, before)
    total_shots = sum(_sequence_stats(row)[0] for row in current)
    shot_sequences = sum(_sequence_stats(row)[1] for row in current)
    xg_values = [_sequence_stats(row)[2] for row in current]
    total_xg = sum(xg_values) if all(value is not None for value in xg_values) else None
    recent_support = len({row.match_id for row in current})
    reference_support = len({row.match_id for row in before})
    evidence_ids = tuple(_diverse_ids(current, 5))
    reference_ids = tuple(_diverse_ids(before, 3))
    counterexample_ids = tuple(_diverse_ids(counterexamples, 2))
    reasons: list[str] = []
    if len(current) < minimum_sample:
        reasons.append(f"recent sample {len(current)} below minimum {minimum_sample}")
    if recent_support < 2:
        reasons.append("recent examples cover fewer than two matches")
    if completeness["delivery_group"] < minimum_completeness:
        reasons.append("delivery-group completeness below threshold")
    if recent_total == 0 or reference_total == 0:
        reasons.append("one comparison window contains no corners")
    if abs(difference) < minimum_effect:
        reasons.append(f"absolute difference below {minimum_effect * 100:.0f} percentage points")
    if float(ci_low) <= 0.0 <= float(ci_high):
        reasons.append("match-block interval includes zero")
    if len(evidence_ids) < 3:
        reasons.append("fewer than three retrievable examples")
    relative = None if abs(reference_share) < 1e-12 else difference / reference_share * 100
    return DeliveryGroupComparison(
        delivery_group=group,
        recent_count=len(current),
        reference_count=len(before),
        recent_share=recent_share,
        reference_share=reference_share,
        share_difference=difference,
        relative_difference_pct=relative,
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        resampling_unit="match",
        recent_total=recent_total,
        reference_total=reference_total,
        recent_match_support=recent_support,
        reference_match_support=reference_support,
        total_shots=total_shots,
        shot_producing_sequences=shot_sequences,
        shot_producing_rate=shot_sequences / len(current) if current else None,
        total_xg=total_xg,
        completeness=completeness,
        window_sensitivity="pending",
        review_eligible=not reasons,
        suppression_reasons=tuple(reasons),
        evidence_ids=evidence_ids,
        reference_evidence_ids=reference_ids,
        counterexample_evidence_ids=counterexample_ids,
    )


def _match_block_share_difference(
    recent: list[EvidenceSequence],
    reference: list[EvidenceSequence],
    recent_group: list[EvidenceSequence],
    reference_group: list[EvidenceSequence],
    recent_matches: list[int],
    reference_matches: list[int],
    samples: int,
    rng: np.random.Generator,
) -> np.ndarray:
    if not recent_matches or not reference_matches:
        return np.array([], dtype=float)
    recent_by_match = _match_counts(recent, recent_group)
    reference_by_match = _match_counts(reference, reference_group)
    output = np.empty(samples, dtype=float)
    for index in range(samples):
        sampled_recent = rng.choice(recent_matches, size=len(recent_matches), replace=True)
        sampled_reference = rng.choice(reference_matches, size=len(reference_matches), replace=True)
        recent_group, recent_total = _sample_counts(sampled_recent, recent_by_match)
        reference_group, reference_total = _sample_counts(sampled_reference, reference_by_match)
        output[index] = (recent_group / recent_total if recent_total else 0.0) - (
            reference_group / reference_total if reference_total else 0.0
        )
    return output


def _match_counts(
    sequences: list[EvidenceSequence], group_rows: list[EvidenceSequence]
) -> dict[int, tuple[int, int]]:
    output: dict[int, tuple[int, int]] = {}
    group_ids = {row.evidence_id for row in group_rows}
    match_ids = {row.match_id for row in sequences}
    for match_id in match_ids:
        rows = [row for row in sequences if row.match_id == match_id]
        output[match_id] = (sum(row.evidence_id in group_ids for row in rows), len(rows))
    return output


def _sample_counts(
    sampled_matches: np.ndarray, counts: dict[int, tuple[int, int]]
) -> tuple[int, int]:
    group_total = 0
    all_total = 0
    for match_id in sampled_matches:
        group_count, total = counts.get(int(match_id), (0, 0))
        group_total += group_count
        all_total += total
    return group_total, all_total


def _window_checks(
    sequences: list[EvidenceSequence],
    match_dates: dict[int, str],
    recent_matches: list[int],
    baseline_matches: list[int],
    dimensions: tuple[str, ...],
    group: str,
) -> list[float]:
    ordered_ids = sorted(match_dates, key=lambda match_id: (match_dates[match_id], match_id))
    recent_end = max((ordered_ids.index(match_id) for match_id in recent_matches), default=-1) + 1
    output: list[float] = []
    for window in sorted(
        {max(2, len(recent_matches) - 1), len(recent_matches), len(recent_matches) + 1}
    ):
        if recent_end < window:
            continue
        alternate_recent = ordered_ids[recent_end - window : recent_end]
        alternate_reference = ordered_ids[
            max(0, recent_end - window - len(baseline_matches)) : recent_end - window
        ]
        current_rows = [row for row in sequences if row.match_id in alternate_recent]
        reference_rows = [row for row in sequences if row.match_id in alternate_reference]
        current_count = sum(delivery_group_label(row, dimensions) == group for row in current_rows)
        reference_count = sum(
            delivery_group_label(row, dimensions) == group for row in reference_rows
        )
        output.append(
            (current_count / len(current_rows) if current_rows else 0.0)
            - (reference_count / len(reference_rows) if reference_rows else 0.0)
        )
    return output


def _sequence_stats(sequence: EvidenceSequence) -> tuple[int, int, float | None]:
    shots = [event for event in sequence.events if event.get("type") == "Shot"]
    xg = [event.get("xg") for event in shots]
    return (
        len(shots),
        int(bool(shots)),
        sum(float(value) for value in xg) if all(value is not None for value in xg) else None,
    )


def _completeness(
    current: list[EvidenceSequence], before: list[EvidenceSequence]
) -> dict[str, Any]:
    rows = current + before
    if not rows:
        return {
            "delivery_group": 0.0,
            "shot_xg": 0.0,
            "locations": 0.0,
            "movement_endpoints": 0.0,
        }

    def rate(key: str) -> float:
        return sum(row.quality.get(key) in {"observed", "not_applicable"} for row in rows) / len(
            rows
        )

    return {
        "delivery_group": rate("delivery_length"),
        "shot_xg": rate("shot_xg"),
        "locations": rate("locations"),
        "movement_endpoints": rate("movement_endpoints"),
    }


def _diverse_ids(rows: list[EvidenceSequence], limit: int) -> list[str]:
    output: list[str] = []
    seen_matches: set[int] = set()
    for row in sorted(rows, key=lambda item: (item.match_date, item.evidence_id), reverse=True):
        if row.match_id in seen_matches:
            continue
        output.append(row.evidence_id)
        seen_matches.add(row.match_id)
        if len(output) == limit:
            break
    return output


def classify_stability(values: list[float], minimum: float = 0.05) -> str:
    if len(values) < 2:
        return "insufficient nearby windows"
    material_signs = [math.copysign(1, value) for value in values if abs(value) >= minimum]
    if not material_signs:
        return "no material signal"
    if len(set(material_signs)) == 1 and len(material_signs) == len(values):
        return "consistent direction"
    if len(set(material_signs)) > 1:
        return "mixed direction"
    return "sensitive to window size"
