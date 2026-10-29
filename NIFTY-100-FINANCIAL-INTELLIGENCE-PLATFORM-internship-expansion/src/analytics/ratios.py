"""
ratios.py

Financial Ratio Engine
Sprint 2 - Day 08

Profitability Ratios
"""

# --------------------------------------------------
# Net Profit Margin
# --------------------------------------------------

def net_profit_margin(net_profit, sales):
    """
    Net Profit Margin (%)

    Formula:
        (Net Profit / Sales) × 100

    Rules:
        • Return None if sales is 0 or None.
        • Round result to 2 decimal places.
    """

    if sales is None:
        return None

    if sales == 0:
        return None

    return round((net_profit / sales) * 100, 2)


# --------------------------------------------------
# Operating Profit Margin
# --------------------------------------------------

def operating_profit_margin(operating_profit, sales):
    """
    Operating Profit Margin (%)

    Formula:
        (Operating Profit / Sales) × 100

    Rules:
        • Return None if sales is 0 or None.
        • Round result to 2 decimal places.
    """

    if sales is None:
        return None

    if sales == 0:
        return None

    return round((operating_profit / sales) * 100, 2)


# --------------------------------------------------
# OPM Cross Check
# --------------------------------------------------

def opm_cross_check(calculated_opm, source_opm):
    """
    Compare calculated OPM with source OPM.

    Returns:
        True  -> Difference <= 1%
        False -> Difference > 1%
    """

    if calculated_opm is None:
        return False

    if source_opm is None:
        return False

    difference = abs(calculated_opm - source_opm)

    return difference <= 1


# --------------------------------------------------
# Return on Equity (ROE)
# --------------------------------------------------

def return_on_equity(net_profit, equity_capital, reserves):
    """
    Return on Equity (ROE)

    Formula:
        Net Profit / (Equity Capital + Reserves) × 100

    Rules:
        • Return None if:
            - equity_capital is None
            - reserves is None
            - (equity + reserves) <= 0
        • Round result to 2 decimal places.
    """

    if equity_capital is None:
        return None

    if reserves is None:
        return None

    equity = equity_capital + reserves

    if equity <= 0:
        return None

    return round((net_profit / equity) * 100, 2)


# --------------------------------------------------
# Return on Capital Employed (ROCE)
# --------------------------------------------------

def return_on_capital_employed(
    ebit,
    equity_capital,
    reserves,
    borrowings
):
    """
    Return on Capital Employed (ROCE)

    Formula:
        EBIT / (Equity Capital + Reserves + Borrowings) × 100

    Rules:
        • Return None if capital employed <= 0.
        • Round result to 2 decimal places.
    """

    if equity_capital is None:
        return None

    if reserves is None:
        return None

    if borrowings is None:
        return None

    capital_employed = (
        equity_capital +
        reserves +
        borrowings
    )

    if capital_employed <= 0:
        return None

    return round(
        (ebit / capital_employed) * 100,
        2
    )


# --------------------------------------------------
# Financial Sector ROCE Check
# --------------------------------------------------

def roce_benchmark(roce, broad_sector):
    """
    ROCE benchmark check.

    Financial companies are evaluated
    differently from other sectors.

    Returns:
        Financial Sector
        Excellent
        Good
        Average
        Poor
    """

    if roce is None:
        return None

    if broad_sector == "Financials":
        return "Financial Sector"

    if roce >= 20:
        return "Excellent"

    if roce >= 15:
        return "Good"

    if roce >= 10:
        return "Average"

    return "Poor"

# --------------------------------------------------
# Return on Assets (ROA)
# --------------------------------------------------

def return_on_assets(net_profit, total_assets):
    """
    Return on Assets (ROA)

    Formula:
        Net Profit / Total Assets × 100

    Rules:
        • Return None if total_assets is None.
        • Return None if total_assets <= 0.
        • Round result to 2 decimal places.
    """

    if total_assets is None:
        return None

    if total_assets <= 0:
        return None

    return round(
        (net_profit / total_assets) * 100,
        2
    )
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



# --------------------------------------------------
# Interest Coverage Ratio (ICR)
# --------------------------------------------------

def interest_coverage_ratio(
    operating_profit,
    other_income,
    interest
):
    """
    Interest Coverage Ratio

    Formula:
        (Operating Profit + Other Income) / Interest

    Rules:
        • Return None if interest is 0 or None.
        • Round result to 2 decimal places.
    """

    if interest is None:
        return None

    if interest == 0:
        return None

    return round(
        (operating_profit + other_income) / interest,
        2
    )


# --------------------------------------------------
# ICR Label
# --------------------------------------------------

def icr_label(icr):
    """
    Display label for Interest Coverage Ratio.

    Returns:
        "Debt Free" if ICR is None
        "" otherwise
    """

    if icr is None:
        return "Debt Free"

    return ""


# --------------------------------------------------
# ICR Warning Flag
# --------------------------------------------------

def icr_warning_flag(icr):
    """
    Warning if ICR < 1.5
    """

    if icr is None:
        return False

    return icr < 1.5


# --------------------------------------------------
# Net Debt
# --------------------------------------------------

def net_debt(
    borrowings,
    investments
):
    """
    Net Debt

    Formula:
        Borrowings - Investments

    Rules:
        • Return None if borrowings or investments is None.
        • Round result to 2 decimal places.
    """

    if borrowings is None:
        return None

    if investments is None:
        return None

    return round(
        borrowings - investments,
        2
    )

# --------------------------------------------------
# Asset Turnover Ratio
# --------------------------------------------------

def asset_turnover(
    sales,
    total_assets
):
    """
    Asset Turnover

    Formula:
        Sales / Total Assets

    Rules:
        • Return None if total_assets <= 0.
        • Round result to 2 decimal places.
    """

    if total_assets is None:
        return None

    if total_assets <= 0:
        return None

    return round(
        sales / total_assets,
        2
    )
    