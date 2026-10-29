import pytest

from src.analytics.ratios import (
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    icr_label,
    icr_warning_flag,
    net_debt,
    asset_turnover
)


# --------------------------------------------------
# Test 1
# Debt-to-Equity Normal
# --------------------------------------------------

def test_debt_to_equity():

    assert debt_to_equity(
        500,
        1000,
        1000
    ) == 0.25


# --------------------------------------------------
# Test 2
# Debt Free
# --------------------------------------------------

def test_debt_free():

    assert debt_to_equity(
        0,
        1000,
        1000
    ) == 0


# --------------------------------------------------
# Test 3
# High Leverage Flag
# --------------------------------------------------

def test_high_leverage():

    assert high_leverage_flag(
        6,
        "Technology"
    ) is True


# --------------------------------------------------
# Test 4
# Financial Company
# --------------------------------------------------

def test_financial_company():

    assert high_leverage_flag(
        6,
        "Financials"
    ) is False


# --------------------------------------------------
# Test 5
# Interest Coverage Ratio
# --------------------------------------------------

def test_interest_coverage():

    assert interest_coverage_ratio(
        500,
        100,
        100
    ) == 6.0


# --------------------------------------------------
# Test 6
# Debt Free Label
# --------------------------------------------------

def test_icr_label():

    assert icr_label(None) == "Debt Free"


# --------------------------------------------------
# Test 7
# Net Debt
# --------------------------------------------------

def test_net_debt():

    assert net_debt(
        1000,
        300
    ) == 700


# --------------------------------------------------
# Test 8
# Asset Turnover
# --------------------------------------------------

def test_asset_turnover():

    assert asset_turnover(
        2000,
        1000
    ) == 2.0