"""
Shared fixtures for the internship-expansion test suites
(data quality, health score, benchmarking, PDF reports, dashboard).

`synthetic_tables` is a tiny, fully controlled database that is CLEAN by
construction (no data-quality errors or warnings), so a test can break
exactly one thing and check that exactly that thing is reported.

`real_bundle` runs the full pipeline on db/nifty100.db once per session.
"""

from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "db" / "nifty100.db"

YEARS = [2019, 2020, 2021, 2022, 2023, 2024]


def make_company(cid, *, sales0=1000.0, growth=0.10, npm=0.15, opm=0.20, equity=500.0,
                 borrowings=100.0, interest=10.0, cfo_ratio=1.0, years=YEARS, month="Mar"):
    """Statement rows for one company. Every identity holds exactly."""

    pl, bs, cf, fr, mc = [], [], [], [], []

    for i, y in enumerate(years):
        label = f"{month} {y}"
        sales = round(sales0 * (1 + growth) ** i, 2)
        net_profit = round(sales * npm, 2)
        op_profit = round(sales * opm, 2)
        pbt = round(net_profit / 0.75, 2)
        total = round(equity * (1 + 0.1 * i) + borrowings + 200, 2)
        eq_cap = 50.0
        reserves = round(equity * (1 + 0.1 * i) - eq_cap, 2)
        cfo = round(net_profit * cfo_ratio, 2)
        inv = -round(sales * 0.05, 2)
        fin = round(-(cfo + inv) + 10, 2)

        pl.append(dict(company_id=cid, year=label, sales=sales, expenses=round(sales - op_profit, 2),
                       operating_profit=op_profit, opm_percentage=round(opm * 100, 1),
                       other_income=5.0, interest=interest, depreciation=20.0,
                       profit_before_tax=pbt, tax_percentage=25.0, net_profit=net_profit,
                       eps=round(net_profit / 10, 2), dividend_payout=20.0))
        bs.append(dict(company_id=cid, year=label, equity_capital=eq_cap, reserves=reserves,
                       borrowings=borrowings, other_liabilities=200.0, total_liabilities=total,
                       fixed_assets=300.0, cwip=10.0, investments=50.0,
                       other_asset=round(total - 360.0, 2), total_assets=total))
        cf.append(dict(company_id=cid, year=label, operating_activity=cfo, investing_activity=inv,
                       financing_activity=fin, net_cash_flow=round(cfo + inv + fin, 2)))
        fr.append(dict(company_id=cid, year=label,
                       net_profit_margin_pct=round(npm * 100, 2),
                       operating_profit_margin_pct=round(opm * 100, 2),
                       return_on_equity_pct=round(net_profit / (eq_cap + reserves) * 100, 2),
                       debt_to_equity=round(borrowings / (eq_cap + reserves), 2),
                       interest_coverage=10.0, asset_turnover=1.0, free_cash_flow_cr=cfo + inv,
                       capex_cr=-inv, earnings_per_share=round(net_profit / 10, 2),
                       book_value_per_share=50.0, dividend_payout_ratio_pct=20.0,
                       total_debt_cr=borrowings, cash_from_operations_cr=cfo,
                       revenue_cagr_5yr=growth * 100, pat_cagr_5yr=growth * 100,
                       eps_cagr_5yr=growth * 100, composite_quality_score=60.0))
        mc.append(dict(company_id=cid, year=str(y), market_cap_crore=sales * 10, enterprise_value_crore=sales * 10.5,
                       pe_ratio=20.0, pb_ratio=3.0, ev_ebitda=12.0, dividend_yield_pct=1.0))

    return pl, bs, cf, fr, mc


def build_tables(companies):
    """companies: list of (company_id, sector, sub_sector, kwargs for make_company)."""

    pl, bs, cf, fr, mc = [], [], [], [], []
    for cid, _sector, _sub, kwargs in companies:
        rows = make_company(cid, **kwargs)
        for acc, new in zip((pl, bs, cf, fr, mc), rows):
            acc.extend(new)

    return {
        "companies": pd.DataFrame({
            "id": [c[0] for c in companies],
            "company_name": [f"{c[0]} Limited" for c in companies],
        }),
        "sectors": pd.DataFrame({
            "company_id": [c[0] for c in companies],
            "broad_sector": [c[1] for c in companies],
            "sub_sector": [c[2] for c in companies],
            "market_cap_category": "Large Cap",
        }),
        "peer_groups": pd.DataFrame({
            "peer_group_name": ["Tech"] * 3,
            "company_id": ["A", "B", "C"],
            "is_benchmark": [1, 0, 0],
        }),
        "profitandloss": pd.DataFrame(pl),
        "balancesheet": pd.DataFrame(bs),
        "cashflow": pd.DataFrame(cf),
        "financial_ratios": pd.DataFrame(fr),
        "market_cap": pd.DataFrame(mc),
        "stock_prices": pd.DataFrame({
            "company_id": ["A"], "date": ["2024-03-28"], "open_price": [10.0], "high_price": [12.0],
            "low_price": [9.0], "close_price": [11.0], "volume": [1000], "adjusted_close": [11.0],
        }),
    }


@pytest.fixture
def synthetic_tables():
    """A, B, C industrial (curated group 'Tech'); D industrial without a curated group;
    F1, F2, F3 financials; Z alone in its sector."""

    return build_tables([
        ("A", "Industrials", "Software", dict(growth=0.15, npm=0.20, opm=0.28, borrowings=50.0, interest=5.0, cfo_ratio=1.1)),
        ("B", "Industrials", "Software", dict(growth=0.10, npm=0.15, opm=0.22, borrowings=150.0, interest=15.0, cfo_ratio=0.9)),
        ("C", "Industrials", "Software", dict(growth=0.05, npm=0.08, opm=0.12, borrowings=400.0, interest=40.0, cfo_ratio=0.6)),
        ("D", "Industrials", "Machinery", dict(growth=0.08, npm=0.10, opm=0.15, borrowings=100.0, interest=10.0)),
        ("F1", "Financials", "Banks", dict(growth=0.12, npm=0.18, opm=0.30, borrowings=3000.0, interest=300.0)),
        ("F2", "Financials", "Banks", dict(growth=0.09, npm=0.14, opm=0.25, borrowings=3500.0, interest=350.0)),
        ("F3", "Financials", "Banks", dict(growth=0.15, npm=0.22, opm=0.33, borrowings=2800.0, interest=280.0)),
        ("Z", "Real Estate", "Developers", dict()),
    ])


@pytest.fixture(scope="session")
def real_bundle():
    if not DB_PATH.exists():
        pytest.skip("db/nifty100.db not available")

    from src.analytics.platform_data import build_bundle

    return build_bundle(DB_PATH)
