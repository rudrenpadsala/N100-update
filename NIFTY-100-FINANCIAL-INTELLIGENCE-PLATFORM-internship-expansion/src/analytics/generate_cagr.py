"""
generate_cagr.py

Sprint 2
Day 15

Generate Revenue, PAT and EPS CAGR
for every company.
"""

import os
import sqlite3
import pandas as pd

from src.analytics.cagr import (
    revenue_cagr,
    pat_cagr,
    eps_cagr
)

DB_PATH = "db/nifty100.db"
OUTPUT_FILE = "output/company_cagr.csv"


def main():

    print("=" * 60)
    print("CAGR ENGINE")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            sales,
            net_profit,
            eps
        FROM profitandloss
        """,
        conn
    )

    print("Rows Loaded :", len(df))


    # ----------------------------------
    # Sort Data
    # ----------------------------------

    df = (
        df
        .sort_values(
            ["company_id", "year"]
        )
        .reset_index(drop=True)
    )

    results = []

    # ----------------------------------
    # Process Each Company
    # ----------------------------------

    for company in df["company_id"].unique():

        company_df = (
            df[df["company_id"] == company]
            .copy()
            .reset_index(drop=True)
        )

        if len(company_df) < 4:
            continue

        start = company_df.iloc[0]
        end = company_df.iloc[-1]

        years = len(company_df) - 1

        revenue_value, revenue_flag = revenue_cagr(
            start["sales"],
            end["sales"],
            years
        )

        pat_value, pat_flag = pat_cagr(
            start["net_profit"],
            end["net_profit"],
            years
        )

        eps_value, eps_flag = eps_cagr(
            start["eps"],
            end["eps"],
            years
        )


        results.append({

            "company_id": company,

            "start_year": start["year"],
            "end_year": end["year"],

            "revenue_cagr_pct": revenue_value,
            "revenue_flag": revenue_flag,

            "pat_cagr_pct": pat_value,
            "pat_flag": pat_flag,

            "eps_cagr_pct": eps_value,
            "eps_flag": eps_flag

        })

    # ----------------------------------
    # Create DataFrame
    # ----------------------------------

    cagr_df = pd.DataFrame(results)

    print("\nCompanies Processed :", len(cagr_df))

    print("\nPreview:")

    print(cagr_df.head())


    # ----------------------------------
    # Save Output
    # ----------------------------------

    os.makedirs("output", exist_ok=True)

    cagr_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n✓ company_cagr.csv generated successfully.")
    print("Saved to :", OUTPUT_FILE)

    print("\nTotal Companies :", len(cagr_df))

    print("\nRevenue CAGR Summary")
    print(cagr_df["revenue_cagr_pct"].describe())

    print("\nPAT CAGR Summary")
    print(cagr_df["pat_cagr_pct"].describe())

    print("\nEPS CAGR Summary")
    print(cagr_df["eps_cagr_pct"].describe())

    conn.close()


if __name__ == "__main__":
    main()