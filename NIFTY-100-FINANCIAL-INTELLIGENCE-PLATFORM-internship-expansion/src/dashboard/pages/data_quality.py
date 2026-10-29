# data_quality.py
#
# Internship Expansion - Module 1 on the dashboard:
# missing values, duplicate records, inconsistent periods, invalid metrics.

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.analytics.platform_data import get_bundle  # noqa: E402
from src.quality.data_quality import summarize  # noqa: E402

from utils.theme import metric_card, page_header, style_plot  # noqa: E402

SEVERITY_COLORS = {"error": "#EF4444", "warning": "#F59E0B", "info": "#9CA3AF"}

CATEGORY_LABELS = {
    "missing_value": "Missing values",
    "duplicate": "Duplicate records",
    "period": "Inconsistent periods",
    "invalid_metric": "Invalid metrics",
}


@st.cache_resource(show_spinner="Running data-quality checks...")
def load_bundle():
    return get_bundle()


def show():

    page_header(
        "🧪",
        "Data Quality Monitor",
        "Missing values, duplicate records, inconsistent financial periods and invalid metrics "
        "found in the database.",
    )

    bundle = load_bundle()
    issues = bundle.issues
    stats = summarize(issues, bundle.tables)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Errors", f"{stats['errors']:,}")
    with c2:
        metric_card("Warnings", f"{stats['warnings']:,}")
    with c3:
        metric_card("Info notes", f"{stats['info']:,}")
    with c4:
        clean = stats["clean_record_pct"]
        metric_card("Clean records", f"{clean:.1f}%" if clean is not None else "n/a")

    st.caption(
        f"{stats['records_checked']:,} statement rows checked; {stats['records_flagged']:,} have at "
        "least one error or warning. Info notes (TTM rows, no dividend paid, ...) are expected and "
        "do not count as flagged."
    )

    if issues.empty:
        st.success("No data-quality issues found.")
        return

    view = issues.copy()
    view["category_label"] = view["category"].map(CATEGORY_LABELS).fillna(view["category"])

    # ---- overview chart -------------------------------------------------
    counts = (
        view.groupby(["category_label", "severity"]).size().reset_index(name="issues")
    )
    fig = px.bar(
        counts, x="category_label", y="issues", color="severity",
        color_discrete_map=SEVERITY_COLORS, barmode="stack",
        category_orders={"severity": ["error", "warning", "info"]},
        labels={"category_label": "", "issues": "Issues"},
        title="Issues by category and severity",
    )
    fig = style_plot(fig)
    for trace in fig.data:
        trace.marker.color = SEVERITY_COLORS[trace.name]
    st.plotly_chart(fig, use_container_width=True)

    # ---- filters --------------------------------------------------------
    st.markdown("#### Explore the findings")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        severities = st.multiselect("Severity", ["error", "warning", "info"], default=["error", "warning"])
    with f2:
        categories = st.multiselect(
            "Category", sorted(view["category_label"].unique()), default=sorted(view["category_label"].unique())
        )
    with f3:
        tables = st.multiselect("Table", sorted(view["table"].unique()))
    with f4:
        checks = st.multiselect("Check", sorted(view["check"].unique()))

    company = st.text_input("Company ticker (optional)", "").strip().upper()

    filtered = view[view["severity"].isin(severities) & view["category_label"].isin(categories)]
    if tables:
        filtered = filtered[filtered["table"].isin(tables)]
    if checks:
        filtered = filtered[filtered["check"].isin(checks)]
    if company:
        filtered = filtered[filtered["company_id"].astype(str).str.upper() == company]

    st.write(f"**{len(filtered):,}** findings match")

    by_check = (
        filtered.groupby(["category_label", "check", "severity"]).size().reset_index(name="issues")
        .sort_values("issues", ascending=False)
    )
    st.dataframe(
        by_check.rename(columns={"category_label": "Category", "check": "Check",
                                 "severity": "Severity", "issues": "Issues"}),
        use_container_width=True, hide_index=True,
    )

    with st.expander("Row-level findings", expanded=False):
        st.dataframe(
            filtered[["severity", "category_label", "check", "table", "company_id", "period", "column", "detail"]]
            .rename(columns={"category_label": "category"}),
            use_container_width=True, hide_index=True,
        )

    st.download_button(
        "⬇️ Download findings (CSV)",
        data=filtered.drop(columns=["category_label"]).to_csv(index=False).encode("utf-8"),
        file_name="data_quality_findings.csv",
        mime="text/csv",
    )

    # ---- worst companies --------------------------------------------------
    st.markdown("#### Companies with the most errors and warnings")

    worst = (
        view[view["severity"].isin(["error", "warning"])]
        .groupby("company_id")["severity"].value_counts().unstack(fill_value=0)
        .reindex(columns=["error", "warning"], fill_value=0)
    )
    worst["total"] = worst.sum(axis=1)
    worst = worst.sort_values(["error", "total"], ascending=False).head(15).reset_index()
    st.dataframe(
        worst.rename(columns={"company_id": "Ticker", "error": "Errors", "warning": "Warnings", "total": "Total"}),
        use_container_width=True, hide_index=True,
    )
