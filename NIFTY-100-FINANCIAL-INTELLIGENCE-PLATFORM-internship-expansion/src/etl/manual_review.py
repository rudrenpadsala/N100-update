"""
manual_review.py

Manual Data Quality Review
"""

from loader import load_all_excel_files


def main():

    datasets = load_all_excel_files()

    companies = datasets["companies"]

    sample = companies.sample(n=5, random_state=42)

    print("=" * 80)
    print("MANUAL REVIEW")
    print("=" * 80)

    for _, company in sample.iterrows():

        company_id = str(company["id"]).strip()

        print("\n" + "=" * 80)
        print("Company :", company["company_name"])
        print("ID      :", company_id)
        print("=" * 80)

        for dataset_name, df in datasets.items():

            if "company_id" in df.columns:

                rows = df[
                    df["company_id"]
                    .astype(str)
                    .str.strip()
                    == company_id
                ]

                print(f"{dataset_name:<20} {len(rows)} rows")

            elif dataset_name == "companies":

                print(f"{dataset_name:<20} 1 row")


if __name__ == "__main__":
    main()