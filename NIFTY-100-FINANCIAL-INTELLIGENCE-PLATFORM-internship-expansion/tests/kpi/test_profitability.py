import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    opm_cross_check,
    return_on_equity,
    return_on_capital_employed,
    roce_benchmark,
    return_on_assets
)


# --------------------------------------------------
# Test 1
# Net Profit Margin - Normal Case
# --------------------------------------------------

def test_net_profit_margin():

    assert net_profit_margin(200, 1000) == 20.0


# --------------------------------------------------
# Test 2
# Net Profit Margin - Sales = 0
# --------------------------------------------------

def test_net_profit_margin_zero_sales():

    assert net_profit_margin(200, 0) is None


# --------------------------------------------------
# Test 3
# Operating Profit Margin
# --------------------------------------------------

def test_operating_profit_margin():

    assert operating_profit_margin(300, 1000) == 30.0


# --------------------------------------------------
# Test 4
# OPM Cross Check
# --------------------------------------------------

def test_opm_cross_check():

    assert opm_cross_check(30, 35) is False


# --------------------------------------------------
# Test 5
# ROE Normal
# --------------------------------------------------

def test_return_on_equity():

    assert return_on_equity(200, 500, 500) == 20.0


# --------------------------------------------------
# Test 6
# ROE Negative Equity
# --------------------------------------------------

def test_return_on_equity_negative():

    assert return_on_equity(100, -100, -50) is None


# --------------------------------------------------
# Test 7
# ROCE
# --------------------------------------------------

def test_return_on_capital_employed():

    assert return_on_capital_employed(
        300,
        500,
        500,
        500
    ) == 20.0


# --------------------------------------------------
# Test 8
# ROA
# --------------------------------------------------

def test_return_on_assets():

    assert return_on_assets(200, 1000) == 20.0


# --------------------------------------------------
# Debt-to-Equity Ratio
# --------------------------------------------------

def debt_to_equity(
    borrowings,
    equity_capital,
    reserves
):
    """
    Debt-to-Equity Ratio

    Formula:
        Borrowings / (Equity Capital + Reserves)

    Rules:
        • Return 0 if borrowings = 0
        • Return None if equity <= 0
        • Round to 2 decimal places
    """

    if borrowings is None:
        return None

    if borrowings == 0:
        return 0

    if equity_capital is None or reserves is None:
        return None

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return round(
        borrowings / equity,
        2
    )

# --------------------------------------------------
# High Leverage Flag
# --------------------------------------------------

def high_leverage_flag(
    debt_equity,
    broad_sector
):
    """
    High leverage check.

    Financial companies are excluded.

    Returns:
        True / False
    """

    if debt_equity is None:
        return False

    if broad_sector == "Financials":
        return False

    return debt_equity > 5