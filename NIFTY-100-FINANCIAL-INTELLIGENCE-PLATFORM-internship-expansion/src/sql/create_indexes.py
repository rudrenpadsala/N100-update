"""
create_indexes.py

Creates indexes for faster SQL queries.
"""

from db_utils import get_connection


INDEXES = [

    """
    CREATE INDEX IF NOT EXISTS idx_market_company
    ON market_cap(company_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_profit_company
    ON profitandloss(company_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_balance_company
    ON balancesheet(company_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_cash_company
    ON cashflow(company_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_stock_company
    ON stock_prices(company_id);
    """,

    """
    CREATE INDEX IF NOT EXISTS idx_stock_date
    ON stock_prices(date);
    """

]


def create_indexes():

    conn = get_connection()

    cursor = conn.cursor()

    print("=" * 60)
    print("Creating Indexes")
    print("=" * 60)

    for sql in INDEXES:

        cursor.execute(sql)

    conn.commit()

    conn.close()

    print("All indexes created successfully.")


if __name__ == "__main__":
    create_indexes()