def test_de_ratio():

    borrowings = 1000
    equity = 2000

    de_ratio = borrowings / equity

    assert de_ratio == 0.5



def test_de_flag():

    de_ratio = 0.3

    if de_ratio < 0.5:
        label = "Low Debt"

    assert label == "Low Debt"