import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"

conn = sqlite3.connect(DB_PATH)

query = """
SELECT
    company_id,
    year,
    return_on_equity_pct,
    debt_to_equity,
    net_profit_margin_pct,
    asset_turnover
FROM financial_ratios
WHERE return_on_equity_pct > 15
  AND debt_to_equity < 1
ORDER BY return_on_equity_pct DESC;
"""

df = pd.read_sql(query, conn)

conn.close()

print("=" * 60)
print("SCREENER PREVIEW")
print("=" * 60)

print("\nCompanies Found :", len(df))

print("\nTop 20 Companies")
print(df.head(20))

df.to_csv(
    "output/screener_preview.csv",
    index=False
)

print("\n✓ Saved:")
print("output/screener_preview.csv")