"""
dq_rules.py

Data Quality Rules (DQ-01 to DQ-08)
"""

import pandas as pd


# -------------------------------------------------
# DQ-01 Primary Key Uniqueness
# -------------------------------------------------
def dq01_primary_key(df, dataset_name):
    failures = []

    if "id" not in df.columns:
        return failures

    duplicates = df[df["id"].duplicated()]

    for index, row in duplicates.iterrows():
        failures.append({
            "rule": "DQ-01",
            "severity": "CRITICAL",
            "dataset": dataset_name,
            "row": index + 2,
            "message": f"Duplicate Primary Key: {row['id']}"
        })

    return failures


# -------------------------------------------------
# DQ-02 company_id + year uniqueness
# -------------------------------------------------
def dq02_company_year(df, dataset_name):

    failures = []

    required = ["company_id", "year"]

    if not all(col in df.columns for col in required):
        return failures

    duplicates = df[
        df.duplicated(
            subset=["company_id", "year"],
            keep=False
        )
    ]

    for index, row in duplicates.iterrows():

        failures.append({

            "rule": "DQ-02",

            "severity": "CRITICAL",

            "dataset": dataset_name,

            "row": index + 2,

            "message": (
                f"Duplicate company_id={row['company_id']} "
                f"year={row['year']}"
            )

        })

    return failures

# -------------------------------------------------
# DQ-03 company_id should exist
# -------------------------------------------------
# -------------------------------------------------
# DQ-03 Foreign Key Check
# company_id must exist in companies table
# -------------------------------------------------
def dq03_foreign_key(df, companies, dataset_name):

    failures = []

    # Skip datasets without company_id
    if "company_id" not in df.columns:
        return failures

    # Normalize company IDs from companies table
    valid_ids = (
        companies["id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Normalize company IDs from current dataset
    company_ids = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Find invalid company IDs
    invalid_rows = df[~company_ids.isin(valid_ids)]

    # Store failures
    for index, row in invalid_rows.iterrows():

        failures.append({

            "rule": "DQ-03",

            "severity": "CRITICAL",

            "dataset": dataset_name,

            "row": index + 2,

            "message": f"Invalid company_id '{row['company_id']}' not found in companies table"

        })

    return failures


# -------------------------------------------------
# DQ-04 Balance Sheet Check
# Assets ≈ Liabilities
# -------------------------------------------------
def dq04_balance_sheet(df):

    failures = []

    required = [

        "total_assets",

        "total_liabilities"

    ]

    if not all(col in df.columns for col in required):
        return failures

    tolerance = 0.01

    for index, row in df.iterrows():

        assets = row["total_assets"]

        liabilities = row["total_liabilities"]

        if pd.isna(assets) or pd.isna(liabilities):
            continue

        if assets == 0:
            continue

        difference = abs(assets - liabilities) / assets

        if difference > tolerance:

            failures.append({

                "rule": "DQ-04",

                "severity": "WARNING",

                "dataset": "balancesheet",

                "row": index + 2,

                "message": "Balance Sheet mismatch"

            })

    return failures


# -------------------------------------------------
# DQ-05 OPM Check
# -------------------------------------------------

def dq05_opm(df):

    failures = []

    required = [
        "sales",
        "operating_profit",
        "opm_percentage"
    ]

    if not all(col in df.columns for col in required):
        return failures

    for index, row in df.iterrows():

        sales = row["sales"]
        op = row["operating_profit"]
        opm = row["opm_percentage"]

        # Skip missing values
        if pd.isna(sales):
            continue

        if pd.isna(op):
            continue

        if pd.isna(opm):
            continue

        # Avoid division by zero
        if sales == 0:
            continue

        calculated_opm = round((op / sales) * 100, 2)

        if abs(calculated_opm - opm) > 1:

            failures.append({

                "rule": "DQ-05",

                "severity": "WARNING",

                "dataset": "profitandloss",

                "row": index + 2,

                "message": (
                    f"Incorrect OPM "
                    f"(Expected {calculated_opm}, Found {opm})"
                )

            })

    return failures


# -------------------------------------------------
# DQ-06 Positive Sales
# -------------------------------------------------
def dq06_positive_sales(df):

    failures = []

    if "sales" not in df.columns:
        return failures

    invalid = df[df["sales"] <= 0]

    for index, row in invalid.iterrows():

        failures.append({

            "rule": "DQ-06",

            "severity": "WARNING",

            "dataset": "profitandloss",

            "row": index + 2,

            "message": "Sales <= 0"

        })

    return failures


# -------------------------------------------------
# DQ-07 Positive Expenses
# -------------------------------------------------
def dq07_positive_expenses(df):

    failures = []

    if "expenses" not in df.columns:
        return failures

    invalid = df[df["expenses"] < 0]

    for index, row in invalid.iterrows():

        failures.append({

            "rule": "DQ-07",

            "severity": "WARNING",

            "dataset": "profitandloss",

            "row": index + 2,

            "message": "Negative Expenses"

        })

    return failures


# -------------------------------------------------
# DQ-08 Net Profit Check
# -------------------------------------------------
def dq08_net_profit(df):

    failures = []

    if "net_profit" not in df.columns:
        return failures

    invalid = df[df["net_profit"].isna()]

    for index, row in invalid.iterrows():

        failures.append({

            "rule": "DQ-08",

            "severity": "WARNING",

            "dataset": "profitandloss",

            "row": index + 2,

            "message": "Missing Net Profit"

        })
    return failures

# -------------------------------------------------
# DQ-09 Missing Year
# -------------------------------------------------
def dq09_missing_year(df, dataset_name):

    failures = []

    if "year" not in df.columns:
        return failures

    invalid = df[df["year"].isna()]

    for index, row in invalid.iterrows():

        failures.append({

            "rule": "DQ-09",

            "severity": "WARNING",

            "dataset": dataset_name,

            "row": index + 2,

            "message": "Missing Year"

        })

    return failures


# -------------------------------------------------
# DQ-10 Future Year
# -------------------------------------------------
def dq10_future_year(df, dataset_name):

    failures = []

    if "year" not in df.columns:
        return failures

    current_year = pd.Timestamp.now().year

    years = pd.to_numeric(df["year"], errors="coerce")

    invalid = df[years > current_year]

    for index, row in invalid.iterrows():

        failures.append({

            "rule": "DQ-10",

            "severity": "WARNING",

            "dataset": dataset_name,

            "row": index + 2,

            "message": f"Future Year {row['year']}"

        })

    return failures


# -------------------------------------------------
# DQ-11 Net Cash Flow Missing
# -------------------------------------------------
def dq11_cashflow(df):

    failures = []

    if "net_cash_flow" not in df.columns:
        return failures

    invalid = df[df["net_cash_flow"].isna()]

    for index, row in invalid.iterrows():

        failures.append({

            "rule": "DQ-11",

            "severity": "WARNING",

            "dataset": "cashflow",

            "row": index + 2,

            "message": "Missing Net Cash Flow"

        })

    return failures


# -------------------------------------------------
# DQ-12 Website Missing
# -------------------------------------------------
def dq12_website(df):

    failures = []

    if "website" not in df.columns:
        return failures

    invalid = df[df["website"].isna()]

    for index, row in invalid.iterrows():

        failures.append({

            "rule": "DQ-12",

            "severity": "WARNING",

            "dataset": "companies",

            "row": index + 2,

            "message": "Missing Website"

        })

    return failures


# -------------------------------------------------
# DQ-13 Close Price Missing
# -------------------------------------------------
def dq13_stock_price(df):

    failures = []

    if "close_price" not in df.columns:
        return failures

    invalid = df[df["close_price"].isna()]

    for index, row in invalid.iterrows():

        failures.append({

            "rule": "DQ-13",

            "severity": "WARNING",

            "dataset": "stock_prices",

            "row": index + 2,

            "message": "Missing Close Price"

        })

    return failures


# -------------------------------------------------
# DQ-14 Sector Missing
# -------------------------------------------------
def dq14_sector(df):

    failures = []

    if "broad_sector" not in df.columns:
        return failures

    invalid = df[df["broad_sector"].isna()]

    for index, row in invalid.iterrows():

        failures.append({

            "rule": "DQ-14",

            "severity": "WARNING",

            "dataset": "sectors",

            "row": index + 2,

            "message": "Missing Sector"

        })

    return failures


# -------------------------------------------------
# DQ-15 Market Cap Missing
# -------------------------------------------------
def dq15_market_cap(df):

    failures = []

    if "market_cap_crore" not in df.columns:
        return failures

    invalid = df[df["market_cap_crore"].isna()]

    for index, row in invalid.iterrows():

        failures.append({

            "rule": "DQ-15",

            "severity": "WARNING",

            "dataset": "market_cap",

            "row": index + 2,

            "message": "Missing Market Cap"

        })

    return failures


# -------------------------------------------------
# DQ-16 Duplicate Company Name
# -------------------------------------------------
def dq16_duplicate_company(df):

    failures = []

    if "company_name" not in df.columns:
        return failures

    duplicates = df[df["company_name"].duplicated()]

    for index, row in duplicates.iterrows():

        failures.append({

            "rule": "DQ-16",

            "severity": "CRITICAL",

            "dataset": "companies",

            "row": index + 2,

            "message": f"Duplicate Company {row['company_name']}"

        })

    return failures

    