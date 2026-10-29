import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "db" / "nifty100.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

tables = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "stock_prices"
]

print("=" * 50)
print("ROW COUNTS")
print("=" * 50)

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table:<20} : {count}")

print("\n" + "=" * 50)
print("FOREIGN KEY CHECK")
print("=" * 50)

cursor.execute("PRAGMA foreign_key_check")
errors = cursor.fetchall()

if len(errors) == 0:
    print("✔ No Foreign Key Violations")
else:
    print("Foreign Key Errors:")
    for row in errors:
        print(row)

conn.close()