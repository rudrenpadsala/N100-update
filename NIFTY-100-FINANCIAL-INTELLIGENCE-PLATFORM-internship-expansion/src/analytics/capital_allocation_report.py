"""
capital_allocation_report.py

Sprint 5
Day 32

Capital Allocation Report

Verifies the existing output/capital_allocation.csv (produced by
src/analytics/capital_allocation.py in an earlier sprint), then adds
two Sprint 5 deliverables on top of the same cash flow signage logic
already implemented in src/analytics/cashflow_kpis.py:

    - A pattern distribution summary (how many companies currently
      sit in each capital allocation pattern).
    - pattern_changes.csv (companies whose pattern this year differs
      from their pattern the previous year).

Also appends both as new sheets to output/cashflow_intelligence.xlsx
(Day 31 deliverable) so the two Sprint 5 analyses live together.

Outputs:
    output/pattern_distribution.csv
    output/pattern_changes.csv
    output/cashflow_intelligence.xlsx (updated, new sheets appended)
"""

import os
import sqlite3

import pandas as pd
from openpyxl import load_workbook

from src.analytics.cashflow_kpis import capital_allocation_pattern, _year_key

DB_PATH = "db/nifty100.db"
OUTPUT_DIR = "output"
EXISTING_ALLOCATION_CSV = os.path.join(OUTPUT_DIR, "capital_allocation.csv")
INTELLIGENCE_XLSX = os.path.join(OUTPUT_DIR, "cashflow_intelligence.xlsx")

EXPECTED_ALLOCATION_COLUMNS = {
    "company_id", "year", "net_profit", "dividend_payout",
    "borrowings", "operating_activity", "capex", "free_cash_flow"
}


# --------------------------------------------------
# Step 1: Verify Existing Capital Allocation Data
# --------------------------------------------------

def verify_existing_capital_allocation():
    """
    Sanity-check output/capital_allocation.csv from the earlier
    sprint before building on top of it. Does not modify the file.
    """

    if not os.path.exists(EXISTING_ALLOCATION_CSV):
        print(f"⚠ {EXISTING_ALLOCATION_CSV} not found — run "
              f"src/analytics/capital_allocation.py first.")
        return None

    existing = pd.read_csv(EXISTING_ALLOCATION_CSV)

    missing_cols = EXPECTED_ALLOCATION_COLUMNS - set(existing.columns)

    print(f"✔ Verified {EXISTING_ALLOCATION_CSV}")
    print(f"  Rows            : {len(existing)}")
    print(f"  Companies       : {existing['company_id'].nunique()}")

    if missing_cols:
        print(f"  ⚠ Missing expected columns: {missing_cols}")
    else:
        print("  Columns         : OK")

    duplicate_rows = existing.duplicated(subset=["company_id", "year"]).sum()

    if duplicate_rows:
        print(f"  ⚠ {duplicate_rows} duplicate company/year rows found "
              f"(pre-existing data quality issue, not modified here).")

    return existing


# --------------------------------------------------
# Step 2: Company/Year Pattern Table
# --------------------------------------------------

def build_pattern_history():
    """
    Recompute the full (cfo_sign, cfi_sign, cff_sign, pattern_label)
    history for every company/year, scoped to the 92 master
    companies, deduplicated on (company_id, year).

    Sprint 5 data-quality note: reuses cashflow_kpis._year_key() to
    collapse the "Mar 2024" / "Mar-24" duplicate rows in the raw
    `cashflow` table onto a single canonical year (see Day 31 for
    the full explanation).
    """

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql("SELECT id FROM companies", conn)
    valid_ids = set(companies["id"])

    cashflow = pd.read_sql(
        "SELECT company_id, year, operating_activity, investing_activity, "
        "financing_activity FROM cashflow",
        conn
    )

    conn.close()

    cashflow = cashflow[cashflow["company_id"].isin(valid_ids)]
    cashflow = cashflow[cashflow["year"] != "TTM"]
    cashflow["year_key"] = _year_key(cashflow["year"])
    cashflow = cashflow.dropna(subset=["year_key"])
    cashflow = cashflow.sort_values(["company_id", "year_key"])
    cashflow = cashflow.drop_duplicates(subset=["company_id", "year_key"], keep="first")

    rows = []

    for _, row in cashflow.iterrows():

        cfo_sign, cfi_sign, cff_sign, pattern = capital_allocation_pattern(
            row["operating_activity"],
            row["investing_activity"],
            row["financing_activity"]
        )

        rows.append({
            "company_id": row["company_id"],
            "year": row["year"],
            "year_key": row["year_key"],
            "cfo_sign": cfo_sign,
            "cfi_sign": cfi_sign,
            "cff_sign": cff_sign,
            "pattern_label": pattern
        })

    history = pd.DataFrame(rows)
    history = history.sort_values(["company_id", "year_key"])

    return history


# --------------------------------------------------
# Step 3: Pattern Distribution Summary
# --------------------------------------------------

def build_pattern_distribution(history):
    """
    Distribution of the latest-year capital allocation pattern
    across all companies.
    """

    latest = history.drop_duplicates(subset=["company_id"], keep="last")

    distribution = (
        latest["pattern_label"]
        .value_counts()
        .rename_axis("pattern_label")
        .reset_index(name="company_count")
    )

    distribution["pct_of_companies"] = round(
        distribution["company_count"] / len(latest) * 100, 1
    )

    return distribution.sort_values("company_count", ascending=False)


# --------------------------------------------------
# Step 4: Pattern Changes
# --------------------------------------------------

def build_pattern_changes(history):
    """
    Companies whose latest-year pattern differs from their
    previous reported year's pattern.
    """

    changes = []

    for company_id, group in history.groupby("company_id"):

        group = group.reset_index(drop=True)

        if len(group) < 2:
            continue

        previous = group.iloc[-2]
        latest = group.iloc[-1]

        if previous["pattern_label"] != latest["pattern_label"]:
            changes.append({
                "company_id": company_id,
                "previous_year": previous["year"],
                "previous_pattern": previous["pattern_label"],
                "latest_year": latest["year"],
                "latest_pattern": latest["pattern_label"]
            })

    return pd.DataFrame(changes)


# --------------------------------------------------
# Step 5: Append to cashflow_intelligence.xlsx
# --------------------------------------------------

def append_to_intelligence_workbook(distribution, changes):

    if not os.path.exists(INTELLIGENCE_XLSX):
        print(f"⚠ {INTELLIGENCE_XLSX} not found — run "
              f"src/analytics/cashflow_kpis.py (Day 31) first. Skipping update.")
        return

    with pd.ExcelWriter(
        INTELLIGENCE_XLSX,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace"
    ) as writer:

        distribution.to_excel(writer, sheet_name="Pattern_Distribution", index=False)
        changes.to_excel(writer, sheet_name="Pattern_Changes", index=False)

    print(f"✔ Updated {INTELLIGENCE_XLSX} with Pattern_Distribution and Pattern_Changes sheets")


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

def main():

    print("=" * 60)
    print("Capital Allocation Report (Sprint 5 - Day 32)")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    verify_existing_capital_allocation()

    history = build_pattern_history()
    distribution = build_pattern_distribution(history)
    changes = build_pattern_changes(history)

    distribution_path = os.path.join(OUTPUT_DIR, "pattern_distribution.csv")
    changes_path = os.path.join(OUTPUT_DIR, "pattern_changes.csv")

    distribution.to_csv(distribution_path, index=False)
    changes.to_csv(changes_path, index=False)

    append_to_intelligence_workbook(distribution, changes)

    print(f"\n✔ Pattern distribution ({len(distribution)} patterns):")
    print(distribution.to_string(index=False))
    print(f"\n✔ Companies with a pattern change: {len(changes)}")
    print(f"✔ Saved: {distribution_path}")
    print(f"✔ Saved: {changes_path}")


if __name__ == "__main__":
    main()
