import os
import sqlite3
import pandas as pd

from src.analytics.cashflow_kpis import capital_allocation_pattern


def main():

    conn = sqlite3.connect("db/nifty100.db")

    df = pd.read_sql(
        "SELECT * FROM cashflow",
        conn
    )

    conn.close()

    rows = []

    for _, row in df.iterrows():

        cfo, cfi, cff, pattern = capital_allocation_pattern(
            row["operating_activity"],
            row["investing_activity"],
            row["financing_activity"]
        )

        rows.append({
            "company_id": row["company_id"],
            "year": row["year"],
            "cfo_sign": cfo,
            "cfi_sign": cfi,
            "cff_sign": cff,
            "pattern_label": pattern
        })

    output = pd.DataFrame(rows)

    os.makedirs("output", exist_ok=True)

    output.to_csv(
        "output/capital_allocation.csv",
        index=False
    )

    print("✅ capital_allocation.csv generated successfully.")


if __name__ == "__main__":
    main()