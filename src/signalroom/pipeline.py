from __future__ import annotations

import json
import shutil
from dataclasses import replace
from pathlib import Path

from .adapters.statsbomb import (
    ATTRIBUTION,
    SOURCE_REPOSITORY,
    SOURCE_REVISION,
    StatsBombOpenDataAdapter,
)
from .capabilities import capability_notice
from .config import CaseConfig
from .deadballs import analyze_attacking_final_third_dead_balls
from .evidence import build_metric_evidence, validate_evidence_references
from .metrics import METRIC_VERSION, calculate_match_metrics
from .ml import profile_publication, team_profile_features
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
    dead_ball_summaries, dead_ball_sequences = analyze_attacking_final_third_dead_balls(
        matches, events, config.team, SOURCE_REVISION
    )

    output = Path(output_root) / config.slug
    assets = output / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    recent_ids = set(metrics.iloc[-config.recent_matches :]["match_id"].astype(int))
    evidence: list = []
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
    routine_dicts = [routine.to_dict() for routine in routines]
    published_routines = [row for row in routine_dicts if row["publish"]]
    representative_ids = {
        evidence_id
        for routine in routine_dicts
        for evidence_id in routine["evidence_ids"]
    }
    representative_ids.update(
        evidence_id
        for summary in dead_ball_summaries
        for evidence_id in summary.evidence_ids
    )
    evidence.extend(
        sequence
        for sequence in corner_sequences + dead_ball_sequences
        if sequence.evidence_id in representative_ids
    )
    unique_evidence = {sequence.evidence_id: sequence for sequence in evidence}
    evidence_errors = validate_evidence_references(unique_evidence.values(), events)
    if evidence_errors:
        raise ValueError("Evidence validation failed: " + "; ".join(evidence_errors))
    routine_index = [
        {
            "evidence_id": sequence.evidence_id,
            "match_id": sequence.match_id,
            "match_date": sequence.match_date,
            "opponent": sequence.opponent,
            "label": sequence.label,
            "start_minute": sequence.start_minute,
            "start_event_id": sequence.start_event_id,
            "source_event_ids": list(sequence.source_event_ids),
            "events": [{"type": event.get("type"), "xg": event.get("xg")} for event in sequence.events],
            "quality": sequence.quality,
        }
        for sequence in corner_sequences
    ]
    evidence_sequence_count = sum(
        sequence.evidence_id.startswith("DB-") for sequence in unique_evidence.values()
    )
    bundle: dict[str, object] = {
        "schema_version": "1.2.0",
        "case": {
            "slug": config.slug,
            "team": config.team,
            "competition": config.competition_label,
            "season": config.season_label,
            "matches": len(matches),
            "first_match": matches[0].date,
            "last_match": matches[-1].date,
            "historical_only": True,
            "matches_detail": [
                {"match_id": match.match_id, "date": match.date, "opponent": match.away_team if match.home_team == config.team else match.home_team}
                for match in matches
            ],
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
            "set_piece_version": "1.1.0",
            "baseline_matches": config.baseline_matches,
            "recent_matches": config.recent_matches,
            "minimum_evidence_sequences": config.minimum_evidence_sequences,
            "bootstrap_samples": config.bootstrap_samples,
            "multiple_comparison_control": "Benjamini-Hochberg",
            "selection_rule": "|Hedges g| >= 0.5, bootstrap direction >= 0.80, sensitivity >= 2/3, plus q <= 0.20 or stronger effect/stability",
            "short_corner_definition": "first delivery length <= 15 StatsBomb pitch units",
            "shot_rate_definition": "share of corner sequences containing at least one team shot",
            "comparison_baseline": "selected team previous chronological window; competition-wide routine baseline is not present in this source bundle",
            "uncertainty_definition": "bootstrap uncertainty for routine-share differences",
            "stability_definition": "direction under nearby recent-window sizes, with minimum routine sample",
            "dead_ball_taxonomy": "corner, wide attacking free kick, indirect attacking free kick near the box, direct free kick; other restarts are architecture-only",
            "dead_ball_free_kick_note": "Free-kick categories are event-location buckets, not referee-certified direct/indirect labels.",
        },
        "product_path": "Evidence-first dead-ball opponent preparation",
        "capability": capability_notice("event"),
        "findings": findings,
        "comparisons": [comparison.to_dict() for comparison in final_comparisons],
        "set_piece_lab": {
            "corner_count": len(corner_sequences),
            "minimum_cluster": 4,
            "published_routines": published_routines,
            "suppressed_routines": [row for row in routine_dicts if not row["publish"]],
            "routine_index": routine_index,
            "quality": {
                "corner_length_complete": sum(bool(row.quality.get("corner_length_available")) for row in corner_sequences) / len(corner_sequences) if corner_sequences else 0.0,
                "locations_complete": sum(bool(row.quality.get("locations_complete")) for row in corner_sequences) / len(corner_sequences) if corner_sequences else 0.0,
                "movement_endpoints_complete": sum(bool(row.quality.get("movement_endpoints_complete")) for row in corner_sequences) / len(corner_sequences) if corner_sequences else 0.0,
                "shot_xg_complete": sum(bool(row.quality.get("shot_xg_complete")) for row in corner_sequences) / len(corner_sequences) if corner_sequences else 0.0,
            },
        },
        "dead_ball_lab": {
            "domain": "attacking final-third dead balls",
            "capability_level": "event",
            "supported_restart_types": ["corner", "wide_free_kick", "indirect_free_kick", "direct_free_kick"],
            "architecture_only_restart_types": ["attacking_throw_in", "goal_kick", "kick_off", "penalty", "defensive_dead_ball"],
            "sequence_count": len(dead_ball_sequences),
            "evidence_sequence_count": evidence_sequence_count,
            "evidence_policy": "one deterministic representative sequence referenced by each summary or routine, while category counts use the full selected-team event set",
            "summaries": [summary.to_dict() for summary in dead_ball_summaries],
            "profile_features": team_profile_features(dead_ball_sequences, len(matches)),
            "ml": profile_publication(0, len(dead_ball_sequences), minimum_team_count=5),
            "limitations": [
                "First contact means the first recorded contact-like event, not a verified aerial touch.",
                "Off-ball movement, screens, marking, and tactical intent cannot be verified from this event-only package.",
                "Competition peer prevalence is not published unless complete comparable source coverage is loaded.",
            ],
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
    strongest = max(
        final_comparisons,
        key=lambda item: abs(item.standardized_effect)
        if item.standardized_effect is not None
        else 0.0,
    )
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
