# home.py
import streamlit as st
import pandas as pd
import plotly.express as px

from utils.db import (
    get_companies,
    get_ratios,
    get_sectors,
    get_market_cap,
)
from utils.theme import page_header


def section_header(text: str):
    """Small helper so subheaders animate in with a slight stagger."""
    st.markdown(f"### {text}")


def show():

    page_header(
        "🏠",
        "Nifty 100 Analytics Dashboard",
        "A quick pulse check across the Nifty 100 universe — quality, valuation and growth at a glance.",
    )

    companies = get_companies()
    ratios = get_ratios()
    sectors = get_sectors()

    # -------------------------
    # Sidebar Year Filter
    # -------------------------

    ratios["calendar_year"] = (
    ratios["year"]
    .str[-4:]
    .astype(int)
)

    years = sorted(
        ratios["calendar_year"].unique(),
        reverse=True,
    )

    selected_year = st.sidebar.selectbox(
        "Select Year",
        years,
    )

    ratios = ratios[
        ratios["calendar_year"] == selected_year
    ]

    # -------------------------
    # Merge Data
    # -------------------------

    companies = companies.rename(columns={"id": "company_id"})

    df = ratios.merge(
        companies,
        on="company_id",
        how="left",
    )

    df = df.merge(
        sectors,
        on="company_id",
        how="left",
    )

    # -------------------------
    # KPI Cards
    # -------------------------

    section_header(f"Summary — FY {selected_year} Performance & Fundamentals")

    # Dynamic Median P/E from verified valuation dataset
    try:
        mc_df = get_market_cap()
        if not mc_df.empty and "year" in mc_df.columns:
            mc_year = mc_df[mc_df["year"] == selected_year]
            if mc_year.empty:
                mc_year = mc_df[mc_df["year"] == mc_df["year"].max()]
            pe_clean = mc_year["pe_ratio"].dropna()
            pe_clean = pe_clean[(pe_clean > 0) & (pe_clean < 250)]
            median_pe_val = pe_clean.median()
            median_pe_text = f"{median_pe_val:.2f}x" if pd.notna(median_pe_val) else "N/A"
        else:
            median_pe_text = "N/A"
    except Exception:
        median_pe_text = "N/A"

    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)

    c1.metric(
        "Average ROE",
        f"{df['return_on_equity_pct'].mean():.2f}%"
    )

    c2.metric(
        "Median P/E",
        median_pe_text
    )

    c3.metric(
        "Median D/E",
        f"{df['debt_to_equity'].median():.2f}"
    )

    c4.metric(
        "Total Companies",
        len(companies)
    )

    c5.metric(
        "Median Revenue CAGR",
        f"{df['revenue_cagr_5yr'].median():.2f}%"
    )

    c6.metric(
        "Debt-Free Companies",
        int((df["debt_to_equity"] <= 0.10).sum())
    )

    st.divider()

    # -------------------------
    # Charts
    # -------------------------

    left, right = st.columns(2)

    with left:

        section_header("Sector Breakdown")

        sector_df = (
            df.groupby("broad_sector")
            .size()
            .reset_index(name="Companies")
        )

        fig = px.pie(
            sector_df,
            names="broad_sector",
            values="Companies",
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.Sunsetdark,
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            pull=[0.03] * len(sector_df),
            marker=dict(line=dict(color="#ffffff", width=2)),
        )

        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            transition=dict(duration=500, easing="cubic-in-out"),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with right:

        section_header("Top 5 Quality Companies")

        top5 = (
            df.sort_values(
                "composite_quality_score",
                ascending=False,
            )
            .head(5)[
                [
                    "company_name",
                    "return_on_equity_pct",
                    "debt_to_equity",
                    "composite_quality_score",
                ]
            ]
        )

        try:
            styled_top5 = top5.style.background_gradient(
                subset=["composite_quality_score"],
                cmap="Purples",
            )
        except Exception:
            # matplotlib not installed, or gradient styling failed -
            # fall back to a plain (unstyled) table instead of crashing.
            styled_top5 = top5

        st.dataframe(
            styled_top5,
            use_container_width=True,
            hide_index=True,
        )