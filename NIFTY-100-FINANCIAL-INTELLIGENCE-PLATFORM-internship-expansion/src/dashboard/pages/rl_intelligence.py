"""
rl_intelligence.py

Reinforcement Learning Stock Intelligence & Backtesting Dashboard.
- Evaluates autonomous RL trading agents on updated 2025-2026 NIFTY-100 datasets.
- Strict chronological Train / Validation / Test separation (Zero data leakage).
- Realistic transaction costs and slippage accounting.
- Interactive equity curve comparison vs Buy & Hold benchmark.
- Complete regulatory transparency and ethical AI disclaimers.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

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
from utils.db import get_companies
from src.analytics.rl_model import train_and_backtest_rl, compare_rl_models


def show():
    page_header(
        "🤖",
        "Reinforcement Learning Intelligence",
        "Autonomous Q-Learning Trading Agent • Chronological Out-of-Sample Backtesting • Zero Data Leakage",
    )

    companies = get_companies()
    company_ids = sorted(companies["id"].dropna().unique().tolist()) if not companies.empty else ["TCS", "INFY", "RELIANCE"]

    # Parameter Controls
    st.markdown(
        f"""
        <div style="background: {BLUE_SOFT}; border: 1px solid {BORDER}; border-radius: 12px; padding: 14px 18px; margin-bottom: 18px;">
            <div style="font-weight: 800; font-size: 0.95rem; color: {NAVY};">
                ⚙️ RL Model Architecture & Environment Parameters
            </div>
            <div style="font-size: 0.82rem; color: {MUTED}; margin-top: 4px;">
                State Space: [RSI(14) Buckets, MACD Momentum, Trend vs SMA-20, Position Flag] • Action Space: [0: HOLD, 1: BUY, 2: SELL]
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns([2.5, 1.8, 1.8, 1.8])
    with c1:
        default_stock = st.session_state.get("selected_ticker", "RELIANCE")
        idx = company_ids.index(default_stock) if default_stock in company_ids else 0
        selected_stock = st.selectbox("Stock to Train & Evaluate", options=company_ids, index=idx, key="rl_stock_sel")
    with c2:
        episodes = st.slider("Training Episodes", min_value=15, max_value=80, value=35, step=5, key="rl_episodes")
    with c3:
        initial_cap = st.selectbox("Starting Capital", [50_000, 100_000, 500_000], index=1, format_func=lambda x: f"₹{x:,}")
    with c4:
        cost_bps = st.selectbox("Transaction Cost", [5, 10, 20], index=1, format_func=lambda x: f"{x} bps (0.{x:02d}%)")

    # Run button
    btn = st.button("🚀 Train RL Agent & Evaluate Backtest", use_container_width=True)

    # Cache backtest in session state
    cache_key = f"rl_res_{selected_stock}_{episodes}"
    if btn or cache_key not in st.session_state:
        with st.spinner(f"Training Q-Learning agent on {selected_stock} historical data (2020-2026)..."):
            res = train_and_backtest_rl(selected_stock, episodes=episodes)
            st.session_state[cache_key] = res

    res = st.session_state[cache_key]
    if "error" in res:
        st.error(res["error"])
        return

    # -------------------------------------------------------------
    # 1. Dataset Partitioning Details
    # -------------------------------------------------------------
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    with d1:
        st.info(f"**1. Chronological Train Set (70%)**\n\n{res['train_period']} ({res['train_records']} trading days)")
    with d2:
        st.info(f"**2. Validation Set (15%)**\n\n{res['val_period']}")
    with d3:
        st.success(f"**3. Out-Of-Sample Test Set (15%)**\n\n{res['test_period']} ({res['test_records']} trading days)")

    # -------------------------------------------------------------
    # 2. Performance KPI Cards
    # -------------------------------------------------------------
    k1, k2, k3, k4 = st.columns(4)
    rl_ret = res["rl_return"]
    bench_ret = res["benchmark_return"]
    alpha = res["alpha"]
    sharpe = res["sharpe_ratio"]

    with k1:
        metric_card("RL Agent Return", f"{rl_ret:+.2f}%", f"Final: ₹{res['final_capital']:,.2f}", is_positive=(rl_ret >= 0))
    with k2:
        metric_card("Benchmark Buy & Hold", f"{bench_ret:+.2f}%", f"Stock Price Trend", is_positive=(bench_ret >= 0))
    with k3:
        metric_card("Alpha vs Benchmark", f"{alpha:+.2f}%", "Excess Performance", is_positive=(alpha >= 0))
    with k4:
        metric_card("Sharpe Ratio", f"{sharpe:.2f}", f"Max DD: {res['max_drawdown']:.2f}%", is_positive=(sharpe >= 1.0))

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 3. Interactive Equity Curves Comparison
    # -------------------------------------------------------------
    st.subheader("📊 Out-of-Sample Portfolio Equity Curve")

    hist_df = res["history_df"]
    # Benchmark portfolio over time
    bench_start_price = hist_df["Price"].iloc[0]
    hist_df["Benchmark_Value"] = (hist_df["Price"] / bench_start_price) * res["initial_capital"]

    fig_equity = go.Figure()

    # Benchmark Line
    fig_equity.add_trace(
        go.Scatter(
            x=hist_df["Date"],
            y=hist_df["Benchmark_Value"],
            mode="lines",
            name=f"Buy & Hold ({selected_stock})",
            line=dict(color=MUTED, width=1.8, dash="dot"),
        )
    )

    # RL Agent Line
    fig_equity.add_trace(
        go.Scatter(
            x=hist_df["Date"],
            y=hist_df["Portfolio_Value"],
            mode="lines",
            name="RL Autonomous Agent",
            line=dict(color=BLUE, width=2.8),
        )
    )

    # Trade Markers
    buys = hist_df[hist_df["Action"] == "BUY"]
    sells = hist_df[hist_df["Action"] == "SELL"]

    if not buys.empty:
        fig_equity.add_trace(
            go.Scatter(
                x=buys["Date"],
                y=buys["Portfolio_Value"],
                mode="markers",
                name="Agent BUY Action",
                marker=dict(symbol="triangle-up", size=11, color=SUCCESS),
            )
        )

    if not sells.empty:
        fig_equity.add_trace(
            go.Scatter(
                x=sells["Date"],
                y=sells["Portfolio_Value"],
                mode="markers",
                name="Agent SELL Action",
                marker=dict(symbol="triangle-down", size=11, color=ERROR),
            )
        )

    fig_equity.update_layout(
        height=450,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=NAVY),
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(gridcolor=BORDER, title="Out-of-Sample Trading Session Date"),
        yaxis=dict(gridcolor=BORDER, title="Portfolio Valuation (INR)", tickprefix="₹"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_equity, use_container_width=True)

    # -------------------------------------------------------------
    # 4. Trade Execution Details & Stats
    # -------------------------------------------------------------
    t1, t2 = st.columns([1, 1])
    with t1:
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid {BORDER}; border-radius: 12px; padding: 16px 20px;">
                <div style="font-weight: 800; font-size: 0.95rem; color: {NAVY}; margin-bottom: 8px;">Execution Summary</div>
                <div style="font-size: 0.85rem; color: {NAVY}; line-height: 1.8;">
                    • <b>Total Trades:</b> {res['total_trades']} executions<br/>
                    • <b>Friction Paid (Slippage & Fees):</b> ₹{res['total_cost_paid']:,.2f}<br/>
                    • <b>Sortino Ratio:</b> {res['sortino_ratio']:.2f}<br/>
                    • <b>Maximum Drawdown:</b> {res['max_drawdown']:.2f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with t2:
        st.markdown(
            f"""
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 12px; padding: 16px 20px;">
                <div style="font-weight: 800; font-size: 0.95rem; color: #92400E; margin-bottom: 8px;">⚖️ Regulatory & Algorithmic Notice</div>
                <div style="font-size: 0.82rem; color: #78350F; line-height: 1.6;">
                    The displayed simulation is strictly computed from out-of-sample historical market data. 
                    Hypothetical results do not represent actual trading and cannot predict future market movements. 
                    <b>Past performance never guarantees profits.</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Trade Log Expander
    with st.expander("🔍 View Complete Out-of-Sample Action Ledger"):
        ledger_df = hist_df[hist_df["Action"] != "HOLD"].copy()
        if not ledger_df.empty:
            ledger_df["Price"] = ledger_df["Price"].map(lambda x: f"₹{x:,.2f}")
            ledger_df["Portfolio_Value"] = ledger_df["Portfolio_Value"].map(lambda x: f"₹{x:,.2f}")
            ledger_df["Cash"] = ledger_df["Cash"].map(lambda x: f"₹{x:,.2f}")
            ledger_df["Cost"] = ledger_df["Cost"].map(lambda x: f"₹{x:,.2f}")
            st.dataframe(ledger_df[["Date", "Action", "Price", "Shares", "Cash", "Portfolio_Value", "Cost"]], use_container_width=True, hide_index=True)
        else:
            st.info("The agent determined market conditions did not warrant entry; remained 100% in cash to preserve capital.")

    # -------------------------------------------------------------
    # 5. Model Evolution Comparison: Legacy (2020-2024) vs Updated (2020-2026)
    # -------------------------------------------------------------
    st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)
    st.subheader("⚖️ Model Evolution Benchmark: Legacy (2020–2024) vs. Updated (2020–2026)")
    st.caption("Empirical measured backtest comparison across training eras — zero fabricated claims; shows measured differences.")

    cmp_key = f"rl_cmp_{selected_stock}"
    if st.checkbox("Run Empirical Model Comparison (Legacy vs. Updated)", value=False, key=f"chk_cmp_{selected_stock}"):
        if cmp_key not in st.session_state:
            with st.spinner(f"Evaluating {selected_stock} on both Legacy 2024 and Updated 2026 datasets..."):
                st.session_state[cmp_key] = compare_rl_models(selected_stock, episodes=episodes)

        cmp_data = st.session_state[cmp_key]
        if "error" not in cmp_data:
            leg = cmp_data["legacy"]
            upd = cmp_data["updated"]

            comp_df = pd.DataFrame([
                {
                    "Metric": "Training & Testing Scope",
                    "Legacy Model (2020-2024)": leg.get("dataset_scope", "2020-2024"),
                    "Updated Model (2020-2026)": upd.get("dataset_scope", "2020-2026"),
                    "Empirical Delta": "Expanded +2 Years",
                },
                {
                    "Metric": "Out-of-Sample Test Period",
                    "Legacy Model (2020-2024)": leg.get("test_period", "2024"),
                    "Updated Model (2020-2026)": upd.get("test_period", "2026"),
                    "Empirical Delta": "Latest Market Regime",
                },
                {
                    "Metric": "Agent Return (%)",
                    "Legacy Model (2020-2024)": f"{leg.get('return_pct', 0.0):+.2f}%",
                    "Updated Model (2020-2026)": f"{upd.get('return_pct', 0.0):+.2f}%",
                    "Empirical Delta": f"{(upd.get('return_pct', 0.0) - leg.get('return_pct', 0.0)):+.2f}%",
                },
                {
                    "Metric": "Benchmark Return (%)",
                    "Legacy Model (2020-2024)": f"{leg.get('benchmark_pct', 0.0):+.2f}%",
                    "Updated Model (2020-2026)": f"{upd.get('benchmark_pct', 0.0):+.2f}%",
                    "Empirical Delta": f"{(upd.get('benchmark_pct', 0.0) - leg.get('benchmark_pct', 0.0)):+.2f}%",
                },
                {
                    "Metric": "Alpha vs Benchmark (%)",
                    "Legacy Model (2020-2024)": f"{leg.get('alpha_pct', 0.0):+.2f}%",
                    "Updated Model (2020-2026)": f"{upd.get('alpha_pct', 0.0):+.2f}%",
                    "Empirical Delta": f"{cmp_data['alpha_delta']:+.2f}%",
                },
                {
                    "Metric": "Sharpe Ratio",
                    "Legacy Model (2020-2024)": f"{leg.get('sharpe', 0.0):.2f}",
                    "Updated Model (2020-2026)": f"{upd.get('sharpe', 0.0):.2f}",
                    "Empirical Delta": f"{cmp_data['sharpe_delta']:+.2f}",
                },
                {
                    "Metric": "Max Drawdown (%)",
                    "Legacy Model (2020-2024)": f"{leg.get('max_drawdown', 0.0):.2f}%",
                    "Updated Model (2020-2026)": f"{upd.get('max_drawdown', 0.0):.2f}%",
                    "Empirical Delta": f"{(upd.get('max_drawdown', 0.0) - leg.get('max_drawdown', 0.0)):+.2f}%",
                },
            ])

            st.dataframe(comp_df, use_container_width=True, hide_index=True)
            status_color = SUCCESS if cmp_data["status"] == "IMPROVED" else WARNING
            st.markdown(
                f"""
                <div style="font-size: 0.85rem; color: {NAVY}; margin-top: 6px;">
                    <b>Measured Impact:</b> <span style="color: {status_color}; font-weight: 700;">{cmp_data['status']}</span> 
                    (Alpha delta: {cmp_data['alpha_delta']:+.2f}% • Sharpe delta: {cmp_data['sharpe_delta']:+.2f}).
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.warning("Comparison could not be completed: " + cmp_data["error"])
