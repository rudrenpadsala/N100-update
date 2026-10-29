import sqlite3
from pathlib import Path

# ==========================================
# Project Paths
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_DIR = BASE_DIR / "db"
DB_PATH = DB_DIR / "nifty100.db"

SCHEMA_PATH = DB_DIR / "schema.sql"


def create_database():

    print("=" * 60)
    print("Creating SQLite Database")
    print("=" * 60)

    DB_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    # Enable Foreign Keys
    conn.execute("PRAGMA foreign_keys = ON;")

    cursor = conn.cursor()

    # Read schema.sql
    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
        schema = file.read()

    # Execute entire schema
    cursor.executescript(schema)

    conn.commit()

    print("\nDatabase Created Successfully")

    print(f"Database : {DB_PATH}")

    # Verify Tables
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name;
    """)

    tables = cursor.fetchall()

    print("\nTables Created")

    for table in tables:
        print(f"✔ {table[0]}")

    print(f"\nTotal Tables : {len(tables)}")

    conn.close()

    print("\nDone!")


if __name__ == "__main__":
    create_database()