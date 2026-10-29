import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"

conn = sqlite3.connect(DB_PATH)

ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn
)

conn.close()

print("=" * 60)
print("SPRINT 2 REVIEW")
print("=" * 60)

print("\nTotal Rows")
print(len(ratios))

print("\nColumns")
for col in ratios.columns:
    print("-", col)

print("\nNull Values")
print(ratios.isnull().sum())

print("\nSample Records")
print(ratios.head())

print("\nSummary Statistics")
print(ratios.describe(include="all"))