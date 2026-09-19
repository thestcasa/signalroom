from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class RightsError(ValueError):
    """Raised when an artifact would exceed the declared source rights."""


@dataclass(frozen=True)
class RightsManifest:
    provider: str
    source_revision: str
    publication_mode: str
    rights: dict[str, str]
    attribution: dict[str, Any]
    license_reference: str
    source_repository: str

    @classmethod
    def load(cls, path: str | Path) -> RightsManifest:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            provider=str(payload["provider"]),
            source_revision=str(payload["source_revision"]),
            publication_mode=str(payload["publication_mode"]),
            rights=dict(payload["rights"]),
            attribution=dict(payload["attribution"]),
            license_reference=str(payload["license_reference"]),
            source_repository=str(payload["source_repository"]),
        )

    def require_public_artifact(self, artifact_class: str) -> None:
        key = {
            "derived_aggregate": "derived_aggregates_public",
            "derived_sequence_summary": "derived_sequence_summaries_public",
            "source_event_id": "source_event_ids_public",
            "source_event_excerpt": "source_event_excerpts_public",
            "raw_record": "raw_redistribution",
        }.get(artifact_class)
        if key is None:
            raise RightsError(f"Unknown artifact rights class: {artifact_class}")
        status = self.rights.get(key, "unresolved")
        if not status.startswith("allowed"):
            raise RightsError(
                f"Public artifact class {artifact_class!r} is blocked by {key}={status!r}"
            )

    def public_metadata(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "source_revision": self.source_revision,
            "publication_mode": self.publication_mode,
            "license_reference": self.license_reference,
            "attribution": self.attribution,
            "blocked_public_artifacts": [
                "raw records",
                "source event identifiers",
                "source event excerpts",
            ],
        }


def default_rights_manifest() -> RightsManifest:
    root = Path(__file__).resolve().parents[2]
    return RightsManifest.load(root / "manifests" / "statsbomb-open-data.json")


def validate_public_payload(payload: Any) -> list[str]:
    """Reject provider record leakage from a generated public bundle.

    Public evidence uses SignalRoom-owned opaque IDs and derived summaries. Provider
    event IDs, raw payloads, and source coordinate arrays must stay in the ignored cache.
    """
    errors: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            forbidden = {"raw", "source_event_ids", "start_event_id", "event_id"}
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else key
                if key in forbidden:
                    errors.append(f"Forbidden public source field at {child_path}")
                walk(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(payload, "")
    return errors
