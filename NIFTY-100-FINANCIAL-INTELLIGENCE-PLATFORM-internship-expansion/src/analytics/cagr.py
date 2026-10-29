"""
cagr.py

Sprint 2
Day 10

CAGR Engine
"""

# --------------------------------------------------
# CAGR Formula
# --------------------------------------------------

def calculate_cagr(start_value, end_value, years):
    """
    CAGR Formula

    CAGR = ((End / Start)^(1/Years) - 1) × 100

    Edge Cases:
        Positive -> Positive
        Zero Base
        Turnaround
        Decline to Loss
        Both Negative
        Insufficient Years
    """

    if years is None or years <= 0:
        return None, "INVALID_YEARS"

    if start_value is None or end_value is None:
        return None, "MISSING_DATA"

    if years < 3:
        return None, "INSUFFICIENT"

    if start_value == 0:
        return None, "ZERO_BASE"

    if start_value > 0 and end_value < 0:
        return None, "DECLINE_TO_LOSS"

    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"

    if start_value < 0 and end_value < 0:
        return None, "BOTH_NEGATIVE"

    cagr = (
        ((end_value / start_value) ** (1 / years)) - 1
    ) * 100

    return round(cagr, 2), "OK"


# --------------------------------------------------
# Revenue CAGR
# --------------------------------------------------

def revenue_cagr(start_sales, end_sales, years):
    """
    Revenue CAGR
    """
    return calculate_cagr(
        start_sales,
        end_sales,
        years
    )


# --------------------------------------------------
# PAT CAGR
# --------------------------------------------------

def pat_cagr(start_pat, end_pat, years):
    """
    PAT CAGR
    """
    return calculate_cagr(
        start_pat,
        end_pat,
        years
    )


# --------------------------------------------------
# EPS CAGR
# --------------------------------------------------

def eps_cagr(start_eps, end_eps, years):
    """
    EPS CAGR
    """
    return calculate_cagr(
        start_eps,
        end_eps,
        years
    )


# --------------------------------------------------
# CAGR Flag Helpers
# --------------------------------------------------

def is_turnaround(flag):
    """
    Returns True if company moved
    from loss to profit.
    """
    return flag == "TURNAROUND"


def is_decline_to_loss(flag):
    """
    Returns True if company moved
    from profit to loss.
    """
    return flag == "DECLINE_TO_LOSS"


def is_zero_base(flag):
    """
    Returns True if CAGR
    cannot be calculated
    because starting value is zero.
    """
    return flag == "ZERO_BASE"


def is_both_negative(flag):
    """
    Returns True if both
    start and end values are negative.
    """
    return flag == "BOTH_NEGATIVE"


def is_insufficient(flag):
    """
    Returns True if
    less than required years exist.
    """
    return flag == "INSUFFICIENT"


def is_valid(flag):
    """
    Returns True if CAGR
    calculation is valid.
    """
    return flag == "OK"


