import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "db" / "nifty100.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

queries = [
    ("Companies", "SELECT COUNT(*) FROM companies"),
    ("Profit & Loss", "SELECT COUNT(*) FROM profitandloss"),
    ("Balance Sheet", "SELECT COUNT(*) FROM balancesheet"),
    ("Cash Flow", "SELECT COUNT(*) FROM cashflow"),
    ("Stock Prices", "SELECT COUNT(*) FROM stock_prices")
]

print("=" * 50)
print("ROW COUNTS")
print("=" * 50)

for name, query in queries:
    cursor.execute(query)
    count = cursor.fetchone()[0]
    print(f"{name:<20}: {count}")

print("\n" + "=" * 50)
print("FOREIGN KEY CHECK")
print("=" * 50)

cursor.execute("PRAGMA foreign_key_check")
violations = cursor.fetchall()

if len(violations) == 0:
    print("✅ No Foreign Key Violations")
else:
    print("❌ Foreign Key Violations Found:")
    for row in violations:
        print(row)

conn.close()