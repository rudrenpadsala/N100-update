"""
test_dq_rules.py

Sprint 6
Day 41

Unit tests for the DQ-01 through DQ-16 data quality rules
in src/etl/dq_rules.py.
"""

import pandas as pd

from src.etl.dq_rules import (
    dq01_primary_key,
    dq02_company_year,
    dq03_foreign_key,
    dq04_balance_sheet,
    dq05_opm,
    dq06_positive_sales,
    dq07_positive_expenses,
    dq08_net_profit,
    dq09_missing_year,
    dq10_future_year,
    dq11_cashflow,
    dq12_website,
    dq13_stock_price,
    dq14_sector,
    dq15_market_cap,
    dq16_duplicate_company,
)


def test_dq01_primary_key_flags_duplicates():
    df = pd.DataFrame({"id": [1, 2, 2, 3]})
    failures = dq01_primary_key(df, "profitandloss")
    assert len(failures) == 1
    assert failures[0]["rule"] == "DQ-01"


def test_dq01_primary_key_passes_when_unique():
    df = pd.DataFrame({"id": [1, 2, 3]})
    assert dq01_primary_key(df, "profitandloss") == []


def test_dq02_company_year_flags_duplicates():
    df = pd.DataFrame(
        {
            "company_id": ["ABB", "ABB", "TCS"],
            "year": ["Mar 2020", "Mar 2020", "Mar 2020"],
        }
    )
    failures = dq02_company_year(df, "profitandloss")
    assert len(failures) == 2
    assert all(f["rule"] == "DQ-02" for f in failures)


def test_dq02_company_year_passes_when_unique():
    df = pd.DataFrame({"company_id": ["ABB", "TCS"], "year": ["Mar 2020", "Mar 2020"]})
    assert dq02_company_year(df, "profitandloss") == []


def test_dq03_foreign_key_flags_unknown_company():
    df = pd.DataFrame({"company_id": ["ABB", "GHOST"]})
    companies = pd.DataFrame({"id": ["ABB", "TCS"]})
    failures = dq03_foreign_key(df, companies, "profitandloss")
    assert len(failures) == 1
    assert "GHOST" in failures[0]["message"]


def test_dq03_foreign_key_is_case_insensitive():
    df = pd.DataFrame({"company_id": ["abb"]})
    companies = pd.DataFrame({"id": ["ABB"]})
    assert dq03_foreign_key(df, companies, "profitandloss") == []


def test_dq04_balance_sheet_flags_mismatch():
    df = pd.DataFrame({"total_assets": [1000.0], "total_liabilities": [800.0]})
    failures = dq04_balance_sheet(df)
    assert len(failures) == 1
    assert failures[0]["severity"] == "WARNING"


def test_dq04_balance_sheet_passes_within_tolerance():
    df = pd.DataFrame({"total_assets": [1000.0], "total_liabilities": [999.0]})
    assert dq04_balance_sheet(df) == []


def test_dq04_balance_sheet_skips_zero_assets():
    df = pd.DataFrame({"total_assets": [0.0], "total_liabilities": [50.0]})
    assert dq04_balance_sheet(df) == []


def test_dq05_opm_flags_incorrect_margin():
    df = pd.DataFrame(
        {"sales": [100.0], "operating_profit": [20.0], "opm_percentage": [5.0]}
    )
    failures = dq05_opm(df)
    assert len(failures) == 1
    assert "Expected 20.0" in failures[0]["message"]


def test_dq05_opm_passes_when_correct():
    df = pd.DataFrame(
        {"sales": [100.0], "operating_profit": [20.0], "opm_percentage": [20.0]}
    )
    assert dq05_opm(df) == []


def test_dq06_positive_sales_flags_non_positive():
    df = pd.DataFrame({"sales": [100.0, 0.0, -5.0]})
    failures = dq06_positive_sales(df)
    assert len(failures) == 2


def test_dq07_positive_expenses_flags_negative():
    df = pd.DataFrame({"expenses": [100.0, -1.0]})
    failures = dq07_positive_expenses(df)
    assert len(failures) == 1


def test_dq08_net_profit_flags_missing():
    df = pd.DataFrame({"net_profit": [100.0, None]})
    failures = dq08_net_profit(df)
    assert len(failures) == 1


def test_dq09_missing_year_flags_null_year():
    df = pd.DataFrame({"year": ["Mar 2020", None]})
    failures = dq09_missing_year(df, "cashflow")
    assert len(failures) == 1


def test_dq10_future_year_flags_year_beyond_current():
    df = pd.DataFrame({"year": [2020, 2099]})
    failures = dq10_future_year(df, "profitandloss")
    assert len(failures) == 1
    assert "2099" in failures[0]["message"]


def test_dq10_future_year_passes_for_past_years():
    df = pd.DataFrame({"year": [2020, 2021]})
    assert dq10_future_year(df, "profitandloss") == []


def test_dq11_cashflow_flags_missing_net_cash_flow():
    df = pd.DataFrame({"net_cash_flow": [100.0, None]})
    failures = dq11_cashflow(df)
    assert len(failures) == 1


def test_dq12_website_flags_missing():
    df = pd.DataFrame({"website": ["https://x.com", None]})
    failures = dq12_website(df)
    assert len(failures) == 1


def test_dq13_stock_price_flags_missing_close_price():
    df = pd.DataFrame({"close_price": [100.0, None]})
    failures = dq13_stock_price(df)
    assert len(failures) == 1


def test_dq14_sector_flags_missing_broad_sector():
    df = pd.DataFrame({"broad_sector": ["IT", None]})
    failures = dq14_sector(df)
    assert len(failures) == 1


def test_dq15_market_cap_flags_missing_value():
    df = pd.DataFrame({"market_cap_crore": [500.0, None]})
    failures = dq15_market_cap(df)
    assert len(failures) == 1


def test_dq16_duplicate_company_flags_duplicate_name():
    df = pd.DataFrame({"company_name": ["ABB Ltd", "ABB Ltd", "TCS Ltd"]})
    failures = dq16_duplicate_company(df)
    assert len(failures) == 1
    assert failures[0]["severity"] == "CRITICAL"


def test_all_rules_return_empty_list_when_column_absent():
    """
    Every rule should degrade gracefully (no crash, no
    false positives) when its target column is missing
    from the dataset being checked.
    """
    df = pd.DataFrame({"unrelated_column": [1, 2, 3]})

    assert dq01_primary_key(df, "x") == []
    assert dq02_company_year(df, "x") == []
    assert dq03_foreign_key(df, pd.DataFrame({"id": []}), "x") == []
    assert dq04_balance_sheet(df) == []
    assert dq05_opm(df) == []
    assert dq06_positive_sales(df) == []
    assert dq07_positive_expenses(df) == []
    assert dq08_net_profit(df) == []
    assert dq09_missing_year(df, "x") == []
    assert dq10_future_year(df, "x") == []
    assert dq11_cashflow(df) == []
    assert dq12_website(df) == []
    assert dq13_stock_price(df) == []
    assert dq14_sector(df) == []
    assert dq15_market_cap(df) == []
    assert dq16_duplicate_company(df) == []
