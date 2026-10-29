# capital.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.db import (
    get_companies,
    get_ratios,
    get_sectors,
)
from utils.theme import page_header
from utils.helpers import display_value

# ==========================================================
# Divider
# ==========================================================

def divider():

    st.markdown("---")


# ==========================================================
# Safe Numeric
# ==========================================================

def num(df, column):

    if column not in df.columns:
        return pd.Series([0] * len(df), index=df.index)

    return pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0)


# ==========================================================
# Safe Text
# ==========================================================

def text(df, column):

    if column not in df.columns:
        return pd.Series(["Unknown"] * len(df), index=df.index)

    return (
        df[column]
        .fillna("Unknown")
        .astype(str)
    )


# ==========================================================
# Safe Slider Helper
# ==========================================================

def safe_slider(label, series, default, step, side=st.sidebar):
    """
    Builds a slider whose min/max always come from the data and whose
    default value is clamped inside [min, max] so Streamlit never raises
    'The default value must be between min and max'.
    """

    if series.empty or series.isna().all():
        s_min, s_max = 0.0, 1.0
    else:
        s_min = float(series.min())
        s_max = float(series.max())

    # Guard against min == max (Streamlit needs min < max)
    if s_min == s_max:
        s_max = s_min + 1.0

    clamped_default = min(max(default, s_min), s_max)

    return side.slider(
        label,
        s_min,
        s_max,
        clamped_default,
        step,
    )


# ==========================================================
# Capital Allocation Classification
# ==========================================================

def classify_company(row):

    roe = row.get("return_on_equity_pct", 0)
    debt = row.get("debt_to_equity", 0)
    rev = row.get("revenue_cagr_5yr", 0)
    fcf = row.get("free_cash_flow_cr", 0)

    if roe >= 25 and debt <= 0.30:
        return "High Quality"

    elif rev >= 18:
        return "Growth Focus"

    elif debt <= 0.10:
        return "Debt Free"

    elif fcf >= 1000:
        return "Cash Generator"

    elif debt >= 2:
        return "Highly Leveraged"

    elif rev <= 5:
        return "Turnaround"

    elif roe >= 15:
        return "Capital Efficient"

    else:
        return "Balanced"

# ==========================================================
# Main Page
# ==========================================================

def show():

    page_header(
        "💰",
        "Capital Allocation Map",
        "See how companies are deploying capital across the Nifty 100.",
    )

    # ======================================================
    # Load Database Tables
    # ======================================================

    companies = get_companies()
    ratios = get_ratios()
    sectors = get_sectors()

    if companies.empty or ratios.empty:

        st.error("Database tables are empty.")
        st.stop()

    # ======================================================
    # Latest Financial Year
    # ======================================================

    if "year" not in ratios.columns or "company_id" not in ratios.columns:
        st.error("Ratios table is missing 'year' or 'company_id' column.")
        st.stop()

    # --------------------------------------------------------
    # Rank financial years by number of unique companies they
    # cover. This avoids two bugs:
    #   1) Treating "year" as a string and picking the
    #      alphabetically-largest value (e.g. "Sep 2024" > "Mar 2024")
    #      instead of the most recent / most complete year.
    #   2) Accidentally landing on a sparse quarterly snapshot
    #      (e.g. "Sep 2024" with only 1 company) instead of the
    #      full annual dataset (e.g. "Mar 2024" with 91 companies).
    # --------------------------------------------------------

    year_counts = (
        ratios.groupby("year")["company_id"]
        .nunique()
        .sort_values(ascending=False)
    )

    if year_counts.empty:
        st.error("No financial year data found in Ratios table.")
        st.stop()

    # Only offer years that have reasonable company coverage
    # (i.e. exclude incomplete/partial snapshots). Threshold is
    # relative to the fullest year so it adapts to any dataset size.
    coverage_threshold = max(1, int(year_counts.max() * 0.5))
    available_years = year_counts[year_counts >= coverage_threshold].index.tolist()

    if not available_years:
        available_years = year_counts.index.tolist()

    # Sort years chronologically in descending order so latest (Mar 2026) is always index 0
    import re
    available_years = sorted(
        available_years,
        key=lambda y: int(re.search(r'(\d{4})', str(y)).group(1)) if re.search(r'(\d{4})', str(y)) else 0,
        reverse=True,
    )

    st.sidebar.subheader("📅 Financial Year")

    selected_year = st.sidebar.selectbox(
        "Select Year",
        available_years,
        index=0,
        help="Only years with sufficient company coverage are shown.",
    )

    latest_year = selected_year

    ratios = (
        ratios[
            ratios["year"] == latest_year
        ]
        .copy()
    )

    # ======================================================
    # Rename Company ID (Companies table)
    # ======================================================

    if "id" in companies.columns and "company_id" not in companies.columns:
        companies = companies.rename(columns={"id": "company_id"})

    # ======================================================
    # Rename Company ID (Sectors table) -- handles the case
    # where sectors uses "id" instead of "company_id"
    # ======================================================

    if "company_id" not in sectors.columns:
        if "id" in sectors.columns:
            sectors = sectors.rename(columns={"id": "company_id"})
        else:
            sectors = sectors.copy()
            sectors["company_id"] = np.nan

    if "company_id" not in ratios.columns:
        st.error("Ratios table is missing a 'company_id' column.")
        st.stop()

    # ======================================================
    # Merge Tables
    # ======================================================

    df = (
        ratios.merge(
            companies,
            on="company_id",
            how="left",
        )
        .merge(
            sectors,
            on="company_id",
            how="left",
        )
    )

    # ======================================================
    # Clean Numeric Columns
    # ======================================================

    numeric_cols = [
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "operating_profit_margin_pct",
        "interest_coverage",
        "composite_quality_score",
        "index_weight_pct",
    ]

    for col in numeric_cols:
        df[col] = num(df, col)

    # ======================================================
    # Clean Text Columns
    # ======================================================

    text_cols = [
        "company_name",
        "broad_sector",
        "sub_sector",
        "market_cap_category",
    ]

    for col in text_cols:
        df[col] = text(df, col)

    # ======================================================
    # Capital Allocation Pattern
    # ======================================================

    df["Capital Pattern"] = df.apply(
        classify_company,
        axis=1,
    )

    # ======================================================
    # Remove Duplicate Companies
    # ======================================================

    if "company_id" in df.columns:
        df = (
            df.sort_values(
                "composite_quality_score",
                ascending=False,
            )
            .drop_duplicates(
                subset="company_id"
            )
            .reset_index(drop=True)
        )
    else:
        df = df.reset_index(drop=True)

    # ======================================================
    # Market Cap Category
    # ======================================================

    if "market_cap_category" not in df.columns or df["market_cap_category"].eq("Unknown").all():
        df["market_cap_category"] = df.get("market_cap_category", "Large Cap")
        df["market_cap_category"] = df["market_cap_category"].replace("Unknown", "Large Cap")

    # ======================================================
    # Quick Check
    # ======================================================

    st.caption(
        f"Loaded {len(df)} companies | Financial Year : {latest_year}"
    )

    if df.empty:
        st.warning("No company data available after merging tables.")
        st.stop()

    # ======================================================
    # Sidebar Filters
    # ======================================================

    st.sidebar.title("🎯 Filters")

    # -----------------------------
    # Company Search
    # -----------------------------

    company_search = st.sidebar.text_input(
        "🔍 Search Company",
        "",
        placeholder="Type company name..."
    )

    # -----------------------------
    # Pattern Filter
    # -----------------------------

    pattern_options = ["All"] + sorted(
        df["Capital Pattern"].dropna().unique().tolist()
    )

    selected_pattern = st.sidebar.selectbox(
        "Capital Pattern",
        pattern_options,
    )

    # -----------------------------
    # Sector Filter
    # -----------------------------

    sector_options = ["All"] + sorted(
        df["broad_sector"].dropna().unique().tolist()
    )

    selected_sector = st.sidebar.selectbox(
        "Sector",
        sector_options,
    )

    # -----------------------------
    # Market Cap Filter
    # -----------------------------

    market_cap_options = ["All"] + sorted(
        df["market_cap_category"].dropna().unique().tolist()
    )

    selected_market_cap = st.sidebar.selectbox(
        "Market Cap",
        market_cap_options,
    )

    st.sidebar.divider()

    st.sidebar.subheader("📊 Financial Filters")

    # -----------------------------
    # ROE  (default = data minimum -> shows ALL companies until user tightens it)
    # -----------------------------

    roe_min = safe_slider(
        "Minimum ROE (%)",
        df["return_on_equity_pct"],
        default=float(df["return_on_equity_pct"].min()) if not df["return_on_equity_pct"].empty else 0.0,
        step=1.0,
    )

    # -----------------------------
    # Debt  (default = data maximum -> shows ALL companies until user tightens it)
    # -----------------------------

    debt_max = safe_slider(
        "Maximum Debt / Equity",
        df["debt_to_equity"],
        default=float(df["debt_to_equity"].max()) if not df["debt_to_equity"].empty else 1.0,
        step=0.10,
    )

    # -----------------------------
    # Revenue CAGR  (default = data minimum -> shows ALL companies until user tightens it)
    # -----------------------------

    revenue_min = safe_slider(
        "Minimum Revenue CAGR",
        df["revenue_cagr_5yr"],
        default=float(df["revenue_cagr_5yr"].min()) if not df["revenue_cagr_5yr"].empty else 0.0,
        step=1.0,
    )

    # -----------------------------
    # Quality Score  (default = data minimum, NOT median -> median alone would
    # cut ~50% of companies before the user even touches a filter)
    # -----------------------------

    quality_min = safe_slider(
        "Minimum Quality Score",
        df["composite_quality_score"],
        default=float(df["composite_quality_score"].min()) if not df["composite_quality_score"].empty else 0.0,
        step=1.0,
    )

    # ======================================================
    # Apply Filters
    # ======================================================

    filtered = df.copy()

    if company_search:
        filtered = filtered[
            filtered["company_name"]
            .str.contains(company_search, case=False, na=False)
        ]

    if selected_pattern != "All":
        filtered = filtered[filtered["Capital Pattern"] == selected_pattern]

    if selected_sector != "All":
        filtered = filtered[filtered["broad_sector"] == selected_sector]

    if selected_market_cap != "All":
        filtered = filtered[filtered["market_cap_category"] == selected_market_cap]

    filtered = filtered[filtered["return_on_equity_pct"] >= roe_min]
    filtered = filtered[filtered["debt_to_equity"] <= debt_max]
    filtered = filtered[filtered["revenue_cagr_5yr"] >= revenue_min]
    filtered = filtered[filtered["composite_quality_score"] >= quality_min]

    st.sidebar.success(f"Showing {len(filtered)} Companies")

    if filtered.empty:
        st.warning("⚠️ No companies match the selected filters. Try widening your filter ranges.")
        st.stop()

    # ======================================================
    # Dashboard KPIs
    # ======================================================

    divider()

    st.subheader("📈 Capital Allocation Overview")

    total_companies = len(filtered)
    avg_roe = filtered["return_on_equity_pct"].mean()
    avg_debt = filtered["debt_to_equity"].mean()
    avg_revenue = filtered["revenue_cagr_5yr"].mean()
    avg_quality = filtered["composite_quality_score"].mean()
    avg_fcf = filtered["free_cash_flow_cr"].mean()

    k1, k2, k3 = st.columns(3)
    k4, k5, k6 = st.columns(3)

    k1.metric("🏢 Companies", f"{total_companies}")
    k2.metric("📈 Avg ROE", display_value(avg_roe, "%"))
    k3.metric("💰 Avg Revenue CAGR", display_value(avg_revenue, "%"))
    k4.metric("🏆 Avg Quality Score", display_value(avg_quality))
    k5.metric("🏦 Avg Debt / Equity", display_value(avg_debt))
    k6.metric(
        "💵 Avg Free Cash Flow",
        "N/A" if pd.isna(avg_fcf) else f"{avg_fcf:,.0f} Cr",
    )

    divider()

    # ======================================================
    # Pattern Summary
    # ======================================================

    st.subheader("📊 Capital Allocation Summary")

    summary = (
        filtered
        .groupby("Capital Pattern")
        .agg(
            Companies=("company_id", "count"),
            Avg_ROE=("return_on_equity_pct", "mean"),
            Avg_Quality=("composite_quality_score", "mean"),
            Avg_Revenue=("revenue_cagr_5yr", "mean"),
        )
        .reset_index()
    )

    st.dataframe(summary.fillna("N/A"), use_container_width=True, hide_index=True)

    divider()

    # ======================================================
    # Top 10 Companies
    # ======================================================

    st.subheader("🏆 Highest Quality Companies")

    top10 = (
        filtered
        .sort_values("composite_quality_score", ascending=False)
        [[
            "company_name",
            "Capital Pattern",
            "broad_sector",
            "return_on_equity_pct",
            "debt_to_equity",
            "composite_quality_score",
        ]]
        .head(10)
    )

    top10.columns = [
        "Company",
        "Pattern",
        "Sector",
        "ROE (%)",
        "Debt",
        "Quality Score",
    ]

    st.dataframe(top10.fillna("N/A"), use_container_width=True, hide_index=True)

    divider()

    # ======================================================
    # Capital Allocation Treemap
    # ======================================================

    st.subheader("🌳 Capital Allocation Map")

    treemap_df = filtered.copy()

    treemap_df["TreeValue"] = (
        treemap_df["free_cash_flow_cr"]
        .abs()
        .replace(0, np.nan)
    )

    treemap_df["TreeValue"] = (
        treemap_df["TreeValue"]
        .fillna(treemap_df["composite_quality_score"])
        .replace(0, 1)
        .fillna(1)
    )

    fig = px.treemap(
        treemap_df,
        path=["Capital Pattern", "company_name"],
        values="TreeValue",
        color="composite_quality_score",
        color_continuous_scale="Viridis",
        hover_name="company_name",
        hover_data={
            "Capital Pattern": False,
            "TreeValue": False,
            "return_on_equity_pct": ":.2f",
            "debt_to_equity": ":.2f",
            "revenue_cagr_5yr": ":.2f",
            "free_cash_flow_cr": ":,.0f",
            "composite_quality_score": ":.2f",
            "broad_sector": True,
        },
    )

    fig.update_traces(
        textinfo="label",
        marker=dict(line=dict(color="white", width=1.5)),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Sector : %{customdata[4]}<br>"
            "ROE : %{customdata[0]:.2f}%<br>"
            "Debt/Equity : %{customdata[1]:.2f}<br>"
            "Revenue CAGR : %{customdata[2]:.2f}%<br>"
            "Free Cash Flow : %{customdata[3]:,.0f} Cr<br>"
            "Quality Score : %{color:.2f}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=720,
        margin=dict(t=20, l=5, r=5, b=5),
        coloraxis_colorbar=dict(title="Quality"),
    )

    st.plotly_chart(fig, use_container_width=True)

    divider()

    # ======================================================
    # Distribution Charts
    # ======================================================

    st.subheader("📊 Capital Allocation Analytics")

    col1, col2 = st.columns(2)

    # ------------------------------------------------------
    # Pattern Distribution
    # ------------------------------------------------------

    with col1:

        pattern_chart = (
            filtered
            .groupby("Capital Pattern")
            .size()
            .reset_index(name="Companies")
            .sort_values("Companies", ascending=False)
        )

        fig1 = px.bar(
            pattern_chart,
            x="Capital Pattern",
            y="Companies",
            color="Companies",
            color_continuous_scale="Viridis",
            text="Companies",
        )

        fig1.update_traces(textposition="outside")

        fig1.update_layout(
            title="Companies by Capital Pattern",
            xaxis_title="",
            yaxis_title="Companies",
            height=450,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
        )

        st.plotly_chart(fig1, use_container_width=True)

    # ------------------------------------------------------
    # Sector Distribution
    # ------------------------------------------------------

    with col2:

        sector_chart = (
            filtered
            .groupby("broad_sector")
            .size()
            .reset_index(name="Companies")
            .sort_values("Companies", ascending=False)
        )

        fig2 = px.pie(
            sector_chart,
            names="broad_sector",
            values="Companies",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )

        fig2.update_traces(textposition="inside", textinfo="percent+label")

        fig2.update_layout(
            title="Sector Distribution",
            height=450,
            margin=dict(l=20, r=20, t=40, b=20),
        )

        st.plotly_chart(fig2, use_container_width=True)

    divider()

    # ======================================================
    # Company Explorer
    # ======================================================

    st.subheader("🔍 Company Explorer")

    search = st.text_input(
        "Search Company",
        placeholder="Type company name...",
        key="company_explorer_search",
    )

    company_df = filtered.copy()

    if search:
        company_df = company_df[
            company_df["company_name"]
            .str.contains(search, case=False, na=False)
        ]

    company_df = company_df.sort_values("composite_quality_score", ascending=False)

    company_table = company_df[
        [
            "company_name",
            "Capital Pattern",
            "broad_sector",
            "return_on_equity_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "free_cash_flow_cr",
            "composite_quality_score",
        ]
    ].copy()

    company_table.columns = [
        "Company",
        "Pattern",
        "Sector",
        "ROE (%)",
        "Debt/Equity",
        "Revenue CAGR (%)",
        "Free Cash Flow (Cr)",
        "Quality Score",
    ]

    # ======================================================
    # Format Numbers
    # ======================================================

    company_table["ROE (%)"] = company_table["ROE (%)"].round(2)
    company_table["Debt/Equity"] = company_table["Debt/Equity"].round(2)
    company_table["Revenue CAGR (%)"] = company_table["Revenue CAGR (%)"].round(2)
    company_table["Free Cash Flow (Cr)"] = company_table["Free Cash Flow (Cr)"].round(0)
    company_table["Quality Score"] = company_table["Quality Score"].round(2)

    # ======================================================
    # Display Table
    # ======================================================

    st.dataframe(
        company_table.fillna("N/A"),
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    st.success(f"{len(company_table)} companies displayed.")

    divider()

    # ======================================================
    # Top 10 Highest Quality Companies
    # ======================================================

    st.subheader("🏆 Top 10 Highest Quality Companies")

    top10 = (
        filtered
        .sort_values("composite_quality_score", ascending=False)
        .head(10)
        .copy()
    )

    ranking = top10[
        [
            "company_name",
            "Capital Pattern",
            "return_on_equity_pct",
            "debt_to_equity",
            "composite_quality_score",
        ]
    ]

    ranking.columns = [
        "Company",
        "Pattern",
        "ROE (%)",
        "Debt/Equity",
        "Quality Score",
    ]

    left, right = st.columns([1.2, 1])

    # -----------------------------------------------------
    # Ranking Table
    # -----------------------------------------------------

    with left:
        st.dataframe(ranking.fillna("N/A"), use_container_width=True, hide_index=True, height=420)

    # -----------------------------------------------------
    # Horizontal Ranking Chart
    # -----------------------------------------------------

    with right:

        fig_rank = px.bar(
            top10,
            x="composite_quality_score",
            y="company_name",
            orientation="h",
            color="return_on_equity_pct",
            color_continuous_scale="Viridis",
            text="composite_quality_score",
        )

        fig_rank.update_traces(texttemplate="%{text:.1f}", textposition="outside")

        fig_rank.update_layout(
            title="Quality Score Ranking",
            xaxis_title="Quality Score",
            yaxis_title="",
            height=420,
            yaxis=dict(autorange="reversed"),
            coloraxis_colorbar=dict(title="ROE"),
            margin=dict(t=50, l=10, r=10, b=10),
        )

        st.plotly_chart(fig_rank, use_container_width=True)

    divider()

    # ======================================================
    # Best Performing Company
    # ======================================================

    if not top10.empty:
        best = top10.iloc[0]

        st.success(
            f"""
### 🥇 Best Capital Allocation Company

**{best['company_name']}**

• Pattern : **{best['Capital Pattern']}**

• ROE : **{display_value(best.get('return_on_equity_pct'), '%')}**

• Debt / Equity : **{display_value(best.get('debt_to_equity'))}**

• Quality Score : **{display_value(best.get('composite_quality_score'))}**
"""
        )

    divider()

    # ======================================================
    # Advanced Analytics
    # ======================================================

    st.subheader("📈 Advanced Capital Allocation Analytics")

    col1, col2 = st.columns(2)

    # ------------------------------------------------------
    # Sector Average ROE
    # ------------------------------------------------------

    with col1:

        sector_kpi = (
            filtered
            .groupby("broad_sector")
            .agg(
                Avg_ROE=("return_on_equity_pct", "mean"),
                Companies=("company_id", "count"),
            )
            .reset_index()
            .sort_values("Avg_ROE", ascending=False)
        )

        fig_sector = px.bar(
            sector_kpi,
            x="broad_sector",
            y="Avg_ROE",
            color="Companies",
            color_continuous_scale="Viridis",
            text="Avg_ROE",
        )

        fig_sector.update_traces(texttemplate="%{text:.1f}", textposition="outside")

        fig_sector.update_layout(
            title="Average ROE by Sector",
            xaxis_title="",
            yaxis_title="ROE (%)",
            height=450,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
        )

        st.plotly_chart(fig_sector, use_container_width=True)

    # ------------------------------------------------------
    # Pattern Comparison
    # ------------------------------------------------------

    with col2:

        pattern_stats = (
            filtered
            .groupby("Capital Pattern")
            .agg(
                Avg_Quality=("composite_quality_score", "mean"),
                Avg_Debt=("debt_to_equity", "mean"),
            )
            .reset_index()
        )

        pattern_stats["Avg_Quality"] = pattern_stats["Avg_Quality"].fillna(0)
        pattern_stats["Avg_Debt"] = pattern_stats["Avg_Debt"].fillna(0)

        # size values must be non-negative for plotly
        pattern_stats["Avg_Quality"] = pattern_stats["Avg_Quality"].clip(lower=0)

        fig_pattern = px.scatter(
            pattern_stats,
            x="Avg_Debt",
            y="Avg_Quality",
            size="Avg_Quality",
            color="Capital Pattern",
            text="Capital Pattern",
        )

        fig_pattern.update_traces(textposition="top center")

        fig_pattern.update_layout(
            title="Quality vs Debt",
            xaxis_title="Average Debt / Equity",
            yaxis_title="Average Quality Score",
            height=450,
            margin=dict(l=20, r=20, t=40, b=20),
        )

        st.plotly_chart(fig_pattern, use_container_width=True)

    divider()

    # ======================================================
    # Pattern Statistics
    # ======================================================

    st.subheader("📋 Pattern Statistics")

    stats = (
        filtered
        .groupby("Capital Pattern")
        .agg(
            Companies=("company_id", "count"),
            Avg_ROE=("return_on_equity_pct", "mean"),
            Avg_Debt=("debt_to_equity", "mean"),
            Avg_Revenue=("revenue_cagr_5yr", "mean"),
            Avg_Quality=("composite_quality_score", "mean"),
        )
        .reset_index()
    )

    stats.columns = [
        "Pattern",
        "Companies",
        "Average ROE",
        "Average Debt",
        "Average Revenue CAGR",
        "Average Quality",
    ]

    st.dataframe(stats.round(2).fillna("N/A"), use_container_width=True, hide_index=True)

    divider()

    # ======================================================
    # Download Results
    # ======================================================

    st.subheader("📥 Export Results")

    export_df = company_table.copy()

    csv = export_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Download Company List (CSV)",
        data=csv,
        file_name="capital_allocation_map.csv",
        mime="text/csv",
        use_container_width=True,
    )

    divider()

    # ======================================================
    # Dashboard Summary
    # ======================================================

    st.subheader("📌 Dashboard Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Companies", len(filtered))
    c2.metric("Patterns", filtered["Capital Pattern"].nunique())
    c3.metric("Sectors", filtered["broad_sector"].nunique())
    c4.metric("Latest Year", latest_year)

    divider()

    # ======================================================
    # Dataset Information
    # ======================================================

    with st.expander("ℹ Dataset Information", expanded=False):

        st.markdown(
            f"""
### Financial Year

**{latest_year}**

### Database Tables Used

- Companies
- Financial Ratios
- Sectors

### Total Records

- Companies Loaded : **{len(df)}**
- Companies Displayed : **{len(filtered)}**

### Capital Allocation Patterns

- High Quality
- Growth Focus
- Cash Generator
- Debt Free
- Capital Efficient
- Highly Leveraged
- Turnaround
- Balanced

### Metrics Used

- Return on Equity
- Debt / Equity
- Revenue CAGR
- Free Cash Flow
- Composite Quality Score

### Dashboard

Sprint 4 • Day 25
"""
        )

    divider()

    # ======================================================
    # Footer
    # ======================================================

    st.caption(
        "📊 N100 Financial Analytics Dashboard "
    )


if __name__ == "__main__":
    show()