import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"

conn = sqlite3.connect(DB_PATH)

ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn
)

conn.close()

print("=" * 60)
print("KPI VALIDATION REPORT")
print("=" * 60)

kpi_columns = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "free_cash_flow_cr"
]

report = []

for col in kpi_columns:

    report.append({
        "KPI": col,
        "Total Rows": len(ratios),
        "Non Null": ratios[col].count(),
        "Null": ratios[col].isnull().sum()
    })

validation = pd.DataFrame(report)

print(validation)

validation.to_csv(
    "output/kpi_validation_report.csv",
    index=False
)

print("\n✓ KPI Validation Report Saved")
print("output/kpi_validation_report.csv")