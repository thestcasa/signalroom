from __future__ import annotations

import json
from html import escape
from pathlib import Path


def deterministic_finding_text(finding: dict[str, object]) -> str:
    direction = "increased" if float(finding["absolute_change"]) > 0 else "decreased"
    return (
        f"{finding['label']} {direction} from {float(finding['baseline_value']):.2f} "
        f"to {float(finding['recent_value']):.2f} {finding['unit']}. "
        f"The match-resampled 95% interval for the change was "
        f"[{float(finding['ci_low']):.2f}, {float(finding['ci_high']):.2f}], "
        f"with {finding['reliability']} reliability."
    )


def validate_grounded_bundle(bundle: dict[str, object]) -> list[str]:
    errors: list[str] = []
    evidence = {row["evidence_id"] for row in bundle["evidence"]}
    for finding in bundle["findings"]:
        if not finding["publish"]:
            errors.append(f"Suppressed metric leaked into findings: {finding['metric']}")
        if len(finding["evidence_ids"]) < bundle["method"]["minimum_evidence_sequences"]:
            errors.append(f"Insufficient evidence for {finding['metric']}")
        missing = set(finding["evidence_ids"]) - evidence
        if missing:
            errors.append(f"Missing evidence references for {finding['metric']}: {sorted(missing)}")
        expected = deterministic_finding_text(finding)
        if finding["narrative"] != expected:
            errors.append(f"Narrative mismatch for {finding['metric']}")
    for routine in bundle["set_piece_lab"]["published_routines"]:
        missing = set(routine["evidence_ids"]) - evidence
        if missing:
            errors.append(f"Missing routine evidence: {sorted(missing)}")
    return errors


def write_html_report(bundle: dict[str, object], output: Path) -> None:
    findings = bundle["findings"]
    if findings:
        finding_cards = "".join(
            f"""<article class="card"><div class="eyebrow">{escape(str(row["reliability"]))} reliability</div>
            <h3>{escape(str(row["label"]))}</h3><p>{escape(str(row["narrative"]))}</p>
            <p class="evidence">Evidence: {", ".join(escape(str(value)) for value in row["evidence_ids"])}</p></article>"""
            for row in findings
        )
    else:
        finding_cards = "<article class='card'><h3>No broad changes passed the gate</h3><p>The system suppressed every tested metric. Review the descriptive diagnostics, but do not publish a tactical-change claim.</p></article>"
    routines = "".join(
        f"<tr><td>{escape(str(row['routine']))}</td><td>{row['count']}</td><td>{float(row['share']) * 100:.1f}%</td><td>{row['corners_with_shot']}</td><td>{float(row['shot_rate']) * 100:.1f}%</td><td>{row['shots']}</td><td>{float(row['xg']):.2f}</td></tr>"
        for row in bundle["set_piece_lab"]["published_routines"][:6]
    )
    html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>SignalRoom | {escape(str(bundle["case"]["team"]))}</title><style>{_css()}</style></head>
    <body><header><div class="brand">SIGNAL<span>ROOM</span></div><div class="tag">Evidence-linked football intelligence</div></header>
    <main><section class="hero"><div><div class="eyebrow">Historical case study · {escape(str(bundle["case"]["season"]))}</div>
    <h1>{escape(str(bundle["case"]["team"]))}</h1><p class="lede">A cautious match-window review with a complete attacking-corner evidence trail.</p></div>
    <div class="stat"><b>{bundle["case"]["matches"]}</b><span>matches</span><b>{bundle["set_piece_lab"]["corner_count"]}</b><span>corners</span></div></section>
    <section><div class="section-head"><div><div class="eyebrow">SignalRoom</div><h2>Changes worth analyst attention</h2></div><p>Baseline: {bundle["method"]["baseline_matches"]} matches · Recent: {bundle["method"]["recent_matches"]} matches</p></div>
    <div class="grid">{finding_cards}</div><img class="wide" src="assets/metric_comparison.png" alt="Metric comparison"></section>
    <section><div class="section-head"><div><div class="eyebrow">SetPieceLab</div><h2>Attacking corner routines</h2></div><p>Clusters below require at least four examples.</p></div>
    <div class="split"><img src="assets/corner_map.png" alt="Corner delivery map"><img src="assets/routine_shares.png" alt="Routine shares"></div>
    <table><thead><tr><th>Routine</th><th>n</th><th>Share</th><th>Corners with shot</th><th>Conversion</th><th>Total shots</th><th>xG</th></tr></thead><tbody>{routines}</tbody></table></section>
    <section class="method"><div><div class="eyebrow">Method guardrails</div><h2>Built to abstain</h2></div><ul><li>Match-level bootstrap intervals and window sensitivity checks</li><li>Benjamini-Hochberg correction across tested metrics</li><li>Minimum sample and evidence-sequence gates</li><li>Every published claim links to source event IDs</li></ul></section>
    <footer><img src="assets/statsbomb-open-data-logo.png" alt="StatsBomb" class="source-logo"><br><b>Historical analysis, not current tactical advice.</b> Data: StatsBomb Open Data. No club affiliation or endorsement is claimed. Source revision {escape(str(bundle["data"]["source_revision"]))}.</footer>
    </main></body></html>"""
    output.write_text(html, encoding="utf-8")


def _css() -> str:
    return """
    :root{--ink:#102a43;--teal:#007c7c;--coral:#b9473d;--paper:#f7f5ef;--mist:#e8f1f5}*{box-sizing:border-box}
    body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,sans-serif}header{display:flex;justify-content:space-between;padding:22px 5vw;border-bottom:1px solid #cdd9df}.brand{font-weight:900;letter-spacing:.08em}.brand span{color:var(--teal)}.tag{font-size:13px;color:#547086}main{max-width:1180px;margin:auto;padding:0 28px}.hero{min-height:350px;display:flex;align-items:center;justify-content:space-between}.hero h1{font-size:clamp(48px,8vw,100px);line-height:.9;margin:14px 0;max-width:850px;letter-spacing:-.055em}.lede{font-size:20px;color:#45657a}.eyebrow{text-transform:uppercase;letter-spacing:.16em;font-size:11px;font-weight:800;color:var(--coral)}.stat{display:grid;grid-template-columns:auto auto;gap:3px 12px;border-left:4px solid var(--teal);padding-left:18px}.stat b{font-size:30px}.stat span{align-self:center;color:#587287}.section-head{display:flex;justify-content:space-between;align-items:end;margin:70px 0 22px}.section-head h2,.method h2{font-size:34px;margin:6px 0}.section-head p{font-size:13px;color:#587287}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}.card{background:white;border:1px solid #dce5e9;border-radius:14px;padding:22px;box-shadow:0 8px 30px rgba(16,42,67,.05)}.card h3{font-size:22px;margin:8px 0}.card p{line-height:1.55}.evidence{font:11px ui-monospace,monospace;color:#587287}.wide{width:100%;margin-top:18px;border-radius:14px}.split{display:grid;grid-template-columns:1.15fr .85fr;gap:18px}.split img{width:100%;background:white;border-radius:14px;border:1px solid #dce5e9}table{width:100%;border-collapse:collapse;margin-top:20px;background:white;border-radius:12px;overflow:hidden}th,td{text-align:left;padding:13px;border-bottom:1px solid #e3eaed;font-size:13px}.method{display:grid;grid-template-columns:1fr 1fr;background:var(--ink);color:white;padding:35px;margin:70px 0 30px;border-radius:16px}.method li{margin:10px 0;color:#dce8ed}footer{font-size:12px;color:#5b7383;padding:25px 0 50px;border-top:1px solid #d3dee3}@media(max-width:760px){.hero,.section-head{display:block}.stat{margin-top:35px;width:max-content}.split,.method{grid-template-columns:1fr}.hero{padding:70px 0}.section-head p{margin-top:8px}}
    .source-logo{width:150px;height:auto;margin-bottom:12px}
    """


def dump_bundle(bundle: dict[str, object], output: Path) -> None:
    output.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")
