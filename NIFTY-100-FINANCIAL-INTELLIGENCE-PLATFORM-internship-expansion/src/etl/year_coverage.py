"""
year_coverage.py

Checks:
1. Year coverage for each company
2. Companies having less than 5 years of data

Output:
output/company_year_coverage.csv
"""

from pathlib import Path
import pandas as pd

from loader import load_all_excel_files

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def main():

    datasets = load_all_excel_files()

    companies = datasets["companies"]
    profit = datasets["profitandloss"]

    report = []

    for _, company in companies.iterrows():

        company_id = str(company["id"]).strip()

        df = profit[
            profit["company_id"]
            .astype(str)
            .str.strip()
            == company_id
        ]

        years = sorted(
            df["year"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        report.append({

            "company_id": company_id,

            "company_name": company["company_name"],

            "year_count": len(years),

            "first_year": years[0] if years else "",

            "last_year": years[-1] if years else "",

            "less_than_5_years": "YES" if len(years) < 5 else "NO"

        })

    report_df = pd.DataFrame(report)

    output_file = OUTPUT_DIR / "company_year_coverage.csv"

    report_df.to_csv(output_file, index=False)

    print("=" * 70)
    print("Year Coverage Report Generated")
    print("=" * 70)

    print(report_df.head())

    print("\nSaved :", output_file)


if __name__ == "__main__":
    main()