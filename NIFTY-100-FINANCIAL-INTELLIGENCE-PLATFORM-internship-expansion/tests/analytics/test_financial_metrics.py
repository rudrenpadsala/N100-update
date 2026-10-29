"""Latest-year indicators: formulas, history rules and bad-data guards."""

import numpy as np
import pandas as pd
import pytest

from src.analytics.financial_metrics import PLAUSIBLE_RANGE, build_metrics
from tests.conftest import build_tables


def row(metrics, cid):
    return metrics[metrics.company_id == cid].iloc[0]


def test_one_row_per_master_company(synthetic_tables):
    m = build_metrics(synthetic_tables)
    assert sorted(m.company_id) == ["A", "B", "C", "D", "F1", "F2", "F3", "Z"]
    assert (m.as_of_year == 2024).all()


def test_formulas_match_hand_calculation():
    tables = build_tables([("A", "Industrials", "X", dict(
        sales0=1000.0, growth=0.0, npm=0.10, opm=0.20, equity=500.0, borrowings=250.0,
        interest=20.0, cfo_ratio=1.2))])
    r = row(build_metrics(tables), "A")

    equity = 50.0 + (500.0 * 1.5 - 50.0)           # 2024 is year index 5 -> equity x 1.5
    assert r.sales == 1000.0 and r.net_profit == 100.0
    assert r.net_margin_pct == pytest.approx(10.0)
    assert r.operating_margin_pct == pytest.approx(20.0)
    assert r.roe_pct == pytest.approx(100.0 / equity * 100)
    assert r.debt_to_equity == pytest.approx(250.0 / equity)
    pbt = round(100.0 / 0.75, 2)                     # the fixture stores PBT to 2 decimals
    assert r.interest_coverage == pytest.approx((pbt + 20.0) / 20.0)
    assert r.cfo_to_pat == pytest.approx(1.2)
    assert r.asset_turnover == pytest.approx(1000.0 / (equity + 250.0 + 200.0))
    assert r.fcf == pytest.approx(120.0 - 50.0)     # CFO + investing


def test_cagr_uses_five_year_window(synthetic_tables):
    r = row(build_metrics(synthetic_tables), "A")
    assert r.revenue_cagr_pct == pytest.approx(15.0, abs=0.01)
    assert r.profit_cagr_pct == pytest.approx(15.0, abs=0.01)


def test_cagr_needs_three_years_of_history():
    tables = build_tables([("A", "Industrials", "X", dict(years=[2023, 2024]))])
    r = row(build_metrics(tables), "A")
    assert np.isnan(r.revenue_cagr_pct)
    assert "year" in r.metric_notes["revenue_cagr_pct"]


def test_profit_cagr_not_meaningful_for_negative_profit():
    tables = build_tables([("A", "Industrials", "X", dict(npm=-0.05))])
    r = row(build_metrics(tables), "A")
    assert np.isnan(r.profit_cagr_pct) and "not positive" in r.metric_notes["profit_cagr_pct"]
    assert np.isnan(r.cfo_to_pat) and "not positive" in r.metric_notes["cfo_to_pat"]


def test_zero_interest_marks_company_interest_free():
    tables = build_tables([("A", "Industrials", "X", dict(interest=0.0, borrowings=0.0))])
    r = row(build_metrics(tables), "A")
    assert bool(r.interest_free) and np.isnan(r.interest_coverage)


def test_implausible_roe_is_excluded_with_a_reason():
    tables = build_tables([("A", "Industrials", "X", dict(equity=0.6))])   # tiny equity -> huge ROE
    tables["balancesheet"].loc[:, "reserves"] = 0.1
    r = row(build_metrics(tables), "A")
    assert np.isnan(r.roe_pct)
    assert "plausible range" in r.metric_notes["roe_pct"]


def test_negative_net_worth_blocks_roe_and_leverage():
    tables = build_tables([("A", "Industrials", "X", dict())])
    tables["balancesheet"].loc[:, "reserves"] = -500.0
    r = row(build_metrics(tables), "A")
    assert np.isnan(r.roe_pct) and np.isnan(r.debt_to_equity)
    assert "net worth" in r.metric_notes["roe_pct"]


def test_missing_balance_sheet_for_latest_year_is_explained():
    tables = build_tables([("A", "Industrials", "X", dict())])
    tables["balancesheet"] = tables["balancesheet"].query("year != 'Mar 2024'")
    r = row(build_metrics(tables), "A")
    assert np.isnan(r.roe_pct) and "no balance sheet" in r.metric_notes["roe_pct"]


def test_company_without_profit_and_loss_gets_an_empty_row():
    tables = build_tables([("A", "Industrials", "X", dict()), ("B", "Industrials", "X", dict())])
    tables["profitandloss"] = tables["profitandloss"].query("company_id != 'B'")
    r = row(build_metrics(tables), "B")
    assert pd.isna(r.as_of_year) and pd.isna(r.roe_pct)


def test_half_year_balance_sheet_row_is_not_used():
    tables = build_tables([("A", "Industrials", "X", dict())])
    half = tables["balancesheet"].query("year == 'Mar 2024'").copy()
    half["year"] = "Sep 2024"
    half["borrowings"] = 99999.0
    tables["balancesheet"] = pd.concat([tables["balancesheet"], half], ignore_index=True)
    assert row(build_metrics(tables), "A").borrowings == 100.0


def test_label_variants_resolve_to_the_same_year():
    tables = build_tables([("A", "Industrials", "X", dict())])
    tables["cashflow"].loc[tables["cashflow"].year == "Mar 2024", "year"] = "Mar-24"
    assert row(build_metrics(tables), "A").cfo_to_pat == pytest.approx(1.0)


def test_plausible_ranges_are_ordered():
    for metric, (low, high) in PLAUSIBLE_RANGE.items():
        assert low < high, metric


def test_real_database_matches_stored_ratios(real_bundle):
    """Independent cross-check: our ROE / margins agree with the updated ratio table."""

    fr = real_bundle.tables["financial_ratios"]
    # Test against the latest available fiscal year (2026)
    fr_latest = fr[fr.year == "Mar 2026"].drop_duplicates("company_id").set_index("company_id")
    m = real_bundle.metrics.set_index("company_id")
    common = [c for c in m.index if c in fr_latest.index and m.loc[c, "as_of_year"] == 2026]

    assert len(common) > 80
    nm = (m.loc[common, "net_margin_pct"] - fr_latest.loc[common, "net_profit_margin_pct"]).abs()
    assert (nm.dropna() < 0.05).all()
    assert (m.loc[common, "debt_to_equity"].dropna() >= 0).all()
