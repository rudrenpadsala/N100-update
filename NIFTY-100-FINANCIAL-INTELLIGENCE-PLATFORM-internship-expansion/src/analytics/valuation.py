"""
Day 26 - Valuation Module

Generates:

1. valuation_summary.xlsx
2. valuation_flags.csv
"""

import sqlite3
import pandas as pd
from pathlib import Path

# ==========================================================
# PATHS
# ==========================================================

DB_PATH = "db/nifty100.db"

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

SUMMARY_FILE = OUTPUT_DIR / "valuation_summary.xlsx"

FLAGS_FILE = OUTPUT_DIR / "valuation_flags.csv"


# ==========================================================
# CONNECT DATABASE
# ==========================================================

conn = sqlite3.connect(DB_PATH)

print("Connected to database")


# ==========================================================
# LOAD TABLES
# ==========================================================

companies = pd.read_sql(
    "SELECT * FROM companies",
    conn,
)

ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn,
)

market = pd.read_sql(
    "SELECT * FROM market_cap",
    conn,
)

sectors = pd.read_sql(
    "SELECT * FROM sectors",
    conn,
)

conn.close()

print("Loaded Tables")

print("Companies :", len(companies))
print("Ratios    :", len(ratios))
print("MarketCap :", len(market))
print("Sectors   :", len(sectors))

# ==========================================================
# KEEP LATEST RECORD FOR EACH COMPANY
# ==========================================================

# Financial Ratios
ratios = (
    ratios
    .sort_values("year")
    .groupby("company_id", as_index=False)
    .last()
)

# Market Cap
market = (
    market
    .sort_values("year")
    .groupby("company_id", as_index=False)
    .last()
)

print("Latest Ratios :", len(ratios))
print("Latest Market :", len(market))

# ==========================================================
# PREPARE COMPANIES
# ==========================================================

companies = companies.rename(
    columns={
        "id": "company_id"
    }
)

companies = companies[
    [
        "company_id",
        "company_name",
    ]
]

sectors = sectors[
    [
        "company_id",
        "broad_sector",
    ]
]

# ==========================================================
# MERGE ALL TABLES
# ==========================================================

valuation = ratios.merge(

    companies,

    on="company_id",

    how="left",

)

valuation = valuation.merge(

    market,

    on="company_id",

    how="left",

    suffixes=("", "_market"),

)

valuation = valuation.merge(

    sectors,

    on="company_id",

    how="left",

)

print()

print("Merged Dataset")

print(valuation.shape)

print()

print(valuation.head())

# ==========================================================
# KEEP REQUIRED COLUMNS
# ==========================================================

valuation = valuation[
    [
        "company_id",
        "company_name",
        "broad_sector",
        "free_cash_flow_cr",
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
    ]
]

print()

print("Final Columns")

print(valuation.columns.tolist())

# ==========================================================
# HANDLE MISSING VALUES
# ==========================================================

valuation["free_cash_flow_cr"] = (
    valuation["free_cash_flow_cr"]
    .fillna(0)
)

valuation["market_cap_crore"] = (
    valuation["market_cap_crore"]
    .fillna(0)
)

valuation["pe_ratio"] = (
    valuation["pe_ratio"]
    .fillna(0)
)

valuation["pb_ratio"] = (
    valuation["pb_ratio"]
    .fillna(0)
)

valuation["ev_ebitda"] = (
    valuation["ev_ebitda"]
    .fillna(0)
)

# ==========================================================
# FCF YIELD (%)
# ==========================================================

valuation["FCF_yield_pct"] = (

    valuation["free_cash_flow_cr"]

    /

    valuation["market_cap_crore"]

) * 100

valuation["FCF_yield_pct"] = (

    valuation["FCF_yield_pct"]

    .replace([float("inf"), -float("inf")], 0)

    .fillna(0)

)

# ==========================================================
# SECTOR MEDIAN PE
# ==========================================================

sector_median = (

    valuation

    .groupby("broad_sector")["pe_ratio"]

    .median()

    .reset_index()

)

sector_median = sector_median.rename(

    columns={

        "pe_ratio": "sector_median_pe"

    }

)

valuation = valuation.merge(

    sector_median,

    on="broad_sector",

    how="left",

)

# ==========================================================
# PE VS SECTOR MEDIAN (%)
# ==========================================================

valuation["PE_vs_sector_median_pct"] = (

    valuation["pe_ratio"]

    /

    valuation["sector_median_pe"]

) * 100

valuation["PE_vs_sector_median_pct"] = (

    valuation["PE_vs_sector_median_pct"]

    .replace([float("inf"), -float("inf")], 0)

    .fillna(0)

)

# ==========================================================
# PREVIEW
# ==========================================================

print()

print("Calculated Columns")

print(

    valuation[

        [

            "company_name",

            "FCF_yield_pct",

            "sector_median_pe",

            "PE_vs_sector_median_pct",

        ]

    ].head()

)

# ==========================================================
# APPLY VALUATION FLAGS
# ==========================================================

def valuation_flag(row):

    pe = row["pe_ratio"]
    sector_pe = row["sector_median_pe"]

    if pd.isna(pe) or pd.isna(sector_pe):
        return "Fair"

    if sector_pe == 0:
        return "Fair"

    if pe > sector_pe * 1.5:
        return "Caution"

    elif pe < sector_pe * 0.7:
        return "Discount"

    else:
        return "Fair"


valuation["flag"] = valuation.apply(
    valuation_flag,
    axis=1,
)

# ==========================================================
# RENAME COLUMNS
# ==========================================================

valuation = valuation.rename(
    columns={
        "broad_sector": "sector",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "ev_ebitda": "EV/EBITDA",
        "sector_median_pe": "5yr_median_PE",
    }
)

# ==========================================================
# FINAL OUTPUT COLUMNS
# ==========================================================

valuation_summary = valuation[
    [
        "company_id",
        "company_name",
        "sector",
        "P/E",
        "P/B",
        "EV/EBITDA",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "flag",
    ]
].copy()

print()

print("Flag Summary")

print(
    valuation_summary["flag"].value_counts()
)

# ==========================================================
# EXPORT EXCEL
# ==========================================================

valuation_summary.to_excel(

    SUMMARY_FILE,

    index=False,

)

print()

print("valuation_summary.xlsx generated")

# ==========================================================
# EXPORT FLAGGED COMPANIES
# ==========================================================

valuation_flags = valuation_summary[

    valuation_summary["flag"].isin(

        [

            "Caution",

            "Discount",

        ]

    )

].copy()

valuation_flags.to_csv(

    FLAGS_FILE,

    index=False,

)

print("valuation_flags.csv generated")


# ==========================================================
# DASHBOARD SUMMARY
# ==========================================================

print()

print("=" * 60)

print("VALUATION MODULE COMPLETE")

print("=" * 60)

print()

print("Total Companies :", len(valuation_summary))

print()

print("Flag Counts")

print(

    valuation_summary["flag"].value_counts()

)

print()

print("Output Files")

print("✔", SUMMARY_FILE)

print("✔", FLAGS_FILE)

print()

print("=" * 60)

# ==========================================================
# TOP 10 HIGHEST FCF YIELD
# ==========================================================

print()

print("Top 10 Companies by FCF Yield")

print(

    valuation_summary

    .sort_values(

        "FCF_yield_pct",

        ascending=False,

    )

    [

        [

            "company_name",

            "FCF_yield_pct",

            "flag",

        ]

    ]

    .head(10)

)

