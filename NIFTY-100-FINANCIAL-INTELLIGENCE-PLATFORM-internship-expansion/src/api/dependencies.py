"""
dependencies.py

Sprint 6
Day 38

Shared FastAPI dependencies: a single SQLite connection
factory reused by every router.
"""

import sqlite3
from collections.abc import Generator

DB_PATH = "db/nifty100.db"


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI dependency that yields a SQLite connection with
    row_factory set so query results behave like dicts, and
    guarantees the connection is closed after the request.

    Yields:
        An open sqlite3.Connection.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        yield conn
    finally:
        conn.close()


def rows_to_dicts(rows) -> list:
    """
    Convert a list of sqlite3.Row objects into plain dicts
    so they serialize cleanly to JSON.

    Args:
        rows: Iterable of sqlite3.Row.

    Returns:
        List of dicts.
    """

    return [dict(row) for row in rows]
