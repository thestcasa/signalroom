from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .models import EvidenceSequence
from .statistics import MetricComparison

INK = "#102A43"
TEAL = "#007C7C"
CORAL = "#B9473D"
MIST = "#E8F1F5"
PAPER = "#F7F5EF"


def metric_comparison_chart(comparisons: list[MetricComparison], output: Path) -> None:
    published = [item for item in comparisons if item.publish]
    valid = [item for item in comparisons if item.standardized_effect is not None]
    displayed = (
        published
        or sorted(valid, key=lambda item: abs(item.standardized_effect or 0.0), reverse=True)[:3]
    )
    labels = [item.label for item in displayed]
    effects = [float(item.standardized_effect or 0.0) for item in displayed]
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(9.5, max(3.2, len(labels) * 1.2)), facecolor=PAPER)
    ax.set_facecolor(PAPER)
    colors = [TEAL if value >= 0 else CORAL for value in effects]
    ax.barh(y, effects, height=0.46, color=colors)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.axvline(0, color=INK, linewidth=0.9)
    ax.set_xlabel("Hedges g (recent window relative to baseline)")
    title = "Published standardized changes" if published else "Strongest descriptive changes"
    ax.set_title(title, loc="left", color=INK, fontsize=16, weight="bold", pad=30)
    if not published:
        ax.text(
            0,
            1.015,
            "None passed every publication gate",
            transform=ax.transAxes,
            color="#587287",
            fontsize=9,
            va="bottom",
        )
    for index, item in enumerate(displayed):
        value = effects[index]
        detail = f"{item.baseline_value:.2f} → {item.recent_value:.2f} {item.unit}"
        annotation_x = value if value >= 0 else 0.0
        ax.annotate(
            detail,
            xy=(annotation_x, index),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            ha="left",
            fontsize=8,
            color=INK,
        )
    ax.grid(axis="x", alpha=0.18)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)


def corner_map(sequences: list[EvidenceSequence], output: Path, team: str) -> None:
    points = []
    for sequence in sequences:
        first = sequence.events[0]
        start = first["location"]
        end = first["end_location"]
        if None not in start + end:
            points.append((float(start[0]), float(start[1]), float(end[0]), float(end[1])))
    fig, ax = plt.subplots(figsize=(9.5, 6.2), facecolor=PAPER)
    ax.set_facecolor("#113D36")
    _draw_pitch(ax)
    for x, y, end_x, end_y in points:
        ax.plot([x, end_x], [y, end_y], color="#8BE0D5", alpha=0.20, linewidth=1)
        ax.scatter(end_x, end_y, s=18, color=CORAL, alpha=0.55, edgecolors="none")
    ax.set_title(
        f"{team} attacking-corner deliveries", loc="left", color=INK, fontsize=15, weight="bold"
    )
    ax.text(
        0,
        -7,
        f"{len(points)} deliveries. Each line is linked to its source event in the evidence table.",
        color=INK,
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)


def routine_share_chart(routines: list[dict[str, object]], output: Path) -> None:
    rows = [row for row in routines if row["publish"]][:6]
    labels = [str(row["routine"]) for row in rows][::-1]
    shares = [float(row["share"]) * 100 for row in rows][::-1]
    lower = [float(row["share_ci_low"]) * 100 for row in rows][::-1]
    upper = [float(row["share_ci_high"]) * 100 for row in rows][::-1]
    errors = np.array(
        [
            [value - low for value, low in zip(shares, lower, strict=True)],
            [high - value for value, high in zip(shares, upper, strict=True)],
        ]
    )
    fig, ax = plt.subplots(figsize=(9.5, max(3.5, len(rows) * 0.72)), facecolor=PAPER)
    ax.set_facecolor(PAPER)
    ax.barh(
        labels, shares, color=TEAL, xerr=errors, capsize=3, error_kw={"ecolor": INK, "alpha": 0.7}
    )
    ax.set_xlabel("Share of attacking corners (%)")
    ax.set_title("Repeatable corner routines", loc="left", color=INK, fontsize=16, weight="bold")
    ax.grid(axis="x", alpha=0.18)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)


def trend_chart(frame: pd.DataFrame, metric: str, label: str, output: Path, recent_n: int) -> None:
    values = frame[metric].astype(float)
    rolling = values.rolling(5, min_periods=3).mean()
    fig, ax = plt.subplots(figsize=(10, 3.8), facecolor=PAPER)
    ax.set_facecolor(PAPER)
    ax.plot(frame["date"], values, color="#A9BAC6", marker="o", linewidth=1, label="Match")
    ax.plot(frame["date"], rolling, color=TEAL, linewidth=2.5, label="5-match mean")
    ax.axvspan(len(frame) - recent_n - 0.5, len(frame) - 0.5, color=CORAL, alpha=0.08)
    ax.set_title(label, loc="left", color=INK, fontsize=14, weight="bold")
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False, ncol=2)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)


def _draw_pitch(ax: plt.Axes) -> None:
    line = "#D8F0E9"
    ax.plot([0, 120, 120, 0, 0], [0, 0, 80, 80, 0], color=line, linewidth=1.5)
    ax.plot([60, 60], [0, 80], color=line, linewidth=1)
    ax.add_patch(plt.Circle((60, 40), 10, fill=False, edgecolor=line, linewidth=1))
    ax.plot([102, 120, 120, 102, 102], [18, 18, 62, 62, 18], color=line, linewidth=1)
    ax.plot([0, 18, 18, 0], [18, 18, 62, 62], color=line, linewidth=1)
    ax.set_xlim(-2, 122)
    ax.set_ylim(82, -2)
    ax.set_aspect("equal")
    ax.axis("off")
