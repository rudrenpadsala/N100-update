"""
review_summary.py

Day 6 Review Summary
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT = BASE_DIR / "output"

coverage_file = OUTPUT / "company_year_coverage.csv"
validation_file = OUTPUT / "validation_failures.csv"

# ------------------------------------
# Read Reports
# ------------------------------------

coverage = pd.read_csv(coverage_file)
validation = pd.read_csv(validation_file)

# ------------------------------------
# Statistics
# ------------------------------------

total_companies = len(coverage)

less_than_5 = len(
    coverage[
        coverage["less_than_5_years"] == "YES"
    ]
)

total_failures = len(validation)

critical = len(
    validation[
        validation["severity"] == "CRITICAL"
    ]
)

warning = len(
    validation[
        validation["severity"] == "WARNING"
    ]
)

# ------------------------------------
# Summary
# ------------------------------------

summary = pd.DataFrame({

    "Metric": [

        "Total Companies",

        "Companies <5 Years",

        "Validation Failures",

        "Critical Failures",

        "Warning Failures"

    ],

    "Value": [

        total_companies,

        less_than_5,

        total_failures,

        critical,

        warning

    ]

})

summary_path = OUTPUT / "review_summary.csv"

summary.to_csv(summary_path, index=False)

print("=" * 60)
print("DAY 6 REVIEW SUMMARY")
print("=" * 60)

print(summary)

print("\nSummary Saved")

print(summary_path)