"""
verify_database.py

Verify SQLite database after loading data.
"""

import sqlite3
from pathlib import Path

# ==========================================
# Paths
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "db" / "nifty100.db"


def verify_database():

    print("=" * 60)
    print("Database Verification")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    tables = [

        "companies",
        "analysis",
        "balancesheet",
        "cashflow",
        "documents",
        "financial_ratios",
        "market_cap",
        "peer_groups",
        "profitandloss",
        "prosandcons",
        "sectors",
        "stock_prices"

    ]

    total_rows = 0

    for table in tables:

        cursor.execute(f"SELECT COUNT(*) FROM {table}")

        rows = cursor.fetchone()[0]

        total_rows += rows

        print(f"{table:<20} {rows:>8} rows")

    print("-" * 60)

    print(f"Total Rows Loaded : {total_rows}")

    conn.close()


if __name__ == "__main__":
    verify_database()