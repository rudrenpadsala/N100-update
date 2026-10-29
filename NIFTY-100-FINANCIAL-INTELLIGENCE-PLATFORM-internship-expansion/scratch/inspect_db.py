import sqlite3
import pandas as pd

conn = sqlite3.connect('NIFTY-100-FINANCIAL-INTELLIGENCE-PLATFORM-internship-expansion/db/nifty100.db')
cursor = conn.cursor()
tables = [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Tables in DB:', tables)
print('--- Schema of stock_prices ---')
for row in cursor.execute("PRAGMA table_info(stock_prices)").fetchall():
    print(row)
print('--- Date Range of stock_prices ---')
print(pd.read_sql('SELECT MIN(date), MAX(date), COUNT(*), COUNT(DISTINCT company_id) FROM stock_prices', conn))
print('--- Sample rows of stock_prices ---')
print(pd.read_sql('SELECT * FROM stock_prices ORDER BY date DESC LIMIT 5', conn))
