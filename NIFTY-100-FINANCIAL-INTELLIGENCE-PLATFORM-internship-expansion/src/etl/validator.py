"""
validator.py

Run all Data Quality Rules (DQ-01 to DQ-16)
"""

import os

from loader import load_all_excel_files
from report import save_validation_report, generate_summary

from dq_rules import (
    dq01_primary_key,
    dq02_company_year,
    dq03_foreign_key,
    dq04_balance_sheet,
    dq05_opm,
    dq06_positive_sales,
    dq07_positive_expenses,
    dq08_net_profit,
    dq09_missing_year,
    dq10_future_year,
    dq11_cashflow,
    dq12_website,
    dq13_stock_price,
    dq14_sector,
    dq15_market_cap,
    dq16_duplicate_company
)


def main():

    print("=" * 60)
    print("Running Data Quality Validation")
    print("=" * 60)

    datasets = load_all_excel_files()

    failures = []

    companies = datasets["companies"]

    # ------------------------------------------------
    # DQ-01 Primary Key
    # ------------------------------------------------
    for name, df in datasets.items():
        failures.extend(dq01_primary_key(df, name))

    # ------------------------------------------------
    # DQ-02 Company + Year
    # ------------------------------------------------
    for name, df in datasets.items():
        failures.extend(dq02_company_year(df, name))

    # ------------------------------------------------
    # DQ-03 Foreign Key
    # ------------------------------------------------
    for name, df in datasets.items():

        if name != "companies":
            failures.extend(
                dq03_foreign_key(
                    df,
                    companies,
                    name
                )
            )

    # ------------------------------------------------
    # DQ-04 Balance Sheet
    # ------------------------------------------------
    failures.extend(
        dq04_balance_sheet(
            datasets["balancesheet"]
        )
    )

    # ------------------------------------------------
    # DQ-05 OPM
    # ------------------------------------------------
    failures.extend(
        dq05_opm(
            datasets["profitandloss"]
        )
    )

    # ------------------------------------------------
    # DQ-06 Sales
    # ------------------------------------------------
    failures.extend(
        dq06_positive_sales(
            datasets["profitandloss"]
        )
    )

    # ------------------------------------------------
    # DQ-07 Expenses
    # ------------------------------------------------
    failures.extend(
        dq07_positive_expenses(
            datasets["profitandloss"]
        )
    )

    # ------------------------------------------------
    # DQ-08 Net Profit
    # ------------------------------------------------
    failures.extend(
        dq08_net_profit(
            datasets["profitandloss"]
        )
    )

    # ------------------------------------------------
    # DQ-09 Missing Year
    # ------------------------------------------------
    for name, df in datasets.items():
        failures.extend(
            dq09_missing_year(df, name)
        )

    # ------------------------------------------------
    # DQ-10 Future Year
    # ------------------------------------------------
    for name, df in datasets.items():
        failures.extend(
            dq10_future_year(df, name)
        )

    # ------------------------------------------------
    # DQ-11 Cash Flow
    # ------------------------------------------------
    failures.extend(
        dq11_cashflow(
            datasets["cashflow"]
        )
    )

    # ------------------------------------------------
    # DQ-12 Website
    # ------------------------------------------------
    failures.extend(
        dq12_website(
            datasets["companies"]
        )
    )

    # ------------------------------------------------
    # DQ-13 Stock Prices
    # ------------------------------------------------
    failures.extend(
        dq13_stock_price(
            datasets["stock_prices"]
        )
    )

    # ------------------------------------------------
    # DQ-14 Sector
    # ------------------------------------------------
    failures.extend(
        dq14_sector(
            datasets["sectors"]
        )
    )

    # ------------------------------------------------
    # DQ-15 Market Cap
    # ------------------------------------------------
    failures.extend(
        dq15_market_cap(
            datasets["market_cap"]
        )
    )

    # ------------------------------------------------
    # DQ-16 Duplicate Company
    # ------------------------------------------------
    failures.extend(
        dq16_duplicate_company(
            datasets["companies"]
        )
    )

    # ------------------------------------------------
    # Save Reports
    # ------------------------------------------------
    failure_df = save_validation_report(failures)

    generate_summary(failure_df)

    print("\n" + "=" * 60)
    print("Validation Complete")
    print("=" * 60)

    print(f"Total Failures : {len(failure_df)}")

    if not failure_df.empty:

        critical = len(
            failure_df[
                failure_df["severity"] == "CRITICAL"
            ]
        )

        warning = len(
            failure_df[
                failure_df["severity"] == "WARNING"
            ]
        )

        print(f"Critical : {critical}")
        print(f"Warning  : {warning}")

    print("\nReports Generated")

    print("✔ validation_failures.csv")
    print("✔ validation_summary.csv")


if __name__ == "__main__":
    main()