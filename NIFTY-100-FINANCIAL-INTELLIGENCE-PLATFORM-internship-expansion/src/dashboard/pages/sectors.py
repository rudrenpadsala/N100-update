# sectors.py
import streamlit as st
import pandas as pd
import plotly.express as px

from utils.db import (
    get_companies,
    get_ratios,
    get_sectors,
)
from utils.theme import page_header
from utils.helpers import display_value

# get_market_cap and get_pl are imported defensively. If either is
# missing from utils/db.py, a plain `from utils.db import get_market_cap`
# at module load time would raise ImportError and crash the ENTIRE
# dashboard on startup (app.py imports every page module up front),
# not just this page. Catching it here means a missing function just
# triggers the in-page fallback instead of taking the whole app down.
try:
    from utils.db import get_market_cap
    HAS_MARKET_CAP = True
except ImportError:
    HAS_MARKET_CAP = False

try:
    from utils.db import get_pl
    HAS_PL = True
except ImportError:
    HAS_PL = False


# =========================================================
# Helper Functions
# =========================================================

def divider():
    st.markdown("<hr/>", unsafe_allow_html=True)


def safe_series(df, column, default=0):

    if column not in df.columns:
        return pd.Series([default] * len(df))

    return df[column].fillna(default)


def safe_float(value):

    try:

        if pd.isna(value):
            return 0.0

        return float(value)

    except Exception:

        return 0.0


# Candidate column names for revenue, in priority order.
REVENUE_CANDIDATES = [
    "sales",
    "revenue",
    "revenue_cr",
    "sales_cr",
    "net_sales_cr",
    "total_revenue_cr",
]

def find_revenue_column(df):
    for col in REVENUE_CANDIDATES:
        if col in df.columns:
            return col
    return None


# =========================================================
# Sector Analysis
# =========================================================

def show():

    page_header(
        "🏭",
        "Sector Analysis",
        "Compare sectors across profitability, leverage and growth.",
    )

    # -----------------------------------------------------
    # Load Data
    # -----------------------------------------------------

    companies = get_companies()
    ratios = get_ratios()
    sectors = get_sectors()

    if (
        companies.empty
        or ratios.empty
        or sectors.empty
    ):

        st.warning(
            "Sector data not available."
        )

        st.stop()

    # Market cap is required by the sprint spec for bubble sizing.
    # Loaded here (visibly, not silently) so a failure surfaces
    # immediately rather than after several merges.
    market_cap_ok = False
    market = pd.DataFrame()

    if HAS_MARKET_CAP:
        try:
            market = get_market_cap()

            market_cap_ok = (
                not market.empty
                and "company_id" in market.columns
                and "market_cap_crore" in market.columns
            )
            if market_cap_ok:
                market = (
                    market.sort_values("year")
                    .groupby("company_id", as_index=False)
                    .last()
                )

        except Exception:
            market = pd.DataFrame()
            market_cap_ok = False

    if not market_cap_ok:
        reason = (
            "utils.db.get_market_cap() does not exist yet"
            if not HAS_MARKET_CAP
            else "get_market_cap() returned no usable 'company_id' / "
                 "'market_cap_crore' columns"
        )

        st.warning(
            f"⚠️ Market Cap data could not be loaded ({reason}). "
            "Falling back to Composite Quality Score for bubble size."
        )

    # -----------------------------------------------------
    # Rename Company ID
    # -----------------------------------------------------

    companies = companies.rename(
        columns={
            "id": "company_id"
        }
    )

    # -----------------------------------------------------
    # Merge Company Names
    # -----------------------------------------------------

    df = ratios.merge(

        companies[
            [
                "company_id",
                "company_name",
            ]
        ],

        on="company_id",

        how="left",

    )

    # -----------------------------------------------------
    # Merge Sector Data
    # -----------------------------------------------------

    df = df.merge(

        sectors,

        on="company_id",

        how="left",

    )

    # -----------------------------------------------------
    # Merge Market Cap
    # -----------------------------------------------------

    if market_cap_ok:
        df = df.merge(
            market[["company_id", "market_cap_crore"]],
            on="company_id",
            how="left",
        )

    # -----------------------------------------------------
    # Resolve Revenue Column
    #
    # Tries known column names first. If none are present on the
    # merged table, falls back to loading Profit & Loss data (if
    # get_pl exists) and merging a revenue column from there. If
    # that also fails, a visible warning is shown and the chart
    # falls back to Revenue CAGR so the page doesn't crash.
    # -----------------------------------------------------

    revenue_col = find_revenue_column(df)
    revenue_ok = revenue_col is not None

    if not revenue_ok and HAS_PL:
        try:
            pl = get_pl()

            pl_revenue_col = find_revenue_column(pl)

            if (
                not pl.empty
                and "company_id" in pl.columns
                and pl_revenue_col is not None
            ):
                latest_pl = (
                    pl.sort_values("year")
                    .groupby("company_id", as_index=False)
                    .last()
                )
                df = df.merge(
                    latest_pl[["company_id", pl_revenue_col]],
                    on="company_id",
                    how="left",
                )

                revenue_col = pl_revenue_col
                revenue_ok = True

        except Exception:
            pass

    if not revenue_ok:
        st.warning(
            "⚠️ No Revenue column found on Ratios, Companies, or "
            "Profit & Loss data. Falling back to Revenue CAGR (5yr) "
            "for the X axis instead of Revenue."
        )
        revenue_col = "revenue_cagr_5yr"

    # -----------------------------------------------------
    # Fill Missing Values
    # -----------------------------------------------------

    df["return_on_equity_pct"] = safe_series(
        df,
        "return_on_equity_pct",
    )

    df["revenue_cagr_5yr"] = safe_series(
        df,
        "revenue_cagr_5yr",
    )

    df["free_cash_flow_cr"] = safe_series(
        df,
        "free_cash_flow_cr",
    )

    df["composite_quality_score"] = safe_series(
        df,
        "composite_quality_score",
    )

    df["index_weight_pct"] = safe_series(
        df,
        "index_weight_pct",
    )

    df[revenue_col] = safe_series(
        df,
        revenue_col,
    )

    if market_cap_ok:
        df["market_cap_crore"] = safe_series(
            df,
            "market_cap_crore",
        )

    # -----------------------------------------------------
    # Keep latest record PER COMPANY, not just the single
    # latest year across the whole table (the original bug:
    # df["year"].max() picked Sep 2024, a year only 1 of 92
    # companies had a row for, dropping the other 91).
    # -----------------------------------------------------

    df = (
        df
        .sort_values("year")
        .groupby("company_id", as_index=False)
        .last()
    )

    latest_year = "Latest Available"

    # Bubble size column: Market Cap per spec, quality score fallback.
    bubble_size_col = "market_cap_crore" if market_cap_ok else "composite_quality_score"
    bubble_size_label = "Market Cap (Cr)" if market_cap_ok else "Quality Score"

    # X-axis label reflects whichever column actually got used.
    x_axis_label = "Revenue (Cr)" if revenue_col != "revenue_cagr_5yr" else "Revenue CAGR (%)"

    # -----------------------------------------------------
    # Sidebar Filters
    # -----------------------------------------------------

    st.sidebar.header("🔍 Filters")

    sector_list = sorted(
        df["broad_sector"].dropna().unique().tolist()
    )

    selected_sector = st.sidebar.selectbox(
        "Sector",
        ["All"] + sector_list,
    )

    subsector_list = sorted(
        df["sub_sector"].dropna().unique().tolist()
    )

    selected_subsector = st.sidebar.selectbox(
        "Sub Sector",
        ["All"] + subsector_list,
    )

    search_company = st.sidebar.text_input(
        "Search Company"
    )

    roe = st.sidebar.slider(
        "Minimum ROE (%)",
        0,
        50,
        10,
    )

    growth = st.sidebar.slider(
        "Minimum Revenue CAGR (%)",
        -20,
        50,
        0,
    )

    quality = st.sidebar.slider(
        "Minimum Quality Score",
        0,
        100,
        0,
    )

    # -----------------------------------------------------
    # Apply Filters
    # -----------------------------------------------------

    sector_df = df.copy()

    if selected_sector != "All":
        sector_df = sector_df[
            sector_df["broad_sector"] == selected_sector
        ]

    if selected_subsector != "All":
        sector_df = sector_df[
            sector_df["sub_sector"] == selected_subsector
        ]

    if search_company:
        sector_df = sector_df[
            sector_df["company_name"]
            .str.contains(
                search_company,
                case=False,
                na=False,
            )
        ]

    sector_df = sector_df[
        sector_df["return_on_equity_pct"] >= roe
    ]

    sector_df = sector_df[
        sector_df["revenue_cagr_5yr"] >= growth
    ]

    sector_df = sector_df[
        sector_df["composite_quality_score"] >= quality
    ]

    if sector_df.empty:

        st.warning(
            "No companies match the selected filters."
        )

        st.stop()

    # -----------------------------------------------------
    # KPI Cards
    # -----------------------------------------------------

    header_label = (
        selected_sector if selected_sector != "All" else "All Sectors"
    )

    st.subheader(header_label)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Companies",
        len(sector_df),
    )

    c2.metric(
        "Average ROE",
        display_value(sector_df["return_on_equity_pct"].mean(), "%")
    )

    c3.metric(
        "Average Revenue CAGR",
        display_value(sector_df["revenue_cagr_5yr"].mean(), "%")
    )

    c4.metric(
        "Average Quality Score",
        display_value(sector_df["composite_quality_score"].mean())
    )

    divider()

    # -----------------------------------------------------
    # Bubble Chart — X = Revenue, Y = ROE,
    # Size = Market Cap, Colour = Sub Sector
    # -----------------------------------------------------

    st.subheader("📈 Sector Bubble Chart")

    st.caption(
        f"X = {x_axis_label} | Y = ROE | Bubble Size = {bubble_size_label} | Colour = Sub Sector"
    )

    bubble_df = sector_df.copy()

    bubble_df["return_on_equity_pct"] = (
        bubble_df["return_on_equity_pct"]
        .fillna(0)
    )

    bubble_df[revenue_col] = (
        bubble_df[revenue_col]
        .fillna(0)
    )

    bubble_df[bubble_size_col] = (
        bubble_df[bubble_size_col]
        .fillna(0 if bubble_size_col == "market_cap_crore" else 10)
    )

    # size values must be non-negative for plotly
    bubble_df[bubble_size_col] = bubble_df[bubble_size_col].clip(lower=0)

    bubble_df["sub_sector"] = (
        bubble_df["sub_sector"]
        .fillna("Unknown")
    )

    bubble_df["company_name"] = (
        bubble_df["company_name"]
        .fillna("Unknown")
    )

    fig = px.scatter(

        bubble_df,

        x=revenue_col,

        y="return_on_equity_pct",

        size=bubble_size_col,

        color="sub_sector",

        hover_name="company_name",

        hover_data={

            revenue_col: ":.2f",

            "return_on_equity_pct": ":.2f",

            bubble_size_col: ":.2f",

            "sub_sector": True,

        },

        size_max=70,

    )

    fig.update_traces(

        marker=dict(

            opacity=0.85,

            line=dict(
                width=1,
                color="white",
            ),

        )

    )

    fig.update_layout(

        height=650,

        template="plotly_white",

        xaxis_title=x_axis_label,

        yaxis_title="ROE (%)",

        legend_title="Sub Sector",

        hovermode="closest",

        margin=dict(

            l=20,

            r=20,

            t=40,

            b=20,

        ),

    )

    st.plotly_chart(

        fig,

        use_container_width=True,

    )

    divider()

    # -----------------------------------------------------
    # Sector Median KPI Chart
    # -----------------------------------------------------

    st.subheader("📊 Sector Median KPIs")

    median_df = pd.DataFrame(

        {

            "Metric": [

                "ROE",

                "Revenue CAGR",

                "FCF",

                "Quality Score",

            ],

            "Value": [

                sector_df["return_on_equity_pct"].median(),

                sector_df["revenue_cagr_5yr"].median(),

                sector_df["free_cash_flow_cr"].median(),

                sector_df["composite_quality_score"].median(),

            ],

        }

    )

    bar = px.bar(

        median_df,

        x="Metric",

        y="Value",

        color="Metric",

        text="Value",

    )

    bar.update_traces(

        texttemplate="%{text:.2f}",

        textposition="outside",

    )

    bar.update_layout(

        height=500,

        margin=dict(
            l=20,
            r=20,
            t=40,
            b=20,
        ),

        template="plotly_white",

        showlegend=False,

        yaxis_title="Median Value",

        xaxis_title="",

    )

    st.plotly_chart(

        bar,

        use_container_width=True,

    )

    divider()

    # -----------------------------------------------------
    # Top Companies
    # -----------------------------------------------------

    st.subheader("🏆 Top Companies in Sector")

    top_companies = (

        sector_df

        .sort_values(

            "composite_quality_score",

            ascending=False,

        )

        [

            [

                "company_name",

                "sub_sector",

                "return_on_equity_pct",

                "revenue_cagr_5yr",

                "free_cash_flow_cr",

                "composite_quality_score",

            ]

        ]

        .copy()

    )

    top_companies.columns = [

        "Company",

        "Sub Sector",

        "ROE (%)",

        "Revenue CAGR (%)",

        "FCF (Cr)",

        "Quality Score",

    ]

    st.dataframe(

        top_companies.fillna("N/A"),

        use_container_width=True,

        hide_index=True,

    )

    divider()

    # -----------------------------------------------------
    # Download CSV
    # -----------------------------------------------------

    st.subheader("📥 Export Data")

    csv = top_companies.to_csv(
        index=False
    ).encode("utf-8")

    export_name = (
        selected_sector.lower().replace(" ", "_")
        if selected_sector != "All"
        else "all_sectors"
    )

    st.download_button(
        label="Download Sector Analysis (CSV)",
        data=csv,
        file_name=f"{export_name}_sector_analysis.csv",
        mime="text/csv",
    )

    divider()

    # -----------------------------------------------------
    # Sector Summary
    # -----------------------------------------------------

    st.subheader("📈 Sector Summary")

    s1, s2, s3 = st.columns(3)

    s1.metric(
        "Highest ROE",
        display_value(sector_df["return_on_equity_pct"].max(), "%")
    )

    s2.metric(
        "Highest Revenue CAGR",
        display_value(sector_df["revenue_cagr_5yr"].max(), "%")
    )

    s3.metric(
        "Highest Quality Score",
        display_value(sector_df["composite_quality_score"].max())
    )

    divider()

    # -----------------------------------------------------
    # Dataset Information
    # -----------------------------------------------------

    with st.expander("ℹ Dataset Information"):

        st.write(
            f"**Financial Year:** {latest_year} (per-company latest)"
        )

        st.write(
            f"**Selected Sector:** {header_label}"
        )

        st.write(
            f"**Companies Shown:** {len(sector_df)}"
        )

        st.write(
            f"**Total Companies:** {len(df)}"
        )

        market_cap_note = (
            "Market Capitalization data is available and is used for bubble size."
            if market_cap_ok
            else "Market Capitalization data could not be loaded, "
                 "so Composite Quality Score is used as the bubble size instead."
        )

        revenue_note = (
            f"Revenue column used: `{revenue_col}`."
            if revenue_col != "revenue_cagr_5yr"
            else "No Revenue column was found, so Revenue CAGR (5yr) is used "
                 "on the X axis instead."
        )

        st.markdown(
            f"""
### Bubble Chart

- **X Axis:** {x_axis_label}
- **Y Axis:** Return on Equity (ROE)
- **Bubble Size:** {bubble_size_label}
- **Bubble Colour:** Sub Sector

### Data Sources

- Companies
- Financial Ratios
- Sectors
- Market Cap

> Note: {market_cap_note} {revenue_note}
            """
        )

    divider()

    # -----------------------------------------------------
    # Footer
    # -----------------------------------------------------

    st.caption(
        "📊 N100 Financial Analytics Dashboard | Sector Analysis"
    )