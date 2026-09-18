from __future__ import annotations

import json
import shutil
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from .adapters.statsbomb import (
    ATTRIBUTION,
    SOURCE_REPOSITORY,
    SOURCE_REVISION,
    StatsBombOpenDataAdapter,
)
from .config import CaseConfig
from .evidence import build_metric_evidence, validate_evidence_references
from .metrics import METRIC_VERSION, calculate_match_metrics
from .reporting import (
    deterministic_finding_text,
    dump_bundle,
    validate_grounded_bundle,
    write_html_report,
)
from .setpieces import analyze_attacking_corners
from .statistics import compare_windows
from .validation import validate_dataset
from .visuals import corner_map, metric_comparison_chart, routine_share_chart, trend_chart


def build_case(
    config: CaseConfig,
    output_root: str | Path = "artifacts/cases",
    cache_dir: str | Path = "data/cache/statsbomb",
) -> Path:
    adapter = StatsBombOpenDataAdapter(cache_dir=cache_dir)
    matches, events = adapter.load_case(config)
    validation = validate_dataset(matches, events)
    metrics, metric_event_ids = calculate_match_metrics(matches, events, config.team)
    comparisons = compare_windows(metrics, config)
    routines, corner_sequences = analyze_attacking_corners(matches, events, config.team)

    output = Path(output_root) / config.slug
    assets = output / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    recent_ids = set(metrics.iloc[-config.recent_matches :]["match_id"].astype(int))
    evidence = list(corner_sequences)
    findings = []
    final_comparisons = []
    for comparison in comparisons:
        ids = [
            event_id
            for (match_id, metric), values in metric_event_ids.items()
            if metric == comparison.metric and match_id in recent_ids
            for event_id in values
        ]
        sequences = build_metric_evidence(
            ids, events, matches, config.team, comparison.label, limit=5
        )
        publish = comparison.publish and len(sequences) >= config.minimum_evidence_sequences
        if comparison.publish and not publish:
            comparison = replace(
                comparison,
                publish=False,
                reliability="suppressed",
                suppression_reason="insufficient retrievable evidence sequences",
            )
        final_comparisons.append(comparison)
        if publish:
            evidence.extend(sequences)
            item = comparison.to_dict()
            item["evidence_ids"] = [sequence.evidence_id for sequence in sequences]
            item["narrative"] = deterministic_finding_text(item)
            findings.append(item)
    unique_evidence = {sequence.evidence_id: sequence for sequence in evidence}
    evidence_errors = validate_evidence_references(unique_evidence.values(), events)
    if evidence_errors:
        raise ValueError("Evidence validation failed: " + "; ".join(evidence_errors))
    routine_dicts = [routine.to_dict() for routine in routines]
    published_routines = [row for row in routine_dicts if row["publish"]]
    bundle: dict[str, object] = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "case": {
            "slug": config.slug,
            "team": config.team,
            "competition": config.competition_label,
            "season": config.season_label,
            "matches": len(matches),
            "first_match": matches[0].date,
            "last_match": matches[-1].date,
            "historical_only": True,
        },
        "data": {
            "provider": ATTRIBUTION,
            "source_repository": SOURCE_REPOSITORY,
            "source_revision": SOURCE_REVISION,
            "competition_id": config.competition_id,
            "season_id": config.season_id,
            "events": len(events),
            "validation": validation.__dict__,
            "limitations": [
                "Event data does not reveal off-ball positioning outside recorded actions.",
                "StatsBomb 360 is not available for the selected WSL season.",
                "Historical open data must not be presented as current tactical advice.",
            ],
        },
        "method": {
            "metric_version": METRIC_VERSION,
            "baseline_matches": config.baseline_matches,
            "recent_matches": config.recent_matches,
            "minimum_evidence_sequences": config.minimum_evidence_sequences,
            "bootstrap_samples": config.bootstrap_samples,
            "multiple_comparison_control": "Benjamini-Hochberg",
            "selection_rule": "|Hedges g| >= 0.5, bootstrap direction >= 0.80, sensitivity >= 2/3, plus q <= 0.20 or stronger effect/stability",
        },
        "product_path": "Narrow SignalRoom MVP with SetPieceLab as the most complete module",
        "findings": findings,
        "comparisons": [comparison.to_dict() for comparison in final_comparisons],
        "set_piece_lab": {
            "corner_count": len(corner_sequences),
            "minimum_cluster": 4,
            "published_routines": published_routines,
            "suppressed_routines": [row for row in routine_dicts if not row["publish"]],
        },
        "evidence": [sequence.to_dict() for sequence in unique_evidence.values()],
    }
    grounding_errors = validate_grounded_bundle(bundle)
    if grounding_errors:
        raise ValueError("Grounding validation failed: " + "; ".join(grounding_errors))
    metrics.to_csv(output / "match_metrics.csv", index=False)
    dump_bundle(bundle, output / "bundle.json")
    metric_comparison_chart(final_comparisons, assets / "metric_comparison.png")
    corner_map(corner_sequences, assets / "corner_map.png", config.team)
    routine_share_chart(routine_dicts, assets / "routine_shares.png")
    strongest = max(final_comparisons, key=lambda item: abs(item.standardized_effect))
    trend_chart(
        metrics,
        strongest.metric,
        strongest.label,
        assets / "metric_trend.png",
        config.recent_matches,
    )
    write_html_report(bundle, output / "report.html")
    logo = Path("assets/statsbomb-open-data-logo.png")
    if logo.exists():
        shutil.copy2(logo, assets / "statsbomb-open-data-logo.png")
    return output


def copy_static_app_assets(case_dirs: list[Path], target: Path = Path("artifacts/demo")) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    manifest = []
    for case_dir in case_dirs:
        destination = target / case_dir.name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(case_dir, destination)
        manifest.append({"slug": case_dir.name, "bundle": f"{case_dir.name}/bundle.json"})
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return target
