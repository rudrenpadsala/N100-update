import sqlite3
import numpy as np
import pandas as pd

from pathlib import Path

# ==========================================================
# PATHS
# ==========================================================

DB_PATH = "db/nifty100.db"

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "peer_comparison.xlsx"


# ==========================================================
# LOAD TABLES
# ==========================================================

def load_tables():
    """
    Load all required SQLite tables.
    """

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql(
        "SELECT * FROM companies",
        conn
    )

    financial_ratios = pd.read_sql(
        "SELECT * FROM financial_ratios",
        conn
    )

    peer_groups = pd.read_sql(
        "SELECT * FROM peer_groups",
        conn
    )

    analysis = pd.read_sql(
        "SELECT * FROM analysis",
        conn
    )

    sectors = pd.read_sql(
        "SELECT * FROM sectors",
        conn
    )

    market_cap = pd.read_sql(
        "SELECT * FROM market_cap",
        conn
    )

    conn.close()

    return (
        companies,
        financial_ratios,
        peer_groups,
        analysis,
        sectors,
        market_cap
    )


# ==========================================================
# KEEP LATEST YEAR
# ==========================================================

def latest_year(df):
    """
    Keep latest financial year for each company.
    """

    if "year" not in df.columns:
        return df.copy()

    latest = (
        df
        .sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    return latest


# ==========================================================
# PREPARE DATA
# ==========================================================

def prepare_data():
    """
    Build one master dataframe for peer ranking.
    """

    (
        companies,
        financial_ratios,
        peer_groups,
        analysis,
        sectors,
        market_cap
    ) = load_tables()

    # ---------------------------------------------
    # Latest financial ratios
    # ---------------------------------------------

    financial_ratios = latest_year(financial_ratios)

    # ---------------------------------------------
    # Latest market cap
    # ---------------------------------------------

    market_cap = latest_year(market_cap)

    # ---------------------------------------------
    # Analysis has multiple rows per company.
    # Keep only ONE row.
    # ---------------------------------------------

    analysis = analysis.drop_duplicates(
        subset="company_id",
        keep="last"
    )

        # ---------------------------------------------
    # Merge Companies
    # company_id == companies.id
    # ---------------------------------------------

    df = financial_ratios.merge(
        companies,
        left_on="company_id",
        right_on="id",
        how="left",
        suffixes=("", "_company")
    )

    # ---------------------------------------------
    # Merge Analysis
    # ---------------------------------------------

    df = df.merge(
        analysis,
        on="company_id",
        how="left",
        suffixes=("", "_analysis")
    )

    # ---------------------------------------------
    # Merge Sector
    # ---------------------------------------------

    df = df.merge(
        sectors[
            [
                "company_id",
                "broad_sector",
                "sub_sector",
                "market_cap_category"
            ]
        ],
        on="company_id",
        how="left"
    )

    # ---------------------------------------------
    # Merge Market Cap
    # ---------------------------------------------

    df = df.merge(
        market_cap[
            [
                "company_id",
                "market_cap_crore",
                "pe_ratio",
                "pb_ratio",
                "dividend_yield_pct"
            ]
        ],
        on="company_id",
        how="left"
    )

    # ---------------------------------------------
    # Merge Peer Groups
    # ---------------------------------------------

    df = df.merge(
        peer_groups[
            [
                "company_id",
                "peer_group_name",
                "is_benchmark"
            ]
        ],
        on="company_id",
        how="left"
    )

    # ---------------------------------------------
    # Remove duplicate companies
    # ---------------------------------------------

    df = (
        df
        .drop_duplicates(
            subset="company_id",
            keep="last"
        )
        .reset_index(drop=True)
    )

    return df


# ==========================================================
# PREVIEW TABLES
# ==========================================================

def preview_tables():
    """
    Preview loaded tables.
    """

    (
        companies,
        financial_ratios,
        peer_groups,
        analysis,
        sectors,
        market_cap
    ) = load_tables()

    print("=" * 60)
    print("DATA LOADED")
    print("=" * 60)

    print(f"Companies          : {len(companies)}")
    print(f"Financial Ratios   : {len(financial_ratios)}")
    print(f"Peer Groups        : {len(peer_groups)}")
    print(f"Analysis           : {len(analysis)}")
    print(f"Sectors            : {len(sectors)}")
    print(f"Market Cap         : {len(market_cap)}")


# ==========================================================
# PREVIEW PREPARED DATA
# ==========================================================

def preview_prepared_data():
    """
    Preview prepared dataframe.
    """

    df = prepare_data()

    print("=" * 60)
    print("PREPARED DATA")
    print("=" * 60)

    print(df.head())

    print("\nRows :", len(df))

    print(
        "Peer Groups Assigned :",
        df["peer_group_name"].notna().sum()
    )

    return df


# ==========================================================
# Percentile Rank
# ==========================================================

def calculate_percentile(series, inverse=False):
    """
    Calculate percentile rank (0-100).

    inverse=True means lower values are better.
    """

    if len(series) == 1:
        return pd.Series([100], index=series.index)

    rank = series.rank(method="average", pct=True)

    if inverse:
        rank = 1 - rank

    return (rank * 100).round(2)


# ==========================================================
# Peer Percentile Engine
# ==========================================================

def calculate_peer_percentiles():

    """
    Compute peer percentile rankings
    for every company inside its peer group.
    """

    df = prepare_data()

    metrics = {

        "ROE": (
            "return_on_equity_pct",
            False
        ),

        "ROCE": (
            "roce_percentage",
            False
        ),

        "Net Profit Margin": (
            "net_profit_margin_pct",
            False
        ),

        "Debt to Equity": (
            "debt_to_equity",
            True
        ),

        "Free Cash Flow": (
            "free_cash_flow_cr",
            False
        ),

        "PAT CAGR 5Y": (
            "pat_cagr_5yr",
            False
        ),

        "Revenue CAGR 5Y": (
            "revenue_cagr_5yr",
            False
        ),

        "EPS CAGR 5Y": (
            "eps_cagr_5yr",
            False
        ),

        "Interest Coverage": (
            "interest_coverage",
            False
        ),

        "Asset Turnover": (
            "asset_turnover",
            False
        )

    }

    results = []

    grouped = df.groupby("peer_group_name")

    for peer_name, group in grouped:

        if pd.isna(peer_name):
            continue

        for metric_name, (column, inverse) in metrics.items():

            if column not in group.columns:
                continue

            values = group[column].fillna(0)

            percentiles = calculate_percentile(
                values,
                inverse=inverse
            )

            temp = pd.DataFrame({

                "company_id":
                    group["company_id"],

                "peer_group_name":
                    peer_name,

                "metric":
                    metric_name,

                "value":
                    values,

                "percentile_rank":
                    percentiles,

                "year":
                    group["year"]

            })

            results.append(temp)

    final_df = pd.concat(
        results,
        ignore_index=True
    )

    print("\n" + "=" * 60)
    print("Peer Percentiles Generated")
    print("=" * 60)

    print("Rows :", len(final_df))

    print(final_df.head())

    return final_df


# ==========================================================
# Save Peer Percentiles
# ==========================================================

# ==========================================================
# Save Peer Percentiles
# ==========================================================

def save_peer_percentiles():

    """
    Save percentile rankings into SQLite.
    """

    df = calculate_peer_percentiles()

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    # ------------------------------------------
    # Clear old records
    # ------------------------------------------

    cursor.execute(
        "DELETE FROM peer_percentiles"
    )

    conn.commit()

    # ------------------------------------------
    # Insert new records
    # ------------------------------------------

    df.to_sql(
        "peer_percentiles",
        conn,
        if_exists="append",
        index=False
    )

    conn.commit()

    print("\n" + "=" * 60)
    print("Peer Percentiles Saved")
    print("=" * 60)

    print(f"Rows inserted : {len(df)}")

    conn.close()

    return df

# ==========================================================
# Export Peer Comparison Excel
# ==========================================================

# ==========================================================
# Export Peer Comparison Excel
# ==========================================================

def export_peer_comparison(df):

    """
    Export one worksheet per peer group.
    """

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl"
    ) as writer:

        peer_groups = sorted(
            df["peer_group_name"].dropna().unique()
        )

        for peer in peer_groups:

            temp = (
                df[df["peer_group_name"] == peer]
                .sort_values(
                    ["metric", "percentile_rank"],
                    ascending=[True, False]
                )
            )

            sheet = peer[:31]

            temp.to_excel(
                writer,
                sheet_name=sheet,
                index=False
            )

    print("\n" + "=" * 60)
    print("Peer Comparison Excel Generated")
    print("=" * 60)
    print(f"Saved : {OUTPUT_FILE}")

    return OUTPUT_FILE


# ==========================================================
# Main
# ==========================================================

# ==========================================================
# Main
# ==========================================================

def main():

    print("=" * 60)
    print("Peer Ranking Engine")
    print("=" * 60)

    # ------------------------------------------
    # Calculate + Save Peer Percentiles
    # ------------------------------------------

    df = save_peer_percentiles()

    # ------------------------------------------
    # Export Excel
    # ------------------------------------------

    export_peer_comparison(df)

    # ------------------------------------------
    # Summary
    # ------------------------------------------

    print("\n" + "=" * 60)
    print("Peer Ranking Completed Successfully")
    print("=" * 60)

    print(f"Total Percentile Records : {len(df)}")
    print(f"Peer Groups Processed    : {df['peer_group_name'].nunique()}")
    print(f"Metrics Ranked           : {df['metric'].nunique()}")
    print(f"Excel File               : {OUTPUT_FILE}")
    print("SQLite Table             : peer_percentiles")

    print("=" * 60)


# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":
    main()