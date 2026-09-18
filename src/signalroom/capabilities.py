from __future__ import annotations

from typing import Any

CAPABILITY_REGISTRY: dict[str, dict[str, Any]] = {
    "event": {
        "label": "Level 1 · event data",
        "supports": [
            "restart classification", "delivery locations", "recorded first contact",
            "shots and xG", "second-phase recorded events", "player involvement",
        ],
        "cannot_verify": ["off-ball movement", "screens", "marking structure", "video clips"],
        "source_status": "implemented",
    },
    "event_360": {
        "label": "Level 2 · event plus 360",
        "supports": ["player positions", "team shape", "runs into zones", "spacing"],
        "cannot_verify": ["synchronized video review"],
        "source_status": "adapter-ready, not used in current cases",
    },
    "tracking": {
        "label": "Level 2 · tracking",
        "supports": ["continuous positions", "movement timing", "separation", "shape"],
        "cannot_verify": ["visual tactical intent without analyst review"],
        "source_status": "adapter-ready, not used in current cases",
    },
    "video": {
        "label": "Level 3 · synchronized video",
        "supports": ["visual verification", "screens", "decoy runs", "review clips"],
        "cannot_verify": [],
        "source_status": "not available in current cases",
    },
}


def capability_notice(level: str = "event") -> dict[str, Any]:
    value = dict(CAPABILITY_REGISTRY[level])
    value["level"] = level
    return value
