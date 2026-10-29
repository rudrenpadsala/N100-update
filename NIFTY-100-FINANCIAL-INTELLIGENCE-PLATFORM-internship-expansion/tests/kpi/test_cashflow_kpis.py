from src.analytics.cashflow_kpis import (
    free_cash_flow,
    fcf_conversion_rate,
    cfo_quality_score,
    capex_intensity,
    capital_allocation_pattern
)


# --------------------------------------------------
# Test 1
# --------------------------------------------------

def test_free_cash_flow():

    assert free_cash_flow(
        500,
        -200
    ) == 300


# --------------------------------------------------
# Test 2
# --------------------------------------------------

def test_negative_fcf():

    assert free_cash_flow(
        300,
        -500
    ) == -200


# --------------------------------------------------
# Test 3
# --------------------------------------------------

def test_fcf_conversion():

    assert fcf_conversion_rate(
        300,
        600
    ) == 50.0


# --------------------------------------------------
# Test 4
# --------------------------------------------------

def test_fcf_zero_profit():

    assert fcf_conversion_rate(
        300,
        0
    ) is None


# --------------------------------------------------
# Test 5
# --------------------------------------------------

def test_cfo_quality():

    score, label = cfo_quality_score(
        1200,
        1000
    )

    assert score == 1.2
    assert label == "High Quality"


# --------------------------------------------------
# Test 6
# --------------------------------------------------

def test_capex_intensity():

    intensity, label = capex_intensity(
        -150,
        1000
    )

    assert intensity == 15.0
    assert label == "Capital Intensive"


# --------------------------------------------------
# Test 7
# --------------------------------------------------

def test_reinvestor():

    _, _, _, pattern = capital_allocation_pattern(
        500,
        -200,
        -100
    )

    assert pattern == "Reinvestor"


# --------------------------------------------------
# Test 8
# --------------------------------------------------

def test_growth_debt():

    _, _, _, pattern = capital_allocation_pattern(
        -500,
        -200,
        100
    )

    assert pattern == "Growth Funded by Debt"