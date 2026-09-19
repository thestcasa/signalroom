from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

from .evidence import validate_bundle_evidence


def deterministic_finding_text(finding: dict[str, object]) -> str:
    direction = "increased" if float(finding["absolute_change"]) > 0 else "decreased"
    return (
        f"{finding['label']} {direction} from {float(finding['baseline_value']):.2f} "
        f"to {float(finding['recent_value']):.2f} {finding['unit']}. "
        f"The match-resampled 95% interval for the change was "
        f"[{float(finding['ci_low']):.2f}, {float(finding['ci_high']):.2f}], "
        f"with {finding['reliability']} reliability."
    )


def validate_grounded_bundle(bundle: dict[str, Any]) -> list[str]:
    errors = validate_bundle_evidence(bundle)
    if bundle.get("schema_version") != "2.0.0":
        errors.append("Expected schema version 2.0.0")
    if not bundle.get("case", {}).get("historical_only"):
        errors.append("Case must remain explicitly historical")
    coverage = bundle.get("data", {}).get("coverage", {})
    peer = bundle.get("peer_baseline", {})
    if peer.get("status") == "descriptive" and not coverage.get("complete"):
        errors.append("Peer baseline published from incomplete fixture coverage")
    evidence_ids = [str(row["evidence_id"]) for row in bundle.get("evidence", [])]
    if len(evidence_ids) != len(set(evidence_ids)):
        errors.append("Duplicate public evidence IDs")
    if any("source_event_ids" in row for row in bundle.get("evidence", [])):
        errors.append("Public evidence must not include source event IDs")
    return errors


def write_html_report(bundle: dict[str, Any], output: Path) -> None:
    groups = bundle["set_piece_lab"]["delivery_groups"][:8]
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row['delivery_group']))}</td>"
        f"<td>{int(row['count'])}</td>"
        f"<td>{int(row['matches'])}</td>"
        f"<td>{float(row['share']) * 100:.1f}%</td>"
        f"<td>{int(row['corners_with_shot'])}</td>"
        "</tr>"
        for row in groups
    )
    peer = bundle.get("peer_baseline", {})
    peer_text = (
        f"Complete {int(peer['teams'])}-team competition population, with "
        f"{int(peer['peer_teams'])} leave-target-out peers."
        if peer.get("status") == "descriptive"
        else f"Peer comparison suppressed: {escape(str(peer.get('reason', 'unavailable')))}."
    )
    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SignalRoom | {escape(str(bundle["case"]["team"]))}</title><style>{_css()}</style></head>
<body><header><div class="brand">SIGNAL<span>ROOM</span></div><div>Historical set-piece evidence workbench</div></header>
<main><section class="hero"><div class="eyebrow">Historical case · cutoff {escape(str(bundle["case"]["historical_cutoff"]))}</div>
<h1>{escape(str(bundle["case"]["team"]))}</h1><p>{escape(str(bundle["positioning"]))}</p>
<div class="stats"><b>{bundle["case"]["matches"]}</b><span>target matches</span><b>{bundle["dead_ball_lab"]["sequence_count"]}</b><span>recorded dead balls</span></div></section>
<section><div class="eyebrow">Coverage</div><h2>Declared population</h2><p>{peer_text}</p><p>Public output contains attributed aggregates and derived evidence summaries. Raw provider records and source event IDs are not redistributed.</p></section>
<section><div class="eyebrow">Recorded corners</div><h2>Delivery groups</h2><table><thead><tr><th>Group</th><th>n</th><th>Matches</th><th>Share</th><th>Shot-producing</th></tr></thead><tbody>{rows}</tbody></table></section>
<section><div class="eyebrow">Evidence</div><h2>{len(bundle["evidence"])} resolvable derived summaries</h2><p>Each displayed reference resolves to a rights-safe evidence card with match context, recorded player roles, outcome, termination, quality state and provenance.</p></section>
<section class="limits"><h2>What this does not establish</h2><ul>{"".join(f"<li>{escape(str(item))}</li>" for item in bundle["data"]["limitations"])}</ul></section>
<footer><img src="assets/statsbomb-open-data-logo.png" alt="StatsBomb Open Data"><p>Data: StatsBomb Open Data. Historical analysis only. No club or provider endorsement is claimed. Source revision {escape(str(bundle["data"]["source_revision"]))}.</p></footer>
</main></body></html>"""
    output.write_text(html, encoding="utf-8")


def preparation_brief_html(
    bundle: dict[str, Any],
    comparisons: list[dict[str, Any]],
    baseline_label: str,
    recent_matches: int,
    baseline_matches: int,
    analyst_notes: str = "",
) -> str:
    eligible = [row for row in comparisons if row.get("review_eligible")][:5]
    if eligible:
        observations = "".join(
            f"<article><h3>{escape(str(row['delivery_group']))}</h3>"
            f"<p>{int(row['recent_count'])}/{int(row['recent_total'])} recent versus "
            f"{int(row['reference_count'])}/{int(row['reference_total'])} reference. "
            f"Difference {float(row['share_difference']) * 100:+.1f} pp, match-block 95% interval "
            f"[{float(row['ci_low']) * 100:.1f}, {float(row['ci_high']) * 100:.1f}] pp. "
            f"Match support {int(row['recent_match_support'])} recent and "
            f"{int(row['reference_match_support'])} reference.</p>"
            f"<p>Derived evidence: {escape(', '.join(str(value) for value in row['evidence_ids']))}</p></article>"
            for row in eligible
        )
    else:
        observations = (
            "<p><strong>No delivery-group difference passed every review gate.</strong> "
            "The descriptive distribution remains available without a change claim.</p>"
        )
    notes = escape(analyst_notes.strip()) if analyst_notes.strip() else "No analyst notes recorded."
    limitations = "".join(f"<li>{escape(str(item))}</li>" for item in bundle["data"]["limitations"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>SignalRoom briefing | {escape(str(bundle["case"]["team"]))}</title><style>{_brief_css()}</style></head>
<body><div class='eyebrow'>SignalRoom · historical recorded set pieces</div><h1>{escape(str(bundle["case"]["team"]))}</h1>
<p class='meta'>{escape(str(bundle["case"]["competition"]))} · {escape(str(bundle["case"]["season"]))} · cutoff {escape(str(bundle["case"]["historical_cutoff"]))} · {escape(baseline_label)} · recent {recent_matches} versus preceding {baseline_matches} matches</p>
<h2>Review shortlist</h2>{observations}<h2>Analyst notes</h2><p>{notes}</p>
<h2>Definitions</h2><p>Groups describe recorded corner delivery side, pass length category and target lane. They do not establish a routine, tactical intent, danger or causality. Uncertainty resamples complete matches.</p>
<h2>Limitations</h2><ul>{limitations}</ul>
<footer>Data: StatsBomb Open Data. Public output contains derived analysis, not raw provider records or source event IDs. Historical case, no club or provider endorsement, and no external analyst validation.</footer></body></html>"""


def dump_bundle(bundle: dict[str, Any], output: Path) -> None:
    output.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")


def _css() -> str:
    return """
:root{--ink:#102a43;--teal:#007c7c;--coral:#b9473d;--paper:#f7f5ef}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,system-ui,sans-serif}header{display:flex;justify-content:space-between;padding:22px 5vw;border-bottom:1px solid #cdd9df}.brand{font-weight:900;letter-spacing:.08em}.brand span{color:var(--teal)}main{max-width:1050px;margin:auto;padding:0 28px}.hero{padding:90px 0 55px}.hero h1{font-size:clamp(48px,8vw,92px);line-height:.92;margin:12px 0;letter-spacing:-.05em}.hero p{max-width:720px;font-size:19px;color:#45657a}.eyebrow{text-transform:uppercase;letter-spacing:.16em;font-size:11px;font-weight:800;color:var(--coral)}.stats{display:flex;gap:15px;align-items:baseline;margin-top:28px}.stats b{font-size:28px}.stats span{color:#587287;margin-right:18px}section{margin:35px 0 65px}h2{font-size:34px;margin:8px 0 18px}table{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden}th,td{text-align:left;padding:13px;border-bottom:1px solid #e3eaed;font-size:13px}.limits{background:#102a43;color:white;padding:28px;border-radius:14px}.limits li{margin:9px 0;color:#dce8ed}footer{border-top:1px solid #d3dee3;padding:28px 0 50px;font-size:12px;color:#5b7383}footer img{width:150px}@media(max-width:680px){header{display:block}.hero{padding-top:55px}.stats{display:grid;grid-template-columns:auto 1fr}th,td{padding:9px 6px;font-size:11px}}
"""


def _brief_css() -> str:
    return """body{font-family:Inter,system-ui,sans-serif;color:#102a43;background:#f7f5ef;max-width:900px;margin:0 auto;padding:40px 24px;line-height:1.45}h1{font-size:48px;line-height:1;margin:12px 0}h2{margin-top:42px}.eyebrow{color:#9e3e35;text-transform:uppercase;letter-spacing:.14em;font-size:11px;font-weight:800}article{background:white;border:1px solid #d7e1e6;border-radius:12px;padding:18px;margin:12px 0}.meta{color:#587287}footer{border-top:1px solid #d7e1e6;margin-top:42px;padding-top:18px;font-size:12px;color:#587287}"""
