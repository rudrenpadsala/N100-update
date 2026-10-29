import sqlite3
import pandas as pd


DB_PATH = "db/nifty100.db"


def calculate_debt_risk():

    conn = sqlite3.connect(DB_PATH)


    # Load Profit & Loss
    pnl = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            operating_profit,
            interest
        FROM profitandloss
        """,
        conn
    )


    # Load Balance Sheet
    bs = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            equity_capital,
            reserves,
            borrowings
        FROM balancesheet
        """,
        conn
    )


    # Merge data
    df = pnl.merge(
        bs,
        on=["company_id", "year"],
        how="inner"
    )


    # Calculate Equity
    df["shareholders_equity"] = (
        df["equity_capital"]
        +
        df["reserves"]
    )


    # Debt Equity Ratio
    df["de_ratio"] = (
        df["borrowings"]
        /
        df["shareholders_equity"]
    )


    # Interest Coverage Ratio
    df["icr"] = (
        df["operating_profit"]
        /
        df["interest"]
    )


    # D/E Risk Label
    def de_label(value):

        if value < 0.5:
            return "Low Debt"

        elif value <= 1.5:
            return "Moderate Debt"

        else:
            return "High Debt"


    df["de_flag"] = df["de_ratio"].apply(de_label)


    # ICR Risk Label
    def icr_label(value):

        if value > 5:
            return "Safe"

        elif value >= 2:
            return "Watch"

        else:
            return "Risk"


    df["icr_label"] = df["icr"].apply(icr_label)


    # Remove infinite values
    df.replace(
        [float("inf"), -float("inf")],
        None,
        inplace=True
    )


    # Output columns
    result = df[
        [
            "company_id",
            "year",
            "borrowings",
            "shareholders_equity",
            "de_ratio",
            "de_flag",
            "operating_profit",
            "interest",
            "icr",
            "icr_label"
        ]
    ]


    # Save CSV
    output = "output/debt_risk_analysis.csv"

    result.to_csv(
        output,
        index=False
    )


    print("✅ Debt Risk Analysis Generated Successfully")
    print(f"Saved: {output}")
    print(f"Total Records: {len(result)}")


if __name__ == "__main__":
    calculate_debt_risk()