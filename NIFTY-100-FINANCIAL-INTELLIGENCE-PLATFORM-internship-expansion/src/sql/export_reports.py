"""
export_reports.py

Export Analytics Reports from SQLite
"""

from pathlib import Path
import pandas as pd

from db_utils import get_connection

# ==========================================
# Output Folder
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]

REPORT_DIR = BASE_DIR / "output" / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# Reports
# ==========================================

REPORTS = {

    "company_overview": """
    SELECT * FROM company_overview;
    """,

    "financial_summary": """
    SELECT * FROM financial_summary;
    """,

    "market_summary": """
    SELECT * FROM market_summary;
    """,

    "stock_summary": """
    SELECT * FROM stock_summary;
    """,

    "top_sales": """
    SELECT
        c.company_name,
        MAX(p.sales) AS sales
    FROM profitandloss p
    JOIN companies c
    ON p.company_id = c.id
    GROUP BY c.company_name
    ORDER BY sales DESC
    LIMIT 20;
    """,

    "top_profit": """
    SELECT
        c.company_name,
        MAX(p.net_profit) AS net_profit
    FROM profitandloss p
    JOIN companies c
    ON p.company_id = c.id
    GROUP BY c.company_name
    ORDER BY net_profit DESC
    LIMIT 20;
    """,

    "sector_summary": """
    SELECT
        broad_sector,
        COUNT(*) AS total_companies
    FROM sectors
    GROUP BY broad_sector
    ORDER BY total_companies DESC;
    """,

    "market_cap_summary": """
    SELECT
        c.company_name,
        MAX(m.market_cap_crore) AS market_cap
    FROM market_cap m
    JOIN companies c
    ON m.company_id = c.id
    GROUP BY c.company_name
    ORDER BY market_cap DESC
    LIMIT 20;
    """

}

# ==========================================
# Export Reports
# ==========================================

def export_reports():

    conn = get_connection()

    print("=" * 60)
    print("Exporting Analytics Reports")
    print("=" * 60)

    for name, query in REPORTS.items():

        print(f"\nGenerating {name}...")

        df = pd.read_sql_query(query, conn)

        file_path = REPORT_DIR / f"{name}.csv"

        df.to_csv(file_path, index=False)

        print(f"✔ Saved : {file_path.name}")

    conn.close()

    print("\n" + "=" * 60)
    print("All Reports Exported Successfully")
    print("=" * 60)


if __name__ == "__main__":
    export_reports()