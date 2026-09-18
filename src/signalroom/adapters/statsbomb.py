from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests

from ..config import CaseConfig
from ..models import Event, Match

BASE_URL = "https://raw.githubusercontent.com/hudl/open-data/master/data"
ATTRIBUTION = "StatsBomb Open Data"
SOURCE_REPOSITORY = "https://github.com/hudl/open-data"


class StatsBombOpenDataAdapter:
    """A cache-first adapter for the documented StatsBomb Open Data layout."""

    def __init__(self, cache_dir: str | Path = "data/cache/statsbomb", workers: int = 8):
        self.cache_dir = Path(cache_dir)
        self.workers = workers
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "SignalRoom/0.1 research case study"})

    def _get_json(self, relative_path: str) -> Any:
        target = self.cache_dir / relative_path
        if target.exists():
            return json.loads(target.read_text(encoding="utf-8"))
        target.parent.mkdir(parents=True, exist_ok=True)
        url = f"{BASE_URL}/{relative_path}"
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                response = self.session.get(url, timeout=90)
                response.raise_for_status()
                payload = response.json()
                target.write_text(json.dumps(payload), encoding="utf-8")
                return payload
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"Unable to acquire {url}: {last_error}")

    def competitions(self) -> list[dict[str, Any]]:
        return self._get_json("competitions.json")

    def load_case(self, config: CaseConfig) -> tuple[list[Match], list[Event]]:
        raw_matches = self._get_json(f"matches/{config.competition_id}/{config.season_id}.json")
        selected = [
            raw
            for raw in raw_matches
            if config.team
            in (raw["home_team"]["home_team_name"], raw["away_team"]["away_team_name"])
        ]
        selected.sort(key=lambda raw: (raw["match_date"], raw["match_id"]))
        if not selected:
            raise ValueError(
                f"Team {config.team!r} not found in competition={config.competition_id}, "
                f"season={config.season_id}"
            )
        matches = [self._parse_match(raw, config) for raw in selected]
        raw_by_match: dict[int, list[dict[str, Any]]] = {}
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {
                pool.submit(self._get_json, f"events/{match.match_id}.json"): match.match_id
                for match in matches
            }
            for future in as_completed(futures):
                raw_by_match[futures[future]] = future.result()
        events = [
            self._parse_event(raw, match.match_id)
            for match in matches
            for raw in raw_by_match[match.match_id]
        ]
        return matches, events

    @staticmethod
    def _parse_match(raw: dict[str, Any], config: CaseConfig) -> Match:
        return Match(
            match_id=int(raw["match_id"]),
            date=raw["match_date"],
            home_team=raw["home_team"]["home_team_name"],
            away_team=raw["away_team"]["away_team_name"],
            competition=config.competition_label,
            season=config.season_label,
        )

    @staticmethod
    def _parse_event(raw: dict[str, Any], match_id: int) -> Event:
        location = raw.get("location") or [None, None]
        detail = raw.get("pass") or raw.get("carry") or raw.get("shot") or {}
        end_location = detail.get("end_location") or [None, None]
        return Event(
            event_id=str(raw["id"]),
            match_id=match_id,
            index=int(raw["index"]),
            period=int(raw["period"]),
            timestamp=raw["timestamp"],
            minute=int(raw["minute"]),
            second=int(raw["second"]),
            team=raw["team"]["name"],
            player=(raw.get("player") or {}).get("name"),
            event_type=raw["type"]["name"],
            possession=int(raw["possession"]),
            possession_team=raw["possession_team"]["name"],
            play_pattern=raw["play_pattern"]["name"],
            x=_number(location, 0),
            y=_number(location, 1),
            end_x=_number(end_location, 0),
            end_y=_number(end_location, 1),
            outcome=detail.get("outcome", {}).get("name"),
            subtype=detail.get("type", {}).get("name"),
            xg=(raw.get("shot") or {}).get("statsbomb_xg"),
            raw=raw,
        )


def _number(values: list[Any], index: int) -> float | None:
    if len(values) <= index or values[index] is None:
        return None
    return float(values[index])
