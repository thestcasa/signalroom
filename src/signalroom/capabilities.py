from __future__ import annotations

from typing import Any

CAPABILITY_REGISTRY: dict[str, dict[str, Any]] = {
    "event": {
        "label": "Level 1 · event data",
        "supports": [
            "recorded restart classification",
            "delivery locations",
            "first recorded post-delivery event",
            "shots and xG",
            "recorded player roles",
        ],
        "cannot_verify": [
            "physical first contact",
            "football phases",
            "off-ball movement",
            "screens",
            "marking structure",
            "tactical intent",
            "video clips",
        ],
        "source_status": "implemented",
    },
    "event_360": {
        "label": "Level 2 · event plus 360",
        "supports": [
            "event-linked position snapshots",
            "visible-area polygons",
            "spacing at a snapshot",
        ],
        "cannot_verify": ["continuous runs", "screens", "assignments", "synchronized video review"],
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
