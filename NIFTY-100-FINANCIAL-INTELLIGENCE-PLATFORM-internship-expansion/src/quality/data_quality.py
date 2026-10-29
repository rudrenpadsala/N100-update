"""
data_quality.py

Internship Expansion - Module 1
Data Quality Monitoring

Scans the loaded database tables and reports four families of problems:

    1. missing_value      null values in financial columns, and companies that
                          have no rows at all in a table
    2. duplicate          the same company-period appearing more than once
    3. period             inconsistent / unusable period labels, mixed fiscal
                          year-ends, gaps, and tables that disagree on the
                          latest reported year
    4. invalid_metric     values that break accounting identities or fall
                          outside a plausible range

Every finding is one row with the same columns, so the result can be
filtered in the dashboard, exported to CSV and quoted in PDF reports:

    table, company_id, period, category, check, severity, column, value, detail

Severity:
    error    the value cannot be trusted / an integrity rule is broken
    warning  suspicious; analysts should look at it
    info     expected or harmless (e.g. a TTM row, no dividend paid)

Usage:
    python -m src.quality.data_quality            # writes output/data_quality_report.csv
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.quality.periods import (
    add_period_columns, USABLE_KINDS, fiscal_year_end_months, mark_off_cycle,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / "db" / "nifty100.db"
DEFAULT_OUTPUT = REPO_ROOT / "output" / "data_quality_report.csv"

ISSUE_COLUMNS = [
    "table", "company_id", "period", "category", "check",
    "severity", "column", "value", "detail",
]

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}

# Tables whose rows are keyed by (company_id, period label).
PERIOD_TABLES = [
    "profitandloss", "balancesheet", "cashflow", "financial_ratios", "market_cap",
]

# Columns where a null is a real gap (error/warning) ...
CRITICAL_COLUMNS = {
    "profitandloss": ["sales", "net_profit"],
    "balancesheet": ["equity_capital", "reserves", "borrowings", "total_assets"],
    "cashflow": ["operating_activity", "investing_activity", "financing_activity"],
    "financial_ratios": ["return_on_equity_pct", "debt_to_equity"],
    "market_cap": ["market_cap_crore", "pe_ratio"],
}

# ... and columns where a null is common and usually legitimate
# (no dividend paid, no interest expense, too little history for a CAGR).
EXPECTED_NULL_COLUMNS = {
    "profitandloss": ["tax_percentage", "dividend_payout"],
    "financial_ratios": [
        "interest_coverage", "revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr",
        "dividend_payout_ratio_pct",
    ],
}

# Columns that are scanned for nulls at all (everything else is ignored).
NULL_SCAN_COLUMNS = {
    "profitandloss": [
        "sales", "expenses", "operating_profit", "opm_percentage", "net_profit",
        "eps", "tax_percentage", "dividend_payout",
    ],
    "balancesheet": [
        "equity_capital", "reserves", "borrowings", "total_liabilities",
        "total_assets",
    ],
    "cashflow": [
        "operating_activity", "investing_activity", "financing_activity",
        "net_cash_flow",
    ],
    "financial_ratios": [
        "net_profit_margin_pct", "operating_profit_margin_pct",
        "return_on_equity_pct", "debt_to_equity", "interest_coverage",
        "asset_turnover", "free_cash_flow_cr", "capex_cr", "earnings_per_share",
        "dividend_payout_ratio_pct", "cash_from_operations_cr",
        "revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr",
    ],
    "market_cap": ["market_cap_crore", "pe_ratio", "pb_ratio"],
}

_MONTH_NAMES = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

# Tolerances for identities that are rounded in the source data.
BALANCE_SHEET_TOLERANCE = 1.0        # Rs crore
CASHFLOW_TOLERANCE = 5.0             # Rs crore


# =====================================================================
# Loading
# =====================================================================

def load_tables(db_path: Optional[os.PathLike] = None) -> Dict[str, pd.DataFrame]:
    """Read every table needed by the analytics modules into DataFrames."""

    path = Path(db_path) if db_path else DEFAULT_DB_PATH

    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")

    names = [
        "companies", "sectors", "peer_groups", "stock_prices",
        *PERIOD_TABLES,
    ]

    conn = sqlite3.connect(str(path))

    try:
        return {name: pd.read_sql(f"SELECT * FROM {name}", conn) for name in names}
    finally:
        conn.close()


# =====================================================================
# Issue helper
# =====================================================================

def _issue(table, company_id, period, category, check, severity, column=None,
           value=None, detail=""):
    return {
        "table": table,
        "company_id": company_id,
        "period": period,
        "category": category,
        "check": check,
        "severity": severity,
        "column": column,
        "value": value,
        "detail": detail,
    }


def _fmt(value) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "n/a"
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


# =====================================================================
# The monitor
# =====================================================================

class DataQualityMonitor:
    """Runs every data-quality check against a dict of table DataFrames."""

    def __init__(self, tables: Dict[str, pd.DataFrame]):
        self.tables = tables
        self.master_ids = (
            set(tables["companies"]["id"].astype(str))
            if "companies" in tables and not tables["companies"].empty
            else set()
        )

        # Fiscal-year-end month per company, learned from every period table.
        self.fy_months = fiscal_year_end_months(
            [tables.get(t) for t in PERIOD_TABLES]
        )

        # Banks, NBFCs and insurers: expense / margin rules do not apply.
        self.financial_ids = set()
        sectors = tables.get("sectors")
        if sectors is not None and not sectors.empty:
            self.financial_ids = set(
                sectors.loc[sectors["broad_sector"] == "Financials", "company_id"].astype(str)
            )

    # ------------------------------------------------------------
    def run(self) -> pd.DataFrame:
        issues: List[dict] = []

        issues += self.check_missing_values()
        issues += self.check_company_coverage()
        issues += self.check_duplicates()
        issues += self.check_periods()
        issues += self.check_invalid_metrics()
        issues += self.check_referential_integrity()

        if not issues:
            return pd.DataFrame(columns=ISSUE_COLUMNS)

        df = pd.DataFrame(issues, columns=ISSUE_COLUMNS)
        df["_sev"] = df["severity"].map(SEVERITY_ORDER)
        df = df.sort_values(
            ["_sev", "table", "company_id", "period"], kind="stable"
        ).drop(columns="_sev")

        return df.reset_index(drop=True)

    # ------------------------------------------------------------
    def _period_table(self, name: str) -> Optional[pd.DataFrame]:
        df = self.tables.get(name)
        if df is None or df.empty or "year" not in df.columns:
            return None
        return mark_off_cycle(add_period_columns(df, "year"), self.fy_months)

    # ------------------------------------------------------------
    # 1. Missing values
    # ------------------------------------------------------------
    def check_missing_values(self) -> List[dict]:
        out: List[dict] = []

        for table, columns in NULL_SCAN_COLUMNS.items():
            df = self.tables.get(table)
            if df is None or df.empty:
                continue

            critical = set(CRITICAL_COLUMNS.get(table, []))
            expected = set(EXPECTED_NULL_COLUMNS.get(table, []))

            for column in columns:
                if column not in df.columns:
                    continue

                rows = df[df[column].isna()]

                for _, row in rows.iterrows():
                    if column in critical:
                        severity = "error"
                    elif column in expected:
                        severity = "info"
                    else:
                        severity = "warning"

                    out.append(_issue(
                        table, row.get("company_id"), row.get("year"),
                        "missing_value", "null_value", severity, column, None,
                        f"{column} is empty",
                    ))

        return out

    def check_company_coverage(self) -> List[dict]:
        """Master companies that have no rows at all in a table."""

        out: List[dict] = []

        for table in PERIOD_TABLES:
            df = self.tables.get(table)
            if df is None:
                continue

            present = set(df["company_id"].astype(str))

            for company_id in sorted(self.master_ids - present):
                out.append(_issue(
                    table, company_id, None, "missing_value",
                    "company_missing_from_table", "warning", None, None,
                    f"{company_id} has no rows in {table}",
                ))

        return out

    # ------------------------------------------------------------
    # 2. Duplicates
    # ------------------------------------------------------------
    def check_duplicates(self) -> List[dict]:
        out: List[dict] = []

        for table in PERIOD_TABLES:
            df = self._period_table(table)
            if df is None:
                continue

            usable = df[df["period_kind"].isin(USABLE_KINDS) & ~df["off_cycle"]]
            value_cols = [
                c for c in usable.columns
                if c not in ("id", "company_id", "year", "period_kind",
                             "year_key", "period_month")
            ]

            for (company_id, year_key), group in usable.groupby(
                ["company_id", "year_key"], sort=False
            ):
                if len(group) < 2:
                    continue

                labels = ", ".join(sorted(set(group["year"].astype(str))))
                identical = (
                    group[value_cols].astype(object).where(group[value_cols].notna(), None)
                    .drop_duplicates().shape[0] == 1
                )

                out.append(_issue(
                    table, company_id, f"{int(year_key)}", "duplicate",
                    "duplicate_period_identical" if identical
                    else "duplicate_period_conflicting",
                    "warning" if identical else "error", None, len(group),
                    f"{len(group)} rows for the same company-year (labels: {labels})"
                    + ("; values identical" if identical
                       else "; values differ - cannot tell which is correct"),
                ))

        # Duplicate sector / peer-group assignments.
        sectors = self.tables.get("sectors")
        if sectors is not None and not sectors.empty:
            dup = sectors[sectors.duplicated("company_id", keep=False)]
            for company_id in sorted(set(dup["company_id"])):
                out.append(_issue(
                    "sectors", company_id, None, "duplicate",
                    "duplicate_sector_assignment", "error", None, None,
                    "company is assigned to more than one sector row",
                ))

        peers = self.tables.get("peer_groups")
        if peers is not None and not peers.empty:
            dup = peers[peers.duplicated("company_id", keep=False)]
            for company_id in sorted(set(dup["company_id"])):
                out.append(_issue(
                    "peer_groups", company_id, None, "duplicate",
                    "multiple_peer_groups", "warning", None, None,
                    "company belongs to more than one peer group",
                ))

        return out

    # ------------------------------------------------------------
    # 3. Period consistency
    # ------------------------------------------------------------
    def check_periods(self) -> List[dict]:
        out: List[dict] = []
        latest_by_table: Dict[str, pd.Series] = {}

        for table in PERIOD_TABLES:
            df = self._period_table(table)
            if df is None:
                continue

            # --- label format problems -----------------------------------
            labels = df.groupby(["company_id", "year", "period_kind"], dropna=False).size()
            for (company_id, label, kind), _ in labels.items():
                if kind == "standard":
                    continue

                if kind == "ttm":
                    out.append(_issue(
                        table, company_id, label, "period", "ttm_row", "info",
                        "year", label,
                        "trailing-twelve-month row; excluded from annual analytics",
                    ))
                elif kind == "year_only" and table == "market_cap":
                    # market_cap is an annual-snapshot table keyed by bare year by design.
                    continue
                elif kind in ("abbreviated", "year_only"):
                    out.append(_issue(
                        table, company_id, label, "period",
                        "non_standard_period_label", "warning", "year", label,
                        f"label '{label}' is not in 'Mon YYYY' format; normalised for analytics",
                    ))
                else:
                    out.append(_issue(
                        table, company_id, label, "period",
                        "unusable_period_label", "warning", "year", label,
                        f"label '{label}' is {kind}; row excluded from annual analytics",
                    ))

            usable = df[df["period_kind"].isin(USABLE_KINDS) & ~df["off_cycle"]]

            # --- off-cycle rows (half-year snapshots, transition periods) ---
            off = df[df["off_cycle"] & df["period_kind"].isin(USABLE_KINDS)]
            for company_id, group in off.groupby("company_id"):
                labels = ", ".join(sorted(set(group["year"].astype(str))))
                fy = self.fy_months.get(company_id)
                out.append(_issue(
                    table, company_id, None, "period", "off_cycle_period",
                    "warning", "year", len(group),
                    f"{len(group)} row(s) ({labels}) do not fall on the company's fiscal year-end month "
                    f"({_MONTH_NAMES.get(fy, fy)}); treated as part-year data and excluded from annual analytics",
                ))

            # --- gaps in the annual sequence -----------------------------
            years = usable.groupby("company_id")["year_key"].apply(
                lambda s: sorted(set(int(v) for v in s.dropna()))
            )
            for company_id, ys in years.items():
                if len(ys) < 2:
                    continue
                missing = sorted(set(range(ys[0], ys[-1] + 1)) - set(ys))
                if missing:
                    out.append(_issue(
                        table, company_id, None, "period", "gap_in_years",
                        "warning", "year", None,
                        f"no annual row for {', '.join(str(m) for m in missing)}",
                    ))

            latest_by_table[table] = years.apply(lambda ys: ys[-1] if ys else np.nan)

        # --- tables disagree on the latest year --------------------------
        core = [t for t in ("profitandloss", "balancesheet", "cashflow", "financial_ratios")
                if t in latest_by_table]

        if len(core) >= 2:
            frame = pd.DataFrame({t: latest_by_table[t] for t in core})
            if self.master_ids:
                frame = frame[frame.index.astype(str).isin(self.master_ids)]
            for company_id, row in frame.iterrows():
                values = row.dropna()
                if values.nunique() > 1:
                    detail = ", ".join(f"{t}={int(v)}" for t, v in values.items())
                    out.append(_issue(
                        "all_statements", company_id, None, "period",
                        "latest_year_mismatch", "warning", "year", None,
                        f"statements end in different years ({detail})",
                    ))

        return out

    # ------------------------------------------------------------
    # 4. Invalid metrics
    # ------------------------------------------------------------
    def check_invalid_metrics(self) -> List[dict]:
        out: List[dict] = []

        def add(table, row, check, severity, column, value, detail):
            out.append(_issue(
                table, row.get("company_id"), row.get("year", row.get("date")),
                "invalid_metric", check, severity, column, value, detail,
            ))

        # ---- profit & loss ---------------------------------------------
        pl = self.tables.get("profitandloss")
        if pl is not None and not pl.empty:
            for _, r in pl.iterrows():
                if _lt(r.get("sales"), 0):
                    add("profitandloss", r, "negative_sales", "error", "sales",
                        r["sales"], f"sales is negative ({_fmt(r['sales'])})")
                if (r.get("company_id") not in self.financial_ids
                        and _notnull(r.get("sales")) and _notnull(r.get("expenses"))
                        and r["sales"] > 0 and 0 <= r["expenses"] < 0.05 * r["sales"]):
                    add("profitandloss", r, "expenses_implausibly_low", "warning",
                        "expenses", r["expenses"],
                        f"expenses {_fmt(r['expenses'])} are under 5% of sales {_fmt(r['sales'])}; "
                        "operating margin derived from this row is likely overstated")
                if _lt(r.get("expenses"), 0):
                    add("profitandloss", r, "negative_expenses", "error", "expenses",
                        r["expenses"], f"expenses are negative ({_fmt(r['expenses'])})")
                if _outside(r.get("opm_percentage"), -100, 100):
                    add("profitandloss", r, "opm_out_of_range", "warning",
                        "opm_percentage", r["opm_percentage"],
                        f"operating margin {_fmt(r['opm_percentage'])}% is outside -100..100")
                if _outside(r.get("tax_percentage"), -100, 100):
                    add("profitandloss", r, "tax_rate_out_of_range", "warning",
                        "tax_percentage", r["tax_percentage"],
                        f"tax rate {_fmt(r['tax_percentage'])}% is outside -100..100")
                if _gt(r.get("net_profit"), r.get("sales")) and _gt(r.get("sales"), 0):
                    add("profitandloss", r, "profit_exceeds_sales", "warning",
                        "net_profit", r["net_profit"],
                        f"net profit {_fmt(r['net_profit'])} exceeds sales {_fmt(r['sales'])}")
                if _sign_conflict(r.get("net_profit"), r.get("eps")):
                    add("profitandloss", r, "eps_sign_mismatch", "warning", "eps",
                        r["eps"], "EPS and net profit have opposite signs")

        # ---- balance sheet ---------------------------------------------
        bs = self.tables.get("balancesheet")
        if bs is not None and not bs.empty:
            for _, r in bs.iterrows():
                ta, tl = r.get("total_assets"), r.get("total_liabilities")
                if _notnull(ta) and _notnull(tl) and abs(ta - tl) > BALANCE_SHEET_TOLERANCE:
                    add("balancesheet", r, "balance_sheet_not_balanced", "error",
                        "total_assets", ta,
                        f"total assets {_fmt(ta)} != total liabilities {_fmt(tl)}")
                if _lt(ta, 0):
                    add("balancesheet", r, "negative_total_assets", "error",
                        "total_assets", ta, "total assets are negative")
                if _lt(r.get("borrowings"), 0):
                    add("balancesheet", r, "negative_borrowings", "error",
                        "borrowings", r["borrowings"], "borrowings are negative")
                eq, rs = r.get("equity_capital"), r.get("reserves")
                if _notnull(eq) and _notnull(rs) and (eq + rs) < 0:
                    add("balancesheet", r, "negative_net_worth", "warning",
                        "reserves", eq + rs,
                        f"net worth (equity + reserves) is negative ({_fmt(eq + rs)})")

        # ---- cash flow ---------------------------------------------------
        cf = self.tables.get("cashflow")
        if cf is not None and not cf.empty:
            for _, r in cf.iterrows():
                parts = [r.get("operating_activity"), r.get("investing_activity"),
                         r.get("financing_activity")]
                net = r.get("net_cash_flow")
                if all(_notnull(p) for p in parts) and _notnull(net):
                    if abs(sum(parts) - net) > CASHFLOW_TOLERANCE:
                        add("cashflow", r, "cashflow_does_not_add_up", "warning",
                            "net_cash_flow", net,
                            f"operating + investing + financing = {_fmt(sum(parts))} but net cash flow is {_fmt(net)}")

        # ---- financial ratios -------------------------------------------
        fr = self.tables.get("financial_ratios")
        if fr is not None and not fr.empty:
            for _, r in fr.iterrows():
                roe = r.get("return_on_equity_pct")
                if _notnull(roe) and abs(roe) > 1000:
                    add("financial_ratios", r, "roe_implausible", "error",
                        "return_on_equity_pct", roe,
                        f"ROE of {_fmt(roe)}% is implausible (likely a tiny or negative equity base)")
                elif _notnull(roe) and abs(roe) > 100:
                    add("financial_ratios", r, "roe_extreme", "warning",
                        "return_on_equity_pct", roe,
                        f"ROE of {_fmt(roe)}% is unusually high/low")
                if _lt(r.get("debt_to_equity"), 0):
                    add("financial_ratios", r, "negative_debt_to_equity", "error",
                        "debt_to_equity", r["debt_to_equity"], "debt-to-equity is negative")
                elif _gt(r.get("debt_to_equity"), 50):
                    add("financial_ratios", r, "debt_to_equity_extreme", "warning",
                        "debt_to_equity", r["debt_to_equity"],
                        f"debt-to-equity of {_fmt(r['debt_to_equity'])} is extreme")
                if _outside(r.get("net_profit_margin_pct"), -100, 100):
                    add("financial_ratios", r, "net_margin_out_of_range", "warning",
                        "net_profit_margin_pct", r["net_profit_margin_pct"],
                        f"net margin {_fmt(r['net_profit_margin_pct'])}% is outside -100..100")
                if _outside(r.get("operating_profit_margin_pct"), -100, 100):
                    add("financial_ratios", r, "operating_margin_out_of_range", "warning",
                        "operating_profit_margin_pct", r["operating_profit_margin_pct"],
                        f"operating margin {_fmt(r['operating_profit_margin_pct'])}% is outside -100..100")
                if _outside(r.get("composite_quality_score"), 0, 100):
                    add("financial_ratios", r, "quality_score_out_of_range", "error",
                        "composite_quality_score", r["composite_quality_score"],
                        "composite quality score must be between 0 and 100")

        # ---- market cap -------------------------------------------------
        mc = self.tables.get("market_cap")
        if mc is not None and not mc.empty:
            for _, r in mc.iterrows():
                if _notnull(r.get("market_cap_crore")) and r["market_cap_crore"] <= 0:
                    add("market_cap", r, "non_positive_market_cap", "error",
                        "market_cap_crore", r["market_cap_crore"],
                        "market capitalisation must be positive")
                if _notnull(r.get("pe_ratio")) and r["pe_ratio"] <= 0:
                    add("market_cap", r, "non_positive_pe", "warning", "pe_ratio",
                        r["pe_ratio"], "P/E is zero or negative (loss-making or bad data)")
                if _lt(r.get("pb_ratio"), 0):
                    add("market_cap", r, "negative_pb", "warning", "pb_ratio",
                        r["pb_ratio"], "P/B is negative")
                if _outside(r.get("dividend_yield_pct"), 0, 25):
                    add("market_cap", r, "dividend_yield_out_of_range", "warning",
                        "dividend_yield_pct", r["dividend_yield_pct"],
                        f"dividend yield {_fmt(r['dividend_yield_pct'])}% is outside 0..25")

        # ---- stock prices -----------------------------------------------
        sp = self.tables.get("stock_prices")
        if sp is not None and not sp.empty:
            bad_range = sp[(sp["high_price"] < sp["low_price"])]
            for _, r in bad_range.iterrows():
                add("stock_prices", r, "high_below_low", "error", "high_price",
                    r["high_price"], "daily high is below daily low")
            bad_close = sp[(sp["close_price"] <= 0) | sp["close_price"].isna()]
            for _, r in bad_close.iterrows():
                add("stock_prices", r, "invalid_close_price", "error", "close_price",
                    r["close_price"], "close price is missing or not positive")

        return out

    # ------------------------------------------------------------
    # Referential integrity
    # ------------------------------------------------------------
    def check_referential_integrity(self) -> List[dict]:
        out: List[dict] = []

        if not self.master_ids:
            return out

        for table in PERIOD_TABLES + ["stock_prices", "sectors", "peer_groups"]:
            df = self.tables.get(table)
            if df is None or df.empty or "company_id" not in df.columns:
                continue

            orphans = sorted(set(df["company_id"].dropna().astype(str)) - self.master_ids)
            for company_id in orphans:
                count = int((df["company_id"].astype(str) == company_id).sum())
                out.append(_issue(
                    table, company_id, None, "invalid_metric", "orphan_company_id",
                    "error", "company_id", count,
                    f"{count} rows reference a company that is not in the companies master list",
                ))

        return out


# =====================================================================
# Small helpers
# =====================================================================

def _notnull(v) -> bool:
    return v is not None and not (isinstance(v, float) and np.isnan(v)) and not pd.isna(v)


def _lt(v, limit) -> bool:
    return _notnull(v) and v < limit


def _gt(v, limit) -> bool:
    return _notnull(v) and _notnull(limit) and v > limit


def _outside(v, low, high) -> bool:
    return _notnull(v) and (v < low or v > high)


def _sign_conflict(a, b) -> bool:
    return _notnull(a) and _notnull(b) and a != 0 and b != 0 and (a > 0) != (b > 0)


# =====================================================================
# Convenience API used by the dashboard, reports and CLI
# =====================================================================

def run_quality_checks(tables: Optional[Dict[str, pd.DataFrame]] = None,
                       db_path: Optional[os.PathLike] = None) -> pd.DataFrame:
    if tables is None:
        tables = load_tables(db_path)
    return DataQualityMonitor(tables).run()


def summarize(issues: pd.DataFrame, tables: Optional[Dict[str, pd.DataFrame]] = None) -> dict:
    """Headline numbers for the dashboard."""

    if issues.empty:
        by_sev = {"error": 0, "warning": 0, "info": 0}
    else:
        by_sev = {s: int((issues["severity"] == s).sum()) for s in SEVERITY_ORDER}

    records = 0
    if tables:
        records = sum(len(tables[t]) for t in PERIOD_TABLES if t in tables)

    flagged = 0
    if not issues.empty:
        flagged = int(issues[issues["severity"].isin(["error", "warning"])]
                      [["table", "company_id", "period"]].drop_duplicates().shape[0])

    return {
        "total_issues": int(len(issues)),
        "errors": by_sev["error"],
        "warnings": by_sev["warning"],
        "info": by_sev["info"],
        "records_checked": int(records),
        "records_flagged": flagged,
        "clean_record_pct": round(100 * (1 - flagged / records), 1) if records else None,
    }


def company_issues(issues: pd.DataFrame, company_id: str) -> pd.DataFrame:
    if issues.empty:
        return issues
    return issues[issues["company_id"].astype(str) == str(company_id)]


def company_reliability(issues: pd.DataFrame, company_id: str, recent_from_year: Optional[int] = None) -> dict:
    """
    Plain-language data-reliability rating for one company.

        Low     at least one error-level issue in the recent window
        Medium  at least one warning-level issue in the recent window
        High    nothing worse than info-level notes

    Info-level notes (TTM rows, no dividend) never lower the rating.
    Issues with no period (coverage gaps, mixed year-ends) always count.
    """

    mine = company_issues(issues, company_id)

    if mine.empty:
        return {"rating": "High", "errors": 0, "warnings": 0, "info": 0}

    if recent_from_year is not None:
        years = mine["period"].map(_period_year)
        recent = years.isna() | (years >= recent_from_year)
        mine = mine[recent]

    errors = int((mine["severity"] == "error").sum())
    warnings = int((mine["severity"] == "warning").sum())
    info = int((mine["severity"] == "info").sum())

    rating = "Low" if errors else ("Medium" if warnings else "High")

    return {"rating": rating, "errors": errors, "warnings": warnings, "info": info}


def _period_year(label):
    from src.quality.periods import parse_period
    if label is None or (isinstance(label, float) and np.isnan(label)):
        return np.nan
    text = str(label).strip()
    if text.isdigit() and len(text) == 4:
        return int(text)
    p = parse_period(text)
    return p.year if p.year is not None else np.nan


def company_warnings(issues: pd.DataFrame, company_id: str,
                     recent_from_year: Optional[int] = None, limit: int = 12) -> List[str]:
    """Human-readable warning lines for PDF reports (errors first)."""

    mine = company_issues(issues, company_id)
    mine = mine[mine["severity"].isin(["error", "warning"])]

    if recent_from_year is not None and not mine.empty:
        years = mine["period"].map(_period_year)
        mine = mine[years.isna() | (years >= recent_from_year)]

    lines: List[str] = []
    seen = set()

    for _, r in mine.iterrows():
        where = f"{r['table']}" + (f" ({r['period']})" if pd.notna(r["period"]) else "")
        line = f"[{r['severity'].upper()}] {where}: {r['detail']}"
        if line not in seen:
            seen.add(line)
            lines.append(line)

    if len(lines) > limit:
        extra = len(lines) - limit
        lines = lines[:limit] + [f"... and {extra} more (see data-quality dashboard)"]

    return lines


# =====================================================================
# CLI
# =====================================================================

def main() -> None:
    tables = load_tables()
    issues = run_quality_checks(tables)

    DEFAULT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    issues.to_csv(DEFAULT_OUTPUT, index=False)

    s = summarize(issues, tables)

    print("Data quality report")
    print("-------------------")
    for key, value in s.items():
        print(f"{key:>18}: {value}")
    print()
    print(issues.groupby(["category", "check", "severity"]).size().to_string())
    print(f"\nSaved: {DEFAULT_OUTPUT}")


if __name__ == "__main__":
    main()
