from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from .config import CaseConfig
from .metrics import METRICS, MetricDefinition


@dataclass(frozen=True)
class MetricComparison:
    metric: str
    label: str
    definition: str
    unit: str
    baseline_value: float
    recent_value: float
    absolute_change: float
    relative_change_pct: float | None
    standardized_effect: float
    ci_low: float
    ci_high: float
    direction_probability: float
    p_value: float
    q_value: float
    sensitivity_agreement: float
    baseline_n: int
    recent_n: int
    reliability: str
    publish: bool
    suppression_reason: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def compare_windows(frame: pd.DataFrame, config: CaseConfig) -> list[MetricComparison]:
    required = config.baseline_matches + config.recent_matches
    if len(frame) < required:
        raise ValueError(f"Need {required} matches, received {len(frame)}")
    baseline = frame.iloc[-required : -config.recent_matches]
    recent = frame.iloc[-config.recent_matches :]
    raw: list[dict[str, object]] = []
    for index, metric in enumerate(METRICS):
        before = baseline[metric.key].astype(float).to_numpy()
        after = recent[metric.key].astype(float).to_numpy()
        rng = np.random.default_rng(config.random_seed + index)
        bootstrap = _bootstrap_differences(before, after, config.bootstrap_samples, rng)
        difference = float(after.mean() - before.mean())
        direction_probability = float(max(np.mean(bootstrap > 0), np.mean(bootstrap < 0)))
        ci_low, ci_high = np.quantile(bootstrap, [0.025, 0.975])
        raw.append(
            {
                "definition": metric,
                "baseline": float(before.mean()),
                "recent": float(after.mean()),
                "difference": difference,
                "relative": None
                if abs(before.mean()) < 1e-12
                else difference / before.mean() * 100,
                "effect": _standardized_effect(before, after),
                "ci_low": float(ci_low),
                "ci_high": float(ci_high),
                "direction_probability": direction_probability,
                "p_value": _permutation_p_value(before, after, rng),
                "sensitivity": _sensitivity(frame, metric, config),
            }
        )
    q_values = _benjamini_hochberg([float(item["p_value"]) for item in raw])
    results: list[MetricComparison] = []
    for item, q_value in zip(raw, q_values, strict=True):
        metric = item["definition"]
        assert isinstance(metric, MetricDefinition)
        effect = float(item["effect"])
        direction_probability = float(item["direction_probability"])
        sensitivity = float(item["sensitivity"])
        publish = (
            abs(effect) >= 0.5
            and direction_probability >= 0.80
            and sensitivity >= 2 / 3
            and (q_value <= 0.20 or (abs(effect) >= 0.8 and direction_probability >= 0.90))
        )
        if publish and q_value <= 0.10 and direction_probability >= 0.95:
            reliability = "high"
        elif publish:
            reliability = "moderate"
        else:
            reliability = "suppressed"
        reason = None
        if not publish:
            failures = []
            if abs(effect) < 0.5:
                failures.append("negligible standardized effect")
            if direction_probability < 0.80:
                failures.append("unstable bootstrap direction")
            if sensitivity < 2 / 3:
                failures.append("window sensitivity")
            if q_value > 0.20 and not (abs(effect) >= 0.8 and direction_probability >= 0.90):
                failures.append("weak multiple-comparison evidence")
            reason = ", ".join(failures)
        results.append(
            MetricComparison(
                metric=metric.key,
                label=metric.label,
                definition=metric.description,
                unit=metric.unit,
                baseline_value=float(item["baseline"]),
                recent_value=float(item["recent"]),
                absolute_change=float(item["difference"]),
                relative_change_pct=item["relative"],
                standardized_effect=effect,
                ci_low=float(item["ci_low"]),
                ci_high=float(item["ci_high"]),
                direction_probability=direction_probability,
                p_value=float(item["p_value"]),
                q_value=q_value,
                sensitivity_agreement=sensitivity,
                baseline_n=config.baseline_matches,
                recent_n=config.recent_matches,
                reliability=reliability,
                publish=publish,
                suppression_reason=reason,
            )
        )
    return results


def _bootstrap_differences(
    baseline: np.ndarray, recent: np.ndarray, samples: int, rng: np.random.Generator
) -> np.ndarray:
    before = rng.choice(baseline, size=(samples, len(baseline)), replace=True).mean(axis=1)
    after = rng.choice(recent, size=(samples, len(recent)), replace=True).mean(axis=1)
    return after - before


def _standardized_effect(baseline: np.ndarray, recent: np.ndarray) -> float:
    n1, n2 = len(baseline), len(recent)
    pooled_numerator = (n1 - 1) * baseline.var(ddof=1) + (n2 - 1) * recent.var(ddof=1)
    pooled = math.sqrt(pooled_numerator / (n1 + n2 - 2)) if n1 + n2 > 2 else 0.0
    if pooled < 1e-12:
        return 0.0 if abs(recent.mean() - baseline.mean()) < 1e-12 else math.inf
    correction = 1 - 3 / (4 * (n1 + n2) - 9)
    return float(correction * (recent.mean() - baseline.mean()) / pooled)


def _permutation_p_value(
    baseline: np.ndarray, recent: np.ndarray, rng: np.random.Generator, samples: int = 5000
) -> float:
    observed = abs(recent.mean() - baseline.mean())
    combined = np.concatenate([baseline, recent])
    exceed = 0
    for _ in range(samples):
        permuted = rng.permutation(combined)
        difference = abs(permuted[len(baseline) :].mean() - permuted[: len(baseline)].mean())
        exceed += difference >= observed - 1e-12
    return (exceed + 1) / (samples + 1)


def _sensitivity(frame: pd.DataFrame, metric: MetricDefinition, config: CaseConfig) -> float:
    main_n = config.recent_matches
    main_required = config.baseline_matches + main_n
    main_before = frame.iloc[-main_required:-main_n][metric.key].astype(float).mean()
    main_after = frame.iloc[-main_n:][metric.key].astype(float).mean()
    main_direction = np.sign(main_after - main_before)
    checks = []
    for recent_n in sorted({max(config.minimum_recent_matches, main_n - 1), main_n, main_n + 1}):
        required = config.baseline_matches + recent_n
        if len(frame) < required:
            continue
        before = frame.iloc[-required:-recent_n][metric.key].astype(float).to_numpy()
        after = frame.iloc[-recent_n:][metric.key].astype(float).to_numpy()
        effect = _standardized_effect(before, after)
        checks.append(
            np.sign(after.mean() - before.mean()) == main_direction and abs(effect) >= 0.25
        )
    return float(np.mean(checks)) if checks else 0.0


def _benjamini_hochberg(p_values: list[float]) -> list[float]:
    count = len(p_values)
    order = np.argsort(p_values)
    adjusted = np.empty(count, dtype=float)
    running = 1.0
    for reverse_rank, idx in enumerate(order[::-1], start=1):
        rank = count - reverse_rank + 1
        running = min(running, p_values[int(idx)] * count / rank)
        adjusted[int(idx)] = min(1.0, running)
    return adjusted.tolist()
