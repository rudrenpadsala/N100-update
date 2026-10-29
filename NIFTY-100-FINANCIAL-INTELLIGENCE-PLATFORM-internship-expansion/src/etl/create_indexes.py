"""
create_indexes.py

Sprint 6
Day 43

Adds SQLite indexes needed by the Day 38-40 API layer on
tables that were not already indexed on company_id. Existing
indexes (market_cap, profitandloss, balancesheet, cashflow,
stock_prices) are left untouched.
"""

import sqlite3

DB_PATH = "db/nifty100.db"

# (index_name, table, columns)
NEW_INDEXES = [
    ("idx_ratios_company", "financial_ratios", "company_id"),
    ("idx_ratios_company_year", "financial_ratios", "company_id, year"),
    ("idx_sectors_company", "sectors", "company_id"),
    ("idx_sectors_broad_sector", "sectors", "broad_sector"),
    ("idx_peer_groups_company", "peer_groups", "company_id"),
    ("idx_peer_groups_name", "peer_groups", "peer_group_name"),
    ("idx_peer_percentiles_company", "peer_percentiles", "company_id"),
    ("idx_documents_company", "documents", "company_id"),
    ("idx_prosandcons_company", "prosandcons", "company_id"),
]


def create_indexes() -> None:
    """
    Create every index in NEW_INDEXES if it does not already
    exist. Safe to run repeatedly (idempotent).
    """

    conn = sqlite3.connect(DB_PATH)

    for index_name, table, columns in NEW_INDEXES:
        conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({columns})")
        print(f"✔ Index ensured : {index_name} ON {table}({columns})")

    conn.commit()
    conn.close()

    print("\n✅ Day 43 Index Creation Complete")


if __name__ == "__main__":
    create_indexes()
