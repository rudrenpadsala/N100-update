import sqlite3
import pandas as pd


DB_PATH = "db/nifty100.db"


def calculate_roce():

    conn = sqlite3.connect(DB_PATH)

    # Profit and Loss Data
    pnl = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            operating_profit
        FROM profitandloss
        """,
        conn
    )


    # Balance Sheet Data
    bs = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            equity_capital,
            reserves,
            borrowings,
            total_assets,
            total_liabilities
        FROM balancesheet
        """,
        conn
    )


    # Merge P&L and Balance Sheet
    df = pnl.merge(
        bs,
        on=["company_id", "year"],
        how="inner"
    )


    # Calculate Current Liabilities
    df["current_liabilities"] = (
        df["total_liabilities"]
        - df["equity_capital"]
        - df["reserves"]
        - df["borrowings"]
    )


    # Calculate Capital Employed
    df["capital_employed"] = (
        df["total_assets"]
        - df["current_liabilities"]
    )


    # Calculate ROCE
    df["roce_percentage"] = (
        df["operating_profit"]
        /
        df["capital_employed"]
    ) * 100


    # Remove invalid values
    df.replace(
        [float("inf"), -float("inf")],
        None,
        inplace=True
    )


    # Select final columns
    result = df[
        [
            "company_id",
            "year",
            "operating_profit",
            "capital_employed",
            "roce_percentage"
        ]
    ]


    # Save output
    output_file = "output/roce_analysis.csv"

    result.to_csv(
        output_file,
        index=False
    )


    print("✅ ROCE Analysis Generated Successfully")
    print(f"Saved: {output_file}")
    print(f"Total Records: {len(result)}")


if __name__ == "__main__":
    calculate_roce()