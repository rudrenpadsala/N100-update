def test_fcf_calculation():

    operating_cash_flow = 1000
    capex = 300

    fcf = operating_cash_flow - capex

    assert fcf == 700



def test_cfo_quality():

    cfo = 1000
    profit = 800

    quality = cfo / profit

    assert round(quality,2) == 1.25