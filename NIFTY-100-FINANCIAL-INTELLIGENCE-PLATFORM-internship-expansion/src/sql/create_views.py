"""
create_views.py

Create SQL Views for Analytics
"""

from db_utils import get_connection


VIEWS = [

    # ==========================================
    # Company Overview
    # ==========================================
    """
    CREATE VIEW IF NOT EXISTS company_overview AS

    SELECT

        c.id,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        c.face_value,
        c.book_value,
        c.roce_percentage,
        c.roe_percentage

    FROM companies c

    LEFT JOIN sectors s

    ON c.id = s.company_id;
    """,

    # ==========================================
    # Financial Summary
    # ==========================================
    """
    CREATE VIEW IF NOT EXISTS financial_summary AS

    SELECT

        p.company_id,
        c.company_name,

        MAX(p.sales) AS sales,
        MAX(p.net_profit) AS net_profit,
        MAX(p.eps) AS eps,

        MAX(f.return_on_equity_pct) AS roe,

        MAX(f.debt_to_equity) AS debt_to_equity

    FROM profitandloss p

    JOIN companies c

    ON p.company_id = c.id

    LEFT JOIN financial_ratios f

    ON p.company_id = f.company_id

    GROUP BY p.company_id;
    """,

    # ==========================================
    # Market Summary
    # ==========================================
    """
    CREATE VIEW IF NOT EXISTS market_summary AS

    SELECT

        m.company_id,
        c.company_name,

        MAX(m.market_cap_crore) AS market_cap,

        MAX(m.pe_ratio) AS pe,

        MAX(m.pb_ratio) AS pb,

        MAX(m.dividend_yield_pct) AS dividend_yield

    FROM market_cap m

    JOIN companies c

    ON m.company_id = c.id

    GROUP BY m.company_id;
    """,

    # ==========================================
    # Latest Stock Price
    # ==========================================
    """
    CREATE VIEW IF NOT EXISTS stock_summary AS

    SELECT

        company_id,

        MAX(date) AS latest_date,

        MAX(close_price) AS latest_close

    FROM stock_prices

    GROUP BY company_id;
    """

]


def create_views():

    conn = get_connection()

    cursor = conn.cursor()

    print("=" * 60)
    print("Creating SQL Views")
    print("=" * 60)

    for sql in VIEWS:

        cursor.execute(sql)

    conn.commit()

    conn.close()

    print("\nViews Created Successfully!")

    print("\nCreated Views:")

    print("✔ company_overview")

    print("✔ financial_summary")

    print("✔ market_summary")

    print("✔ stock_summary")


if __name__ == "__main__":

    create_views()