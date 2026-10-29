"""
fetch_market_data.py

Fetches daily historical OHLCV data from 1 January 2025 through latest available date
for all 92 NIFTY-100 constituents using publicly accessible Yahoo Finance endpoints.
- Reuses existing company symbols & maps NSE tickers.
- Incremental updates: preserves existing records, prevents duplicates.
- Backs up original database before updating.
- Validates data integrity (no invented prices, strictly actual retrieved data).
- Updates latest_price.csv for seamless dashboard integration.
"""

import os
import re
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "db" / "nifty100.db"
BACKUP_PATH = REPO_ROOT / "db" / "nifty100_backup_pre2025.db"
LATEST_PRICES_PATH = REPO_ROOT / "output" / "sql_results" / "latest_price.csv"


def backup_database():
    """Create a backup of the original SQLite database if not already backed up."""
    if not BACKUP_PATH.exists():
        shutil.copyfile(DB_PATH, BACKUP_PATH)
        print(f"[BACKUP] Created database backup at: {BACKUP_PATH}")
    else:
        print(f"[BACKUP] Backup already present at: {BACKUP_PATH}")


def get_company_ticker_mapping(conn: sqlite3.Connection) -> Dict[str, Tuple[str, str]]:
    """
    Map each company_id to its Yahoo Finance NSE ticker and company name.
    Returns: {company_id: (yf_ticker, company_name)}
    """
    rows = conn.execute("SELECT id, company_name, nse_profile FROM companies ORDER BY id").fetchall()
    mapping = {}
    for cid, name, nse_profile in rows:
        sym = cid
        if nse_profile and "symbol=" in nse_profile:
            m = re.search(r"symbol=([^&]+)", nse_profile)
            if m:
                sym = m.group(1)
        
        # Clean special symbols
        clean_name = name.splitlines()[0].strip()
        if cid == "ABB":
            sym = "ABBOTINDIA"
        elif cid == "M&M":
            sym = "M&M"
        elif cid == "TATAMOTORS":
            sym = "TMCV"
        elif cid == "LTIM":
            sym = "LTM"
        
        yf_ticker = f"{sym}.NS"
        mapping[cid] = (yf_ticker, clean_name)
    return mapping


def ensure_unique_index(conn: sqlite3.Connection):
    """Ensure unique index on stock_prices(company_id, date) to prevent duplicates."""
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_stock_prices_company_date "
        "ON stock_prices (company_id, date)"
    )
    conn.commit()


def fetch_and_update_historical_data(start_date: str = "2025-01-01"):
    """
    Fetch daily historical OHLCV data from start_date to latest date
    and update stock_prices table incrementally.
    """
    backup_database()
    conn = sqlite3.connect(DB_PATH)
    ensure_unique_index(conn)

    mapping = get_company_ticker_mapping(conn)
    total_companies = len(mapping)
    print(f"\n[FETCH] Starting historical data update for {total_companies} companies from {start_date}...")

    # Existing date check
    existing_max_dates = dict(
        conn.execute("SELECT company_id, MAX(date) FROM stock_prices GROUP BY company_id").fetchall()
    )

    # Reverse lookup yf_ticker -> cid
    ticker_to_cid = {yf_ticker: cid for cid, (yf_ticker, _) in mapping.items()}
    all_yf_tickers = list(ticker_to_cid.keys())

    # Download in batches of 25 to balance throughput and reliability
    batch_size = 25
    total_new_rows = 0
    successful_companies = set()
    failed_companies = {}

    for i in range(0, len(all_yf_tickers), batch_size):
        batch = all_yf_tickers[i : i + batch_size]
        print(f"\n[BATCH {i // batch_size + 1}/{(len(all_yf_tickers) + batch_size - 1) // batch_size}] Fetching {len(batch)} tickers...")

        try:
            df = yf.download(batch, start=start_date, group_by="ticker", progress=False, threads=True)
        except Exception as e:
            print(f"[ERROR] Batch download failed: {e}. Retrying individually...")
            df = None

        for yf_t in batch:
            cid = ticker_to_cid[yf_t]
            t_df = None

            if df is not None and len(batch) > 1:
                try:
                    if yf_t in df.columns.levels[0]:
                        t_df = df[yf_t].dropna(how="all")
                except Exception:
                    t_df = None

            # Fallback to single fetch if batch missed it or failed
            if t_df is None or t_df.empty:
                try:
                    time.sleep(0.2)
                    single_df = yf.download(yf_t, start=start_date, progress=False)
                    if single_df is not None and not single_df.empty:
                        # If multiindex columns present
                        if isinstance(single_df.columns, pd.MultiIndex):
                            single_df.columns = single_df.columns.get_level_values(0)
                        t_df = single_df.dropna(how="all")
                except Exception as ex:
                    failed_companies[cid] = str(ex)
                    print(f"  [FAIL] {cid} ({yf_t}): {ex}")
                    continue

            if t_df is None or t_df.empty:
                failed_companies[cid] = "No data returned from source"
                print(f"  [WARN] No data for {cid} ({yf_t})")
                continue

            # Flatten columns if multiindex
            if isinstance(t_df.columns, pd.MultiIndex):
                t_df.columns = t_df.columns.get_level_values(-1)

            # Insert rows
            company_inserted = 0
            cur_max = existing_max_dates.get(cid, "1900-01-01")

            for dt_idx, row in t_df.iterrows():
                dt_str = pd.to_datetime(dt_idx).strftime("%Y-%m-%d")
                
                # Incremental condition: only new dates
                if dt_str <= cur_max:
                    continue

                open_p = float(row.get("Open") or 0.0)
                high_p = float(row.get("High") or 0.0)
                low_p = float(row.get("Low") or 0.0)
                close_p = float(row.get("Close") or 0.0)
                adj_close = float(row.get("Adj Close") if "Adj Close" in row else close_p)
                vol = int(row.get("Volume") or 0)

                # Validation checks
                if close_p <= 0 or high_p < low_p:
                    continue

                try:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO stock_prices 
                        (company_id, date, open_price, high_price, low_price, close_price, volume, adjusted_close)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (cid, dt_str, open_p, high_p, low_p, close_p, vol, adj_close),
                    )
                    company_inserted += 1
                except Exception as insert_err:
                    print(f"  [INSERT ERROR] {cid} on {dt_str}: {insert_err}")

            conn.commit()
            total_new_rows += company_inserted
            successful_companies.add(cid)
            latest_available_date = t_df.index[-1].strftime("%Y-%m-%d")
            latest_close = float(t_df["Close"].iloc[-1])
            print(f"  [OK] {cid:12s} | +{company_inserted:3d} records | Latest: {latest_available_date} | Close: INR {latest_close:,.2f}")

    # Generate updated latest_price.csv
    update_latest_prices_csv(conn)

    # Verification Query
    summary_df = pd.read_sql(
        """
        SELECT 
            COUNT(DISTINCT company_id) as total_companies,
            MIN(date) as min_date,
            MAX(date) as max_date,
            COUNT(*) as total_records
        FROM stock_prices
        """,
        conn,
    )
    conn.close()

    print("\n" + "=" * 60)
    print("HISTORICAL DATA UPDATE COMPLETED")
    print("=" * 60)
    print(f"Companies successfully updated: {len(successful_companies)}/{total_companies}")
    print(f"Failed companies: {len(failed_companies)}")
    if failed_companies:
        print("Failures:", failed_companies)
    print(f"Total new historical records inserted: {total_new_rows:,}")
    print(f"Overall Database Range: {summary_df['min_date'].iloc[0]} to {summary_df['max_date'].iloc[0]}")
    print(f"Total Database Records: {summary_df['total_records'].iloc[0]:,}")
    print("=" * 60)
    return successful_companies, failed_companies, summary_df


def update_latest_prices_csv(conn: sqlite3.Connection):
    """
    Update output/sql_results/latest_price.csv with latest available trading date,
    close price, previous close, change, and pct_change.
    """
    LATEST_PRICES_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    query = """
    WITH RankedPrices AS (
        SELECT 
            company_id,
            date,
            close_price,
            ROW_NUMBER() OVER(PARTITION BY company_id ORDER BY date DESC) as rn
        FROM stock_prices
    )
    SELECT 
        latest.company_id,
        latest.date as latest_date,
        latest.close_price as latest_close,
        COALESCE(prev.close_price, latest.close_price) as prev_close,
        ROUND(latest.close_price - COALESCE(prev.close_price, latest.close_price), 2) as price_change,
        ROUND(((latest.close_price - COALESCE(prev.close_price, latest.close_price)) / COALESCE(prev.close_price, latest.close_price)) * 100, 2) as pct_change
    FROM RankedPrices latest
    LEFT JOIN RankedPrices prev ON latest.company_id = prev.company_id AND prev.rn = 2
    WHERE latest.rn = 1
    ORDER BY latest.company_id
    """
    df = pd.read_sql(query, conn)
    df.to_csv(LATEST_PRICES_PATH, index=False)
    print(f"\n[SYNC] Exported latest prices to: {LATEST_PRICES_PATH} ({len(df)} companies)")


if __name__ == "__main__":
    fetch_and_update_historical_data()
