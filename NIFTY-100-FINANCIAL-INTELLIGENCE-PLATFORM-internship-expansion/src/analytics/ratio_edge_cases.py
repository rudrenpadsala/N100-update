import sqlite3
import pandas as pd
import os

DB_PATH = "db/nifty100.db"

conn = sqlite3.connect(DB_PATH)

companies = pd.read_sql(
    "SELECT * FROM companies",
    conn
)

ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn
)

conn.close()

print("Companies :", len(companies))
print("Ratios    :", len(ratios))

# ----------------------------------
# Merge
# ----------------------------------

df = ratios.merge(
    companies,
    left_on="company_id",
    right_on="id",
    how="left"
)

edge_cases = []

for _, row in df.iterrows():

    # ROE comparison
    if (
        pd.notna(row["return_on_equity_pct"])
        and pd.notna(row["roe_percentage"])
    ):

        diff = abs(
            row["return_on_equity_pct"]
            - row["roe_percentage"]
        )

        if diff > 5:

            edge_cases.append({
                "company_id": row["company_id"],
                "year": row["year"],
                "metric": "ROE",
                "calculated": row["return_on_equity_pct"],
                "source": row["roe_percentage"],
                "difference": round(diff,2),
                "category": "Formula Difference"
            })

os.makedirs("output", exist_ok=True)

pd.DataFrame(edge_cases).to_csv(
    "output/ratio_edge_cases.csv",
    index=False
)

print("\nEdge Cases Found :", len(edge_cases))

print("\nSaved:")
print("output/ratio_edge_cases.csv")


# ----------------------------------
# Create Log File
# ----------------------------------

with open("output/ratio_edge_cases.log", "w") as log:

    log.write("Ratio Edge Cases\n")
    log.write("=" * 60 + "\n\n")

    if len(edge_cases) == 0:
        log.write("No anomalies found.\n")

    else:

        for item in edge_cases:

            log.write(
                f"{item['company_id']} | "
                f"{item['year']} | "
                f"{item['metric']} | "
                f"Calculated={item['calculated']:.2f} | "
                f"Source={item['source']:.2f} | "
                f"Difference={item['difference']:.2f} | "
                f"{item['category']}\n"
            )

print("✓ ratio_edge_cases.log created")

