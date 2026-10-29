def test_roce_calculation():

    operating_profit = 500
    capital_employed = 2000

    roce = (operating_profit / capital_employed) * 100

    assert round(roce, 2) == 25.00