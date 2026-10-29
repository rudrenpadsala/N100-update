"""
============================================================
Sprint 3 - Day 19
Peer Radar Chart Engine
============================================================

Generates radar (polar) charts for every company using:

• ROE
• ROCE
• Net Profit Margin
• Debt to Equity (inverse)
• Free Cash Flow
• PAT CAGR 5Y
• Revenue CAGR 5Y
• Composite Quality Score

Charts are exported to:

reports/radar_charts/

============================================================
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ==========================================================
# Paths
# ==========================================================

DB_PATH = "db/nifty100.db"

OUTPUT_DIR = Path("reports/radar_charts")

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# Radar Metrics
# ==========================================================

RADAR_METRICS = [

    "return_on_equity_pct",

    "roce_percentage",

    "net_profit_margin_pct",

    "debt_to_equity",

    "free_cash_flow_cr",

    "pat_cagr_5yr",

    "revenue_cagr_5yr",

    "composite_quality_score"

]


# ==========================================================
# Load Database Tables
# ==========================================================

def load_data():
    """
    Load all required tables from SQLite.
    """

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql(
        "SELECT * FROM companies",
        conn
    )

    ratios = pd.read_sql(
        "SELECT * FROM financial_ratios",
        conn
    )

    sectors = pd.read_sql(
        "SELECT * FROM sectors",
        conn
    )

    peer_groups = pd.read_sql(
        "SELECT * FROM peer_groups",
        conn
    )

    conn.close()

    print("=" * 60)
    print("DATA LOADED")
    print("=" * 60)

    print(f"Companies        : {len(companies)}")
    print(f"Financial Ratios : {len(ratios)}")
    print(f"Sectors          : {len(sectors)}")
    print(f"Peer Groups      : {len(peer_groups)}")

    return (
        companies,
        ratios,
        sectors,
        peer_groups
    )


# ==========================================================
# Preview Tables
# ==========================================================

def preview_tables():
    

    companies, ratios, sectors, peer_groups = load_data()

    print("\nCompanies")
    print(companies.head())

    print("\nFinancial Ratios")
    print(ratios.head())

    print("\nSectors")
    print(sectors.head())

    print("\nPeer Groups")
    print(peer_groups.head())


# ==========================================================
# Prepare Data
# ==========================================================

def prepare_data():
    """
    Prepare one latest record per company with
    peer group information.
    """

    companies, ratios, sectors, peer_groups = load_data()

    # ------------------------------------------------------
    # Latest Financial Year
    # ------------------------------------------------------

    ratios = (
        ratios
        .sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    # ------------------------------------------------------
    # Merge Company Master
    # ------------------------------------------------------

    df = ratios.merge(
        companies,
        left_on="company_id",
        right_on="id",
        how="left",
        suffixes=("", "_company")
    )

    # ------------------------------------------------------
    # Merge Sector
    # ------------------------------------------------------

    df = df.merge(
        sectors[
            [
                "company_id",
                "broad_sector",
                "sub_sector"
            ]
        ],
        on="company_id",
        how="left"
    )

    # ------------------------------------------------------
    # Merge Peer Groups
    # ------------------------------------------------------

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

    print("\n" + "=" * 60)
    print("PREPARED DATA")
    print("=" * 60)

    print(f"Companies            : {len(df)}")
    print(
        f"Peer Groups Assigned : "
        f"{df['peer_group_name'].notna().sum()}"
    )

    return df


# ==========================================================
# Preview Prepared Data
# ==========================================================

def preview_prepared_data():

    df = prepare_data()

    print()

    print(df.head())

    print()

    print(df.columns.tolist())

    return df

# ==========================================================
# Normalize Metrics
# ==========================================================

def normalize_metrics(df):
    """
    Normalize radar metrics to 0-100.
    """

    df = df.copy()

    metrics = RADAR_METRICS.copy()

    for metric in metrics:

        if metric not in df.columns:
            continue

        values = pd.to_numeric(
            df[metric],
            errors="coerce"
        )

        # --------------------------------------
        # Debt-to-Equity
        # Lower is Better
        # --------------------------------------

        if metric == "debt_to_equity":

            values = values.fillna(values.max())

            minimum = values.min()
            maximum = values.max()

            if maximum != minimum:

                df[metric + "_score"] = (
                    (
                        maximum - values
                    )
                    /
                    (
                        maximum - minimum
                    )
                ) * 100

            else:

                df[metric + "_score"] = 100

        # --------------------------------------
        # Higher is Better
        # --------------------------------------

        else:

            values = values.fillna(0)

            minimum = values.min()
            maximum = values.max()

            if maximum != minimum:

                df[metric + "_score"] = (
                    (
                        values - minimum
                    )
                    /
                    (
                        maximum - minimum
                    )
                ) * 100

            else:

                df[metric + "_score"] = 100

    return df


# ==========================================================
# Nifty 100 Average
# ==========================================================

def get_nifty_average(df):
    """
    Calculate Nifty100 average scores.
    """

    averages = {}

    for metric in RADAR_METRICS:

        column = metric + "_score"

        if column in df.columns:

            averages[column] = df[column].mean()

    return averages


# ==========================================================
# Peer Group Average
# ==========================================================

def get_peer_average(df, peer_group):
    """
    Average score for one peer group.
    """

    peer_df = df[
        df["peer_group_name"] == peer_group
    ]

    averages = {}

    for metric in RADAR_METRICS:

        column = metric + "_score"

        if column in peer_df.columns:

            averages[column] = peer_df[column].mean()

    return averages


# ==========================================================
# Radar Labels
# ==========================================================

RADAR_LABELS = [

    "ROE",

    "ROCE",

    "Net Profit\nMargin",

    "Debt/\nEquity",

    "Free Cash\nFlow",

    "PAT CAGR\n5Y",

    "Revenue CAGR\n5Y",

    "Composite\nScore"

]


# ==========================================================
# Company Radar Values
# ==========================================================

def get_company_values(company_row):
    """
    Return one company's normalized radar values.
    """

    values = []

    for metric in RADAR_METRICS:

        column = metric + "_score"

        if column in company_row.index:

            value = company_row[column]

            if pd.isna(value):
                value = 0

        else:

            value = 0

        values.append(float(value))

    return values


# ==========================================================
# Peer Average Values
# ==========================================================

def get_peer_values(df, peer_group):
    """
    Return average normalized values
    for one peer group.
    """

    peer_avg = get_peer_average(df, peer_group)

    values = []

    for metric in RADAR_METRICS:

        column = metric + "_score"

        values.append(
            float(
                peer_avg.get(column, 0)
            )
        )

    return values


# ==========================================================
# Nifty100 Average Values
# ==========================================================

def get_nifty_values(df):
    """
    Return Nifty100 average values.
    """

    nifty_avg = get_nifty_average(df)

    values = []

    for metric in RADAR_METRICS:

        column = metric + "_score"

        values.append(
            float(
                nifty_avg.get(column, 0)
            )
        )

    return values


# ==========================================================
# Preview Radar Data
# ==========================================================

def preview_radar_data():

    df = prepare_data()

    df = normalize_metrics(df)

    company = df.iloc[0]

    print("=" * 60)
    print("Company")
    print("=" * 60)

    print(company["company_name"])

    print()

    print(get_company_values(company))

    print()

    if pd.notna(company["peer_group_name"]):

        print("=" * 60)
        print("Peer Average")
        print("=" * 60)

        print(
            get_peer_values(
                df,
                company["peer_group_name"]
            )
        )

    else:

        print("=" * 60)
        print("Nifty Average")
        print("=" * 60)

        print(
            get_nifty_values(df)
        )

# ==========================================================
# Create Radar Chart
# ==========================================================

def create_radar_chart(
    company_name,
    company_values,
    reference_values,
    reference_name,
    output_file
):
    """
    Draw one radar chart.
    """

    labels = RADAR_LABELS

    N = len(labels)

    angles = np.linspace(
        0,
        2 * np.pi,
        N,
        endpoint=False
    ).tolist()

    company_values = company_values.copy()
    reference_values = reference_values.copy()

    company_values += company_values[:1]
    reference_values += reference_values[:1]

    angles += angles[:1]

    # ------------------------------------------------------
    # Figure
    # ------------------------------------------------------

    fig = plt.figure(
        figsize=(8, 8)
    )

    ax = plt.subplot(
        111,
        polar=True
    )

    ax.set_theta_offset(
        np.pi / 2
    )

    ax.set_theta_direction(-1)

    # ------------------------------------------------------
    # Axis Labels
    # ------------------------------------------------------

    plt.xticks(
        angles[:-1],
        labels,
        fontsize=10
    )

    ax.set_rlabel_position(0)

    plt.yticks(
        [20, 40, 60, 80],
        ["20", "40", "60", "80"],
        fontsize=8
    )

    plt.ylim(0, 100)

    # ------------------------------------------------------
    # Company
    # ------------------------------------------------------

    ax.plot(
        angles,
        company_values,
        linewidth=2,
        linestyle="-",
        label=company_name
    )

    ax.fill(
        angles,
        company_values,
        alpha=0.25
    )

    # ------------------------------------------------------
    # Peer Average
    # ------------------------------------------------------

    ax.plot(
        angles,
        reference_values,
        linewidth=2,
        linestyle="--",
        label=reference_name
    )

    # ------------------------------------------------------
    # Title
    # ------------------------------------------------------

    plt.title(
        company_name,
        fontsize=14,
        pad=20
    )

    plt.legend(
        loc="upper right",
        bbox_to_anchor=(1.25, 1.10)
    )

    plt.tight_layout()

    plt.savefig(
        output_file,
        dpi=300
    )

    plt.close(fig)


# ==========================================================
# Generate One Company Radar
# ==========================================================

def generate_company_radar(df, company_row):
    """
    Generate one company's radar chart.
    """

    company_values = get_company_values(company_row)

    if pd.notna(company_row["peer_group_name"]):

        reference_values = get_peer_values(
            df,
            company_row["peer_group_name"]
        )

        reference_name = (
            company_row["peer_group_name"]
            + " Average"
        )

    else:

        reference_values = get_nifty_values(df)

        reference_name = "Nifty100 Average"

    company_name = company_row["company_id"]

    output_file = (
        OUTPUT_DIR /
        f"{company_name}_radar.png"
    )

    create_radar_chart(
        company_name,
        company_values,
        reference_values,
        reference_name,
        output_file
    )

    return output_file

# ==========================================================
# Generate All Radar Charts
# ==========================================================

def generate_all_radar_charts():
    """
    Generate radar charts for every company.
    """

    df = prepare_data()

    df = normalize_metrics(df)

    print("\n" + "=" * 60)
    print("Generating Radar Charts")
    print("=" * 60)

    generated = 0

    for _, company in df.iterrows():

        try:

            generate_company_radar(
                df,
                company
            )

            generated += 1

            print(
                f"[{generated:02d}/{len(df)}] "
                f"{company['company_id']}  ✓"
            )

        except Exception as e:

            print(
                f"{company['company_id']}  ERROR : {e}"
            )

    print("\n" + "=" * 60)
    print("Radar Charts Completed")
    print("=" * 60)

    print(f"Charts Generated : {generated}")

    print(f"Folder : {OUTPUT_DIR}")

    return df

# ==========================================================
# Preview Output Folder
# ==========================================================

def preview_generated_charts():

    files = sorted(
        OUTPUT_DIR.glob("*.png")
    )

    print("\n" + "=" * 60)
    print("Generated Charts")
    print("=" * 60)

    print(f"Total PNG Files : {len(files)}")

    for file in files[:10]:

        print(file.name)

    if len(files) > 10:

        print("...")

# ==========================================================
# Validate Radar Charts
# ==========================================================

def validate_radar_output():
    """
    Validate generated radar charts.
    """

    files = sorted(
        OUTPUT_DIR.glob("*.png")
    )

    print("\n" + "=" * 60)
    print("RADAR CHART VALIDATION")
    print("=" * 60)

    print(f"Total Charts : {len(files)}")

    if len(files) == 92:

        print("PASS : All company charts generated")

    else:

        print("WARNING : Missing charts")

    print()

    for file in files[:10]:

        print(file.name)

    if len(files) > 10:

        print("...")

    return len(files)


# ==========================================================
# Generate Summary
# ==========================================================

def radar_summary():
    """
    Print Day 19 summary.
    """

    df = prepare_data()

    print("\n" + "=" * 60)
    print("DAY 19 SUMMARY")
    print("=" * 60)

    print(f"Companies               : {len(df)}")

    print(
        f"Peer Groups Assigned    : "
        f"{df['peer_group_name'].notna().sum()}"
    )

    print(
        f"No Peer Group           : "
        f"{df['peer_group_name'].isna().sum()}"
    )

    print(
        f"Output Folder           : "
        f"{OUTPUT_DIR}"
    )

    print("=" * 60)

# ==========================================================
# Main
# ==========================================================

def main():

    print("=" * 60)
    print("Peer Radar Chart Engine")
    print("=" * 60)

    # ------------------------------------------
    # Generate Charts
    # ------------------------------------------

    generate_all_radar_charts()

    # ------------------------------------------
    # Validate
    # ------------------------------------------

    validate_radar_output()

    # ------------------------------------------
    # Summary
    # ------------------------------------------

    radar_summary()

    print("\n" + "=" * 60)
    print("Day 19 Completed Successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()