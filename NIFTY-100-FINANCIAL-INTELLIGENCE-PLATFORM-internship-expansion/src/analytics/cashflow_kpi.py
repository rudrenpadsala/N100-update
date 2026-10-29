import sqlite3
import pandas as pd


DB_PATH = "db/nifty100.db"


def calculate_cashflow_kpis():

    conn = sqlite3.connect(DB_PATH)


    # Load Cashflow Data
    cashflow = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity,
            net_cash_flow
        FROM cashflow
        """,
        conn
    )


    # Load Profit & Loss Data
    pnl = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            sales,
            net_profit
        FROM profitandloss
        """,
        conn
    )


    # Merge Data
    df = cashflow.merge(
        pnl,
        on=["company_id", "year"],
        how="inner"
    )


    # Convert Investing Activity into CapEx
    df["capex"] = -df["investing_activity"]


    # Free Cash Flow
    df["free_cash_flow"] = (
        df["operating_activity"]
        -
        df["capex"]
    )


    # CFO Quality
    df["cfo_quality"] = (
        df["operating_activity"]
        /
        df["net_profit"]
    )


    # CapEx Intensity
    df["capex_intensity"] = (
        df["capex"]
        /
        df["sales"]
    )


    # FCF Conversion
    df["fcf_conversion"] = (
        df["free_cash_flow"]
        /
        df["net_profit"]
    )


    # Remove infinite values
    df.replace(
        [float("inf"), -float("inf")],
        None,
        inplace=True
    )


    # Final Output
    result = df[
        [
            "company_id",
            "year",
            "operating_activity",
            "capex",
            "free_cash_flow",
            "net_profit",
            "cfo_quality",
            "capex_intensity",
            "fcf_conversion"
        ]
    ]


    # Save CSV
    output = "output/cashflow_kpis.csv"

    result.to_csv(
        output,
        index=False
    )


    print("✅ Cash Flow KPI Analysis Generated Successfully")
    print(f"Saved: {output}")
    print(f"Total Records: {len(result)}")


if __name__ == "__main__":
    calculate_cashflow_kpis()