"""
live_market.py

Professional Market Intelligence & Technical Analysis Dashboard.
- Public Market Data Feed (2025-2026 Daily OHLCV dataset).
- Market Breadth, Advances/Declines, and Index Summary.
- Interactive Candlestick Charts with Volume.
- Technical Indicators: SMA (20, 50), EMA (20, 50), RSI (14), MACD (12, 26, 9).
- Sector Performance & Peer Comparison.
- Searchable & Sortable Constituent Table (all 92 companies).
- No API keys or credentials required; data freshness strictly labeled.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.theme import (
    page_header,
    metric_card,
    NAVY,
    BLUE,
    BORDER,
    SUCCESS,
    ERROR,
    MUTED,
    BLUE_SOFT,
    BROWN,
    BLUE_LIGHT,
)
from utils.db import get_companies, get_sectors
from utils.smartapi_client import get_public_market_provider


def show():
    provider = get_public_market_provider()
    quotes, meta = provider.get_all_quotes()
    companies = get_companies()
    sectors_df = get_sectors()

    latest_date = meta.get("latest_trading_date", "2026-10-29")

    page_header(
        "⚡",
        "Market Intelligence & Technicals",
        f"NIFTY-100 Public Market Data • Updated through {latest_date} • Technical Indicators & Analytics",
    )

    # -------------------------------------------------------------
    # 1. Market Overview & Source Freshness Banner
    # -------------------------------------------------------------
    quotes_list = list(quotes.values())
    total_tracked = len(quotes_list)
    advances = sum(1 for q in quotes_list if q.get("change", 0) > 0)
    declines = sum(1 for q in quotes_list if q.get("change", 0) < 0)
    unchanged = total_tracked - advances - declines
    avg_change = float(np.mean([q.get("pct_change", 0) for q in quotes_list])) if quotes_list else 0.0

    top_gainer = max(quotes_list, key=lambda x: x.get("pct_change", -999)) if quotes_list else {}
    top_loser = min(quotes_list, key=lambda x: x.get("pct_change", 999)) if quotes_list else {}

    col_meta1, col_meta2 = st.columns([3, 2])
    with col_meta1:
        st.markdown(
            f"""
            <div style="background: {BLUE_SOFT}; border: 1px solid {BORDER}; border-left: 5px solid {BLUE}; border-radius: 12px; padding: 12px 18px;">
                <div style="font-weight: 800; font-size: 1rem; color: {NAVY};">
                    📊 NIFTY-100 Market Overview • {latest_date} EOD
                </div>
                <div style="font-size: 0.82rem; color: {MUTED}; margin-top: 4px;">
                    Source: Public Market Data (NSE/Yahoo Finance) • Total Tracked: <b>{total_tracked} Companies</b> • Zero Credentials Required
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_meta2:
        # Market Breadth Bar
        adv_pct = (advances / total_tracked) * 100 if total_tracked > 0 else 50
        dec_pct = (declines / total_tracked) * 100 if total_tracked > 0 else 50
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid {BORDER}; border-radius: 12px; padding: 12px 18px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; font-weight: 700; margin-bottom: 6px;">
                    <span style="color: {SUCCESS};">▲ Advances: {advances} ({adv_pct:.1f}%)</span>
                    <span style="color: {ERROR};">▼ Declines: {declines} ({dec_pct:.1f}%)</span>
                </div>
                <div style="height: 10px; width: 100%; background: {ERROR}; border-radius: 6px; overflow: hidden; display: flex;">
                    <div style="height: 100%; width: {adv_pct}%; background: {SUCCESS};"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Overview KPI Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        metric_card("Constituents", f"{total_tracked} Stocks", f"Freshness: {latest_date}", is_positive=True)
    with kpi2:
        metric_card("Index Momentum", f"{avg_change:+.2f}%", f"{advances} Adv / {declines} Dec", is_positive=(avg_change >= 0))
    with kpi3:
        g_sym = top_gainer.get("company_id", "—")
        g_pct = top_gainer.get("pct_change", 0.0)
        metric_card("Top Gainer", f"{g_sym}", f"+{g_pct:.2f}%", is_positive=True)
    with kpi4:
        l_sym = top_loser.get("company_id", "—")
        l_pct = top_loser.get("pct_change", 0.0)
        metric_card("Top Loser", f"{l_sym}", f"{l_pct:.2f}%", is_positive=False)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 2. Individual Stock Deep-Dive & Technical Indicators
    # -------------------------------------------------------------
    st.subheader("📈 Interactive Stock Candlestick & Technical Analysis")

    company_ids = sorted(list(quotes.keys()))
    default_cid = "TCS" if "TCS" in company_ids else company_ids[0]
    
    qp_sym = st.query_params.get("symbol")
    ss_sym = st.session_state.get("selected_ticker")
    if qp_sym and qp_sym in company_ids:
        default_cid = qp_sym
    elif ss_sym and ss_sym in company_ids:
        default_cid = ss_sym

    default_idx = company_ids.index(default_cid) if default_cid in company_ids else 0

    def format_option(cid):
        q = quotes.get(cid, {})
        name = q.get("company_name", cid)
        chg = q.get("pct_change", 0.0)
        arrow = "▲" if chg >= 0 else "▼"
        return f"{cid} - {name} ({arrow} {chg:+.2f}%)"

    col_sel, col_dur = st.columns([3, 2])
    with col_sel:
        selected_cid = st.selectbox(
            "Select Company to Analyze",
            options=company_ids,
            index=default_idx,
            format_func=format_option,
            key="market_stock_select",
        )
    with col_dur:
        dur_option = st.radio(
            "Lookback Window",
            ["3 Months", "6 Months", "1 Year (Full 2025-2026)", "All Available"],
            horizontal=True,
            key="market_dur_radio",
        )

    # Determine lookback days
    dur_map = {
        "3 Months": 65,
        "6 Months": 130,
        "1 Year (Full 2025-2026)": 260,
        "All Available": 600,
    }
    lookback = dur_map.get(dur_option, 260)

    # Fetch historical data with technical indicators
    hist_df = provider.get_historical_data(selected_cid, limit=lookback)
    q = quotes.get(selected_cid, {})

    price = q.get("price", 0.0)
    change = q.get("change", 0.0)
    pct_change = q.get("pct_change", 0.0)
    is_pos = change >= 0
    color = SUCCESS if is_pos else ERROR
    arrow = "▲" if is_pos else "▼"
    sign = "+" if is_pos else ""

    # Stock Quote Header Card
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid {BORDER}; border-left: 6px solid {color}; border-radius: 14px; padding: 18px 22px; margin-bottom: 16px; box-shadow: 0 4px 14px rgba(11,31,75,0.06);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                <div>
                    <div style="font-size: 1.5rem; font-weight: 800; color: {NAVY};">{q.get('company_name', selected_cid)} ({selected_cid})</div>
                    <div style="font-size: 0.82rem; color: {MUTED}; font-weight: 600;">Exchange: NSE • Symbol: {selected_cid}.NS • Session Date: {q.get('latest_date', latest_date)}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 2.2rem; font-weight: 800; color: {NAVY}; letter-spacing: -0.02em;">₹{price:,.2f}</div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: {color};">{arrow} {sign}{change:,.2f} ({sign}{pct_change:.2f}%)</div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-top: 14px; padding-top: 12px; border-top: 1px solid {BORDER};">
                <div><div style="font-size: 0.72rem; color: {MUTED}; font-weight: 700;">OPEN</div><div style="font-size: 0.95rem; font-weight: 700; color: {NAVY};">₹{q.get('open', 0):,.2f}</div></div>
                <div><div style="font-size: 0.72rem; color: {MUTED}; font-weight: 700;">DAY HIGH</div><div style="font-size: 0.95rem; font-weight: 700; color: {SUCCESS};">₹{q.get('high', 0):,.2f}</div></div>
                <div><div style="font-size: 0.72rem; color: {MUTED}; font-weight: 700;">DAY LOW</div><div style="font-size: 0.95rem; font-weight: 700; color: {ERROR};">₹{q.get('low', 0):,.2f}</div></div>
                <div><div style="font-size: 0.72rem; color: {MUTED}; font-weight: 700;">PREV CLOSE</div><div style="font-size: 0.95rem; font-weight: 700; color: {NAVY};">₹{q.get('close', 0):,.2f}</div></div>
                <div><div style="font-size: 0.72rem; color: {MUTED}; font-weight: 700;">VOLUME</div><div style="font-size: 0.95rem; font-weight: 700; color: {NAVY};">{q.get('volume', 0):,}</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Technical Indicators Selector Toggles
    t_col1, t_col2, t_col3, t_col4 = st.columns(4)
    with t_col1:
        show_sma = st.checkbox("Show SMA (20 & 50)", value=True, key="chk_sma")
    with t_col2:
        show_ema = st.checkbox("Show EMA (20 & 50)", value=True, key="chk_ema")
    with t_col3:
        show_rsi = st.checkbox("Show RSI (14)", value=True, key="chk_rsi")
    with t_col4:
        show_macd = st.checkbox("Show MACD (12, 26, 9)", value=True, key="chk_macd")

    # Build Candlestick Subplots
    if not hist_df.empty:
        subplot_rows = 2  # Row 1: Candlestick, Row 2: Volume
        row_heights = [0.55, 0.15]
        
        if show_rsi and show_macd:
            subplot_rows = 4
            row_heights = [0.45, 0.15, 0.20, 0.20]
        elif show_rsi or show_macd:
            subplot_rows = 3
            row_heights = [0.50, 0.15, 0.25]

        fig = make_subplots(
            rows=subplot_rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=row_heights,
        )

        # 1. Candlestick
        fig.add_trace(
            go.Candlestick(
                x=hist_df.index,
                open=hist_df["Open"],
                high=hist_df["High"],
                low=hist_df["Low"],
                close=hist_df["Close"],
                name="OHLC",
                increasing_line_color=SUCCESS,
                decreasing_line_color=ERROR,
            ),
            row=1,
            col=1,
        )

        # SMA Overlays
        if show_sma:
            fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df["SMA_20"], mode="lines", name="SMA 20", line=dict(color=BLUE, width=1.5)), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df["SMA_50"], mode="lines", name="SMA 50", line=dict(color=BROWN, width=1.5)), row=1, col=1)

        # EMA Overlays
        if show_ema:
            fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df["EMA_20"], mode="lines", name="EMA 20", line=dict(color=BLUE_LIGHT, width=1.5, dash="dot")), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df["EMA_50"], mode="lines", name="EMA 50", line=dict(color="#9333EA", width=1.5, dash="dot")), row=1, col=1)

        # 2. Volume Bar Chart
        vol_colors = [SUCCESS if c >= o else ERROR for c, o in zip(hist_df["Close"], hist_df["Open"])]
        fig.add_trace(
            go.Bar(x=hist_df.index, y=hist_df["Volume"], name="Volume", marker_color=vol_colors, opacity=0.7),
            row=2,
            col=1,
        )

        curr_row = 3
        # 3. RSI
        if show_rsi:
            fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df["RSI"], mode="lines", name="RSI (14)", line=dict(color="#D97706", width=2)), row=curr_row, col=1)
            # Overbought / Oversold threshold lines
            fig.add_hline(y=70, line_dash="dash", line_color=ERROR, opacity=0.6, row=curr_row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color=SUCCESS, opacity=0.6, row=curr_row, col=1)
            fig.update_yaxes(title_text="RSI", range=[0, 100], row=curr_row, col=1)
            curr_row += 1

        # 4. MACD
        if show_macd:
            fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df["MACD"], mode="lines", name="MACD", line=dict(color=BLUE, width=1.5)), row=curr_row, col=1)
            fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df["MACD_Signal"], mode="lines", name="Signal", line=dict(color="#DC2626", width=1.5)), row=curr_row, col=1)
            hist_colors = [SUCCESS if h >= 0 else ERROR for h in hist_df["MACD_Hist"]]
            fig.add_trace(go.Bar(x=hist_df.index, y=hist_df["MACD_Hist"], name="Histogram", marker_color=hist_colors), row=curr_row, col=1)
            fig.update_yaxes(title_text="MACD", row=curr_row, col=1)

        fig.update_layout(
            height=700,
            xaxis_rangeslider_visible=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color=NAVY),
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"No historical chart records found for {selected_cid}.")

    # Direct action link to Company Profile
    btn_c1, btn_c2 = st.columns([2, 3])
    with btn_c1:
        if st.button(f"🏢 View Full Fundamentals & Ratios for {selected_cid}", use_container_width=True):
            st.session_state["selected_ticker"] = selected_cid
            st.query_params["page"] = "profile"
            st.query_params["symbol"] = selected_cid
            st.rerun()

    st.markdown("<hr/>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 3. Sector Performance & Momentum Overview
    # -------------------------------------------------------------
    st.subheader("🏭 Sector Performance Breakdown")

    if not sectors_df.empty:
        # Merge quotes with sector info
        quotes_df = pd.DataFrame(quotes_list)
        sector_summary = quotes_df.merge(sectors_df, left_on="company_id", right_on="company_id", how="left")
        sector_summary["broad_sector"] = sector_summary["broad_sector"].fillna("Other")

        sector_grp = (
            sector_summary.groupby("broad_sector")
            .agg(
                avg_pct_change=("pct_change", "mean"),
                stock_count=("company_id", "count"),
                advances=("change", lambda x: (x > 0).sum()),
                declines=("change", lambda x: (x < 0).sum()),
            )
            .reset_index()
            .sort_values("avg_pct_change", ascending=False)
        )

        sec_col1, sec_col2 = st.columns([3, 2])
        with sec_col1:
            sec_colors = [SUCCESS if x >= 0 else ERROR for x in sector_grp["avg_pct_change"]]
            fig_sec = go.Figure(
                go.Bar(
                    x=sector_grp["avg_pct_change"],
                    y=sector_grp["broad_sector"],
                    orientation="h",
                    marker_color=sec_colors,
                    text=[f"{v:+.2f}%" for v in sector_grp["avg_pct_change"]],
                    textposition="auto",
                )
            )
            fig_sec.update_layout(
                title="Average Daily Momentum by Broad Sector (%)",
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color=NAVY),
                margin=dict(l=10, r=20, t=40, b=20),
                xaxis=dict(gridcolor=BORDER),
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_sec, use_container_width=True)

        with sec_col2:
            st.markdown(f"**Sector Breadth Breakdown ({len(sector_grp)} Sectors)**")
            disp_sec = sector_grp.copy()
            disp_sec["avg_pct_change"] = disp_sec["avg_pct_change"].map(lambda x: f"{x:+.2f}%")
            disp_sec.columns = ["Sector", "Avg Change", "Stocks", "Advances", "Declines"]
            st.dataframe(disp_sec, use_container_width=True, hide_index=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 4. Searchable & Sortable Full Constituent Table
    # -------------------------------------------------------------
    st.subheader(f"📋 All Constituents Market Table ({total_tracked} Companies)")

    fc1, fc2, fc3 = st.columns([2, 1.5, 1.5])
    with fc1:
        kw = st.text_input("🔍 Search by Symbol or Company Name", "", placeholder="e.g. INFY, TCS, Reliance, Bank...").strip().lower()
    with fc2:
        sort_choice = st.selectbox(
            "Sort Order",
            ["Top Gainers", "Top Losers", "Highest Volume", "Highest Price", "Alphabetical (A-Z)"],
            key="grid_sort",
        )
    with fc3:
        filter_dir = st.selectbox(
            "Filter Movement",
            ["All Stocks", "Only Advances (Gains)", "Only Declines (Losses)"],
            key="grid_filt",
        )

    # Filter
    filtered = quotes_list
    if kw:
        filtered = [
            q for q in filtered
            if kw in q.get("company_id", "").lower()
            or kw in q.get("company_name", "").lower()
        ]

    if filter_dir == "Only Advances (Gains)":
        filtered = [q for q in filtered if q.get("change", 0) > 0]
    elif filter_dir == "Only Declines (Losses)":
        filtered = [q for q in filtered if q.get("change", 0) < 0]

    # Sort
    if sort_choice == "Top Gainers":
        filtered.sort(key=lambda x: x.get("pct_change", 0), reverse=True)
    elif sort_choice == "Top Losers":
        filtered.sort(key=lambda x: x.get("pct_change", 0))
    elif sort_choice == "Highest Volume":
        filtered.sort(key=lambda x: x.get("volume", 0), reverse=True)
    elif sort_choice == "Highest Price":
        filtered.sort(key=lambda x: x.get("price", 0), reverse=True)
    elif sort_choice == "Alphabetical (A-Z)":
        filtered.sort(key=lambda x: x.get("company_id", ""))

    table_data = []
    for item in filtered:
        chg = item.get("pct_change", 0.0)
        arrow = "▲" if chg >= 0 else "▼"
        table_data.append({
            "Symbol": item.get("company_id"),
            "Company Name": item.get("company_name"),
            "Close (₹)": f"₹{item.get('price', 0):,.2f}",
            "Change (₹)": f"{item.get('change', 0):+,.2f}",
            "Change (%)": f"{arrow} {chg:+.2f}%",
            "Open (₹)": f"₹{item.get('open', 0):,.2f}",
            "High (₹)": f"₹{item.get('high', 0):,.2f}",
            "Low (₹)": f"₹{item.get('low', 0):,.2f}",
            "Prev Close (₹)": f"₹{item.get('close', 0):,.2f}",
            "Volume": f"{item.get('volume', 0):,}",
            "Date": item.get("latest_date", latest_date),
        })

    if table_data:
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
    else:
        st.info("No matching stocks found.")
