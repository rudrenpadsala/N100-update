"""
check_load_audit.py

Verify load_audit.csv for CRITICAL rejections.
"""

from pathlib import Path
import pandas as pd

# ==========================================
# File Path
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]
AUDIT_FILE = BASE_DIR / "output" / "load_audit.csv"

print("=" * 60)
print("Checking Load Audit")
print("=" * 60)

if not AUDIT_FILE.exists():
    print("❌ load_audit.csv not found.")
    exit()

df = pd.read_csv(AUDIT_FILE)

print("\nTotal Tables :", len(df))

# ------------------------------------------
# Detect critical/rejected rows
# ------------------------------------------

if "status" in df.columns:
    critical = df[df["status"].astype(str).str.upper() == "CRITICAL"]
elif "rejections" in df.columns:
    critical = df[df["rejections"] > 0]
else:
    critical = pd.DataFrame()

if critical.empty:
    print("\n✅ Zero CRITICAL rejections found.")
else:
    print("\n❌ CRITICAL rejections found:")
    print(critical)

print("\nAudit Summary")
print(df)

print("\nCheck completed.")