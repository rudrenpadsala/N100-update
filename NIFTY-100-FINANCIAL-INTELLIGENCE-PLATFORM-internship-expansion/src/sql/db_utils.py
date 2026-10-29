"""
db_utils.py

SQLite Database Connection Utility
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "db" / "nifty100.db"


def get_connection():
    """
    Returns SQLite Connection
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == "__main__":

    conn = get_connection()

    print("Database Connected Successfully!")

    conn.close()