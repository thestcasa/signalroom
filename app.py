from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).parent
CASE_ROOT = ROOT / "artifacts" / "cases"

st.set_page_config(page_title="SignalRoom", page_icon="◉", layout="wide")
st.markdown(
    """
    <style>
    :root { --ink:#102A43; --teal:#00A6A6; --coral:#FF6B5E; --paper:#F7F5EF; }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(247,245,239,.9); }
    .block-container { max-width: 1240px; padding-top: 2rem; }
    .brand { font-size:1.05rem; font-weight:900; letter-spacing:.13em; margin-bottom:2.5rem; }
    .brand span { color:var(--teal); }
    .eyebrow { color:var(--coral); text-transform:uppercase; letter-spacing:.16em; font-weight:800; font-size:.7rem; }
    .hero-title { font-size:clamp(3rem,7vw,6.8rem); line-height:.89; font-weight:850; letter-spacing:-.06em; margin:.55rem 0 1rem; }
    .hero-copy { color:#48677A; font-size:1.1rem; max-width:760px; }
    .signal-card { background:white; border:1px solid #D7E1E6; border-radius:14px; padding:1.2rem; min-height:180px; box-shadow:0 8px 30px rgba(16,42,67,.045); }
    .signal-card h3 { margin:.4rem 0 .65rem; font-size:1.25rem; }
    .reliability { display:inline-block; padding:.23rem .55rem; border-radius:99px; background:#E2F5F1; color:#08766F; font-size:.68rem; font-weight:800; text-transform:uppercase; }
    .evidence-code { font-family:ui-monospace,monospace; color:#587287; font-size:.72rem; }
    .quiet { color:#587287; }
    div[data-testid="stMetric"] { background:white; border:1px solid #D7E1E6; padding:1rem; border-radius:12px; }
    .footer { border-top:1px solid #D1DDE2; margin-top:3rem; padding:1.3rem 0; color:#587287; font-size:.78rem; }
    </style>
    """,
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
st.image(str(ROOT / "assets" / "statsbomb-open-data-logo.png"), width=165)
selected_label = st.selectbox("Historical case", list(labels), label_visibility="collapsed")
case_path = labels[selected_label]
bundle, metrics = load_case(str(case_path))
case = bundle["case"]

st.markdown(
    '<div class="eyebrow">Evidence-linked historical briefing</div>', unsafe_allow_html=True
)
st.markdown(f'<div class="hero-title">{case["team"]}</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-copy">A prioritized review of match-window changes and attacking-corner routines. '
    "The system publishes only findings that pass its stability, magnitude, and evidence gates.</p>",
    unsafe_allow_html=True,
)

metric_cols = st.columns(4)
metric_cols[0].metric("Matches", case["matches"])
metric_cols[1].metric("Source events", f"{bundle['data']['events']:,}")
metric_cols[2].metric("Attacking corners", bundle["set_piece_lab"]["corner_count"])
metric_cols[3].metric("Published changes", len(bundle["findings"]))

briefing_tab, set_piece_tab, evidence_tab, method_tab = st.tabs(
    ["Briefing", "SetPieceLab", "Evidence room", "Method & limits"]
)

with briefing_tab:
    st.subheader("Changes worth analyst attention")
    st.caption(
        f"Baseline {bundle['method']['baseline_matches']} matches versus the latest "
        f"{bundle['method']['recent_matches']} matches. Historical analysis only."
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
    st.image(str(case_path / "assets" / "metric_comparison.png"), width="stretch")
    st.image(str(case_path / "assets" / "metric_trend.png"), width="stretch")
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

with set_piece_tab:
    st.subheader("Attacking corner routines")
    st.caption(
        "Deterministic grouping by delivery side, short/direct choice, and first delivery zone. "
        "Routine shares include 95% Wilson intervals."
    )
    left, right = st.columns([1.15, 0.85])
    left.image(str(case_path / "assets" / "corner_map.png"), width="stretch")
    right.image(str(case_path / "assets" / "routine_shares.png"), width="stretch")
    routines = pd.DataFrame(bundle["set_piece_lab"]["published_routines"])
    if not routines.empty:
        display = routines[["routine", "count", "share", "shots", "xg", "shot_rate"]].copy()
        display["share"] = (display["share"] * 100).map(lambda value: f"{value:.1f}%")
        display["shot_rate"] = (display["shot_rate"] * 100).map(lambda value: f"{value:.1f}%")
        display["xg"] = display["xg"].map(lambda value: f"{value:.2f}")
        st.dataframe(display, hide_index=True, width="stretch")

with evidence_tab:
    st.subheader("Trace every finding to source records")
    evidence = bundle["evidence"]
    options = {
        f"{row['evidence_id']} · {row['match_date']} vs {row['opponent']} · {row['label']}": row
        for row in evidence
    }
    selected_evidence = options[st.selectbox("Evidence sequence", list(options))]
    info_cols = st.columns(4)
    info_cols[0].metric("Reference", selected_evidence["evidence_id"])
    info_cols[1].metric("Match ID", selected_evidence["match_id"])
    info_cols[2].metric("Minute", selected_evidence["start_minute"])
    info_cols[3].metric("Source events", len(selected_evidence["source_event_ids"]))
    event_frame = pd.DataFrame(selected_evidence["events"])
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

with method_tab:
    st.subheader("Publication gates")
    st.write(bundle["method"]["selection_rule"])
    st.json(bundle["method"], expanded=True)
    st.subheader("Metric definitions")
    definitions = pd.DataFrame(bundle["comparisons"])[["label", "definition", "unit"]]
    st.dataframe(definitions, hide_index=True, width="stretch")
    st.subheader("Known limitations")
    for limitation in bundle["data"]["limitations"]:
        st.markdown(f"- {limitation}")
    st.markdown(
        "**Positioning:** SignalRoom supports teams and competitions available through its implemented "
        "event-data adapters. This version uses StatsBomb Open Data and is designed so additional "
        "providers can be added later."
    )

st.markdown(
    f"""<div class="footer"><b>Data: StatsBomb Open Data.</b> No affiliation with {case["team"]} or any club is claimed. 
    This is a historical analytical case study, not current tactical advice. Generated {bundle["generated_at"]}.</div>""",
    unsafe_allow_html=True,
)
