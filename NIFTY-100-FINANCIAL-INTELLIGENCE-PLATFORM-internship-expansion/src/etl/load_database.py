"""
load_database.py

Loads all Excel datasets into SQLite database
and generates load_audit.csv
"""

import sqlite3
from pathlib import Path

import pandas as pd

from loader import load_all_excel_files


# =====================================================
# Paths
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "db" / "nifty100.db"

OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

AUDIT_FILE = OUTPUT_DIR / "load_audit.csv"


# =====================================================
# Load Database
# =====================================================

def load_database():

    print("=" * 60)
    print("Loading Data into SQLite")
    print("=" * 60)

    datasets = load_all_excel_files()

    conn = sqlite3.connect(DB_PATH)

    conn.execute("PRAGMA foreign_keys = ON")

    audit = []

    # ---------------------------------------------
    # Delete Child Tables First
    # ---------------------------------------------

    delete_order = [

        "stock_prices",
        "sectors",
        "prosandcons",
        "peer_groups",
        "market_cap",
        "financial_ratios",
        "documents",
        "cashflow",
        "balancesheet",
        "analysis",
        "profitandloss",
        "companies"

    ]

    print("\nRemoving Existing Records...\n")

    for table in delete_order:

        conn.execute(f"DELETE FROM {table};")

        print(f"✔ Cleared {table}")

    conn.commit()

    # ---------------------------------------------
    # Insert Parent First
    # ---------------------------------------------

    load_order = [

        "companies",

        "analysis",

        "balancesheet",

        "cashflow",

        "documents",

        "financial_ratios",

        "market_cap",

        "peer_groups",

        "profitandloss",

        "prosandcons",

        "sectors",

        "stock_prices"

    ]

    print("\nLoading Tables...\n")

    for table in load_order:

        df = datasets[table]

        print(f"Loading {table}...")

        df.to_sql(

            name=table,

            con=conn,

            if_exists="append",

            index=False

        )

        rows = conn.execute(

            f"SELECT COUNT(*) FROM {table}"

        ).fetchone()[0]

        audit.append({

            "table": table,

            "rows_loaded": rows,

            "status": "SUCCESS"

        })

        print(f"✔ {rows} rows inserted")

    conn.commit()

    conn.close()

    # ---------------------------------------------
    # Save Audit Report
    # ---------------------------------------------

    audit_df = pd.DataFrame(audit)

    audit_df.to_csv(

        AUDIT_FILE,

        index=False

    )

    print("\n" + "=" * 60)

    print("Load Completed Successfully")

    print("=" * 60)

    print(audit_df)

    print(f"\nAudit Report Saved : {AUDIT_FILE}")


# =====================================================
# Main
# =====================================================

if __name__ == "__main__":

    load_database()