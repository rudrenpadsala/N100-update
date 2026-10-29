import sqlite3
import pandas as pd

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    debt_to_equity,
    interest_coverage_ratio,
    asset_turnover
)

from src.analytics.cashflow_kpis import (
    free_cash_flow
)

from src.analytics.cagr import (
    revenue_cagr,
    pat_cagr,
    eps_cagr
)

DB_PATH = "db/nifty100.db"


def main():

    print("=" * 60)
    print("Financial Ratio Engine")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    # ----------------------------------
    # Load Tables
    # ----------------------------------

    profit_loss = pd.read_sql(
        "SELECT * FROM profitandloss",
        conn
    )

    balance_sheet = pd.read_sql(
        "SELECT * FROM balancesheet",
        conn
    )

    cashflow = pd.read_sql(
        "SELECT * FROM cashflow",
        conn
    )

    print("✔ profitandloss :", len(profit_loss))
    print("✔ balancesheet  :", len(balance_sheet))
    print("✔ cashflow      :", len(cashflow))

    # ----------------------------------
    # Remove TTM Rows
    # ----------------------------------

    profit_loss = profit_loss[
        profit_loss["year"] != "TTM"
    ]

    balance_sheet = balance_sheet[
        balance_sheet["year"] != "TTM"
    ]

    cashflow = cashflow[
        cashflow["year"] != "TTM"
    ]

    # ----------------------------------
    # Remove Duplicate Company-Year Records
    # ----------------------------------

    profit_loss = profit_loss.drop_duplicates(
        subset=["company_id", "year"],
        keep="first"
    )

    balance_sheet = balance_sheet.drop_duplicates(
        subset=["company_id", "year"],
        keep="first"
    )

    cashflow = cashflow.drop_duplicates(
        subset=["company_id", "year"],
        keep="first"
    )

    print("\nDuplicates removed.")
    print("Profit & Loss :", len(profit_loss))
    print("Balance Sheet :", len(balance_sheet))
    print("Cash Flow     :", len(cashflow))

    # ----------------------------------
    # Merge Tables
    # ----------------------------------

    df = (
        profit_loss
        .merge(
            balance_sheet,
            on=["company_id", "year"],
            how="inner"
        )
        .merge(
            cashflow,
            on=["company_id", "year"],
            how="inner"
        )
    )

    print("✔ Merged Rows :", len(df))

    # ----------------------------------
# Load Company CAGR
# ----------------------------------

    cagr_df = pd.read_csv("output/company_cagr.csv")

    print("✔ Company CAGR :", len(cagr_df))

    # ----------------------------------
    # Results List
    # ----------------------------------

    results = []

    # ----------------------------------
    # Calculate Ratios
    # ----------------------------------

    for _, row in df.iterrows():

        # -------------------------
        # Basic KPIs
        # -------------------------

        npm = net_profit_margin(
            row["net_profit"],
            row["sales"]
        )

        opm = operating_profit_margin(
            row["operating_profit"],
            row["sales"]
        )

        roe = return_on_equity(
            row["net_profit"],
            row["equity_capital"],
            row["reserves"]
        )

        de = debt_to_equity(
            row["borrowings"],
            row["equity_capital"],
            row["reserves"]
        )

        icr = interest_coverage_ratio(
            row["operating_profit"],
            row["other_income"],
            row["interest"]
        )

        turnover = asset_turnover(
            row["sales"],
            row["total_assets"]
        )

        fcf = free_cash_flow(
            row["operating_activity"],
            row["investing_activity"]
        )

        # -------------------------
        # CAGR (Placeholder)
        # -------------------------

        # -------------------------
# CAGR Lookup
# -------------------------

        company_cagr = cagr_df[
         cagr_df["company_id"] == row["company_id"]
        ]

        if not company_cagr.empty:

            revenue_cagr_5yr = company_cagr.iloc[0]["revenue_cagr_pct"]
            pat_cagr_5yr = company_cagr.iloc[0]["pat_cagr_pct"]
            eps_cagr_5yr = company_cagr.iloc[0]["eps_cagr_pct"]

            revenue_cagr_flag = company_cagr.iloc[0]["revenue_flag"]
            pat_cagr_flag = company_cagr.iloc[0]["pat_flag"]
            eps_cagr_flag = company_cagr.iloc[0]["eps_flag"]

        else:

            revenue_cagr_5yr = None
            pat_cagr_5yr = None
            eps_cagr_5yr = None

            revenue_cagr_flag = None
            pat_cagr_flag = None
            eps_cagr_flag = None

        # -------------------------
        # Additional KPIs
        # -------------------------

        capex = (
            abs(row["investing_activity"])
            if pd.notna(row["investing_activity"])
            else None
        )

        eps = row["eps"]

        if (
            pd.notna(row["equity_capital"])
            and row["equity_capital"] != 0
        ):
            book_value = (
                row["equity_capital"] +
                row["reserves"]
            ) / row["equity_capital"]
        else:
            book_value = None

        dividend = row["dividend_payout"]

        total_debt = row["borrowings"]

        cfo = row["operating_activity"]

        # -------------------------
        # Composite Quality Score
        # -------------------------

        score = 0

        if roe is not None and roe >= 15:
            score += 25

        if de is not None and de <= 1:
            score += 25

        if icr is not None and icr >= 3:
            score += 25

        if fcf is not None and fcf > 0:
            score += 25

        composite_quality_score = score
    

        # -------------------------
        # Save Row
        # -------------------------

        results.append({

            "company_id": row["company_id"],
            "year": row["year"],

            "net_profit_margin_pct": npm,
            "operating_profit_margin_pct": opm,
            "return_on_equity_pct": roe,

            "debt_to_equity": de,
            "interest_coverage": icr,
            "asset_turnover": turnover,

            "free_cash_flow_cr": fcf,
            "capex_cr": capex,

            "earnings_per_share": eps,
            "book_value_per_share": book_value,

            "dividend_payout_ratio_pct": dividend,

            "total_debt_cr": total_debt,

            "cash_from_operations_cr": cfo,

            "revenue_cagr_5yr": revenue_cagr_5yr,
            "pat_cagr_5yr": pat_cagr_5yr,
            "eps_cagr_5yr": eps_cagr_5yr,

            "revenue_cagr_flag": revenue_cagr_flag,
            "pat_cagr_flag": pat_cagr_flag,
            "eps_cagr_flag": eps_cagr_flag,

            "composite_quality_score": composite_quality_score

        })


    # ----------------------------------
    # Create DataFrame
    # ----------------------------------

    ratios = pd.DataFrame(results)

    print("\nCalculated Ratio Rows :", len(ratios))

    print("\nPreview:")
    print(ratios.head())

    # ----------------------------------
    # Save to SQLite
    # ----------------------------------

    print("\nSaving ratios to financial_ratios table...")

    # Clear old data
    conn.execute("DELETE FROM financial_ratios")

    # Keep only required columns
    ratios = ratios[
    [
        "company_id",
        "year",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "eps_cagr_5yr",
        "revenue_cagr_flag",
        "pat_cagr_flag",
        "eps_cagr_flag",
        "composite_quality_score"
    ]
]

    ratios.to_sql(
        "financial_ratios",
        conn,
        if_exists="append",
        index=False
    )

    conn.commit()

    print("✓ financial_ratios table updated successfully.")

    # ----------------------------------
    # Verify Row Count
    # ----------------------------------

    count = pd.read_sql(
        "SELECT COUNT(*) AS total FROM financial_ratios",
        conn
    )

    print("\nRows in financial_ratios:")
    print(count)

    print("\nExpected Rows :", len(ratios))

    # ----------------------------------
    # Close Database
    # ----------------------------------

    conn.close()

    print("\n" + "=" * 60)
    print("Ratio Engine Completed Successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()