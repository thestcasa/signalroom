from __future__ import annotations

import base64
import json
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from signalroom.models import EvidenceSequence
from signalroom.opponent import compare_routines
from signalroom.reporting import preparation_brief_html

ROOT = Path(__file__).parent
CASE_ROOT = ROOT / "artifacts" / "cases"

st.set_page_config(page_title="SignalRoom", page_icon="◉", layout="wide")
st.markdown(
    """
    <style>
    :root { --ink:#102A43; --teal:#007C7C; --coral:#B9473D; --paper:#F7F5EF; }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(247,245,239,.9); }
    .block-container { max-width: 1240px; padding-top: 2rem; }
    .brand { font-size:1.05rem; font-weight:900; letter-spacing:.13em; margin-bottom:2.5rem; }
    .brand span { color:var(--teal); }
    .eyebrow { color:var(--coral); text-transform:uppercase; letter-spacing:.16em; font-weight:800; font-size:.7rem; }
    .hero-title { font-size:clamp(3rem,7vw,6.8rem); line-height:.89; font-weight:850; letter-spacing:-.06em; margin:.55rem 0 1rem; }
    .hero-copy { color:#48677A; font-size:1.1rem; max-width:760px; }
    .workflow { display:flex; gap:.55rem; flex-wrap:wrap; margin:1rem 0 1.6rem; }
    .workflow span { background:#E8F1F5; border-radius:99px; padding:.45rem .7rem; font-size:.8rem; font-weight:750; }
    .workflow b { color:var(--coral); margin-right:.3rem; }
    .signal-card { background:white; border:1px solid #D7E1E6; border-radius:14px; padding:1.2rem; min-height:180px; box-shadow:0 8px 30px rgba(16,42,67,.045); }
    .signal-card h3 { margin:.4rem 0 .65rem; font-size:1.25rem; }
    .reliability { display:inline-block; padding:.23rem .55rem; border-radius:99px; background:#E2F5F1; color:#08766F; font-size:.68rem; font-weight:800; text-transform:uppercase; }
    .evidence-code { font-family:ui-monospace,monospace; color:#587287; font-size:.72rem; }
    .quiet { color:#587287; }
    div[data-testid="stMetric"] { background:white; border:1px solid #D7E1E6; padding:1rem; border-radius:12px; }
    .footer { border-top:1px solid #D1DDE2; margin-top:3rem; padding:1.3rem 0; color:#587287; font-size:.78rem; }
    .sr-image { display:block; width:100%; height:auto; border-radius:12px; }
    .source-logo { width:165px; height:auto; margin-bottom:1rem; }
    @media (max-width: 640px) {
      .block-container { padding-top:1rem; }
      .hero-title { font-size:2.6rem; overflow-wrap:anywhere; }
      .brand { margin-bottom:1.4rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def image_data_uri(path: str) -> str:
    encoded = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_image(path: Path, alt: str, css_class: str = "sr-image") -> None:
    st.markdown(
        f'<img class="{escape(css_class)}" src="{image_data_uri(str(path))}" '
        f'alt="{escape(alt)}">',
        unsafe_allow_html=True,
    )


@st.cache_data
def load_case(path: str) -> tuple[dict, pd.DataFrame]:
    case_path = Path(path)
    bundle = json.loads((case_path / "bundle.json").read_text(encoding="utf-8"))
    metrics = pd.read_csv(case_path / "match_metrics.csv")
    return bundle, metrics


case_dirs = sorted(path.parent for path in CASE_ROOT.glob("*/bundle.json"))
if not case_dirs:
    st.error("No case bundles found. Run `make build-cases` first.")
    st.stop()

labels = {}
for path in case_dirs:
    raw = json.loads((path / "bundle.json").read_text(encoding="utf-8"))
    labels[f"{raw['case']['team']} · {raw['case']['competition']} {raw['case']['season']}"] = path

st.markdown('<div class="brand">SIGNAL<span>ROOM</span></div>', unsafe_allow_html=True)
render_image(
    ROOT / "assets" / "statsbomb-open-data-logo.png",
    "StatsBomb Open Data",
    "source-logo",
)
selected_label = st.selectbox("Historical case", list(labels), label_visibility="collapsed")
case_path = labels[selected_label]
bundle, metrics = load_case(str(case_path))
case = bundle["case"]
dead_ball_lab = bundle.get("dead_ball_lab", {})

match_ids = metrics["match_id"].astype(int).tolist()
match_details = case.get("matches_detail") or [
    {"match_id": int(row.match_id), "date": str(row.date), "opponent": str(row.opponent)}
    for row in metrics.itertuples()
]
max_recent = max(2, min(10, len(match_ids) // 2))
with st.sidebar:
    st.markdown("### Preparation setup")
    st.caption("Advanced controls stay out of the opening view.")
    recent_n = st.slider("Recent window", 2, max_recent, min(6, max_recent))
    max_baseline = max(2, len(match_ids) - recent_n)
    baseline_n = st.slider("Previous window", 2, max_baseline, min(10, max_baseline))
    dimensions = st.multiselect(
        "Routine dimensions",
        ["side", "type", "zone"],
        default=["side", "type", "zone"],
        help="Choose how routines are grouped. Use fewer dimensions for broader families.",
    )
    minimum_sample = st.slider("Minimum routine sample", 2, 8, 4)

corner_rows = bundle["set_piece_lab"].get("routine_index") or [
    row for row in bundle["evidence"] if str(row["evidence_id"]).startswith("SP-")
]
corner_sequences = [
    EvidenceSequence(
        evidence_id=str(row["evidence_id"]),
        match_id=int(row["match_id"]),
        match_date=str(row["match_date"]),
        opponent=str(row["opponent"]),
        start_event_id=str(row["start_event_id"]),
        source_event_ids=tuple(row["source_event_ids"]),
        label=str(row["label"]),
        start_minute=int(row["start_minute"]),
        events=tuple(row["events"]),
        quality=dict(row.get("quality", {})),
    )
    for row in corner_rows
]
recent_ids = match_ids[-recent_n:]
baseline_ids = match_ids[-recent_n - baseline_n : -recent_n]
routine_comparisons = compare_routines(
    corner_sequences,
    {int(row["match_id"]): str(row["date"]) for row in match_details},
    recent_ids,
    baseline_ids,
    dimensions=tuple(dimensions),
    minimum_sample=minimum_sample,
    seed=int(bundle["method"].get("bootstrap_seed", 42)),
    bootstrap_samples=1000,
)
dead_ball_rows = [row for row in bundle["evidence"] if str(row["evidence_id"]).startswith("DB-")]

st.markdown(
    '<div class="eyebrow">Evidence-linked historical briefing</div>', unsafe_allow_html=True
)
st.markdown(
    f'<h1 class="hero-title">{escape(str(case["team"]))}</h1>', unsafe_allow_html=True
)
st.markdown(
    '<p class="hero-copy">Evidence-first opponent preparation from recorded match events. '
    "Find repeated or changing dead-ball behaviours, then open the sequences behind them.</p>",
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="workflow"><span><b>1</b>Choose the opponent</span><span><b>2</b>Find unusual or changing routines</span><span><b>3</b>Open the supporting evidence</span></div>',
    unsafe_allow_html=True,
)

metric_cols = st.columns(4)
metric_cols[0].metric("Matches", case["matches"])
metric_cols[1].metric("Source events", f"{bundle['data']['events']:,}")
metric_cols[2].metric("Final-third dead balls", dead_ball_lab.get("sequence_count", 0))
metric_cols[3].metric("Published changes", len(bundle["findings"]))

briefing_tab, dead_ball_tab, set_piece_tab, evidence_tab, method_tab = st.tabs(
    ["Briefing", "Dead-ball Lab", "SetPieceLab", "Evidence room", "Method & limits"]
)

with briefing_tab:
    st.subheader("What deserves review?")
    published_routines = [row for row in routine_comparisons if row.publish]
    if published_routines:
        st.success(f"{len(published_routines)} routine{'s' if len(published_routines) != 1 else ''} deserve review.")
    else:
        st.info("No broad routine difference passed every evidence gate.")
    st.caption(
        f"Selected team window: latest {recent_n} matches versus the previous {baseline_n}. "
        "Historical evidence only."
    )
    findings = bundle["findings"]
    if not findings:
        st.info(
            "No broad tactical-change metric passed every publication gate. This abstention is an output, "
            "not a missing report. Descriptive comparisons remain available below."
        )
    else:
        columns = st.columns(min(3, len(findings)))
        for index, finding in enumerate(findings):
            with columns[index % len(columns)]:
                st.markdown(
                    f"""<div class="signal-card"><span class="reliability">{finding["reliability"]}</span>
                    <h3>{finding["label"]}</h3><p>{finding["narrative"]}</p>
                    <div class="evidence-code">{", ".join(finding["evidence_ids"])}</div></div>""",
                    unsafe_allow_html=True,
                )
    render_image(
        case_path / "assets" / "metric_comparison.png",
        "Standardized comparison between baseline and recent match windows",
    )
    st.subheader("Routine share versus previous team window")
    if routine_comparisons:
        chart_frame = pd.DataFrame([
            {"Routine": row.routine, "Recent share": row.recent_share * 100, "Previous share": row.baseline_share * 100, "Low": row.ci_low * 100, "High": row.ci_high * 100, "n": row.sample_size}
            for row in routine_comparisons[:8]
        ])
        fig = go.Figure()
        fig.add_bar(x=chart_frame["Routine"], y=chart_frame["Recent share"], name="Recent", marker_color="#007C7C")
        fig.add_bar(x=chart_frame["Routine"], y=chart_frame["Previous share"], name="Previous", marker_color="#A9BDC7")
        fig.update_layout(barmode="group", height=420, yaxis_title="Share of attacking corners (%)", xaxis_title=None, legend_title=None, margin=dict(l=20,r=20,t=40,b=100), title="Which corner routines changed share?")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.caption("Bars show exact shares. Sample sizes and uncertainty appear in the routine table.")
    render_image(
        case_path / "assets" / "metric_trend.png",
        "Match-by-match trend for the strongest descriptive metric change",
    )
    with st.expander("Suppressed comparisons"):
        suppressed = [row for row in bundle["comparisons"] if not row["publish"]]
        st.dataframe(
            pd.DataFrame(suppressed)[
                [
                    "label",
                    "baseline_value",
                    "recent_value",
                    "standardized_effect",
                    "q_value",
                    "sensitivity_agreement",
                    "suppression_reason",
                ]
            ],
            hide_index=True,
            width="stretch",
        )

with dead_ball_tab:
    st.subheader("Attacking final-third dead balls")
    st.caption(
        "What this opponent records most often, what repeats across matches, and what deserves review. "
        "All findings are event-only and descriptive."
    )
    summaries = pd.DataFrame(dead_ball_lab.get("summaries", []))
    if summaries.empty:
        st.info("No supported final-third dead-ball sequences are available.")
    else:
        display = summaries[["restart_type", "count", "matches", "rate_per_match", "share", "total_shots", "shot_producing_rate", "total_xg", "xg_per_restart", "second_phase_rate", "repetition_matches", "publication"]].copy()
        for column in ["share", "shot_producing_rate", "second_phase_rate"]:
            display[column] = (display[column] * 100).map(lambda value: f"{value:.1f}%")
        for column in ["rate_per_match", "xg_per_restart"]:
            display[column] = display[column].map(lambda value: "n/a" if pd.isna(value) else f"{value:.2f}")
        display["total_xg"] = display["total_xg"].map(lambda value: "n/a" if pd.isna(value) else f"{value:.2f}")
        st.dataframe(display.rename(columns={"restart_type": "restart", "count": "n", "matches": "matches with sequence", "rate_per_match": "per match", "share": "share", "total_shots": "shots", "shot_producing_rate": "shot-producing rate", "total_xg": "xG", "xg_per_restart": "xG / restart", "second_phase_rate": "second-phase rate", "repetition_matches": "repetition across matches"}), hide_index=True, width="stretch")
        selected_restart = st.selectbox("Restart type", ["All"] + list(summaries["restart_type"]))
        if selected_restart != "All":
            selected_summary = next(row for row in dead_ball_lab["summaries"] if row["restart_type"] == selected_restart)
            st.write({
                "first-contact zones": selected_summary["first_contact_zones"],
                "delivery targets": selected_summary["delivery_targets"],
                "recurring players": selected_summary["recurring_players"],
                "recurring combinations": selected_summary["recurring_combinations"],
                "review questions": selected_summary["review_questions"],
                "publication": selected_summary["publication"],
                "suppression reasons": selected_summary["suppression_reasons"],
            })
    st.info("Capability: Level 1 event data. Video is not available in this data package, so off-ball movement, screens, marking and intent are not verified.")
    st.subheader("Exploratory team profile")
    st.write(dead_ball_lab.get("ml", {"status": "suppressed", "reason": "not available"}))

with set_piece_tab:
    st.subheader("Attacking corner routines")
    st.caption(
        "Deterministic grouping by delivery side, short/direct choice, and first delivery zone. "
        "Routine shares include 95% Wilson intervals."
    )
    left, right = st.columns([1.15, 0.85])
    with left:
        render_image(
            case_path / "assets" / "corner_map.png",
            "Pitch map of attacking-corner delivery locations",
        )
    with right:
        render_image(
            case_path / "assets" / "routine_shares.png",
            "Published attacking-corner routine shares with confidence intervals",
        )
    routines = pd.DataFrame(bundle["set_piece_lab"]["published_routines"])
    if not routines.empty:
        display = routines[
            [
                "routine",
                "count",
                "share",
                "corners_with_shot",
                "shot_rate",
                "shots",
                "xg",
            ]
        ].copy()
        display["share"] = (display["share"] * 100).map(lambda value: f"{value:.1f}%")
        display["shot_rate"] = (display["shot_rate"] * 100).map(lambda value: f"{value:.1f}%")
        display["xg"] = display["xg"].map(lambda value: f"{value:.2f}")
        display = display.rename(
            columns={
                "count": "corners",
                "corners_with_shot": "shot-producing corners",
                "shot_rate": "conversion",
                "shots": "total shots",
            }
        )
        st.dataframe(display, hide_index=True, width="stretch")
    st.subheader("Comparison observations")
    quality = bundle["set_piece_lab"].get("quality", {})
    st.caption("Data quality for the selected source sequences")
    qcols = st.columns(4)
    for column, (key, label) in zip(qcols, [("corner_length_complete", "Delivery length"), ("locations_complete", "Locations"), ("movement_endpoints_complete", "Move endpoints"), ("shot_xg_complete", "Shot xG")], strict=True):
        column.metric(label, f"{float(quality.get(key, 1))*100:.1f}%")
    st.caption("Routine share is suppressed below 90% completeness. Other metrics can remain valid when their own fields are complete.")
    comparison_frame = pd.DataFrame([row.to_dict() for row in routine_comparisons])
    if comparison_frame.empty:
        st.info("No corner sequences are available for this configuration.")
    else:
        visible = comparison_frame[["routine", "count", "baseline_count", "recent_share", "baseline_share", "absolute_share_difference", "ci_low", "ci_high", "stability", "publish", "evidence_ids", "suppression_reasons"]].copy()
        for column in ["recent_share", "baseline_share", "absolute_share_difference", "ci_low", "ci_high"]:
            visible[column] = (visible[column] * 100).map(lambda value: f"{value:.1f}%")
        visible = visible.rename(columns={"routine":"routine", "count":"recent n", "baseline_count":"previous n", "recent_share":"recent share", "baseline_share":"previous share", "absolute_share_difference":"difference", "ci_low":"CI low", "ci_high":"CI high", "publish":"published", "evidence_ids":"evidence", "suppression_reasons":"why suppressed"})
        st.dataframe(visible, hide_index=True, width="stretch")
        with st.expander("Why a routine was suppressed"):
            suppressed = [row.to_dict() for row in routine_comparisons if not row.publish]
            st.json(suppressed, expanded=False)
    brief = preparation_brief_html(bundle, [row.to_dict() for row in routine_comparisons], "previous team window", recent_n, baseline_n)
    st.download_button("Download deterministic briefing", data=brief, file_name=f"{case['slug']}-preparation-brief.html", mime="text/html")

with evidence_tab:
    st.subheader("Open the supporting sequences")
    evidence = bundle["evidence"]
    def evidence_label(row: dict) -> str:
        return str(row.get("label") or row.get("restart_type") or "sequence")

    def evidence_events(row: dict) -> list[dict]:
        return list(row.get("events") or row.get("ordered_events") or [])

    def evidence_minute(row: dict) -> int:
        if "start_minute" in row:
            return int(row["start_minute"])
        first = evidence_events(row)
        return int(first[0].get("minute", 0)) if first else 0

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        routine_filter = st.selectbox("Restart or routine", ["All"] + sorted({evidence_label(row) for row in evidence}))
    with col_b:
        opponent_filter = st.selectbox("Opponent", ["All"] + sorted({str(row["opponent"]) for row in evidence}))
    with col_c:
        outcome_filter = st.selectbox("Outcome", ["All", "Shot-producing", "No shot"])
    filtered_evidence = [row for row in evidence if (routine_filter == "All" or evidence_label(row) == routine_filter) and (opponent_filter == "All" or row["opponent"] == opponent_filter) and (outcome_filter == "All" or (outcome_filter == "Shot-producing") == any(event.get("type") == "Shot" and event.get("team") == case["team"] for event in evidence_events(row)))]
    options = {
        f"{row['evidence_id']} · {row['match_date']} vs {row['opponent']} · {evidence_label(row)}": row
        for row in filtered_evidence
    }
    if not options:
        st.warning("No sequences match these filters.")
        st.stop()
    selected_evidence = options[st.selectbox("Evidence sequence", list(options))]
    info_cols = st.columns(4)
    info_cols[0].metric("Reference", selected_evidence["evidence_id"])
    info_cols[1].metric("Match ID", selected_evidence["match_id"])
    info_cols[2].metric("Minute", evidence_minute(selected_evidence))
    info_cols[3].metric("Source events", len(selected_evidence["source_event_ids"]))
    event_frame = pd.DataFrame(evidence_events(selected_evidence))
    st.dataframe(event_frame, hide_index=True, width="stretch")
    locations = event_frame.dropna(subset=["location"])
    if not locations.empty:
        points = []
        for _, row in locations.iterrows():
            location = row["location"]
            if location and location[0] is not None:
                points.append(
                    {
                        "x": location[0],
                        "y": location[1],
                        "type": row["type"],
                        "player": row["player"],
                    }
                )
        if points:
            chart = px.scatter(
                pd.DataFrame(points),
                x="x",
                y="y",
                color="type",
                hover_name="player",
                range_x=[0, 120],
                range_y=[80, 0],
            )
            chart.update_layout(height=420, plot_bgcolor="#113D36", paper_bgcolor="#F7F5EF")
            st.plotly_chart(chart, width="stretch")
    st.code("\n".join(selected_evidence["source_event_ids"]), language=None)
    st.download_button("Export event identifiers", data="\n".join(selected_evidence["source_event_ids"]), file_name=f"{selected_evidence['evidence_id']}-events.txt", mime="text/plain")

with method_tab:
    st.subheader("Publication gates")
    st.write(bundle["method"]["selection_rule"])
    st.write("Capability registry", bundle.get("capability", {}))
    st.write("Supported dead-ball taxonomy", dead_ball_lab.get("supported_restart_types", []))
    st.write("Architecture-only future domains", dead_ball_lab.get("architecture_only_restart_types", []))
    st.caption("Peer prevalence is not published unless complete comparable source coverage is loaded. Recent change and repetition are separate questions.")
    st.json(bundle["method"], expanded=True)
    st.subheader("Metric definitions")
    definitions = pd.DataFrame(bundle["comparisons"])[["label", "definition", "unit"]]
    st.dataframe(definitions, hide_index=True, width="stretch")
    st.subheader("SetPieceLab definitions")
    st.markdown(
        "A short corner is a first delivery of at most 15 StatsBomb pitch units. "
        "Conversion is the share of corners whose retained-possession sequence contains at least "
        "one team shot within 20 seconds and 17 subsequent events. Total shots is shown separately."
    )
    st.subheader("Known limitations")
    for limitation in bundle["data"]["limitations"]:
        st.markdown(f"- {limitation}")
    st.markdown(
        "**Positioning:** SignalRoom supports teams and competitions available through its implemented "
        "event-data adapters. This version uses StatsBomb Open Data and is designed so additional "
        "providers can be added later."
    )

st.markdown(
    f"""<div class="footer"><b>Data: StatsBomb Open Data.</b> No affiliation with {escape(str(case["team"]))} or any club is claimed.
    This is a historical analytical case study, not current tactical advice. Source revision {escape(str(bundle["data"]["source_revision"]))}.</div>""",
    unsafe_allow_html=True,
)
