"""
report_data.py

Sprint 5
Day 33 support module

Shared data access layer for the reporting package
(src/reports/tearsheet.py, sector_report.py, portfolio_report.py).

Centralizes the per-company database pulls so all three report
types stay consistent with each other and with the Sprint 5
Day 29-32 outputs (pros/cons, cash flow intelligence).
"""

import os
import sqlite3

import pandas as pd

from src.analytics.cashflow_kpis import _year_key

DB_PATH = "db/nifty100.db"
OUTPUT_DIR = "output"

PROS_CONS_PATH = os.path.join(OUTPUT_DIR, "pros_cons_generated.csv")
CASHFLOW_INTELLIGENCE_PATH = os.path.join(OUTPUT_DIR, "cashflow_intelligence.xlsx")

TREND_YEARS = 6


def _clean_years(df):
    """
    Drop TTM rows, collapse duplicate rows that only differ by year
    label format (e.g. cashflow's "Mar 2024" vs "Mar-24" - see
    cashflow_kpis._year_key), and sort chronologically.
    """

    df = df[df["year"] != "TTM"].copy()
    df["year_key"] = _year_key(df["year"])
    df = df.dropna(subset=["year_key"]).sort_values("year_key")
    df = df.drop_duplicates(subset=["year_key"], keep="first")
    return df.drop(columns="year_key")


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_master_companies():
    """The 92-company master list with sector info joined in."""

    conn = get_connection()

    companies = pd.read_sql(
        "SELECT id, company_name, roce_percentage, book_value FROM companies",
        conn
    )

    sectors = pd.read_sql(
        "SELECT company_id, broad_sector, sub_sector, market_cap_category FROM sectors",
        conn
    )

    conn.close()

    return companies.merge(
        sectors, left_on="id", right_on="company_id", how="left"
    ).drop(columns=["company_id"])


_PROS_CONS_CACHE = None
_INTELLIGENCE_CACHE = None


def load_pros_cons():
    global _PROS_CONS_CACHE

    if _PROS_CONS_CACHE is None:
        if os.path.exists(PROS_CONS_PATH):
            _PROS_CONS_CACHE = pd.read_csv(PROS_CONS_PATH)
        else:
            _PROS_CONS_CACHE = pd.DataFrame(
                columns=["company_id", "type", "rule_id", "text", "confidence_pct"]
            )

    return _PROS_CONS_CACHE


def load_cashflow_intelligence():
    global _INTELLIGENCE_CACHE

    if _INTELLIGENCE_CACHE is None:
        if os.path.exists(CASHFLOW_INTELLIGENCE_PATH):
            _INTELLIGENCE_CACHE = pd.read_excel(
                CASHFLOW_INTELLIGENCE_PATH, sheet_name="Cashflow_Intelligence"
            ).set_index("company_id")
        else:
            _INTELLIGENCE_CACHE = pd.DataFrame()

    return _INTELLIGENCE_CACHE


class CompanyReportData:
    """
    Bundles everything a report (tearsheet / sector / portfolio) needs
    for a single company, fetched once and reused across chart calls.
    """

    def __init__(self, company_id):

        self.company_id = company_id

        conn = get_connection()

        self.pnl = _clean_years(pd.read_sql(
            "SELECT year, sales, net_profit, operating_profit FROM profitandloss "
            "WHERE company_id = ?", conn, params=(company_id,)
        ))

        self.balance_sheet = _clean_years(pd.read_sql(
            "SELECT year, total_assets, total_liabilities, borrowings, reserves, "
            "equity_capital FROM balancesheet WHERE company_id = ?",
            conn, params=(company_id,)
        ))

        self.cashflow = _clean_years(pd.read_sql(
            "SELECT year, operating_activity, investing_activity, financing_activity "
            "FROM cashflow WHERE company_id = ?", conn, params=(company_id,)
        ))

        self.ratios = _clean_years(pd.read_sql(
            "SELECT year, return_on_equity_pct, composite_quality_score, "
            "debt_to_equity, dividend_payout_ratio_pct FROM financial_ratios "
            "WHERE company_id = ?", conn, params=(company_id,)
        ))

        market_cap = pd.read_sql(
            "SELECT year, market_cap_crore, pe_ratio, pb_ratio, dividend_yield_pct "
            "FROM market_cap WHERE company_id = ? ORDER BY year", conn,
            params=(company_id,)
        )
        self.market_cap_latest = market_cap.iloc[-1] if not market_cap.empty else pd.Series(dtype=float)

        company_row = pd.read_sql(
            "SELECT * FROM companies WHERE id = ?", conn, params=(company_id,)
        )
        self.company = company_row.iloc[0] if not company_row.empty else pd.Series(dtype=object)

        sector_row = pd.read_sql(
            "SELECT * FROM sectors WHERE company_id = ?", conn, params=(company_id,)
        )
        self.sector = sector_row.iloc[0] if not sector_row.empty else pd.Series(dtype=object)

        conn.close()

        intelligence = load_cashflow_intelligence()
        self.intelligence = (
            intelligence.loc[company_id] if company_id in intelligence.index
            else pd.Series(dtype=object)
        )

        pros_cons = load_pros_cons()
        company_pc = pros_cons[pros_cons["company_id"] == company_id]
        self.pros = company_pc[company_pc["type"] == "Pro"].sort_values(
            "confidence_pct", ascending=False
        ).to_dict("records")
        self.cons = company_pc[company_pc["type"] == "Con"].sort_values(
            "confidence_pct", ascending=False
        ).to_dict("records")

    def has_sufficient_data(self):
        """
        Minimum bar for generating a tearsheet: at least 2 years of
        Profit & Loss history (needed for every core KPI tile and the
        revenue/profit trend charts).
        """

        return len(self.pnl) >= 2

    def recent(self, df, years=TREND_YEARS):
        return df.tail(years) if df is not None and not df.empty else df
