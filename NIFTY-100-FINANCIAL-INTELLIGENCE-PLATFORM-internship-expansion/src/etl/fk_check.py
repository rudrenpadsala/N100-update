"""
fk_check.py

Verify that there are no Foreign Key violations
in the SQLite database.
"""

import sqlite3
from pathlib import Path

# ==========================================
# Database Path
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "db" / "nifty100.db"

# ==========================================
# Connect Database
# ==========================================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 60)
print("Running Foreign Key Check")
print("=" * 60)

# Enable FK checking
cursor.execute("PRAGMA foreign_keys = ON;")

# Run Foreign Key Check
cursor.execute("PRAGMA foreign_key_check;")

rows = cursor.fetchall()

if len(rows) == 0:
    print("\n✅ No Foreign Key violations found.")
    print("Result: 0 rows returned")
else:
    print(f"\n❌ Found {len(rows)} Foreign Key violation(s):\n")

    for row in rows:
        print(row)

conn.close()

print("\nDatabase check completed.")