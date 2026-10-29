import pandas as pd

from src.etl.normaliser import (
    normalize_year,
    normalize_ticker
)


def test_normalize_year_1():

    df = pd.DataFrame({"year": ["FY2022"]})

    df = normalize_year(df)

    assert df["year"][0] == 2022


def test_normalize_year_2():

    df = pd.DataFrame({"year": ["2023"]})

    df = normalize_year(df)

    assert df["year"][0] == 2023


def test_normalize_year_3():

    df = pd.DataFrame({"year": ["2024*"]})

    df = normalize_year(df)

    assert df["year"][0] == 2024


def test_normalize_year_4():

    df = pd.DataFrame({"year": [None]})

    df = normalize_year(df)

    assert pd.isna(df["year"][0])


def test_normalize_year_5():

    df = pd.DataFrame({"year": ["abcd"]})

    df = normalize_year(df)

    assert pd.isna(df["year"][0])


def test_ticker_uppercase():

    df = pd.DataFrame({

        "ticker": [

            "tcs",
            "infy"

        ]

    })

    df = normalize_ticker(df)

    assert df["ticker"].tolist() == [

        "TCS",
        "INFY"

    ]


def test_ticker_spaces():

    df = pd.DataFrame({

        "ticker": [

            " tcs ",
            " reliance "

        ]

    })

    df = normalize_ticker(df)

    assert df["ticker"].tolist() == [

        "TCS",
        "RELIANCE"

    ]


def test_symbol_column():

    df = pd.DataFrame({

        "symbol": [

            "hdfc",
            "icici"

        ]

    })

    df = normalize_ticker(df)

    assert df["symbol"].tolist() == [

        "HDFC",
        "ICICI"

    ]

# ==========================================
# Additional normalize_year() Tests
# ==========================================

def test_normalize_year_6():

    df = pd.DataFrame({"year": ["FY2018"]})

    df = normalize_year(df)

    assert df["year"][0] == 2018


def test_normalize_year_7():

    df = pd.DataFrame({"year": ["FY2019"]})

    df = normalize_year(df)

    assert df["year"][0] == 2019


def test_normalize_year_8():

    df = pd.DataFrame({"year": ["2020 "]})

    df = normalize_year(df)

    assert df["year"][0] == 2020


def test_normalize_year_9():

    df = pd.DataFrame({"year": [" 2021"]})

    df = normalize_year(df)

    assert df["year"][0] == 2021


def test_normalize_year_10():

    df = pd.DataFrame({"year": ["FY2025"]})

    df = normalize_year(df)

    assert df["year"][0] == 2025


def test_normalize_year_11():

    df = pd.DataFrame({"year": ["2017*"]})

    df = normalize_year(df)

    assert df["year"][0] == 2017


def test_normalize_year_12():

    df = pd.DataFrame({"year": ["2016.0"]})

    df = normalize_year(df)

    assert df["year"][0] == 2016


def test_normalize_year_13():

    df = pd.DataFrame({"year": ["FY2015*"]})

    df = normalize_year(df)

    assert df["year"][0] == 2015


def test_normalize_year_14():

    df = pd.DataFrame({"year": ["2014 "]})

    df = normalize_year(df)

    assert df["year"][0] == 2014


def test_normalize_year_15():

    df = pd.DataFrame({"year": ["2013"]})

    df = normalize_year(df)

    assert df["year"][0] == 2013


def test_normalize_year_16():

    df = pd.DataFrame({"year": ["FY2012"]})

    df = normalize_year(df)

    assert df["year"][0] == 2012


def test_normalize_year_17():

    df = pd.DataFrame({"year": ["2011*"]})

    df = normalize_year(df)

    assert df["year"][0] == 2011


def test_normalize_year_18():

    df = pd.DataFrame({"year": ["2010"]})

    df = normalize_year(df)

    assert df["year"][0] == 2010


def test_normalize_year_19():

    df = pd.DataFrame({"year": ["2009"]})

    df = normalize_year(df)

    assert df["year"][0] == 2009


def test_normalize_year_20():

    df = pd.DataFrame({"year": ["2008"]})

    df = normalize_year(df)

    assert df["year"][0] == 2008


# ==========================================
# Additional normalize_ticker() Tests
# ==========================================

def test_ticker_4():

    df = pd.DataFrame({"ticker": ["TCS"]})

    df = normalize_ticker(df)

    assert df["ticker"][0] == "TCS"


def test_ticker_5():

    df = pd.DataFrame({"ticker": ["infosys"]})

    df = normalize_ticker(df)

    assert df["ticker"][0] == "INFOSYS"


def test_ticker_6():

    df = pd.DataFrame({"ticker": [" hdfcbank "]})

    df = normalize_ticker(df)

    assert df["ticker"][0] == "HDFCBANK"


def test_ticker_7():

    df = pd.DataFrame({"ticker": ["icicibank"]})

    df = normalize_ticker(df)

    assert df["ticker"][0] == "ICICIBANK"


def test_ticker_8():

    df = pd.DataFrame({"ticker": ["sbin"]})

    df = normalize_ticker(df)

    assert df["ticker"][0] == "SBIN"


def test_ticker_9():

    df = pd.DataFrame({"ticker": ["lt"]})

    df = normalize_ticker(df)

    assert df["ticker"][0] == "LT"


def test_ticker_10():

    df = pd.DataFrame({"ticker": ["asianpaint"]})

    df = normalize_ticker(df)

    assert df["ticker"][0] == "ASIANPAINT"


def test_ticker_11():

    df = pd.DataFrame({"ticker": [" tatamotors "]})

    df = normalize_ticker(df)

    assert df["ticker"][0] == "TATAMOTORS"


def test_ticker_12():

    df = pd.DataFrame({"symbol": ["nestleind"]})

    df = normalize_ticker(df)

    assert df["symbol"][0] == "NESTLEIND"


def test_ticker_13():

    df = pd.DataFrame({"symbol": ["itc"]})

    df = normalize_ticker(df)

    assert df["symbol"][0] == "ITC"


def test_ticker_14():

    df = pd.DataFrame({"symbol": [" sunpharma "]})

    df = normalize_ticker(df)

    assert df["symbol"][0] == "SUNPHARMA"


def test_ticker_15():

    df = pd.DataFrame({"symbol": ["ultracemco"]})

    df = normalize_ticker(df)

    assert df["symbol"][0] == "ULTRACEMCO"