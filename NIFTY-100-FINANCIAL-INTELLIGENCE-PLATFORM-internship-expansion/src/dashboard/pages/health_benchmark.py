# health_benchmark.py
#
# Internship Expansion - Modules 2, 3 and 4 on the dashboard:
#   * explainable financial health score
#   * peer / sector benchmarking
#   * downloadable PDF research report

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# The dashboard is started from src/dashboard, so make the repo root importable
# for the shared analytics package (src.analytics, src.quality, src.reports).
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.analytics.benchmarking import benchmark_company, sector_summary  # noqa: E402
from src.analytics.platform_data import get_bundle  # noqa: E402
from src.quality.data_quality import company_reliability, company_warnings  # noqa: E402
from src.reports.research_report import generate_report_bytes  # noqa: E402

from utils.theme import metric_card, page_header, style_plot  # noqa: E402

GREEN = "#10B981"
AMBER = "#F59E0B"
RED = "#EF4444"


@st.cache_resource(show_spinner="Computing health scores and data-quality checks...")
def load_bundle():
    return get_bundle()


@st.cache_data(show_spinner="Building PDF report...", ttl=1800)
def build_pdf(company_id: str) -> bytes:
    return generate_report_bytes(company_id, load_bundle())


def _band_color(points: float) -> str:
    if points >= 75:
        return GREEN
    if points >= 40:
        return AMBER
    return RED


def _num(value, decimals=2, suffix=""):
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value:,.{decimals}f}{suffix}"


def show():

    page_header(
        "🩺",
        "Health Score & Peer Benchmark",
        "A transparent 0-100 financial health score, the reasoning behind it, and how the "
        "company compares with its peers.",
    )

    bundle = load_bundle()
    metrics = bundle.metrics

    labels = {
        f"{r.company_name} ({r.company_id})": r.company_id
        for r in metrics.sort_values("company_name").itertuples()
    }

    choice = st.selectbox("Company", list(labels.keys()), key="hb_company")
    company_id = labels[choice]

    health = bundle.health[company_id]
    peer_set, bench = benchmark_company(company_id, metrics, bundle.league, bundle.peer_groups)

    recent_from = (health.as_of_year - 2) if health.as_of_year else None
    reliability = company_reliability(bundle.issues, company_id, recent_from)

    ranked = bundle.league.dropna(subset=["score"]).reset_index(drop=True)
    pos = ranked.index[ranked["company_id"] == company_id]
    rank_text = f"{int(pos[0]) + 1} of {len(ranked)}" if len(pos) else "not ranked"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Health score", _num(health.score, 1) if health.score is not None else "N/A")
    with c2:
        metric_card("Grade", f"{health.grade} - {health.grade_label}")
    with c3:
        metric_card("Rank by score", rank_text)
    with c4:
        metric_card("Data reliability", reliability["rating"])

    st.caption(
        f"Latest fiscal year: {health.as_of_year or 'n/a'}  |  "
        f"Data coverage: {health.data_coverage_pct:.0f}% of applicable weight"
    )

    tab_score, tab_peers, tab_sector, tab_report = st.tabs(
        ["🔍 Score breakdown", "👥 Peer benchmark", "🏭 Sector league", "📄 PDF report"]
    )

    # -------------------------------------------------------------------
    with tab_score:

        st.markdown("#### How the score is built")
        st.write(
            "Each metric earns 0-100 points between two documented thresholds. The points are "
            "weighted and added up; the *Contribution* column adds up exactly to the total score."
        )

        comp = health.components.copy()
        table = pd.DataFrame({
            "Pillar": comp["pillar"],
            "Metric": comp["label"],
            "Value": [
                "n/a" if pd.isna(v) else f"{v:,.2f}{u}" for v, u in zip(comp["value"], comp["unit"])
            ],
            "Points (0-100)": comp["points"].round(0),
            "Nominal weight": comp["nominal_weight"],
            "Weight used (%)": comp["effective_weight"].round(1),
            "Contribution": comp["contribution"].round(1),
            "Status": comp["status"].str.replace("_", " "),
            "Why": comp["note"],
        })
        st.dataframe(table, use_container_width=True, hide_index=True)

        scored = comp[comp["points"].notna() & (comp["status"] == "scored")]

        if not scored.empty:
            scored = scored.iloc[::-1]
            fig = go.Figure(go.Bar(
                x=scored["points"], y=scored["label"], orientation="h",
                text=scored["points"].round(0).astype(int), textposition="inside",
                marker_color=[_band_color(v) for v in scored["points"]],
            ))
            fig.update_layout(
                title="Points earned per metric", xaxis=dict(range=[0, 100], title="Points"),
                height=70 + 38 * len(scored),
            )
            fig = style_plot(fig)
            fig.update_traces(marker_color=[_band_color(v) for v in scored["points"]])
            st.plotly_chart(fig, use_container_width=True)

        left, right = st.columns(2)
        with left:
            st.markdown("**Strengths**")
            for item in health.strengths or ["No metric earned 75+ points."]:
                st.markdown(f"- {item}")
        with right:
            st.markdown("**Concerns**")
            for item in health.concerns or ["No metric earned fewer than 40 points."]:
                st.markdown(f"- {item}")

        if health.caveats:
            st.markdown("**Caveats**")
            for item in health.caveats:
                st.markdown(f"- {item}")

        warnings = company_warnings(bundle.issues, company_id, recent_from)
        with st.expander(f"Data-quality warnings for this company ({len(warnings)})"):
            if warnings:
                for line in warnings:
                    st.markdown(f"- {line}")
            else:
                st.write("No data-quality errors or warnings for this company.")

    # -------------------------------------------------------------------
    with tab_peers:

        if not peer_set.members:
            st.info(f"No benchmark available: {peer_set.note or 'peer set too small'}.")
        else:
            others = [m for m in peer_set.members if m != company_id]
            st.markdown(
                f"Compared with **{len(others)} peers** in the {peer_set.basis} "
                f"**{peer_set.group_name}**."
            )
            st.caption(", ".join(others))
            if peer_set.note:
                st.caption(peer_set.note)

            view = pd.DataFrame({
                "Metric": bench["label"],
                "Company": [_num(v, 2, "" if u == "pts" else u) for v, u in zip(bench["value"], bench["unit"])],
                "Peer median": [_num(v, 2, "" if u == "pts" else u) for v, u in zip(bench["peer_median"], bench["unit"])],
                "Difference": [_num(v, 2) for v in bench["delta"]],
                "Percentile": bench["percentile"].round(0),
                "Rank": [
                    f"{int(r)} of {int(n)}" if pd.notna(r) else "-" for r, n in zip(bench["rank"], bench["n"])
                ],
                "Verdict": [
                    v if v != "n/a" else (note or "n/a") for v, note in zip(bench["verdict"], bench["note"])
                ],
            })
            st.dataframe(view, use_container_width=True, hide_index=True)
            st.caption(
                "Percentile = share of the other peers the company beats (100 = best; for "
                "debt-to-equity lower is better). P/E is shown for context and not ranked."
            )

            ranked_rows = bench[bench["percentile"].notna()].iloc[::-1]
            if not ranked_rows.empty:
                fig = go.Figure(go.Bar(
                    x=ranked_rows["percentile"], y=ranked_rows["label"], orientation="h",
                    text=ranked_rows["percentile"].round(0).astype(int), textposition="inside",
                ))
                fig.add_vline(x=50, line_dash="dash", line_color="#888888")
                fig.update_layout(
                    title="Position versus peers (percentile)", xaxis=dict(range=[0, 100]),
                    height=90 + 36 * len(ranked_rows),
                )
                fig = style_plot(fig)
                fig.update_traces(marker_color=[_band_color(v * 0.75 + 12) for v in ranked_rows["percentile"]])
                st.plotly_chart(fig, use_container_width=True)

    # -------------------------------------------------------------------
    with tab_sector:

        summary = sector_summary(metrics, bundle.league)

        fig = go.Figure(go.Bar(
            x=summary["median_health_score"], y=summary["broad_sector"], orientation="h",
            text=summary["median_health_score"].round(1), textposition="inside",
        ))
        fig.update_layout(
            title="Median health score by sector", yaxis=dict(autorange="reversed"),
            xaxis=dict(range=[0, 100]), height=420,
        )
        st.plotly_chart(style_plot(fig), use_container_width=True)
        st.caption(
            "Financials are scored on fewer metrics than industrial companies, so compare them with "
            "their own peers rather than across sectors."
        )

        sectors = ["All sectors"] + sorted(metrics["broad_sector"].dropna().unique())
        sector = st.selectbox("League table", sectors, key="hb_sector")

        league = bundle.league
        if sector != "All sectors":
            league = league[league["broad_sector"] == sector]

        st.dataframe(
            league.rename(columns={
                "company_id": "Ticker", "company_name": "Company", "broad_sector": "Sector",
                "score": "Score", "grade": "Grade", "grade_label": "Label",
                "data_coverage_pct": "Coverage %", "as_of_year": "Year",
            }),
            use_container_width=True, hide_index=True,
        )

    # -------------------------------------------------------------------
    with tab_report:

        st.markdown("#### Download a research report")
        st.write(
            "A PDF with the snapshot, the full score breakdown, trend and peer charts, "
            "data-quality warnings and the methodology."
        )

        try:
            pdf = build_pdf(company_id)
        except Exception as exc:  # keep the dashboard alive if one report fails
            st.error(f"Could not build the report: {exc}")
        else:
            st.download_button(
                "⬇️ Download PDF report",
                data=pdf,
                file_name=f"{company_id}_research_report.pdf",
                mime="application/pdf",
            )
            st.caption(f"{len(pdf) / 1024:,.0f} KB")
