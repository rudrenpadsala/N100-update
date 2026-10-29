"""
run_queries.py

Execute SQL Queries
Save Results as CSV
"""

from pathlib import Path
import pandas as pd

from db_utils import get_connection

import queries


# ==========================================
# Output Folder
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "output" / "sql_results"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# All Queries
# ==========================================

QUERY_LIST = {

    "total_companies": queries.TOTAL_COMPANIES,

    "top_roe": queries.TOP_ROE,

    "top_roce": queries.TOP_ROCE,

    "top_market_cap": queries.TOP_MARKET_CAP,

    "sector_count": queries.SECTOR_COUNT,

    "average_pe": queries.AVERAGE_PE,

    "top_dividend": queries.TOP_DIVIDEND,

    "latest_price": queries.LATEST_PRICE,
    "top_sales": queries.TOP_SALES,

"top_profit": queries.TOP_PROFIT,

"highest_eps": queries.HIGHEST_EPS,

"top_book_value": queries.TOP_BOOK_VALUE,

"top_face_value": queries.TOP_FACE_VALUE,

"market_cap_category": queries.MARKET_CAP_CATEGORY,

"average_roe_sector": queries.AVERAGE_ROE_SECTOR,

"total_sectors": queries.TOTAL_SECTORS,

    

}


# ==========================================
# Run Queries
# ==========================================

def run_queries():

    print("=" * 60)

    print("Running SQL Queries")

    print("=" * 60)

    conn = get_connection()

    for name, sql in QUERY_LIST.items():

        print(f"\n{name}")

        print("-" * 60)

        df = pd.read_sql_query(sql, conn)

        print(df)

        output_file = OUTPUT_DIR / f"{name}.csv"

        df.to_csv(output_file, index=False)

        print(f"✔ Saved : {output_file.name}")

    conn.close()

    print("\n")

    print("=" * 60)

    print("All Queries Executed Successfully")

    print("=" * 60)


if __name__ == "__main__":

    run_queries()