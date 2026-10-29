"""
test_clustering.py

Sprint 6
Day 41

Unit tests for src/analytics/clustering.py.
"""

import pandas as pd

from src.analytics.clustering import (
    CLUSTER_FEATURES,
    compute_fcf_cagr,
    impute_by_sector_median,
    parse_period,
)


def test_parse_period_handles_full_month_year_format():
    assert parse_period("Mar 2014") == (2014, 3)


def test_parse_period_handles_hyphenated_short_year_format():
    assert parse_period("Mar-14") == (2014, 3)


def test_parse_period_handles_december():
    assert parse_period("Dec 2012") == (2012, 12)


def test_parse_period_returns_none_for_garbage():
    assert parse_period("not-a-period") is None


def test_parse_period_returns_none_for_non_string():
    assert parse_period(None) is None


def test_compute_fcf_cagr_positive_growth():
    company_df = pd.DataFrame(
        {"period": [(2018, 3), (2023, 3)], "free_cash_flow_cr": [100.0, 200.0]}
    )
    cagr = compute_fcf_cagr(company_df)
    assert cagr is not None
    assert cagr > 0


def test_compute_fcf_cagr_returns_none_with_insufficient_data():
    company_df = pd.DataFrame({"period": [(2023, 3)], "free_cash_flow_cr": [100.0]})
    assert compute_fcf_cagr(company_df) is None


def test_impute_by_sector_median_fills_missing_values():
    df = pd.DataFrame(
        {
            "broad_sector": ["IT", "IT", "IT"],
            "return_on_equity_pct": [10.0, None, 30.0],
            "debt_to_equity": [0.1, 0.2, 0.3],
            "revenue_cagr_5yr": [5.0, 6.0, 7.0],
            "fcf_cagr_5yr": [1.0, 2.0, 3.0],
            "operating_profit_margin_pct": [10.0, 20.0, 30.0],
        }
    )

    result = impute_by_sector_median(df)

    assert result["return_on_equity_pct"].isnull().sum() == 0
    assert result.loc[1, "return_on_equity_pct"] == 20.0


def test_impute_by_sector_median_falls_back_to_global_median():
    # "Finance" has no non-null return_on_equity_pct values at
    # all, so its members must fall back to the global median
    # (computed across every sector) rather than stay null.
    df = pd.DataFrame(
        {
            "broad_sector": ["IT", "IT", "Finance"],
            "return_on_equity_pct": [10.0, 20.0, None],
            "debt_to_equity": [0.1, 0.2, 0.3],
            "revenue_cagr_5yr": [5.0, 6.0, 7.0],
            "fcf_cagr_5yr": [1.0, 2.0, 3.0],
            "operating_profit_margin_pct": [10.0, 20.0, 30.0],
        }
    )

    result = impute_by_sector_median(df)

    assert result["return_on_equity_pct"].isnull().sum() == 0
    assert result.loc[2, "return_on_equity_pct"] == 15.0


def test_cluster_features_list_matches_specification():
    assert CLUSTER_FEATURES == [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]
