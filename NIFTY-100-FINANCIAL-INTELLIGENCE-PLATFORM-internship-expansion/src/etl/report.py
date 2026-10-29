"""
report.py

Generate validation reports.
"""

from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)


def save_validation_report(failures):

    df = pd.DataFrame(failures)

    csv_file = OUTPUT_DIR / "validation_failures.csv"

    df.to_csv(csv_file, index=False)

    print(f"\nValidation report saved: {csv_file}")

    return df


def generate_summary(df):

    if df.empty:

        summary = pd.DataFrame(
            {
                "Total Failures": [0],
                "Critical": [0],
                "Warning": [0],
            }
        )

    else:

        summary = pd.DataFrame(
            {
                "Total Failures": [len(df)],
                "Critical": [len(df[df["severity"] == "CRITICAL"])],
                "Warning": [len(df[df["severity"] == "WARNING"])],
            }
        )

    summary_file = OUTPUT_DIR / "validation_summary.csv"

    summary.to_csv(summary_file, index=False)

    print(f"Summary report saved: {summary_file}")