def test_capital_allocation():

    operating_cash_flow = 1200
    capex = 400

    free_cash_flow = operating_cash_flow - capex

    assert free_cash_flow == 800