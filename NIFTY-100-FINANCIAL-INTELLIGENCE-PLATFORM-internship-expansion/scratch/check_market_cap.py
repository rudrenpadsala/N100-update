import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")
query = "SELECT * FROM market_cap WHERE company_id IN ('RELIANCE', 'TCS', 'INFY', 'HDFCBANK') ORDER BY company_id, year DESC"
df = pd.read_sql(query, conn)
print(df.to_string())
conn.close()
