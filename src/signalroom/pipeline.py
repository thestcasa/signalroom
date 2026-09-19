from __future__ import annotations

import csv
import json
import shutil
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any

from .adapters.statsbomb import (
    ATTRIBUTION,
    SOURCE_REPOSITORY,
    SOURCE_REVISION,
    StatsBombOpenDataAdapter,
)
from .capabilities import capability_notice
from .config import CaseConfig
from .deadballs import RESTART_TYPES, analyze_attacking_final_third_dead_balls
from .evidence import (
    public_evidence_summary,
    validate_bundle_evidence,
    validate_evidence_references,
)
from .metrics import METRIC_VERSION, calculate_match_metrics
from .peer import build_peer_baseline
from .reporting import dump_bundle, validate_grounded_bundle, write_html_report
from .rights import default_rights_manifest, validate_public_payload
from .setpieces import analyze_attacking_corners
from .statistics import compare_windows
from .validation import validate_dataset


def build_case(
    config: CaseConfig,
    output_root: str | Path = "artifacts/cases",
    cache_dir: str | Path = "data/cache/statsbomb",
) -> Path:
    rights = default_rights_manifest()
    if rights.source_revision != SOURCE_REVISION:
        raise ValueError("Rights manifest revision does not match the pinned adapter revision")
    rights.require_public_artifact("derived_aggregate")
    rights.require_public_artifact("derived_sequence_summary")

    adapter = StatsBombOpenDataAdapter(cache_dir=cache_dir)
    population_matches, population_events, population_lineups, coverage = adapter.load_population(
        config
    )
    target_match_ids = {
        match.match_id
        for match in population_matches
        if config.team in {match.home_team, match.away_team}
    }
    matches = [match for match in population_matches if match.match_id in target_match_ids]
    events = [event for event in population_events if event.match_id in target_match_ids]
    lineups = [entry for entry in population_lineups if entry.match_id in target_match_ids]
    if not matches:
        raise ValueError(f"Target team {config.team!r} is absent from the declared population")

    population_validation = validate_dataset(population_matches, population_events)
    target_validation = validate_dataset(matches, events)
    metrics, _ = calculate_match_metrics(matches, events, config.team)
    broad_comparisons = compare_windows(metrics, config)
    delivery_groups, corner_sequences = analyze_attacking_corners(matches, events, config.team)
    dead_ball_summaries, dead_ball_sequences = analyze_attacking_final_third_dead_balls(
        matches, events, config.team, SOURCE_REVISION
    )
    evidence_errors = validate_evidence_references(
        _as_evidence_sequences(dead_ball_sequences), events
    )
    if evidence_errors:
        raise ValueError("Internal evidence validation failed: " + "; ".join(evidence_errors))

    group_by_id = {row.evidence_id: row.label for row in corner_sequences}
    evidence = [
        public_evidence_summary(row, rights, group_by_id.get(row.evidence_id))
        for row in dead_ball_sequences
    ]
    evidence_by_id = {str(row["evidence_id"]): row for row in evidence}
    group_rows = [group.to_dict() for group in delivery_groups]
    for group in group_rows:
        group["evidence_availability"] = {
            "available": sum(
                evidence_id in evidence_by_id for evidence_id in group["evidence_ids"]
            ),
            "requested": len(group["evidence_ids"]),
        }

    peer_baseline = build_peer_baseline(
        population_matches,
        population_events,
        population_lineups,
        config.team,
        coverage,
    )
    player_exposure = _player_exposure(lineups, dead_ball_sequences, config.team)
    source_manifest = _source_manifest(
        adapter, population_matches, coverage, rights.public_metadata()
    )
    field_quality = _field_quality(population_events, population_lineups)
    output = Path(output_root) / config.slug
    output.mkdir(parents=True, exist_ok=True)
    quality_dir = output / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)

    bundle: dict[str, Any] = {
        "schema_version": "2.0.0",
        "case": {
            "slug": config.slug,
            "team": config.team,
            "competition": config.competition_label,
            "season": config.season_label,
            "matches": len(matches),
            "first_match": matches[0].date,
            "last_match": matches[-1].date,
            "historical_cutoff": matches[-1].date,
            "historical_only": True,
            "matches_detail": [
                {
                    "match_id": match.match_id,
                    "date": match.date,
                    "opponent": (
                        match.away_team if match.home_team == config.team else match.home_team
                    ),
                }
                for match in matches
            ],
        },
        "analysis_context": {
            "recent_matches": config.recent_matches,
            "reference_matches": config.baseline_matches,
            "comparison": "latest chronological window versus preceding chronological window",
            "coordinate_orientation": "selected team attacks left-to-right",
        },
        "data": {
            "provider": ATTRIBUTION,
            "source_repository": SOURCE_REPOSITORY,
            "source_revision": SOURCE_REVISION,
            "competition_id": config.competition_id,
            "season_id": config.season_id,
            "target_events": len(events),
            "population_events": len(population_events),
            "target_validation": target_validation.__dict__,
            "population_validation": population_validation.__dict__,
            "coverage": coverage,
            "source_manifest": source_manifest,
            "rights": rights.public_metadata(),
            "modalities": {
                "event": "available",
                "lineup": "available",
                "shot_freeze_frame": "source-available-not-published",
                "360_snapshot": "not-loaded",
                "continuous_tracking": "unavailable",
                "video": "unavailable",
                "human_annotation": "session-only",
            },
            "limitations": _case_limitations(config, coverage),
        },
        "method": {
            "metric_version": METRIC_VERSION,
            "set_piece_version": "2.0.0",
            "minimum_evidence_sequences": config.minimum_evidence_sequences,
            "resampling_unit": "match",
            "bootstrap_samples": config.bootstrap_samples,
            "change_gate": (
                "minimum sample, two-match support, >=5 percentage-point effect, "
                "match-block interval excluding zero, consistent nearby-window direction, "
                "complete evidence, and field quality"
            ),
            "delivery_group_definition": (
                "recorded side, short/direct pass length, and validated two-dimensional target lane"
            ),
            "restart_taxonomy": list(RESTART_TYPES),
            "central_free_kick_note": (
                "Central final-third free-kick pass is a spatial/action category. Legal direct or "
                "indirect status is unavailable."
            ),
            "sequence_rule": (
                "same-period provider-possession event window, maximum 20 seconds and 17 later "
                "events, with explicit termination and censoring"
            ),
        },
        "positioning": (
            "Historical set-piece evidence workbench for inspecting recorded delivery tendencies. "
            "It is not a validated club preparation product."
        ),
        "capability": capability_notice("event"),
        "broad_context": {
            "status": "optional descriptive context",
            "comparisons": [comparison.to_dict() for comparison in broad_comparisons],
        },
        "set_piece_lab": {
            "name": "Recorded corner delivery groups",
            "corner_count": len(corner_sequences),
            "delivery_groups": group_rows,
            "sequence_index": [_public_corner_index(row) for row in corner_sequences],
            "quality": _corner_quality(corner_sequences),
        },
        "dead_ball_lab": {
            "domain": "attacking final-third recorded dead balls",
            "capability_level": "event",
            "supported_restart_types": list(RESTART_TYPES),
            "sequence_count": len(dead_ball_sequences),
            "summaries": [summary.to_dict() for summary in dead_ball_summaries],
            "player_exposure": player_exposure,
            "unsupported_outputs": [
                "football second phase",
                "physical first contact",
                "recurring mixed-team combinations",
                "tactical intent",
                "defensive recommendation",
            ],
        },
        "peer_baseline": peer_baseline,
        "evidence": evidence,
    }
    errors = validate_bundle_evidence(bundle)
    errors.extend(validate_grounded_bundle(bundle))
    errors.extend(validate_public_payload(bundle))
    if errors:
        raise ValueError("Public bundle validation failed: " + "; ".join(errors))

    metrics.to_csv(output / "match_metrics.csv", index=False)
    dump_bundle(bundle, output / "bundle.json")
    write_html_report(bundle, output / "report.html")
    _write_quality_reports(
        quality_dir,
        coverage,
        field_quality,
        delivery_groups,
        errors,
        broad_comparisons,
        source_manifest,
    )
    _write_validation_corpus(
        output / "manual_review_sample.csv",
        population_matches,
        population_events,
        config,
    )
    logo = Path("assets/statsbomb-open-data-logo.png")
    assets = output / "assets"
    assets.mkdir(exist_ok=True)
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


def _as_evidence_sequences(rows: list[Any]) -> list[Any]:
    from .models import EvidenceSequence

    return [
        EvidenceSequence(
            evidence_id=row.evidence_id,
            match_id=row.match_id,
            match_date=row.match_date,
            opponent=row.opponent,
            start_event_id=row.start_event_id,
            source_event_ids=row.source_event_ids,
            label=row.restart_type,
            start_minute=0,
            events=row.ordered_events,
        )
        for row in rows
    ]


def _source_manifest(
    adapter: StatsBombOpenDataAdapter,
    matches: list[Any],
    coverage: dict[str, Any],
    rights: dict[str, Any],
) -> dict[str, Any]:
    event_hashes = [adapter.cached_sha256(f"events/{match.match_id}.json") for match in matches]
    lineup_hashes = [adapter.cached_sha256(f"lineups/{match.match_id}.json") for match in matches]
    return {
        "provider": "statsbomb-open-data",
        "revision": SOURCE_REVISION,
        "competition_scope": coverage["scope"],
        "expected_fixtures": coverage["expected_fixtures"],
        "received_fixtures": coverage["received_fixtures"],
        "modalities": ["events", "lineups"],
        "event_files_sha256": sha256("".join(event_hashes).encode()).hexdigest(),
        "lineup_files_sha256": sha256("".join(lineup_hashes).encode()).hexdigest(),
        "rights": rights,
    }


def _public_corner_index(row: Any) -> dict[str, Any]:
    return {
        "evidence_id": row.evidence_id,
        "match_id": row.match_id,
        "match_date": row.match_date,
        "opponent": row.opponent,
        "label": row.label,
        "start_minute": row.start_minute,
        "events": [
            {"type": event.get("type"), "team_role": event.get("team_role"), "xg": event.get("xg")}
            for event in row.events
        ],
        "quality": row.quality,
        "termination_reason": row.termination_reason,
        "censoring_reason": row.censoring_reason,
        "player_roles": row.player_roles,
        "evidence_status": "available-derived-summary",
    }


def _player_exposure(lineups: list[Any], sequences: list[Any], team: str) -> list[dict[str, Any]]:
    by_player: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"matches": set(), "minutes": 0.0, "minutes_available": True}
    )
    for entry in lineups:
        if entry.team != team:
            continue
        row = by_player[entry.player]
        row["matches"].add(entry.match_id)
        if entry.recorded_minutes is None:
            row["minutes_available"] = False
        else:
            row["minutes"] += entry.recorded_minutes
    roles: dict[str, Counter[str]] = {
        "taker": Counter(),
        "intended_recipient": Counter(),
        "first_post_delivery_actor": Counter(),
        "shot_actor": Counter(),
    }
    for sequence in sequences:
        for role in ("taker", "intended_recipient", "first_post_delivery_actor"):
            value = sequence.player_roles.get(role)
            if value and (
                role != "first_post_delivery_actor"
                or sequence.player_roles.get("first_post_delivery_actor_team") == "selected_team"
            ):
                roles[role][str(value)] += 1
        for value in sequence.player_roles.get("shot_actors", []):
            roles["shot_actor"][str(value)] += 1
    output = []
    for player, exposure in by_player.items():
        output.append(
            {
                "player": player,
                "matches_in_lineup": len(exposure["matches"]),
                "recorded_minutes": (
                    round(float(exposure["minutes"]), 1) if exposure["minutes_available"] else None
                ),
                "restart_taker_count": roles["taker"][player],
                "intended_recipient_count": roles["intended_recipient"][player],
                "first_post_delivery_actor_count": roles["first_post_delivery_actor"][player],
                "shot_actor_count": roles["shot_actor"][player],
            }
        )
    return sorted(
        output,
        key=lambda row: (row["restart_taker_count"], row["matches_in_lineup"]),
        reverse=True,
    )


def _field_quality(events: list[Any], lineups: list[Any]) -> dict[str, Any]:
    passes = [event for event in events if event.event_type == "Pass"]
    shots = [event for event in events if event.event_type == "Shot"]
    moves = [event for event in events if event.event_type in {"Pass", "Carry"}]
    return {
        "events": len(events),
        "lineup_entries": len(lineups),
        "recipient": _status_counts(event.recipient for event in passes),
        "move_end_location": _status_counts(
            (event.end_x, event.end_y)
            if event.end_x is not None and event.end_y is not None
            else None
            for event in moves
        ),
        "shot_xg": _status_counts(event.xg for event in shots),
        "body_part": _status_counts(event.body_part for event in passes + shots),
        "pass_height": _status_counts(event.pass_height for event in passes),
    }


def _status_counts(values: Any) -> dict[str, int]:
    observed = 0
    missing = 0
    for value in values:
        if value is None:
            missing += 1
        else:
            observed += 1
    return {"observed": observed, "missing_or_unavailable": missing}


def _corner_quality(rows: list[Any]) -> dict[str, float]:
    keys = ("delivery_length", "locations", "movement_endpoints", "shot_xg", "sequence")
    if not rows:
        return {key: 0.0 for key in keys}
    return {
        key: sum(row.quality.get(key) in {"observed", "not_applicable"} for row in rows) / len(rows)
        for key in keys
    }


def _case_limitations(config: CaseConfig, coverage: dict[str, Any]) -> list[str]:
    limitations = [
        "Historical event data does not establish tactical intent or current behaviour.",
        "Event data does not show continuous off-ball movement, screens, or marking assignments.",
        "Public evidence is a derived summary; raw provider records and source event IDs are not redistributed.",
        "No external analyst validation has occurred.",
    ]
    if not coverage.get("peer_population_eligible"):
        limitations.append("Competition peer comparison is suppressed for this selected release.")
    if config.team == "Bayer Leverkusen":
        limitations.append(
            "The released Bundesliga sample contains Leverkusen matches only; it is not a league baseline."
        )
    return limitations


def _write_quality_reports(
    target: Path,
    coverage: dict[str, Any],
    field_quality: dict[str, Any],
    delivery_groups: list[Any],
    evidence_errors: list[str],
    comparisons: list[Any],
    source_manifest: dict[str, Any],
) -> None:
    reports = {
        "fixture_coverage.json": coverage,
        "field_quality.json": field_quality,
        "classification.json": {
            "delivery_groups": len(delivery_groups),
            "terminology": "recorded delivery groups, not analyst-confirmed routines",
        },
        "evidence_resolution.json": {
            "errors": evidence_errors,
            "status": "pass" if not evidence_errors else "fail",
        },
        "comparison_gates.json": {
            "broad_context_published": sum(comparison.publish for comparison in comparisons),
            "core_workflow": "corner delivery comparison uses match-block resampling at runtime",
        },
        "exclusions.json": {
            "excluded": [
                "second phase",
                "physical first contact",
                "mixed-team combinations",
                "direct-shot conversion",
                "ML",
                "tactical intent",
                "defensive recommendations",
            ]
        },
        "build_version.json": source_manifest,
    }
    for filename, payload in reports.items():
        (target / filename).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_validation_corpus(
    path: Path,
    matches: list[Any],
    events: list[Any],
    config: CaseConfig,
    limit: int = 80,
) -> None:
    teams = sorted({match.home_team for match in matches} | {match.away_team for match in matches})
    candidates: list[dict[str, Any]] = []
    for team in teams:
        team_matches = [match for match in matches if team in {match.home_team, match.away_team}]
        ids = {match.match_id for match in team_matches}
        team_events = [event for event in events if event.match_id in ids]
        _, sequences = analyze_attacking_final_third_dead_balls(
            team_matches, team_events, team, SOURCE_REVISION
        )
        for sequence in sequences:
            candidates.append(
                {
                    "evidence_id": sequence.evidence_id,
                    "team": team,
                    "match_id": sequence.match_id,
                    "restart_type": sequence.restart_type,
                    "shot_outcome": int(sequence.shot_outcome["shot_count"]) > 0,
                    "termination_reason": sequence.termination_reason,
                    "censoring_reason": sequence.censoring_reason or "",
                }
            )
    selected = _stratified_rows(candidates, limit)
    fields = [
        "evidence_id",
        "team",
        "match_id",
        "restart_type",
        "shot_outcome",
        "termination_reason",
        "censoring_reason",
        "reviewer_1_restart_valid",
        "reviewer_2_restart_valid",
        "reviewer_1_boundary_valid",
        "reviewer_2_boundary_valid",
        "adjudication",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in selected:
            writer.writerow(row)


def _stratified_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    groups: dict[tuple[str, bool, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[
            (
                str(row["restart_type"]),
                bool(row["shot_outcome"]),
                str(row["team"]),
            )
        ].append(row)
    selected: list[dict[str, Any]] = []
    ordered_keys = sorted(groups)
    while len(selected) < min(limit, len(rows)):
        progressed = False
        for key in ordered_keys:
            if groups[key]:
                selected.append(groups[key].pop(0))
                progressed = True
                if len(selected) == min(limit, len(rows)):
                    break
        if not progressed:
            break
    return selected
