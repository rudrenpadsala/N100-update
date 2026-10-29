# profile.py
import time

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_bs,
    get_cf,
    get_sectors,
)
from utils.theme import page_header
from utils.helpers import display_value


def styled_divider():
    st.markdown("<hr/>", unsafe_allow_html=True)


# -------------------------------------------------------
# Safe Helper
# -------------------------------------------------------
def safe_value(value, default=0):
    """Return default when value is None or NaN."""
    if value is None:
        return default

    if pd.isna(value):
        return default

    return value


# -------------------------------------------------------
# Company Profile Page
# -------------------------------------------------------
def show():

    page_header(
        "🏢",
        "Company Profile",
        "Deep-dive into a single company's fundamentals, ratios and history.",
    )

    # ---------------------------------------------------
    # Load Companies
    # ---------------------------------------------------
    companies = get_companies()

    if companies.empty:
        st.error("Company database not found.")
        st.stop()

    # ---------------------------------------------------
    # Search by Ticker (id) OR Company Name.
    #
    # Streamlit's selectbox filters its options list against
    # whatever format_func renders, so typing "TCS" matches the
    # "Tata Consultancy Services Ltd (TCS)" option even though the
    # underlying value passed around is just the ticker id. This
    # replaces the old company_name-only dropdown, which had no way
    # to match on ticker at all.
    # ---------------------------------------------------

    company_ids = (
        companies["id"]
        .dropna()
        .unique()
        .tolist()
    )

    def format_company_option(company_id):
        row = companies.loc[companies["id"] == company_id]

        if row.empty:
            return company_id

        name = row["company_name"].iloc[0]
        return f"{name} ({company_id})"

    company_ids_sorted = sorted(
        company_ids,
        key=lambda cid: format_company_option(cid),
    )

    # Respect ticker click or query param
    target_cid = st.session_state.get("selected_ticker") or st.query_params.get("symbol")
    default_idx = 0
    if target_cid and target_cid in company_ids_sorted:
        default_idx = company_ids_sorted.index(target_cid)

    selected_id = st.selectbox(
        "🔍 Search Company / Ticker",
        company_ids_sorted,
        index=default_idx,
        format_func=format_company_option,
    )

    company_rows = companies[
        companies["id"] == selected_id
    ]

    if company_rows.empty:
        st.warning(
            "Ticker not found — please try another."
        )
        st.stop()

    company = company_rows.iloc[0]

    company_id = company["id"]
    selected_company = company["company_name"]

    # ---------------------------------------------------
    # Load Database Tables
    # ---------------------------------------------------
    ratios = get_ratios(company_id)
    pl = get_pl(company_id)
    bs = get_bs(company_id)
    cf = get_cf(company_id)
    sectors = get_sectors()

    sector = sectors[
        sectors["company_id"] == company_id
    ]

    # ---------------------------------------------------
    # Data Available Indicator
    # ---------------------------------------------------

    if not ratios.empty:

        available_years = len(ratios)

        st.info(
            f"📅 Data Available: {available_years} Financial Years"
        )

        if available_years < 10:

            st.warning(
                f"Only {available_years} years of financial data are available."
            )

    # ---------------------------------------------------
    # Validate Required Data
    # ---------------------------------------------------
    if ratios.empty:
        st.warning(
            "Financial Ratio data not available."
        )
        st.stop()

    if pl.empty:
        st.warning(
            "Profit & Loss data not available."
        )
        st.stop()

    latest = ratios.sort_values(
        "year"
    ).iloc[-1]

    # ---------------------------------------------------
    # Safe Variables
    # ---------------------------------------------------
    roe_raw = latest.get("return_on_equity_pct")
    roe = safe_value(roe_raw)

    roce_raw = company.get("roce_percentage")
    roce = safe_value(roce_raw)

    npm_raw = latest.get("net_profit_margin_pct")
    npm = safe_value(npm_raw)

    debt_raw = latest.get("debt_to_equity")
    debt = safe_value(debt_raw)

    revenue_cagr_raw = latest.get("revenue_cagr_5yr")
    revenue_cagr = safe_value(revenue_cagr_raw)

    pat_cagr = safe_value(
        latest.get("pat_cagr_5yr")
    )

    eps_cagr = safe_value(
        latest.get("eps_cagr_5yr")
    )

    interest = safe_value(
        latest.get("interest_coverage")
    )

    fcf_raw = latest.get("free_cash_flow_cr")
    fcf = safe_value(fcf_raw)

    quality_raw = latest.get("composite_quality_score")
    quality = safe_value(quality_raw)

    # ==========================================================
    # Company Information
    # ==========================================================

    styled_divider()

    # ---------------------------------------------------
    # Sector / Company / Ticker info strip
    #
    # Placed immediately below the page title, matching the layout
    # used by dashboards like Screener and Tickertape. Ticker uses
    # company["id"] (the internal id already used for lookups)
    # rather than chart_link, so it's guaranteed to match whatever
    # was just searched/selected above.
    # ---------------------------------------------------

    sector_name = "N/A"
    sub_sector = "N/A"

    if not sector.empty:
        sector_name = sector.iloc[0]["broad_sector"]
        sub_sector = sector.iloc[0]["sub_sector"]

    strip_col1, strip_col2, strip_col3 = st.columns(3)

    strip_col1.info(f"**Sector**\n\n{sector_name}")
    strip_col2.info(f"**Company**\n\n{company['company_name']}")
    strip_col3.info(f"**Ticker**\n\n{company['id']}")

    # Public Market Data Quote Strip
    try:
        from utils.smartapi_client import get_smartapi_client
        provider = get_smartapi_client()
        live_q = provider.get_company_quote(company_id)
        if live_q:
            lp = live_q.get("price", 0.0)
            lc = live_q.get("change", 0.0)
            lpct = live_q.get("pct_change", 0.0)
            lh = live_q.get("high", 0.0)
            ll = live_q.get("low", 0.0)
            lv = live_q.get("volume", 0)
            ldt = live_q.get("latest_date", "2026-10-29")
            is_pos = lc >= 0
            color = "#10B981" if is_pos else "#EF4444"
            arr = "▲" if is_pos else "▼"
            sign = "+" if is_pos else ""
            status_txt = f"EOD {ldt}"

            st.markdown(
                f"""
                <div style="background: rgba(30, 99, 214, 0.05); border: 1px solid #D3DEF2; border-left: 5px solid {color}; border-radius: 10px; padding: 10px 16px; margin: 10px 0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    <div>
                        <span style="font-weight: 800; font-size: 1.2rem; color: #0B1F4B;">₹{lp:,.2f}</span>
                        <span style="font-weight: 700; font-size: 0.95rem; color: {color}; margin-left: 8px;">{arr} {sign}{lc:,.2f} ({sign}{lpct:.2f}%)</span>
                        <span style="color: #5B6B8C; font-size: 0.82rem; margin-left: 14px;">Day: ₹{ll:,.2f} - ₹{lh:,.2f} • Vol: {lv:,} • Session: <b>{status_txt}</b></span>
                    </div>
                    <div>
                        <a href="?page=live_market&symbol={company_id}" target="_self" style="background: #0B1F4B; color: #FFFFFF !important; text-decoration: none; padding: 5px 12px; border-radius: 6px; font-size: 0.78rem; font-weight: 700;">⚡ View Technicals & Chart</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    except Exception as e:
        pass

    styled_divider()

    info_col, sector_col = st.columns([2, 1])

    with info_col:

        st.subheader(company["company_name"])

        about = company.get("about_company")

        if pd.notna(about):
            st.write(about)
        else:
            st.info("N/A")

        website = company.get("website")

        if pd.isna(website):
            st.write("🌐 **Website:** N/A")
        else:
            st.write(f"🌐 **Website:** {website}")

        face_value_raw = company.get("face_value")
        book_value_raw = company.get("book_value")

        face_value_text = (
            "N/A"
            if face_value_raw is None or pd.isna(face_value_raw)
            else f"₹{face_value_raw}"
        )
        book_value_text = (
            "N/A"
            if book_value_raw is None or pd.isna(book_value_raw)
            else f"₹{book_value_raw}"
        )

        st.write(f"💰 **Face Value:** {face_value_text}")

        st.write(f"📚 **Book Value:** {book_value_text}")

    with sector_col:

        st.subheader("Sector Information")

        if not sector.empty:

            sector_row = sector.iloc[0]

            st.write(
                f"**Sector:** {sector_row['broad_sector']}"
            )

            st.write(
                f"**Sub Sector:** {sector_row['sub_sector']}"
            )

            index_weight_raw = sector_row.get("index_weight_pct")

            st.write(
                f"**Index Weight:** {display_value(index_weight_raw, '%')}"
            )

            market_cap = sector_row.get(
                "market_cap_category"
            )

            if pd.notna(market_cap):
                st.write(
                    f"**Market Cap:** {market_cap}"
                )

        else:

            st.info(
                "Sector information not available."
            )

    # ==========================================================
    # KPI Cards
    # ==========================================================

    styled_divider()

    st.subheader("Key Financial Metrics")

    row1 = st.columns(3)
    row2 = st.columns(3)

    row1[0].metric(
        "ROE",
        display_value(roe_raw, "%")
    )

    row1[1].metric(
        "ROCE",
        display_value(roce_raw, "%")
    )

    row1[2].metric(
        "Net Profit Margin",
        display_value(npm_raw, "%")
    )

    row2[0].metric(
        "Debt / Equity",
        display_value(debt_raw)
    )

    row2[1].metric(
        "Revenue CAGR (5Y)",
        display_value(revenue_cagr_raw, "%")
    )

    fcf_text = (
        "N/A"
        if fcf_raw is None or pd.isna(fcf_raw)
        else f"₹{fcf_raw:.2f} Cr"
    )

    row2[2].metric(
        "Free Cash Flow",
        fcf_text
    )

    st.metric(
        "Composite Quality Score",
        display_value(quality_raw)
    )

    # ==========================================================
    # Revenue vs Net Profit Chart (animated)
    # ==========================================================

    styled_divider()

    st.subheader("Revenue vs Net Profit (10 Years)")

    if not pl.empty:

        chart_df = pl.copy()

        chart_df["sales"] = chart_df["sales"].fillna(0)
        chart_df["net_profit"] = chart_df["net_profit"].fillna(0)

        years = chart_df["year"].tolist()
        sales_final = chart_df["sales"].tolist()
        profit_final = chart_df["net_profit"].tolist()

        max_val = max(sales_final + profit_final)
        y_axis_max = max_val * 1.15 if max_val > 0 else 1

        def build_revenue_fig(sales_vals, profit_vals):
            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=years,
                    y=sales_vals,
                    name="sales",
                    marker_color="#6C63FF",
                )
            )

            fig.add_trace(
                go.Bar(
                    x=years,
                    y=profit_vals,
                    name="net_profit",
                    marker_color="#FF6B9D",
                )
            )

            fig.update_layout(
                title="Revenue vs Net Profit",
                barmode="group",
                height=500,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Financial Year",
                yaxis_title="₹ Crore",
                legend_title="Metric",
                yaxis=dict(range=[0, y_axis_max]),
                transition=dict(duration=0),
            )

            return fig

        revenue_placeholder = st.empty()

        replay_col_rev, _ = st.columns([1, 5])
        play_revenue = replay_col_rev.button(
            "▶ Play Animation",
            key="revenue_play_btn",
        )

        if "revenue_animated_once" not in st.session_state:
            st.session_state.revenue_animated_once = False

        def animate_revenue():
            n_frames = 24
            for i in range(1, n_frames + 1):
                t = i / n_frames
                eased_t = 1 - (1 - t) ** 3  # ease-out cubic

                frame_sales = [v * eased_t for v in sales_final]
                frame_profit = [v * eased_t for v in profit_final]

                fig = build_revenue_fig(frame_sales, frame_profit)

                revenue_placeholder.plotly_chart(
                    fig,
                    use_container_width=True,
                    key=f"revenue_frame_{i}",
                )

                time.sleep(0.02)

            st.session_state.revenue_animated_once = True

        if play_revenue or not st.session_state.revenue_animated_once:
            animate_revenue()
        else:
            final_fig = build_revenue_fig(sales_final, profit_final)
            revenue_placeholder.plotly_chart(
                final_fig,
                use_container_width=True,
                key="revenue_final",
            )

    else:

        st.info("Revenue data not available.")

    # ==========================================================
    # ROE vs ROCE Trend (animated)
    # ==========================================================

    styled_divider()

    st.subheader("ROE vs ROCE Trend")

    if not ratios.empty:

        trend_df = ratios.copy()

        trend_df["return_on_equity_pct"] = (
            trend_df["return_on_equity_pct"]
            .fillna(0)
        )

        trend_years = trend_df["year"].tolist()
        roe_final = trend_df["return_on_equity_pct"].tolist()
        roce_final = [roce] * len(trend_df)

        def build_trend_fig(n_points):
            fig = make_subplots(
                specs=[[{"secondary_y": True}]]
            )

            fig.add_trace(
                go.Scatter(
                    x=trend_years[:n_points],
                    y=roe_final[:n_points],
                    mode="lines+markers",
                    name="ROE",
                    line=dict(color="#6C63FF", width=3),
                ),
                secondary_y=False,
            )

            fig.add_trace(
                go.Scatter(
                    x=trend_years[:n_points],
                    y=roce_final[:n_points],
                    mode="lines+markers",
                    name="ROCE",
                    line=dict(color="#FF6B9D", width=3),
                ),
                secondary_y=True,
            )

            fig.update_layout(
                height=500,
                margin=dict(l=20, r=20, t=40, b=20),
                legend_title="Metric",
                transition=dict(duration=0),
            )

            fig.update_xaxes(
                title_text="Financial Year",
                range=[trend_years[0], trend_years[-1]],
            )

            roe_max = max(roe_final) * 1.15 if max(roe_final) > 0 else 1
            roce_max = max(roce_final) * 1.15 if max(roce_final) > 0 else 1

            fig.update_yaxes(
                title_text="ROE (%)",
                secondary_y=False,
                range=[0, roe_max],
            )

            fig.update_yaxes(
                title_text="ROCE (%)",
                secondary_y=True,
                range=[0, roce_max],
            )

            return fig

        trend_placeholder = st.empty()

        replay_col_trend, _ = st.columns([1, 5])
        play_trend = replay_col_trend.button(
            "▶ Play Animation",
            key="trend_play_btn",
        )

        if "trend_animated_once" not in st.session_state:
            st.session_state.trend_animated_once = False

        def animate_trend():
            total_points = len(trend_years)

            for n_points in range(1, total_points + 1):
                fig = build_trend_fig(n_points)

                trend_placeholder.plotly_chart(
                    fig,
                    use_container_width=True,
                    key=f"trend_frame_{n_points}",
                )

                time.sleep(0.08)

            st.session_state.trend_animated_once = True

        if play_trend or not st.session_state.trend_animated_once:
            animate_trend()
        else:
            final_fig = build_trend_fig(len(trend_years))
            trend_placeholder.plotly_chart(
                final_fig,
                use_container_width=True,
                key="trend_final",
            )

    else:

        st.info("ROE trend data not available.")

    # ==========================================================
    # Pros & Cons
    # ==========================================================

    styled_divider()

    st.subheader("Pros & Cons")

    pros_col, cons_col = st.columns(2)

    with pros_col:

        st.success("Pros")

        pros = []

        if roe >= 15:
            pros.append("✅ Strong Return on Equity")

        if revenue_cagr >= 10:
            pros.append("✅ Healthy Revenue Growth")

        if pat_cagr >= 10:
            pros.append("✅ Strong PAT Growth")

        if eps_cagr >= 10:
            pros.append("✅ Strong EPS Growth")

        if debt <= 0.50:
            pros.append("✅ Low Debt")

        if fcf > 0:
            pros.append("✅ Positive Free Cash Flow")

        if interest >= 3:
            pros.append("✅ Healthy Interest Coverage")

        if quality >= 70:
            pros.append("✅ High Composite Quality Score")

        if len(pros) == 0:
            st.info("No major strengths identified.")

        else:

            for item in pros:
                st.write(item)

    with cons_col:

        st.error("Cons")

        cons = []

        if debt > 1:
            cons.append("❌ High Debt")

        if interest < 3:
            cons.append("❌ Low Interest Coverage")

        if npm < 5:
            cons.append("❌ Low Net Profit Margin")

        if revenue_cagr < 5:
            cons.append("❌ Weak Revenue Growth")

        if pat_cagr < 5:
            cons.append("❌ Weak PAT Growth")

        if eps_cagr < 5:
            cons.append("❌ Weak EPS Growth")

        if fcf < 0:
            cons.append("❌ Negative Free Cash Flow")

        if quality < 50:
            cons.append("❌ Low Composite Quality Score")

        if len(cons) == 0:
            st.info("No major weaknesses identified.")

        else:

            for item in cons:
                st.write(item)

    # ==========================================================
    # Balance Sheet
    # ==========================================================

    styled_divider()

    st.subheader("Balance Sheet")

    if not bs.empty:

        bs_display = (
            bs.sort_values(
                "year",
                ascending=False,
            )
            .fillna("N/A")
        )

        st.dataframe(
            bs_display,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info("Balance Sheet data not available.")

    # ==========================================================
    # Cash Flow Statement
    # ==========================================================

    styled_divider()

    st.subheader("Cash Flow Statement")

    if not cf.empty:

        cf_display = (
            cf.sort_values(
                "year",
                ascending=False,
            )
            .fillna("N/A")
        )

        st.dataframe(
            cf_display,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info("Cash Flow data not available.")

    # ==========================================================
    # Financial Summary
    # ==========================================================

    styled_divider()

    st.subheader("Financial Summary")

    summary_left, summary_right = st.columns(2)

    with summary_left:

        st.metric(
            "Revenue CAGR (5Y)",
            f"{revenue_cagr:.2f}%"
        )

        st.metric(
            "PAT CAGR (5Y)",
            f"{pat_cagr:.2f}%"
        )

        st.metric(
            "EPS CAGR (5Y)",
            f"{eps_cagr:.2f}%"
        )

    with summary_right:

        st.metric(
            "Interest Coverage",
            f"{interest:.2f}"
        )

        st.metric(
            "Debt / Equity",
            f"{debt:.2f}"
        )

        st.metric(
            "Composite Quality Score",
            f"{quality:.2f}"
        )

    # ==========================================================
    # About Company
    # ==========================================================

    styled_divider()

    st.subheader("About Company")

    about = company.get("about_company")

    if pd.notna(about):

        st.info(about)

    else:

        st.info("No company description available.")

    # ==========================================================
    # Useful Links
    # ==========================================================

    styled_divider()

    st.subheader("Useful Links")

    website = company.get("website")
    nse = company.get("nse_profile")
    bse = company.get("bse_profile")

    if pd.notna(website):
        st.markdown(f"🌐 **Website:** {website}")

    if pd.notna(nse):
        st.markdown(f"📈 **NSE Profile:** {nse}")

    if pd.notna(bse):
        st.markdown(f"🏛️ **BSE Profile:** {bse}")

    # ==========================================================
    # Download Financial Data
    # ==========================================================

    styled_divider()

    st.subheader("Download Financial Data")

    if not pl.empty:

        csv = pl.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Download Profit & Loss CSV",
            data=csv,
            file_name=f"{selected_company}_{company_id}_profit_loss.csv",
            mime="text/csv",
        )

    # ==========================================================
    # Footer
    # ==========================================================

    styled_divider()

    st.caption(
            "📊 N100 Financial Analytics Dashboard "
        )