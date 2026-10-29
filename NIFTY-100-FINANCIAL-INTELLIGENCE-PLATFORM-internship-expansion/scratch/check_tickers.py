import sqlite3
import re
import os
import shutil
import time
import pandas as pd
import yfinance as yf

DB_PATH = 'NIFTY-100-FINANCIAL-INTELLIGENCE-PLATFORM-internship-expansion/db/nifty100.db'
BACKUP_PATH = 'NIFTY-100-FINANCIAL-INTELLIGENCE-PLATFORM-internship-expansion/db/nifty100_backup_pre2025.db'

# 1. Backup database if not already backed up
if not os.path.exists(BACKUP_PATH):
    shutil.copyfile(DB_PATH, BACKUP_PATH)
    print(f"Created backup at {BACKUP_PATH}")
else:
    print(f"Backup already exists at {BACKUP_PATH}")

conn = sqlite3.connect(DB_PATH)
companies = conn.execute("SELECT id, company_name, nse_profile FROM companies ORDER BY id").fetchall()

# Map company_id to Yahoo Finance ticker
def get_yf_ticker(cid, nse_profile):
    sym = cid
    if nse_profile and 'symbol=' in nse_profile:
        m = re.search(r'symbol=([^&]+)', nse_profile)
        if m:
            sym = m.group(1)
    # Special cases
    if cid == 'ABB':
        sym = 'ABBOTINDIA'
    return f"{sym}.NS"

print(f"Total companies to update: {len(companies)}")
tickers = {cid: get_yf_ticker(cid, nse) for cid, name, nse in companies}
print("Sample tickers:", list(tickers.items())[:10])
