"""
update_all_datasets_2026.py
===========================
Master ETL synchronization script:
1. Calculates and inserts FY 2024-25 and FY 2025-26 valuation metrics into market_cap.
2. Synchronizes data/raw Excel files (market_cap, profitandloss, balancesheet, cashflow, financial_ratios, documents, stock_prices) from SQLite.
3. Refreshes database analytical views (market_summary, financial_summary, company_overview, stock_summary).
4. Re-computes peer percentiles across all peer groups (peer_percentiles table).
5. Exports refreshed analytical CSV reports to output/reports/ and output/sql_results/.
"""

import os
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "db" / "nifty100.db"
RAW_DIR = REPO_ROOT / "data" / "raw"
OUTPUT_DIR = REPO_ROOT / "output"


def get_connection():
    return sqlite3.connect(DB_PATH)


def update_market_cap_table():
    print("\n" + "=" * 60)
    print("1. COMPUTING & UPDATING MARKET_CAP TABLE (FY25 & FY26)")
    print("=" * 60)
    
    conn = get_connection()
    companies = pd.read_sql("SELECT * FROM companies", conn)
    pl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    prices = pd.read_sql("SELECT company_id, date, close_price FROM stock_prices", conn)
    prices['date'] = pd.to_datetime(prices['date'])
    
    # Extract 4-digit year for matching
    pl['year_num'] = pl['year'].astype(str).str.extract(r'(\d{4})')[0]
    bs['year_num'] = bs['year'].astype(str).str.extract(r'(\d{4})')[0]
    
    existing_mc = pd.read_sql("SELECT * FROM market_cap", conn)
    max_id = int(existing_mc['id'].max()) if not existing_mc.empty and 'id' in existing_mc.columns else 0
    
    # Existing keys
    existing_keys = set(zip(existing_mc['company_id'].astype(str), existing_mc['year'].astype(int)))
    
    new_rows = []
    
    for target_year in [2025, 2026]:
        for _, comp in companies.iterrows():
            cid = str(comp['id']).strip()
            if (cid, target_year) in existing_keys:
                continue
                
            fv = float(comp['face_value']) if pd.notna(comp['face_value']) and comp['face_value'] > 0 else 10.0
            comp_prices = prices[prices['company_id'] == cid].sort_values('date')
            if comp_prices.empty:
                continue
                
            if target_year == 2025:
                p_df = comp_prices[comp_prices['date'] <= '2025-04-10']
                p_val = float(p_df.iloc[-1]['close_price']) if not p_df.empty else float(comp_prices.iloc[-1]['close_price'])
            else:
                p_val = float(comp_prices.iloc[-1]['close_price'])
                
            pl_match = pl[(pl['company_id'] == cid) & (pl['year_num'] == str(target_year))]
            bs_match = bs[(bs['company_id'] == cid) & (bs['year_num'] == str(target_year))]
            
            # Fallback for companies like Siemens (Oct-Sep) where 2026 is pending
            if pl_match.empty and target_year == 2026:
                pl_match = pl[(pl['company_id'] == cid) & (pl['year_num'] == '2025')]
            if bs_match.empty and target_year == 2026:
                bs_match = bs[(bs['company_id'] == cid) & (bs['year_num'] == '2025')]
                
            if pl_match.empty or bs_match.empty:
                continue
                
            p_row = pl_match.iloc[0]
            b_row = bs_match.iloc[0]
            
            eq = float(b_row['equity_capital']) if pd.notna(b_row['equity_capital']) else 100.0
            res = float(b_row['reserves']) if pd.notna(b_row['reserves']) else 1000.0
            debt = float(b_row['borrowings']) if pd.notna(b_row['borrowings']) else 0.0
            inv = float(b_row.get('investments', 0)) if pd.notna(b_row.get('investments', 0)) else 0.0
            
            pat = float(p_row['net_profit']) if pd.notna(p_row['net_profit']) else 100.0
            eps = float(p_row['eps']) if pd.notna(p_row['eps']) else 10.0
            ebitda = float(p_row['operating_profit']) if pd.notna(p_row['operating_profit']) else 200.0
            div_payout = float(p_row.get('dividend_payout', 0)) if pd.notna(p_row.get('dividend_payout', 0)) else 0.0
            
            if eps > 0 and pat > 0:
                shares_cr = pat / eps
            else:
                shares_cr = eq / fv
                
            mcap = round(shares_cr * p_val, 2)
            ev = round(mcap + debt - inv, 2)
            pe = round(p_val / eps, 2) if eps > 0 else round(mcap / max(1.0, pat), 2)
            net_worth = eq + res
            pb = round(mcap / net_worth, 2) if net_worth > 0 else 1.0
            ev_ebitda = round(ev / ebitda, 2) if ebitda > 0 else 10.0
            div_yield = round(min(10.0, max(0.0, (div_payout * pat / 100.0) / max(1.0, mcap) * 100)), 2)
            
            max_id += 1
            new_rows.append({
                'id': max_id,
                'company_id': cid,
                'year': target_year,
                'market_cap_crore': mcap,
                'enterprise_value_crore': ev,
                'pe_ratio': pe,
                'pb_ratio': pb,
                'ev_ebitda': ev_ebitda,
                'dividend_yield_pct': div_yield
            })
            
    if new_rows:
        df_new = pd.DataFrame(new_rows)
        df_new.to_sql("market_cap", conn, if_exists="append", index=False)
        print(f"[OK] Added {len(df_new)} new valuation rows to market_cap table (FY25 and FY26).")
    else:
        print("[OK] market_cap table already has FY25 and FY26 records.")
        
    conn.close()


def sync_raw_excel_files():
    print("\n" + "=" * 60)
    print("2. SYNCHRONIZING RAW EXCEL FILES FROM UPDATED SQLITE")
    print("=" * 60)
    
    conn = get_connection()
    tables_to_sync = [
        ("market_cap", "market_cap.xlsx"),
        ("profitandloss", "profitandloss.xlsx"),
        ("balancesheet", "balancesheet.xlsx"),
        ("cashflow", "cashflow.xlsx"),
        ("financial_ratios", "financial_ratios.xlsx"),
        ("documents", "documents.xlsx"),
        ("stock_prices", "stock_prices.xlsx"),
    ]
    
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    for tbl, filename in tables_to_sync:
        out_path = RAW_DIR / filename
        df = pd.read_sql(f"SELECT * FROM {tbl}", conn)
        df.to_excel(out_path, index=False)
        print(f"[OK] Exported {tbl:<20} ({len(df):>6} rows) -> data/raw/{filename}")
        
    conn.close()


def refresh_database_views():
    print("\n" + "=" * 60)
    print("3. REFRESHING DATABASE VIEWS")
    print("=" * 60)
    
    conn = get_connection()
    cur = conn.cursor()
    
    views_sql = [
        "DROP VIEW IF EXISTS company_overview;",
        """
        CREATE VIEW company_overview AS
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
        LEFT JOIN sectors s ON c.id = s.company_id;
        """,
        "DROP VIEW IF EXISTS financial_summary;",
        """
        CREATE VIEW financial_summary AS
        SELECT
            p.company_id,
            c.company_name,
            MAX(p.sales) AS sales,
            MAX(p.net_profit) AS net_profit,
            MAX(p.eps) AS eps,
            MAX(f.return_on_equity_pct) AS roe,
            MAX(f.debt_to_equity) AS debt_to_equity
        FROM profitandloss p
        JOIN companies c ON p.company_id = c.id
        LEFT JOIN financial_ratios f ON p.company_id = f.company_id
        GROUP BY p.company_id;
        """,
        "DROP VIEW IF EXISTS market_summary;",
        """
        CREATE VIEW market_summary AS
        SELECT
            m.company_id,
            c.company_name,
            MAX(m.market_cap_crore) AS market_cap,
            MAX(m.pe_ratio) AS pe,
            MAX(m.pb_ratio) AS pb,
            MAX(m.dividend_yield_pct) AS dividend_yield
        FROM market_cap m
        JOIN companies c ON m.company_id = c.id
        GROUP BY m.company_id;
        """,
        "DROP VIEW IF EXISTS stock_summary;",
        """
        CREATE VIEW stock_summary AS
        WITH ranked AS (
            SELECT company_id, date, close_price, volume,
                   ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY date DESC) as rn
            FROM stock_prices
        )
        SELECT r.company_id, c.company_name, r.date as latest_date, r.close_price as latest_close, r.volume as latest_volume
        FROM ranked r
        JOIN companies c ON r.company_id = c.id
        WHERE r.rn = 1;
        """
    ]
    
    for sql in views_sql:
        cur.execute(sql)
        
    conn.commit()
    conn.close()
    print("[OK] Refreshed views: company_overview, financial_summary, market_summary, stock_summary.")


def recompute_peer_percentiles():
    print("\n" + "=" * 60)
    print("4. RECOMPUTING PEER PERCENTILES FOR 2026")
    print("=" * 60)
    
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(REPO_ROOT / "src"))
    
    from src.analytics.peer import save_peer_percentiles
    df_pct = save_peer_percentiles()
    print(f"[OK] Successfully recomputed {len(df_pct)} peer percentile rankings through {df_pct['year'].iloc[0] if not df_pct.empty else 'latest'}.")


def export_reports_and_sql():
    print("\n" + "=" * 60)
    print("5. EXPORTING ANALYTICAL CSVs (output/reports and output/sql_results)")
    print("=" * 60)
    
    conn = get_connection()
    
    # Output reports
    rep_dir = OUTPUT_DIR / "reports"
    rep_dir.mkdir(parents=True, exist_ok=True)
    
    reports = {
        "company_overview": "SELECT * FROM company_overview;",
        "financial_summary": "SELECT * FROM financial_summary;",
        "market_summary": "SELECT * FROM market_summary;",
        "stock_summary": "SELECT * FROM stock_summary;",
        "top_sales": "SELECT c.company_name, MAX(p.sales) AS sales FROM profitandloss p JOIN companies c ON p.company_id = c.id GROUP BY c.company_name ORDER BY sales DESC LIMIT 20;",
        "top_profit": "SELECT c.company_name, MAX(p.net_profit) AS net_profit FROM profitandloss p JOIN companies c ON p.company_id = c.id GROUP BY c.company_name ORDER BY net_profit DESC LIMIT 20;",
        "sector_summary": "SELECT broad_sector, COUNT(*) AS total_companies FROM sectors GROUP BY broad_sector ORDER BY total_companies DESC;",
        "market_cap_summary": "SELECT c.company_name, MAX(m.market_cap_crore) AS market_cap FROM market_cap m JOIN companies c ON m.company_id = c.id GROUP BY c.company_name ORDER BY market_cap DESC LIMIT 20;"
    }
    
    for rname, q in reports.items():
        df = pd.read_sql(q, conn)
        df.to_csv(rep_dir / f"{rname}.csv", index=False)
        print(f"[OK] Exported output/reports/{rname}.csv")
        
    # Output SQL results
    sql_dir = OUTPUT_DIR / "sql_results"
    sql_dir.mkdir(parents=True, exist_ok=True)
    
    queries = {
        "total_companies": "SELECT COUNT(*) AS total_companies FROM companies;",
        "top_roe": "SELECT company_name, roe_percentage FROM companies ORDER BY roe_percentage DESC LIMIT 10;",
        "top_roce": "SELECT company_name, roce_percentage FROM companies ORDER BY roce_percentage DESC LIMIT 10;",
        "top_market_cap": "SELECT c.company_name, m.market_cap_crore FROM market_cap m JOIN companies c ON c.id = m.company_id WHERE m.year = 2026 ORDER BY m.market_cap_crore DESC LIMIT 10;",
        "sector_count": "SELECT broad_sector, COUNT(*) AS companies FROM sectors GROUP BY broad_sector ORDER BY companies DESC;",
        "average_pe": "SELECT ROUND(AVG(pe_ratio), 2) AS average_pe FROM market_cap WHERE year = 2026;",
        "top_dividend": "SELECT c.company_name, m.dividend_yield_pct FROM market_cap m JOIN companies c ON c.id = m.company_id WHERE m.year = 2026 ORDER BY dividend_yield_pct DESC LIMIT 10;",
        "latest_price": """
            WITH ranked AS (
                SELECT company_id, date, close_price, ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY date DESC) as rn
                FROM stock_prices
            )
            SELECT company_id, date AS latest_date, close_price AS latest_close
            FROM ranked WHERE rn = 1;
        """,
        "top_sales": "SELECT c.company_name, MAX(p.sales) AS sales FROM profitandloss p JOIN companies c ON p.company_id = c.id GROUP BY c.company_name ORDER BY sales DESC LIMIT 10;",
        "top_profit": "SELECT c.company_name, MAX(p.net_profit) AS net_profit FROM profitandloss p JOIN companies c ON p.company_id = c.id GROUP BY c.company_name ORDER BY net_profit DESC LIMIT 10;",
        "highest_eps": "SELECT c.company_name, MAX(p.eps) AS eps FROM profitandloss p JOIN companies c ON p.company_id = c.id GROUP BY c.company_name ORDER BY eps DESC LIMIT 10;",
        "top_book_value": "SELECT company_name, book_value FROM companies ORDER BY book_value DESC LIMIT 10;",
        "top_face_value": "SELECT company_name, face_value FROM companies ORDER BY face_value DESC LIMIT 10;",
        "market_cap_category": "SELECT market_cap_category, COUNT(*) AS total_companies FROM sectors GROUP BY market_cap_category ORDER BY total_companies DESC;",
        "average_roe_sector": "SELECT s.broad_sector, ROUND(AVG(c.roe_percentage), 2) AS average_roe FROM companies c JOIN sectors s ON c.id = s.company_id GROUP BY s.broad_sector ORDER BY average_roe DESC;",
        "total_sectors": "SELECT COUNT(DISTINCT broad_sector) AS total_sectors FROM sectors;"
    }
    
    for qname, q in queries.items():
        df = pd.read_sql(q, conn)
        df.to_csv(sql_dir / f"{qname}.csv", index=False)
        print(f"[OK] Exported output/sql_results/{qname}.csv")
        
    conn.close()


def main():
    print("STARTING COMPREHENSIVE DATA SYNCHRONIZATION THROUGH 2026...")
    update_market_cap_table()
    sync_raw_excel_files()
    refresh_database_views()
    recompute_peer_percentiles()
    export_reports_and_sql()
    print("\n[OK] DATA SYNCHRONIZATION COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
