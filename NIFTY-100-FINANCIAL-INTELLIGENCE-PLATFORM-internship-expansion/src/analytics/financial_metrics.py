"""
financial_metrics.py

Internship Expansion - Module 2 (Explainable Financial Analytics)

Builds ONE row of transparent financial indicators per company, for the
latest full fiscal year, straight from the raw statements:

    profitandloss  ->  sales, net profit, operating profit, interest, PBT
    balancesheet   ->  equity (capital + reserves), borrowings, total assets
    cashflow       ->  cash from operations, investing cash flow
    market_cap     ->  market cap, P/E, P/B, dividend yield

Every formula is the textbook one and is written out below so that it can
be quoted in reports. A metric that cannot be computed, or that falls
outside a plausible range (bad source data), is left empty and the reason
is recorded in `metric_notes` - it is never silently replaced.

Formulas
--------
ROE (%)                = net profit / (equity capital + reserves) x 100
Net margin (%)         = net profit / sales x 100
Operating margin (%)   = operating profit / sales x 100
Debt-to-equity (x)     = borrowings / (equity capital + reserves)
Interest coverage (x)  = (profit before tax + interest) / interest
Revenue CAGR (%)       = (sales_end / sales_start)^(1/years) - 1,  up to 5 years
Profit CAGR (%)        = same on net profit, only when both ends are positive
CFO / PAT (x)          = operating cash flow / net profit, only when profit > 0
Asset turnover (x)     = sales / total assets
Free cash flow (Rs cr) = operating cash flow + investing cash flow
                         (same definition as src/analytics/cashflow_kpis.py)
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd

from src.quality.periods import annual_rows, fiscal_year_end_months

# A value outside these limits is treated as bad source data, not as a result.
PLAUSIBLE_RANGE = {
    "roe_pct": (-100.0, 100.0),
    "net_margin_pct": (-100.0, 100.0),
    "operating_margin_pct": (-100.0, 100.0),
    "debt_to_equity": (0.0, 50.0),
    "revenue_cagr_pct": (-50.0, 100.0),
    "profit_cagr_pct": (-60.0, 200.0),
    "cfo_to_pat": (-20.0, 20.0),
    "asset_turnover": (0.0, 20.0),
}

CAGR_MAX_YEARS = 5
CAGR_MIN_YEARS = 3

METRIC_COLUMNS = [
    "roe_pct", "net_margin_pct", "operating_margin_pct", "debt_to_equity",
    "interest_coverage", "revenue_cagr_pct", "profit_cagr_pct", "cfo_to_pat",
    "asset_turnover",
]


def _safe_div(a, b) -> float:
    if a is None or b is None or pd.isna(a) or pd.isna(b) or b == 0:
        return np.nan
    return float(a) / float(b)


def _cagr(series: pd.Series, anchor_year: int, require_positive: bool = True):
    """
    CAGR between the anchor year and the earliest value within
    CAGR_MAX_YEARS before it (at least CAGR_MIN_YEARS apart).
    Returns (cagr_pct or nan, reason or None).
    """

    s = series.dropna()
    if anchor_year not in s.index:
        return np.nan, "no value in the latest year"

    end = float(s.loc[anchor_year])
    earlier = s[(s.index >= anchor_year - CAGR_MAX_YEARS) & (s.index < anchor_year)]

    if earlier.empty:
        return np.nan, "no earlier year available for growth"

    start_year = int(earlier.index.min())
    span = anchor_year - start_year

    if span < CAGR_MIN_YEARS:
        return np.nan, f"only {span} year(s) of history (need {CAGR_MIN_YEARS}+)"

    start = float(earlier.loc[start_year])

    if require_positive and (start <= 0 or end <= 0):
        return np.nan, "growth is not meaningful when start or end value is not positive"

    return ((end / start) ** (1.0 / span) - 1.0) * 100.0, None


def build_metrics(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One row per master company with latest-year indicators."""

    companies = tables["companies"][["id", "company_name"]].rename(
        columns={"id": "company_id"}
    )
    sectors = tables["sectors"][["company_id", "broad_sector", "sub_sector", "market_cap_category"]]
    master = companies.merge(sectors, on="company_id", how="left")
    master_ids = set(master["company_id"].astype(str))

    fy = fiscal_year_end_months([
        tables.get("profitandloss"), tables.get("balancesheet"),
        tables.get("cashflow"), tables.get("financial_ratios"),
    ])

    def prepare(name):
        df = tables.get(name)
        if df is None or df.empty:
            return {}
        df = df[df["company_id"].astype(str).isin(master_ids)]
        df = annual_rows(df, fy_months=fy)
        return {cid: g.set_index(g["year_key"].astype(int)) for cid, g in df.groupby("company_id")}

    pl_by = prepare("profitandloss")
    bs_by = prepare("balancesheet")
    cf_by = prepare("cashflow")
    mc_by = prepare("market_cap")

    rows = []

    for _, m in master.iterrows():
        cid = m["company_id"]
        row = {
            "company_id": cid,
            "company_name": m["company_name"],
            "broad_sector": m["broad_sector"],
            "sub_sector": m["sub_sector"],
            "market_cap_category": m["market_cap_category"],
            "is_financial": m["broad_sector"] == "Financials",
        }
        notes: Dict[str, str] = {}

        pl = pl_by.get(cid)
        pl = pl[pl["sales"].notna()] if pl is not None else None

        if pl is None or pl.empty:
            row["as_of_year"] = np.nan
            row["metric_notes"] = {k: "no profit & loss data" for k in METRIC_COLUMNS}
            rows.append(row)
            continue

        anchor = int(pl.index.max())
        p = pl.loc[anchor]
        b = bs_by.get(cid)
        b = b.loc[anchor] if b is not None and anchor in b.index else None
        c = cf_by.get(cid)
        c = c.loc[anchor] if c is not None and anchor in c.index else None

        row["as_of_year"] = anchor
        row["as_of_label"] = str(p["year"])
        row["history_years"] = int(pl.index.nunique())

        sales = p["sales"]
        pat = p["net_profit"]
        row["sales"] = sales
        row["net_profit"] = pat
        row["operating_profit"] = p.get("operating_profit")

        # ---- profitability ------------------------------------------------
        row["net_margin_pct"] = _safe_div(pat, sales) * 100
        row["operating_margin_pct"] = _safe_div(p.get("operating_profit"), sales) * 100

        if b is None:
            equity = np.nan
            for k in ("roe_pct", "debt_to_equity", "asset_turnover"):
                notes[k] = f"no balance sheet row for {anchor}"
            row.update(roe_pct=np.nan, debt_to_equity=np.nan, asset_turnover=np.nan)
            row.update(equity=np.nan, borrowings=np.nan, total_assets=np.nan)
        else:
            equity = b["equity_capital"] + b["reserves"]
            row.update(equity=equity, borrowings=b["borrowings"], total_assets=b["total_assets"])

            if pd.isna(equity) or equity <= 0:
                row["roe_pct"] = np.nan
                row["debt_to_equity"] = np.nan
                notes["roe_pct"] = "net worth is zero or negative"
                notes["debt_to_equity"] = "net worth is zero or negative"
            else:
                row["roe_pct"] = _safe_div(pat, equity) * 100
                row["debt_to_equity"] = _safe_div(b["borrowings"], equity)

            row["asset_turnover"] = _safe_div(sales, b["total_assets"])

        # ---- coverage ------------------------------------------------------
        interest = p.get("interest")
        row["interest_free"] = bool(pd.notna(interest) and interest == 0)

        if pd.notna(interest) and interest > 0 and pd.notna(p.get("profit_before_tax")):
            row["interest_coverage"] = (p["profit_before_tax"] + interest) / interest
        else:
            row["interest_coverage"] = np.nan
            notes["interest_coverage"] = (
                "no interest expense reported" if row["interest_free"]
                else "interest or profit before tax missing"
            )

        # ---- growth --------------------------------------------------------
        row["revenue_cagr_pct"], why = _cagr(pl["sales"], anchor)
        if why:
            notes["revenue_cagr_pct"] = why
        row["profit_cagr_pct"], why = _cagr(pl["net_profit"], anchor)
        if why:
            notes["profit_cagr_pct"] = why

        # ---- cash flow quality ---------------------------------------------
        if c is None or pd.isna(c.get("operating_activity")):
            row["cfo_to_pat"] = np.nan
            row["cfo"] = np.nan
            row["fcf"] = np.nan
            notes["cfo_to_pat"] = f"no cash flow data for {anchor}"
        else:
            cfo = c["operating_activity"]
            row["cfo"] = cfo
            inv = c.get("investing_activity")
            row["fcf"] = cfo + inv if pd.notna(inv) else np.nan
            if pd.notna(pat) and pat > 0:
                row["cfo_to_pat"] = cfo / pat
            else:
                row["cfo_to_pat"] = np.nan
                notes["cfo_to_pat"] = "net profit is not positive, so CFO/PAT is not meaningful"

        # ---- valuation -------------------------------------------------------
        mc = mc_by.get(cid)
        if mc is not None and not mc.empty:
            v = mc.loc[anchor] if anchor in mc.index else mc.iloc[-1]
            row["market_cap_crore"] = v.get("market_cap_crore")
            row["pe_ratio"] = v.get("pe_ratio")
            row["pb_ratio"] = v.get("pb_ratio")
            row["dividend_yield_pct"] = v.get("dividend_yield_pct")

        # ---- plausibility guard ---------------------------------------------
        for metric, (low, high) in PLAUSIBLE_RANGE.items():
            value = row.get(metric)
            if value is not None and pd.notna(value) and not (low <= value <= high):
                notes[metric] = (
                    f"computed value {value:,.2f} is outside the plausible range "
                    f"[{low:g}, {high:g}] - treated as a source-data error and excluded"
                )
                row[metric] = np.nan

        row["metric_notes"] = notes
        rows.append(row)

    df = pd.DataFrame(rows)

    for col in METRIC_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    return df.reset_index(drop=True)
