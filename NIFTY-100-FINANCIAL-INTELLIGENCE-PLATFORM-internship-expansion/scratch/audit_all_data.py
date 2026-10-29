import sqlite3
import os
import glob
import pandas as pd

from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = str(REPO_ROOT / "db" / "nifty100.db")

def audit_db():
    print("=" * 60)
    print("DATABASE AUDIT:")
    print("=" * 60)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for t in tables:
        count = cur.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
        cols = [c[1] for c in cur.execute(f'PRAGMA table_info("{t}")').fetchall()]
        date_cols = [c for c in cols if any(k in c.lower() for k in ['year', 'date', 'period', 'quarter', 'time'])]
        details = []
        for dc in date_cols[:3]:
            try:
                min_v = cur.execute(f'SELECT min("{dc}") FROM "{t}" WHERE "{dc}" IS NOT NULL').fetchone()[0]
                max_v = cur.execute(f'SELECT max("{dc}") FROM "{t}" WHERE "{dc}" IS NOT NULL').fetchone()[0]
                sample_distinct = [str(x[0]) for x in cur.execute(f'SELECT DISTINCT "{dc}" FROM "{t}" WHERE "{dc}" IS NOT NULL ORDER BY "{dc}" DESC LIMIT 5').fetchall()]
                details.append(f"{dc}: range=[{min_v} to {max_v}], recent={sample_distinct}")
            except Exception as e:
                details.append(f"{dc}: err={e}")
        print(f"Table: {t:<28} | Rows: {count:<7} | {' ; '.join(details)}")
    conn.close()

def audit_files():
    print("\n" + "=" * 60)
    print("DATA FILES AUDIT:")
    print("=" * 60)
    base = str(REPO_ROOT)
    patterns = ["data/**/*.csv", "data/**/*.xlsx", "data/**/*.json", "data/**/*.parquet", "output/**/*.json", "output/**/*.csv"]
    for pat in patterns:
        for f in glob.glob(f"{base}/{pat}", recursive=True):
            size = os.path.getsize(f)
            rel = os.path.relpath(f, base)
            print(f"{rel:<50} | {size:>10} bytes")

if __name__ == "__main__":
    audit_db()
    audit_files()
