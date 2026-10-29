"""
health.py

Sprint 6
Day 38

Health check router.
"""

import sqlite3
import time

from fastapi import APIRouter, Depends

from src.api.dependencies import get_db

router = APIRouter(prefix="/health", tags=["Health"])

API_VERSION = "1.0.0"
_SERVICE_START_TIME = time.time()

# Tables reported in the health check row-count summary.
_MONITORED_TABLES = [
    "companies",
    "sectors",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "financial_ratios",
    "market_cap",
    "peer_groups",
    "documents",
    "prosandcons",
    "stock_prices",
]


def _get_table_row_counts(conn: sqlite3.Connection) -> dict:
    """
    Count rows in every monitored table.

    Args:
        conn: Open SQLite connection.

    Returns:
        Dict mapping table name -> row count.
    """

    counts = {}

    for table in _MONITORED_TABLES:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cursor.fetchone()[0]

    return counts


@router.get("")
def get_health(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """
    Report service status, API version, uptime and database
    row counts.

    Returns:
        JSON payload with status, version, uptime and
        database row counts.
    """

    uptime_seconds = round(time.time() - _SERVICE_START_TIME, 2)

    return {
        "status": "ok",
        "version": API_VERSION,
        "uptime_seconds": uptime_seconds,
        "database_row_counts": _get_table_row_counts(conn),
    }
