import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"

conn = sqlite3.connect(DB_PATH)

profit = pd.read_sql(
    """
    SELECT DISTINCT company_id, year
    FROM profitandloss
    WHERE year <> 'TTM'
    """,
    conn,
)

balance = pd.read_sql(
    """
    SELECT DISTINCT company_id, year
    FROM balancesheet
    WHERE year <> 'TTM'
    """,
    conn,
)

cashflow = pd.read_sql(
    """
    SELECT DISTINCT company_id, year
    FROM cashflow
    WHERE year <> 'TTM'
    """,
    conn,
)

profit_keys = set(zip(profit.company_id, profit.year))
balance_keys = set(zip(balance.company_id, balance.year))
cashflow_keys = set(zip(cashflow.company_id, cashflow.year))

all_keys = profit_keys | balance_keys | cashflow_keys

missing = []

for key in sorted(all_keys):
    missing.append({
        "company_id": key[0],
        "year": key[1],
        "profit": key in profit_keys,
        "balance": key in balance_keys,
        "cashflow": key in cashflow_keys
    })

missing_df = pd.DataFrame(missing)

problem_rows = missing_df[
    ~(missing_df["profit"] &
      missing_df["balance"] &
      missing_df["cashflow"])
]

print("=" * 70)
print("MISSING COMPANY-YEAR RECORDS")
print("=" * 70)

print(problem_rows)

print("\nTotal Missing:", len(problem_rows))

problem_rows.to_csv(
    "output/missing_company_years.csv",
    index=False
)

print("\nSaved to output/missing_company_years.csv")

conn.close()