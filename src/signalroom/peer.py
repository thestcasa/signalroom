from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np

from .models import Event, LineupEntry, Match
from .setpieces import analyze_attacking_corners


def build_peer_baseline(
    matches: list[Match],
    events: list[Event],
    lineups: list[LineupEntry],
    target_team: str,
    coverage: dict[str, Any],
) -> dict[str, Any]:
    teams = sorted({match.home_team for match in matches} | {match.away_team for match in matches})
    if not coverage.get("complete") or not coverage.get("peer_population_eligible"):
        return {
            "status": "suppressed",
            "reason": "comparison population is not complete and peer-eligible",
            "teams": len(teams),
            "fixtures": len(matches),
        }
    rows: list[dict[str, Any]] = []
    for team in teams:
        team_matches = [match for match in matches if team in {match.home_team, match.away_team}]
        match_ids = {match.match_id for match in team_matches}
        team_events = [event for event in events if event.match_id in match_ids]
        groups, sequences = analyze_attacking_corners(team_matches, team_events, team)
        shot_sequences = sum(
            any(event.get("type") == "Shot" for event in sequence.events) for sequence in sequences
        )
        exposure = [entry for entry in lineups if entry.team == team]
        rows.append(
            {
                "team": team,
                "matches": len(team_matches),
                "corners": len(sequences),
                "corners_per_match": len(sequences) / len(team_matches) if team_matches else 0.0,
                "shot_producing_rate": shot_sequences / len(sequences) if sequences else 0.0,
                "eligible_players": len({entry.player_id for entry in exposure}),
                "delivery_group_shares": {group.delivery_group: group.share for group in groups},
            }
        )
    target = next((row for row in rows if row["team"] == target_team), None)
    if target is None:
        return {
            "status": "suppressed",
            "reason": "target team is absent from the complete population",
            "teams": len(teams),
            "fixtures": len(matches),
        }
    peers = [row for row in rows if row["team"] != target_team]
    group_names = sorted({name for row in rows for name in row["delivery_group_shares"]})
    percentiles = {
        "corners_per_match": _percentile(
            float(target["corners_per_match"]),
            [float(row["corners_per_match"]) for row in peers],
        ),
        "shot_producing_rate": _percentile(
            float(target["shot_producing_rate"]),
            [float(row["shot_producing_rate"]) for row in peers],
        ),
        "delivery_groups": {
            name: _percentile(
                float(target["delivery_group_shares"].get(name, 0.0)),
                [float(row["delivery_group_shares"].get(name, 0.0)) for row in peers],
            )
            for name in group_names
        },
    }
    fixture_counts = Counter(
        team for match in matches for team in (match.home_team, match.away_team)
    )
    return {
        "status": "descriptive",
        "population": "complete competition-season attacking corners",
        "leave_target_out": True,
        "teams": len(teams),
        "peer_teams": len(peers),
        "fixtures": len(matches),
        "fixture_exposure": dict(sorted(fixture_counts.items())),
        "target": target,
        "target_percentiles": percentiles,
        "team_rows": rows,
        "limitations": [
            "Percentiles are descriptive and schedule-conditional.",
            "They do not establish tactical intent, quality, or causal effectiveness.",
            "A 12-team season is not a defensible clustering population.",
        ],
    }


def _percentile(value: float, peers: list[float]) -> float | None:
    if not peers:
        return None
    below = sum(peer < value for peer in peers)
    equal = sum(np.isclose(peer, value) for peer in peers)
    return (below + 0.5 * equal) / len(peers)
