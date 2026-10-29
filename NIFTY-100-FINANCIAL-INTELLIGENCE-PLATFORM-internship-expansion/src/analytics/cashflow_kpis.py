"""
cashflow_kpis.py

Sprint 2
Day 11

Cash Flow KPI Engine
"""


# --------------------------------------------------
# Free Cash Flow
# --------------------------------------------------

def free_cash_flow(
    operating_activity,
    investing_activity
):
    """
    Free Cash Flow

    Formula:
        Operating Activity + Investing Activity

    Note:
        Investing Activity is usually negative.
        Negative FCF is allowed.
    """

    if operating_activity is None:
        return None

    if investing_activity is None:
        return None

    return round(
        operating_activity +
        investing_activity,
        2
    )

# --------------------------------------------------
# FCF Conversion
# --------------------------------------------------

def fcf_conversion_rate(
    free_cashflow,
    operating_profit
):
    """
    Formula:

    FCF / Operating Profit ×100
    """

    if operating_profit is None:
        return None

    if operating_profit == 0:
        return None

    return round(
        (free_cashflow / operating_profit) * 100,
        2
    )


# --------------------------------------------------
# CFO Quality Score
# --------------------------------------------------

def cfo_quality_score(
    cash_from_operations,
    net_profit
):
    """
    CFO Quality Score

    Formula:
        CFO / PAT

    Rules:
        > 1.0  -> High Quality
        0.5-1.0 -> Moderate
        < 0.5 -> Accrual Risk
        PAT = 0 -> None
    """

    if net_profit is None:
        return None, None

    if net_profit == 0:
        return None, None

    score = cash_from_operations / net_profit

    if score > 1:
        label = "High Quality"

    elif score >= 0.5:
        label = "Moderate"

    else:
        label = "Accrual Risk"

    return round(score, 2), label


# --------------------------------------------------
# CapEx Intensity
# --------------------------------------------------

def capex_intensity(
    investing_activity,
    sales
):
    """
    CapEx Intensity

    Formula:
        abs(Investing Activity) / Sales ×100
    """

    if sales is None:
        return None, None

    if sales == 0:
        return None, None

    intensity = (
        abs(investing_activity) / sales
    ) * 100

    if intensity < 3:
        label = "Asset Light"

    elif intensity <= 8:
        label = "Moderate"

    else:
        label = "Capital Intensive"

    return round(intensity, 2), label


# --------------------------------------------------
# Capital Allocation Pattern
# --------------------------------------------------

def capital_allocation_pattern(
    operating_activity,
    investing_activity,
    financing_activity
):
    """
    Capital Allocation Pattern

    Returns:
        cfo_sign,
        cfi_sign,
        cff_sign,
        pattern_label
    """

    cfo_sign = "+" if operating_activity >= 0 else "-"
    cfi_sign = "+" if investing_activity >= 0 else "-"
    cff_sign = "+" if financing_activity >= 0 else "-"

    pattern = (cfo_sign, cfi_sign, cff_sign)

    patterns = {
        ("+", "-", "-"): "Reinvestor",
        ("+", "+", "-"): "Liquidating Assets",
        ("-", "+", "+"): "Distress Signal",
        ("-", "-", "+"): "Growth Funded by Debt",
        ("+", "+", "+"): "Cash Accumulator",
        ("-", "-", "-"): "Pre-Revenue",
        ("+", "-", "+"): "Mixed"
    }

    label = patterns.get(pattern, "Unknown")

    return (
        cfo_sign,
        cfi_sign,
        cff_sign,
        label
    )


# ====================================================
# Sprint 5 - Day 31
# Cash Flow Intelligence (orchestration layer)
# ====================================================
#
# The functions above are the pure KPI building blocks (Sprint 2,
# Day 11). This section adds the Sprint 5 orchestration that pulls
# data for all companies from the database, runs those building
# blocks across the latest few years, adds distress / deleveraging
# detection, and writes the Sprint 5 deliverables:
#
#   output/cashflow_intelligence.xlsx
#   output/distress_alerts.csv

import os
import sqlite3

import pandas as pd

DB_PATH = "db/nifty100.db"
OUTPUT_DIR = "output"

TREND_YEARS = 5


# --------------------------------------------------
# Distress Detection
# --------------------------------------------------

def detect_distress(pattern_label, cfo_quality_label, free_cashflow):
    """
    Distress Detection

    A company is flagged distressed when its cash flow signature
    matches a "Distress Signal" capital-allocation pattern, or when
    it is simultaneously burning cash (negative FCF) while its cash
    conversion is already weak (Accrual Risk).

    Returns:
        (is_distressed, reason)
    """

    if pattern_label == "Distress Signal":
        return True, "Negative CFO funded by financing/asset sales"

    if cfo_quality_label == "Accrual Risk" and free_cashflow is not None and free_cashflow < 0:
        return True, "Weak cash conversion with negative free cash flow"

    return False, None


# --------------------------------------------------
# Deleveraging Detection
# --------------------------------------------------

def detect_deleveraging(borrowings_series):
    """
    Deleveraging Detection

    Compares the most recent borrowings figure to the figure
    TREND_YEARS ago (or the earliest available year if fewer years
    exist) to classify the debt trend.

    borrowings_series : list/Series of borrowings ordered oldest -> newest

    Returns:
        label in {"Deleveraging", "Increasing Leverage", "Stable", None}
    """

    values = [v for v in borrowings_series if pd.notna(v)]

    if len(values) < 2:
        return None

    start, end = values[0], values[-1]

    if start == 0:
        return None

    change_pct = ((end - start) / abs(start)) * 100

    if change_pct <= -10:
        return "Deleveraging"

    if change_pct >= 10:
        return "Increasing Leverage"

    return "Stable"


# --------------------------------------------------
# Data Loading
# --------------------------------------------------

def _year_key(year_series):
    """
    Sprint 5 data-quality fix: the `cashflow` table contains duplicate
    rows per company/year using two different year label formats
    ("Mar 2024" and the abbreviated "Mar-24") with identical values.
    String-sorting/deduplicating on the raw label treats these as
    different years, which both inflates row counts and can break
    joins against profitandloss/balancesheet (which only use the
    "Mon YYYY" format). This extracts a canonical 4-digit year for
    sorting, deduplication and cross-table joins instead.
    """

    text = year_series.astype(str)

    four_digit = text.str.extract(r"(\d{4})")[0]

    two_digit = text.str.extract(r"-(\d{2})$")[0]
    two_digit_year = two_digit.astype(float)
    two_digit_expanded = two_digit_year.apply(
        lambda yy: (2000 + yy) if pd.notna(yy) and yy < 50 else ((1900 + yy) if pd.notna(yy) else None)
    )

    key = four_digit.astype(float)
    key = key.fillna(two_digit_expanded)

    return key


def _load_source_tables():

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql("SELECT id FROM companies", conn)
    valid_ids = set(companies["id"])

    cashflow = pd.read_sql(
        "SELECT company_id, year, operating_activity, investing_activity, "
        "financing_activity, net_cash_flow FROM cashflow",
        conn
    )

    # Sprint 5 note: a handful of tickers appear in cashflow/pnl/balancesheet
    # (e.g. WIPRO, ZOMATO) but are missing from the `companies` master table
    # upstream (92 rows). Reports need company_name/sector, which only the
    # master table has, so intelligence is scoped to the 92 master companies
    # and the gap is documented rather than silently guessed at.
    cashflow = cashflow[cashflow["company_id"].isin(valid_ids)]

    pnl = pd.read_sql(
        "SELECT company_id, year, sales, operating_profit, net_profit FROM profitandloss",
        conn
    )

    balance_sheet = pd.read_sql(
        "SELECT company_id, year, borrowings FROM balancesheet",
        conn
    )

    conn.close()

    cashflow = cashflow[cashflow["year"] != "TTM"]
    pnl = pnl[pnl["year"] != "TTM"]
    balance_sheet = balance_sheet[balance_sheet["year"] != "TTM"]

    cashflow["year_key"] = _year_key(cashflow["year"])
    pnl["year_key"] = _year_key(pnl["year"])
    balance_sheet["year_key"] = _year_key(balance_sheet["year"])

    cashflow = cashflow.dropna(subset=["year_key"]).sort_values(["company_id", "year_key"])
    pnl = pnl.dropna(subset=["year_key"]).sort_values(["company_id", "year_key"])
    balance_sheet = balance_sheet.dropna(subset=["year_key"]).sort_values(["company_id", "year_key"])

    cashflow = cashflow.drop_duplicates(subset=["company_id", "year_key"], keep="first")
    pnl = pnl.drop_duplicates(subset=["company_id", "year_key"], keep="first")
    balance_sheet = balance_sheet.drop_duplicates(subset=["company_id", "year_key"], keep="first")

    return companies, cashflow, pnl, balance_sheet


# --------------------------------------------------
# Main Orchestration
# --------------------------------------------------

def build_cashflow_intelligence():
    """
    Build the per-company Cash Flow Intelligence table for the
    latest reported year of every company, using up to the last
    TREND_YEARS years of data for trend-based checks (deleveraging).

    Returns:
        pandas.DataFrame
    """

    companies, cashflow, pnl, balance_sheet = _load_source_tables()

    company_ids = sorted(companies["id"].unique())

    rows = []

    for company_id in company_ids:

        cf_hist = cashflow[cashflow["company_id"] == company_id].sort_values("year_key")
        pnl_hist = pnl[pnl["company_id"] == company_id].sort_values("year_key")
        bs_hist = balance_sheet[balance_sheet["company_id"] == company_id].sort_values("year_key")

        if cf_hist.empty:

            rows.append({
                "company_id": company_id,
                "latest_year": None,
                "operating_activity": None,
                "investing_activity": None,
                "financing_activity": None,
                "capex": None,
                "free_cash_flow": None,
                "fcf_conversion_pct": None,
                "cfo_quality_score": None,
                "cfo_quality_label": "Data Missing",
                "capex_intensity_pct": None,
                "capex_intensity_label": "Data Missing",
                "cfo_sign": None,
                "cfi_sign": None,
                "cff_sign": None,
                "capital_allocation_pattern": "Data Missing",
                "debt_trend_label": "Data Missing",
                "is_distressed": False,
                "distress_reason": "Cash flow data unavailable"
            })

            continue

        latest_cf = cf_hist.iloc[-1]
        latest_year = latest_cf["year"]
        latest_year_key = latest_cf["year_key"]

        pnl_row = pnl_hist[pnl_hist["year_key"] == latest_year_key]
        pnl_row = pnl_row.iloc[-1] if not pnl_row.empty else pd.Series(dtype=float)

        sales = pnl_row.get("sales")
        operating_profit = pnl_row.get("operating_profit")
        net_profit = pnl_row.get("net_profit")

        fcf = free_cash_flow(latest_cf["operating_activity"], latest_cf["investing_activity"])
        fcf_conversion = fcf_conversion_rate(fcf, operating_profit) if fcf is not None else None

        cfo_score, cfo_label = cfo_quality_score(latest_cf["operating_activity"], net_profit)
        capex_pct, capex_label = capex_intensity(latest_cf["investing_activity"], sales)

        cfo_sign, cfi_sign, cff_sign, pattern_label = capital_allocation_pattern(
            latest_cf["operating_activity"],
            latest_cf["investing_activity"],
            latest_cf["financing_activity"]
        )

        is_distressed, distress_reason = detect_distress(pattern_label, cfo_label, fcf)

        borrowings_trend = bs_hist.tail(TREND_YEARS)["borrowings"].tolist()
        deleveraging_label = detect_deleveraging(borrowings_trend)

        rows.append({
            "company_id": company_id,
            "latest_year": latest_year,
            "operating_activity": latest_cf["operating_activity"],
            "investing_activity": latest_cf["investing_activity"],
            "financing_activity": latest_cf["financing_activity"],
            "capex": -latest_cf["investing_activity"] if pd.notna(latest_cf["investing_activity"]) else None,
            "free_cash_flow": fcf,
            "fcf_conversion_pct": fcf_conversion,
            "cfo_quality_score": cfo_score,
            "cfo_quality_label": cfo_label,
            "capex_intensity_pct": capex_pct,
            "capex_intensity_label": capex_label,
            "cfo_sign": cfo_sign,
            "cfi_sign": cfi_sign,
            "cff_sign": cff_sign,
            "capital_allocation_pattern": pattern_label,
            "debt_trend_label": deleveraging_label,
            "is_distressed": is_distressed,
            "distress_reason": distress_reason
        })

    return pd.DataFrame(rows)


def main():

    print("=" * 60)
    print("Cash Flow Intelligence (Sprint 5 - Day 31)")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    intelligence = build_cashflow_intelligence()

    xlsx_path = os.path.join(OUTPUT_DIR, "cashflow_intelligence.xlsx")

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        intelligence.to_excel(writer, sheet_name="Cashflow_Intelligence", index=False)

    distress_alerts = intelligence[intelligence["is_distressed"]][
        ["company_id", "latest_year", "capital_allocation_pattern",
         "cfo_quality_label", "free_cash_flow", "distress_reason"]
    ]

    distress_path = os.path.join(OUTPUT_DIR, "distress_alerts.csv")
    distress_alerts.to_csv(distress_path, index=False)

    print(f"✔ Companies analyzed : {len(intelligence)}")
    print(f"✔ Distress alerts    : {len(distress_alerts)}")
    print(f"✔ Saved: {xlsx_path}")
    print(f"✔ Saved: {distress_path}")


if __name__ == "__main__":
    main()