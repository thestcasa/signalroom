from __future__ import annotations

import base64
import json
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from signalroom.evidence import validate_bundle_evidence
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
    .stApp { background:var(--paper); color:var(--ink); }
    [data-testid="stHeader"] { background:rgba(247,245,239,.92); }
    .block-container { max-width:1240px; padding-top:1.5rem; }
    .brand { font-size:1.05rem; font-weight:900; letter-spacing:.13em; margin-bottom:1.7rem; }
    .brand span { color:var(--teal); }
    .eyebrow { color:var(--coral); text-transform:uppercase; letter-spacing:.16em; font-weight:800; font-size:.7rem; }
    .hero-title { font-size:clamp(3rem,7vw,6.2rem); line-height:.9; font-weight:850; letter-spacing:-.055em; margin:.55rem 0 1rem; }
    .hero-copy { color:#48677A; font-size:1.08rem; max-width:790px; }
    .context-strip { display:flex; gap:.55rem; flex-wrap:wrap; margin:1rem 0 1.5rem; }
    .context-strip span { background:#E8F1F5; border-radius:99px; padding:.45rem .72rem; font-size:.78rem; font-weight:700; }
    .evidence-card { background:white; border:1px solid #D7E1E6; border-radius:14px; padding:1.1rem; }
    .quiet { color:#587287; }
    div[data-testid="stMetric"] { background:white; border:1px solid #D7E1E6; padding:.9rem; border-radius:12px; }
    .source-logo { width:155px; height:auto; margin-bottom:.8rem; }
    .footer { border-top:1px solid #D1DDE2; margin-top:3rem; padding:1.3rem 0; color:#587287; font-size:.78rem; }
    @media (max-width:640px) { .block-container{padding-top:.8rem}.hero-title{font-size:2.55rem;overflow-wrap:anywhere}.brand{margin-bottom:1rem} }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_case(path: str) -> tuple[dict, pd.DataFrame]:
    case_path = Path(path)
    return (
        json.loads((case_path / "bundle.json").read_text(encoding="utf-8")),
        pd.read_csv(case_path / "match_metrics.csv"),
    )


@st.cache_data
def image_data_uri(path: str) -> str:
    encoded = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_logo(path: Path) -> None:
    st.markdown(
        f'<img class="source-logo" src="{image_data_uri(str(path))}" alt="StatsBomb Open Data">',
        unsafe_allow_html=True,
    )


case_dirs = sorted(path.parent for path in CASE_ROOT.glob("*/bundle.json"))
if not case_dirs:
    st.error("No case bundles found. Run `make build-cases` first.")
    st.stop()

labels: dict[str, Path] = {}
for path in case_dirs:
    raw = json.loads((path / "bundle.json").read_text(encoding="utf-8"))
    labels[f"{raw['case']['team']} · {raw['case']['competition']} {raw['case']['season']}"] = path

st.markdown('<div class="brand">SIGNAL<span>ROOM</span></div>', unsafe_allow_html=True)
render_logo(ROOT / "assets" / "statsbomb-open-data-logo.png")
selected_label = st.selectbox("Historical case", list(labels), label_visibility="collapsed")
case_path = labels[selected_label]
bundle, metrics = load_case(str(case_path))
case = bundle["case"]

grounding_errors = validate_bundle_evidence(bundle)
if grounding_errors:
    st.error("This case failed evidence-integrity checks and cannot be displayed.")
    st.code("\n".join(grounding_errors), language=None)
    st.stop()

match_details = case["matches_detail"]
match_ids = [int(row["match_id"]) for row in match_details]
match_dates = {int(row["match_id"]): str(row["date"]) for row in match_details}
max_recent = max(2, min(10, len(match_ids) // 2))
with st.sidebar:
    st.markdown("### Analysis context")
    st.caption("One context controls the shortlist, evidence and export.")
    recent_n = st.slider("Recent matches", 2, max_recent, min(6, max_recent))
    max_reference = max(2, len(match_ids) - recent_n)
    reference_n = st.slider("Preceding matches", 2, max_reference, min(10, max_reference))
    dimensions = st.multiselect(
        "Delivery-group dimensions",
        ["side", "type", "lane"],
        default=["side", "type", "lane"],
    )
    minimum_sample = st.slider("Minimum group sample", 2, 10, 4)

recent_ids = match_ids[-recent_n:]
reference_ids = match_ids[-recent_n - reference_n : -recent_n]
context_ids = set(recent_ids + reference_ids)

corner_sequences = [
    EvidenceSequence(
        evidence_id=str(row["evidence_id"]),
        match_id=int(row["match_id"]),
        match_date=str(row["match_date"]),
        opponent=str(row["opponent"]),
        start_event_id="rights-blocked",
        source_event_ids=(),
        label=str(row["label"]),
        start_minute=int(row["start_minute"]),
        events=tuple(row["events"]),
        quality=dict(row.get("quality", {})),
        evidence_status=str(row.get("evidence_status", "available-derived-summary")),
        termination_reason=str(row.get("termination_reason", "unknown")),
        censoring_reason=row.get("censoring_reason"),
        player_roles=dict(row.get("player_roles", {})),
    )
    for row in bundle["set_piece_lab"]["sequence_index"]
]
comparisons = compare_routines(
    corner_sequences,
    match_dates,
    recent_ids,
    reference_ids,
    dimensions=tuple(dimensions),
    minimum_sample=minimum_sample,
    seed=42,
    bootstrap_samples=int(bundle["method"]["bootstrap_samples"]),
)
comparison_rows = [row.to_dict() for row in comparisons]
evidence_by_id = {str(row["evidence_id"]): row for row in bundle["evidence"]}
eligible = [row for row in comparisons if row.review_eligible]

st.markdown(
    '<div class="eyebrow">Historical set-piece evidence workbench</div>', unsafe_allow_html=True
)
st.markdown(f'<h1 class="hero-title">{escape(str(case["team"]))}</h1>', unsafe_allow_html=True)
st.markdown(
    f'<p class="hero-copy">{escape(str(bundle["positioning"]))}</p>', unsafe_allow_html=True
)
st.markdown(
    f'<div class="context-strip"><span>Cutoff {escape(str(case["historical_cutoff"]))}</span>'
    f"<span>Recent {recent_n} matches</span><span>Reference {reference_n} matches</span>"
    f"<span>Event + lineup data</span><span>Historical only</span></div>",
    unsafe_allow_html=True,
)

coverage = bundle["data"]["coverage"]
cols = st.columns(4)
cols[0].metric("Target matches", case["matches"])
cols[1].metric("Population fixtures", coverage["received_fixtures"])
cols[2].metric("Recorded dead balls", bundle["dead_ball_lab"]["sequence_count"])
cols[3].metric("Review-eligible changes", len(eligible))

overview_tab, shortlist_tab, evidence_tab, peer_tab, method_tab = st.tabs(
    ["Overview", "Review shortlist", "Evidence review", "Peer context", "Method & quality"]
)

with overview_tab:
    st.subheader("Preparation context")
    context_frame = pd.DataFrame(
        [
            {
                "Window": "Recent",
                "From": match_dates[recent_ids[0]],
                "To": match_dates[recent_ids[-1]],
                "Matches": len(recent_ids),
            },
            {
                "Window": "Reference",
                "From": match_dates[reference_ids[0]],
                "To": match_dates[reference_ids[-1]],
                "Matches": len(reference_ids),
            },
        ]
    )
    st.dataframe(context_frame, hide_index=True, width="stretch")
    st.subheader("Recorded dead-ball inventory in the selected context")
    context_evidence = [row for row in bundle["evidence"] if int(row["match_id"]) in context_ids]
    inventory = []
    for restart_type in bundle["method"]["restart_taxonomy"]:
        rows = [row for row in context_evidence if row["restart_type"] == restart_type]
        inventory.append(
            {
                "Restart": restart_type.replace("_", " "),
                "n": len(rows),
                "Matches": len({row["match_id"] for row in rows}),
                "Shot-producing": sum(int(row["shot_outcome"]["shot_count"]) > 0 for row in rows),
                "xG": round(
                    sum(float(row["shot_outcome"].get("total_xg") or 0) for row in rows), 3
                ),
            }
        )
    st.dataframe(pd.DataFrame(inventory), hide_index=True, width="stretch")
    st.info(
        "Counts describe recorded event sequences. They do not reveal off-ball movement, legal direct/indirect status, tactical intent, or defensive assignments."
    )

with shortlist_tab:
    st.subheader("Delivery-group changes worth checking")
    if eligible:
        st.success(
            f"{len(eligible)} group difference{'s' if len(eligible) != 1 else ''} passed every review gate."
        )
    else:
        st.info(
            "No group difference passed every review gate. Descriptive rows remain visible without a change claim."
        )
    if comparisons:
        plot_rows = comparisons[:10]
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=[row.share_difference * 100 for row in plot_rows],
                y=[row.delivery_group for row in plot_rows],
                mode="markers",
                marker={
                    "color": ["#007C7C" if row.review_eligible else "#8CA5B1" for row in plot_rows],
                    "size": 10,
                },
                error_x={
                    "type": "data",
                    "symmetric": False,
                    "array": [(row.ci_high - row.share_difference) * 100 for row in plot_rows],
                    "arrayminus": [(row.share_difference - row.ci_low) * 100 for row in plot_rows],
                },
                hovertemplate="%{y}<br>%{x:.1f} pp<extra></extra>",
            )
        )
        figure.add_vline(x=0, line_dash="dot", line_color="#B9473D")
        figure.update_layout(
            height=max(360, 42 * len(plot_rows)),
            xaxis_title="Recent minus reference share (percentage points)",
            yaxis_title=None,
            margin=dict(l=20, r=20, t=20, b=40),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#F7F5EF",
        )
        st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
        table = pd.DataFrame(
            [
                {
                    "Delivery group": row.delivery_group,
                    "Recent": f"{row.recent_count}/{row.recent_total}",
                    "Reference": f"{row.reference_count}/{row.reference_total}",
                    "Match support": f"{row.recent_match_support}/{row.reference_match_support}",
                    "Difference": f"{row.share_difference * 100:+.1f} pp",
                    "95% interval": f"[{row.ci_low * 100:.1f}, {row.ci_high * 100:.1f}] pp",
                    "Nearby windows": row.window_sensitivity,
                    "Review eligible": row.review_eligible,
                    "Why suppressed": "; ".join(row.suppression_reasons),
                }
                for row in comparisons
            ]
        )
        st.dataframe(table, hide_index=True, width="stretch")
    notes = st.text_area(
        "Analyst notes for this briefing",
        key=f"notes-{case['slug']}",
        placeholder="Record a cautious observation or question. Notes are kept only in this session and included in the export.",
    )
    brief = preparation_brief_html(
        bundle,
        comparison_rows,
        "preceding team window",
        recent_n,
        reference_n,
        notes,
    )
    st.download_button(
        "Download current briefing",
        data=brief,
        file_name=f"{case['slug']}-historical-set-piece-brief.html",
        mime="text/html",
    )

with evidence_tab:
    st.subheader("Derived evidence summaries")
    st.caption(
        "The public application exposes derived review cards, not raw provider records, exact source coordinates, or source event IDs."
    )
    group_options = ["All"] + [row.delivery_group for row in comparisons]
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        selected_group = st.selectbox("Delivery group", group_options)
    with col_b:
        selected_window = st.selectbox("Window", ["Recent", "Reference", "Both"])
    with col_c:
        selected_outcome = st.selectbox("Outcome", ["All", "Shot-producing", "No shot"])
    allowed_ids = set(
        recent_ids
        if selected_window == "Recent"
        else reference_ids
        if selected_window == "Reference"
        else recent_ids + reference_ids
    )
    filtered = [row for row in bundle["evidence"] if int(row["match_id"]) in allowed_ids]
    if selected_group != "All":
        filtered = [row for row in filtered if row.get("delivery_group") == selected_group]
    if selected_outcome != "All":
        wants_shot = selected_outcome == "Shot-producing"
        filtered = [
            row for row in filtered if (int(row["shot_outcome"]["shot_count"]) > 0) == wants_shot
        ]
    if not filtered:
        st.warning("No evidence summaries match this complete analysis context.")
    else:
        options = {
            f"{row['evidence_id']} · {row['match_date']} vs {row['opponent']} · {row.get('delivery_group') or row['restart_type']}": row
            for row in filtered
        }
        selected = options[st.selectbox("Evidence card", list(options))]
        cards = st.columns(4)
        cards[0].metric("Reference", selected["evidence_id"])
        cards[1].metric("Date", selected["match_date"])
        cards[2].metric("Minute", selected["minute"])
        cards[3].metric("Termination", selected["termination_reason"])
        left, right = st.columns(2)
        with left:
            st.markdown("#### Recorded delivery")
            st.json(selected["delivery"], expanded=True)
            st.markdown("#### Recorded player roles")
            st.json(selected["player_roles"], expanded=True)
        with right:
            st.markdown("#### Outcome and availability")
            st.json(
                {
                    "shot_outcome": selected["shot_outcome"],
                    "first_post_delivery": selected["first_post_delivery"],
                    "censoring_reason": selected["censoring_reason"],
                    "evidence_status": selected["evidence_status"],
                    "rights_class": selected["rights_class"],
                },
                expanded=True,
            )
            st.markdown("#### Data quality")
            st.json(selected["data_quality"], expanded=True)
        st.markdown("#### Derived event timeline")
        st.dataframe(pd.DataFrame(selected["timeline"]), hide_index=True, width="stretch")
        st.caption(
            f"Provenance: {selected['provenance']['provider']} at {selected['provenance']['source_revision']}. Return path: Evidence review → {selected['evidence_id']}."
        )

with peer_tab:
    st.subheader("Complete competition peer context")
    peer = bundle["peer_baseline"]
    if peer.get("status") != "descriptive":
        st.warning(f"Peer comparison unavailable: {peer.get('reason', 'undeclared reason')}")
    else:
        st.caption(
            f"{peer['fixtures']} fixtures, {peer['teams']} teams, {peer['peer_teams']} leave-target-out peers. Descriptive season comparison only."
        )
        peer_rows = pd.DataFrame(peer["team_rows"])
        display = peer_rows[
            [
                "team",
                "matches",
                "corners",
                "corners_per_match",
                "shot_producing_rate",
                "eligible_players",
            ]
        ].copy()
        display["corners_per_match"] = display["corners_per_match"].map(
            lambda value: f"{value:.2f}"
        )
        display["shot_producing_rate"] = (display["shot_producing_rate"] * 100).map(
            lambda value: f"{value:.1f}%"
        )
        st.dataframe(display, hide_index=True, width="stretch")
        percentiles = peer["target_percentiles"]
        pcols = st.columns(2)
        pcols[0].metric(
            "Corner rate percentile", f"{float(percentiles['corners_per_match']) * 100:.0f}th"
        )
        pcols[1].metric(
            "Shot-producing percentile", f"{float(percentiles['shot_producing_rate']) * 100:.0f}th"
        )
        for limitation in peer["limitations"]:
            st.markdown(f"- {limitation}")

with method_tab:
    st.subheader("Coverage ledger")
    st.json(bundle["data"]["coverage"], expanded=True)
    st.subheader("Rights-aware publication")
    st.json(bundle["data"]["rights"], expanded=True)
    st.subheader("Available modalities")
    st.json(bundle["data"]["modalities"], expanded=True)
    st.subheader("Analytical contract")
    st.json(bundle["method"], expanded=True)
    st.subheader("Known limitations")
    for limitation in bundle["data"]["limitations"]:
        st.markdown(f"- {limitation}")
    st.warning(
        "SignalRoom has not been externally validated and must not be described as club-ready."
    )

st.markdown(
    f"""<div class="footer"><b>Data: StatsBomb Open Data.</b> Public output contains attributed analysis and derived evidence summaries, not redistributed raw records or source event IDs. Historical cutoff {escape(str(case["historical_cutoff"]))}. No club or provider endorsement, no tactical advice, and no external validation.</div>""",
    unsafe_allow_html=True,
)
