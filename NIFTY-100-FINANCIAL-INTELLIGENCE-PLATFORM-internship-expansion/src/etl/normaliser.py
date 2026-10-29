"""
normaliser.py

Normalize data before loading into database.
"""

import pandas as pd


def normalize_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize year column.

    Example:
    FY2022 -> 2022
    2024* -> 2024
    """

    if "year" in df.columns:

        df["year"] = (
            df["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
        )

        df["year"] = pd.to_numeric(
            df["year"],
            errors="coerce"
        )

        df["year"] = df["year"].astype("Int64")

    return df


def normalize_ticker(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize ticker symbols.
    """

    ticker_columns = [
        "ticker",
        "symbol",
        "stock_symbol",
        "nse_symbol"
    ]

    for col in ticker_columns:

        if col in df.columns:

            df[col] = (
                df[col]
                .astype(str)
                .str.upper()
                .str.strip()
            )

    return df


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    df = normalize_year(df)

    df = normalize_ticker(df)

    return df