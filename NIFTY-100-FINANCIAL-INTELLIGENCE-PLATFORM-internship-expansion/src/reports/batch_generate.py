"""
batch_generate.py

Sprint 5
Day 34

Batch Reports

Generates a tearsheet PDF for every company in the 92-company
master list, skipping companies with insufficient data (fewer than
2 years of Profit & Loss history - see
CompanyReportData.has_sufficient_data). Also (re)generates the
sector reports.

Outputs:
    reports/tearsheets/<TICKER>_tearsheet.pdf   (one per company)
    reports/sector/<Sector>_sector_report.pdf   (one per sector)
    output/skipped_tearsheets.csv
"""

import os
import time

import pandas as pd

from src.reports.report_data import get_master_companies
from src.reports.tearsheet import generate_tearsheet
from src.reports.sector_report import generate_all_sector_reports

OUTPUT_DIR = "output"
TEARSHEET_DIR = "reports/tearsheets"


def _basic_pdf_sanity_check(path):
    """
    Lightweight structural check (no external PDF library dependency):
    a well-formed, non-blank multi-KB PDF should have a %PDF header,
    an %%EOF trailer, and be larger than a near-empty page would be.
    """

    try:
        size = os.path.getsize(path)
    except OSError:
        return False, "file not found"

    if size < 3000:
        return False, f"suspiciously small file ({size} bytes) - possible blank page"

    with open(path, "rb") as f:
        head = f.read(8)
        f.seek(-32, os.SEEK_END)
        tail = f.read(32)

    if not head.startswith(b"%PDF-"):
        return False, "missing %PDF header"

    if b"%%EOF" not in tail:
        return False, "missing %%EOF trailer"

    return True, "OK"


def generate_all_tearsheets():

    companies = get_master_companies()

    generated = []
    skipped = []

    for _, row in companies.iterrows():

        company_id = row["id"]

        try:
            path = generate_tearsheet(company_id, output_dir=TEARSHEET_DIR)
        except Exception as exc:  # noqa: BLE001 - batch job must not die on one bad company
            skipped.append({
                "company_id": company_id,
                "company_name": row["company_name"],
                "reason": f"generation error: {exc}"
            })
            continue

        if path is None:
            skipped.append({
                "company_id": company_id,
                "company_name": row["company_name"],
                "reason": "insufficient data (fewer than 2 years of P&L history)"
            })
            continue

        ok, detail = _basic_pdf_sanity_check(path)

        if not ok:
            skipped.append({
                "company_id": company_id,
                "company_name": row["company_name"],
                "reason": f"generated but failed sanity check: {detail}"
            })
            continue

        generated.append(company_id)

    return generated, skipped


def main():

    print("=" * 60)
    print("Batch Report Generation (Sprint 5 - Day 34)")
    print("=" * 60)

    start = time.time()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("\nGenerating company tearsheets...")
    generated, skipped = generate_all_tearsheets()

    skipped_df = pd.DataFrame(skipped, columns=["company_id", "company_name", "reason"])
    skipped_path = os.path.join(OUTPUT_DIR, "skipped_tearsheets.csv")
    skipped_df.to_csv(skipped_path, index=False)

    print(f"✔ Tearsheets generated : {len(generated)}")
    print(f"✔ Tearsheets skipped   : {len(skipped)}")
    print(f"✔ Saved: {skipped_path}")

    print("\nGenerating sector reports...")
    sector_results = generate_all_sector_reports()
    print(f"✔ Sector reports generated : {len(sector_results)}")

    elapsed = time.time() - start
    print(f"\n✔ Batch complete in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
