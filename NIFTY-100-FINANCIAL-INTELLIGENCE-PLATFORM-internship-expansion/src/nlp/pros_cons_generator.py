"""
pros_cons_generator.py

Sprint 5
Day 30

Pros / Cons Generator

Rule based NLP-style generator that produces Pro and Con statements
for every company in the universe, using the same financial_ratios /
market_cap / cashflow tables the rest of the Analytics layer already
relies on (see src/analytics/ratio_engine.py, cashflow_kpis.py).

12 Pro rules + 12 Con rules are evaluated per company. Each rule
returns a confidence score (0-100). Only rules scoring above 60 are
kept. If a company ends up with zero Pros or zero Cons after
filtering, a lower-confidence fallback statement is added so every
company always has at least one of each (documented assumption,
see FALLBACK_CONFIDENCE below).

Output:
    output/pros_cons_generated.csv
        company_id, type, rule_id, text, confidence_pct
"""

import os
import sqlite3

import pandas as pd

from src.analytics.cashflow_kpis import (
    cfo_quality_score,
    capex_intensity,
    capital_allocation_pattern
)

DB_PATH = "db/nifty100.db"
OUTPUT_DIR = "output"

CONFIDENCE_THRESHOLD = 60
FALLBACK_CONFIDENCE = 61


# --------------------------------------------------
# Data Loading
# --------------------------------------------------

def load_company_snapshot():
    """
    Build one row per company_id combining:
        - latest financial_ratios record
        - latest market_cap record
        - latest cashflow record (for CFO quality / capex / pattern)

    Returns the master company list from `companies` (92 rows) as the
    source of truth for which company_ids exist.

    Sprint 5 note: financial_ratios is missing 2 master companies
    (SBIN, ATGL) and contains 2 tickers that are not in the master
    list (ULTRACEMCO, UNIONBANK) - an upstream data gap. Scoping to
    `companies` here (rather than to financial_ratios' own keys)
    keeps this generator aligned with the 92-company universe; the
    2 companies with no ratio row simply fall through to the
    fallback rule below.
    """

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql("SELECT id FROM companies", conn)
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    market_cap = pd.read_sql("SELECT * FROM market_cap", conn)
    cashflow = pd.read_sql("SELECT * FROM cashflow", conn)
    profitandloss = pd.read_sql(
        "SELECT company_id, year, sales, net_profit FROM profitandloss",
        conn
    )

    conn.close()

    company_ids = sorted(companies["id"].unique())

    ratios_latest = (
        ratios.sort_values(["company_id", "year"])
        .drop_duplicates(subset=["company_id"], keep="last")
        .set_index("company_id")
    )

    market_cap_latest = (
        market_cap.sort_values(["company_id", "year"])
        .drop_duplicates(subset=["company_id"], keep="last")
        .set_index("company_id")
    )

    cashflow = cashflow[cashflow["year"] != "TTM"]

    cashflow_latest = (
        cashflow.sort_values(["company_id", "year"])
        .drop_duplicates(subset=["company_id"], keep="last")
        .set_index("company_id")
    )

    pnl_latest = (
        profitandloss.sort_values(["company_id", "year"])
        .drop_duplicates(subset=["company_id"], keep="last")
        .set_index("company_id")
    )

    return company_ids, ratios_latest, market_cap_latest, cashflow_latest, pnl_latest


# --------------------------------------------------
# Confidence Helper
# --------------------------------------------------

def scale_confidence(value, weak_at, strong_at, base=60, ceiling=98):
    """
    Linearly scale a metric's distance past a threshold into a
    confidence score between `base` and `ceiling`.

    weak_at   -> value where the rule just barely triggers (confidence = base)
    strong_at -> value where the rule is maximally true (confidence = ceiling)
    """

    if strong_at == weak_at:
        return base

    span = (value - weak_at) / (strong_at - weak_at)
    span = max(0.0, min(1.0, span))

    return round(base + span * (ceiling - base), 1)


# --------------------------------------------------
# Pro Rules (12)
# --------------------------------------------------

def evaluate_pro_rules(company_id, ratios, mcap, cf, pnl):

    rules = []

    def add(rule_id, text, confidence):
        if confidence is not None and confidence > CONFIDENCE_THRESHOLD:
            rules.append((rule_id, text, round(confidence, 1)))

    roe = ratios.get("return_on_equity_pct")
    if pd.notna(roe) and roe > 15:
        add(
            "PRO_01_HIGH_ROE",
            f"Company has a strong return on equity of {roe:.1f}%.",
            scale_confidence(roe, 15, 40)
        )

    rev_cagr = ratios.get("revenue_cagr_5yr")
    if pd.notna(rev_cagr) and rev_cagr > 12 and ratios.get("revenue_cagr_flag") == "OK":
        add(
            "PRO_02_REVENUE_GROWTH",
            f"Company has delivered strong sales growth of {rev_cagr:.1f}% CAGR over the last 5 years.",
            scale_confidence(rev_cagr, 12, 30)
        )

    pat_cagr = ratios.get("pat_cagr_5yr")
    if pd.notna(pat_cagr) and pat_cagr > 12 and ratios.get("pat_cagr_flag") == "OK":
        add(
            "PRO_03_PROFIT_GROWTH",
            f"Company has delivered strong profit growth of {pat_cagr:.1f}% CAGR over the last 5 years.",
            scale_confidence(pat_cagr, 12, 30)
        )

    dte = ratios.get("debt_to_equity")
    if pd.notna(dte) and dte < 0.3:
        add(
            "PRO_04_LOW_DEBT",
            "Company is almost debt free." if dte < 0.1 else f"Company carries low debt with a debt-to-equity of {dte:.2f}.",
            scale_confidence(0.3 - dte, 0.0, 0.3)
        )

    icr = ratios.get("interest_coverage")
    if pd.notna(icr) and icr > 8:
        add(
            "PRO_05_INTEREST_COVERAGE",
            f"Company comfortably covers its interest obligations ({icr:.1f}x interest coverage).",
            scale_confidence(icr, 8, 30)
        )

    if pd.notna(cf.get("operating_activity")) and pd.notna(pnl.get("net_profit")):
        score, label = cfo_quality_score(cf["operating_activity"], pnl["net_profit"])
        if score is not None and label == "High Quality":
            add(
                "PRO_06_CFO_QUALITY",
                f"Company converts profits into cash efficiently (CFO/PAT of {score:.2f}x).",
                scale_confidence(score, 1.0, 2.0)
            )

    payout = ratios.get("dividend_payout_ratio_pct")
    if pd.notna(payout) and payout > 25:
        add(
            "PRO_07_DIVIDEND_PAYOUT",
            f"Company has been maintaining a healthy dividend payout of {payout:.1f}%.",
            scale_confidence(payout, 25, 60)
        )

    quality = ratios.get("composite_quality_score")
    if pd.notna(quality) and quality >= 70:
        add(
            "PRO_08_QUALITY_SCORE",
            f"Company scores highly on the composite quality framework ({quality:.0f}/100).",
            scale_confidence(quality, 70, 100)
        )

    if pd.notna(cf.get("investing_activity")) and pd.notna(pnl.get("sales")):
        intensity, label = capex_intensity(cf["investing_activity"], pnl["sales"])
        if intensity is not None and label == "Asset Light":
            add(
                "PRO_09_ASSET_LIGHT",
                "Company runs an asset-light business with low capital expenditure needs.",
                scale_confidence(3 - intensity, 0, 3)
            )

    opm = ratios.get("operating_profit_margin_pct")
    if pd.notna(opm) and opm > 20:
        add(
            "PRO_10_OPERATING_MARGIN",
            f"Company maintains a strong operating margin of {opm:.1f}%.",
            scale_confidence(opm, 20, 45)
        )

    eps_cagr = ratios.get("eps_cagr_5yr")
    if pd.notna(eps_cagr) and eps_cagr > 12 and ratios.get("eps_cagr_flag") == "OK":
        add(
            "PRO_11_EPS_GROWTH",
            f"Company has grown earnings per share at {eps_cagr:.1f}% CAGR over the last 5 years.",
            scale_confidence(eps_cagr, 12, 30)
        )

    if pd.notna(cf.get("operating_activity")) and pd.notna(cf.get("investing_activity")) \
            and pd.notna(cf.get("financing_activity")):
        _, _, _, pattern = capital_allocation_pattern(
            cf["operating_activity"], cf["investing_activity"], cf["financing_activity"]
        )
        if pattern == "Reinvestor":
            add(
                "PRO_12_REINVESTOR",
                "Company generates strong operating cash flow and reinvests it into the business.",
                75.0
            )

    return rules


# --------------------------------------------------
# Con Rules (12)
# --------------------------------------------------

def evaluate_con_rules(company_id, ratios, mcap, cf, pnl):

    rules = []

    def add(rule_id, text, confidence):
        if confidence is not None and confidence > CONFIDENCE_THRESHOLD:
            rules.append((rule_id, text, round(confidence, 1)))

    roe = ratios.get("return_on_equity_pct")
    if pd.notna(roe) and roe < 10:
        add(
            "CON_01_LOW_ROE",
            f"Company has a low return on equity of {roe:.1f}%.",
            scale_confidence(10 - roe, 0, 15)
        )

    rev_cagr = ratios.get("revenue_cagr_5yr")
    if pd.notna(rev_cagr) and (rev_cagr < 5 or ratios.get("revenue_cagr_flag") != "OK"):
        add(
            "CON_02_WEAK_REVENUE_GROWTH",
            f"Company has delivered weak sales growth of {rev_cagr:.1f}% CAGR over the last 5 years.",
            scale_confidence(5 - rev_cagr, 0, 15)
        )

    pat_cagr = ratios.get("pat_cagr_5yr")
    if pd.notna(pat_cagr) and (pat_cagr < 5 or ratios.get("pat_cagr_flag") != "OK"):
        add(
            "CON_03_WEAK_PROFIT_GROWTH",
            f"Company has delivered weak profit growth of {pat_cagr:.1f}% CAGR over the last 5 years.",
            scale_confidence(5 - pat_cagr, 0, 15)
        )

    dte = ratios.get("debt_to_equity")
    if pd.notna(dte) and dte > 1.0:
        add(
            "CON_04_HIGH_DEBT",
            f"Company carries a high debt-to-equity ratio of {dte:.2f}.",
            scale_confidence(dte, 1.0, 3.0)
        )

    icr = ratios.get("interest_coverage")
    if pd.notna(icr) and icr < 2:
        add(
            "CON_05_LOW_INTEREST_COVERAGE",
            f"Company has a low interest coverage ratio of {icr:.2f}x.",
            scale_confidence(2 - icr, 0, 2)
        )

    if pd.notna(cf.get("operating_activity")) and pd.notna(pnl.get("net_profit")):
        score, label = cfo_quality_score(cf["operating_activity"], pnl["net_profit"])
        if score is not None and label == "Accrual Risk":
            add(
                "CON_06_ACCRUAL_RISK",
                f"Company's cash generation lags reported profits (CFO/PAT of {score:.2f}x), an accrual risk.",
                scale_confidence(0.5 - score, -0.5, 0.5)
            )

    if pd.notna(cf.get("investing_activity")) and pd.notna(pnl.get("sales")):
        intensity, label = capex_intensity(cf["investing_activity"], pnl["sales"])
        if intensity is not None and label == "Capital Intensive":
            add(
                "CON_07_CAPITAL_INTENSIVE",
                f"Company is capital intensive, spending {intensity:.1f}% of sales on capex.",
                scale_confidence(intensity, 8, 20)
            )

    payout = ratios.get("dividend_payout_ratio_pct")
    if pd.notna(payout) and payout < 10:
        add(
            "CON_08_LOW_DIVIDEND",
            f"Dividend payout has been low at {payout:.1f}% of profits.",
            scale_confidence(10 - payout, 0, 10)
        )

    quality = ratios.get("composite_quality_score")
    if pd.notna(quality) and quality < 50:
        add(
            "CON_09_LOW_QUALITY_SCORE",
            f"Company scores poorly on the composite quality framework ({quality:.0f}/100).",
            scale_confidence(50 - quality, 0, 50)
        )

    pb_ratio = mcap.get("pb_ratio")
    if pd.notna(pb_ratio) and pb_ratio > 8:
        add(
            "CON_10_HIGH_VALUATION",
            f"Stock is trading at a rich {pb_ratio:.2f} times its book value.",
            scale_confidence(pb_ratio, 8, 20)
        )

    if pd.notna(cf.get("operating_activity")) and pd.notna(cf.get("investing_activity")):
        fcf = cf["operating_activity"] + cf["investing_activity"]
        if fcf < 0:
            add(
                "CON_11_NEGATIVE_FCF",
                "Company reported negative free cash flow in the latest year.",
                75.0
            )

    if pd.notna(cf.get("operating_activity")) and pd.notna(cf.get("investing_activity")) \
            and pd.notna(cf.get("financing_activity")):
        _, _, _, pattern = capital_allocation_pattern(
            cf["operating_activity"], cf["investing_activity"], cf["financing_activity"]
        )
        if pattern in ("Distress Signal", "Growth Funded by Debt"):
            add(
                "CON_12_DISTRESS_PATTERN",
                f"Company's cash flow pattern ({pattern}) signals capital allocation stress.",
                80.0
            )

    return rules


# --------------------------------------------------
# Fallback (ensures >=1 Pro and >=1 Con per company)
# --------------------------------------------------

def fallback_pro(ratios):
    roe = ratios.get("return_on_equity_pct")

    if pd.notna(roe):
        return (
            "PRO_FALLBACK_PROFITABLE",
            f"Company remains profitable with a return on equity of {roe:.1f}%.",
            FALLBACK_CONFIDENCE
        )

    return (
        "PRO_FALLBACK_PROFITABLE",
        "Company is part of the Nifty 100 index, reflecting its scale and market standing.",
        FALLBACK_CONFIDENCE
    )


def fallback_con(ratios):
    dte = ratios.get("debt_to_equity")

    if pd.notna(dte):
        return (
            "CON_FALLBACK_WATCH_LEVERAGE",
            f"Company's leverage (debt-to-equity of {dte:.2f}) is worth monitoring going forward.",
            FALLBACK_CONFIDENCE
        )

    return (
        "CON_FALLBACK_DATA_GAP",
        "Detailed financial ratio data is currently unavailable for deeper analysis of this company.",
        FALLBACK_CONFIDENCE
    )


# --------------------------------------------------
# Main Generation Routine
# --------------------------------------------------

def generate_pros_cons():

    company_ids, ratios_latest, mcap_latest, cf_latest, pnl_latest = load_company_snapshot()

    output_rows = []

    for company_id in company_ids:

        ratios = ratios_latest.loc[company_id] if company_id in ratios_latest.index else pd.Series(dtype=float)
        mcap = mcap_latest.loc[company_id] if company_id in mcap_latest.index else pd.Series(dtype=float)
        cf = cf_latest.loc[company_id] if company_id in cf_latest.index else pd.Series(dtype=float)
        pnl = pnl_latest.loc[company_id] if company_id in pnl_latest.index else pd.Series(dtype=float)

        pros = evaluate_pro_rules(company_id, ratios, mcap, cf, pnl)
        cons = evaluate_con_rules(company_id, ratios, mcap, cf, pnl)

        if not pros:
            pros = [fallback_pro(ratios)]

        if not cons:
            cons = [fallback_con(ratios)]

        for rule_id, text, confidence in pros:
            output_rows.append({
                "company_id": company_id,
                "type": "Pro",
                "rule_id": rule_id,
                "text": text,
                "confidence_pct": confidence
            })

        for rule_id, text, confidence in cons:
            output_rows.append({
                "company_id": company_id,
                "type": "Con",
                "rule_id": rule_id,
                "text": text,
                "confidence_pct": confidence
            })

    return pd.DataFrame(output_rows)


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

def main():

    print("=" * 60)
    print("Pros / Cons Generator (Sprint 5 - Day 30)")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    result = generate_pros_cons()

    output_path = os.path.join(OUTPUT_DIR, "pros_cons_generated.csv")
    result.to_csv(output_path, index=False)

    companies = result["company_id"].nunique()
    missing_pro = companies - result[result["type"] == "Pro"]["company_id"].nunique()
    missing_con = companies - result[result["type"] == "Con"]["company_id"].nunique()

    print(f"✔ Companies covered      : {companies}")
    print(f"✔ Total Pro/Con rows     : {len(result)}")
    print(f"✔ Companies missing Pro  : {missing_pro}")
    print(f"✔ Companies missing Con  : {missing_con}")
    print(f"✔ Saved: {output_path}")


if __name__ == "__main__":
    main()
