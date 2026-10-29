import sqlite3
import pandas as pd


DB_PATH = "db/nifty100.db"


def generate_capital_allocation():

    conn = sqlite3.connect(DB_PATH)


    # Profit & Loss Data
    pnl = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            dividend_payout,
            net_profit
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
            borrowings
        FROM balancesheet
        """,
        conn
    )


    # Cash Flow Data
    cf = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity
        FROM cashflow
        """,
        conn
    )


    # Merge all data
    df = pnl.merge(
        bs,
        on=["company_id", "year"],
        how="inner"
    )


    df = df.merge(
        cf,
        on=["company_id", "year"],
        how="inner"
    )


    # Calculate CapEx
    df["capex"] = -df["investing_activity"]


    # Free Cash Flow
    df["free_cash_flow"] = (
        df["operating_activity"]
        -
        df["capex"]
    )


    # Select final columns
    result = df[
        [
            "company_id",
            "year",
            "net_profit",
            "dividend_payout",
            "borrowings",
            "operating_activity",
            "capex",
            "free_cash_flow"
        ]
    ]


    # Save CSV
    output = "output/capital_allocation.csv"

    result.to_csv(
        output,
        index=False
    )


    print("✅ Capital Allocation Report Generated Successfully")
    print(f"Saved: {output}")
    print(f"Total Records: {len(result)}")


if __name__ == "__main__":
    generate_capital_allocation()