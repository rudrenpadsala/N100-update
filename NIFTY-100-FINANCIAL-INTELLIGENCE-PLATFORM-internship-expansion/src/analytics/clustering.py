"""
clustering.py

Sprint 6
Day 36

KMeans Clustering Engine

Groups all N100 companies into 5 quantitative clusters using:
    - return_on_equity_pct
    - debt_to_equity
    - revenue_cagr_5yr
    - fcf_cagr_5yr
    - operating_profit_margin_pct

Pipeline:
    1. Load latest-year fundamentals per company from financial_ratios
    2. Compute fcf_cagr_5yr per company from free_cash_flow_cr history
    3. Impute missing values using sector median (fallback: global median)
    4. Scale features with StandardScaler
    5. Fit KMeans(n_clusters=5, random_state=42)
    6. Generate an elbow plot (k = 2..10)
    7. Export cluster_labels.csv with distance-to-centroid
"""

import os
import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src.analytics.cagr import calculate_cagr

DB_PATH = "db/nifty100.db"

ELBOW_PLOT_FILE = "reports/elbow_plot.png"
CLUSTER_LABELS_FILE = "output/cluster_labels.csv"

CLUSTER_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

N_CLUSTERS = 5
RANDOM_STATE = 42

# Month lookup used to turn "Mar 2014" / "Mar-14" style
# labels into a sortable, chronological value.
_MONTH_LOOKUP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def parse_period(period: str) -> tuple[int, int] | None:
    """
    Parse a financial period label into a sortable
    (year, month) tuple.

    Handles both label formats found in the database:
        "Mar 2014"  -> (2014, 3)
        "Mar-14"    -> (2014, 3)

    Args:
        period: Raw period string from the database.

    Returns:
        A (year, month) tuple, or None if the string
        could not be parsed.
    """

    if not isinstance(period, str):
        return None

    cleaned = period.strip().replace("-", " ")
    parts = cleaned.split()

    if len(parts) != 2:
        return None

    month_token, year_token = parts

    month = _MONTH_LOOKUP.get(month_token.strip().lower())

    if month is None:
        return None

    try:
        year = int(year_token)
    except ValueError:
        return None

    # Two-digit years ("14") are assumed to be 2000s.
    if year < 100:
        year += 2000

    return (year, month)


def load_financial_ratios(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load company-year financial ratio history required
    for clustering.

    Args:
        conn: Open SQLite connection.

    Returns:
        DataFrame with one row per company-year.
    """

    df = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            return_on_equity_pct,
            debt_to_equity,
            revenue_cagr_5yr,
            operating_profit_margin_pct,
            free_cash_flow_cr
        FROM financial_ratios
        """,
        conn,
    )

    df["period"] = df["year"].apply(parse_period)

    df = df[df["period"].notna()].copy()

    df = df.sort_values(["company_id", "period"]).reset_index(drop=True)

    return df


def compute_fcf_cagr(company_df: pd.DataFrame) -> float:
    """
    Compute the free cash flow CAGR for a single company
    using its earliest and latest available data points.

    Args:
        company_df: Rows for a single company, sorted
            chronologically by period.

    Returns:
        The FCF CAGR percentage, or None if it cannot be
        calculated (see cagr.calculate_cagr edge cases).
    """

    fcf_history = company_df.dropna(subset=["free_cash_flow_cr"])

    if len(fcf_history) < 2:
        return None

    start_row = fcf_history.iloc[0]
    end_row = fcf_history.iloc[-1]

    years = end_row["period"][0] - start_row["period"][0]

    fcf_cagr_value, _ = calculate_cagr(
        start_row["free_cash_flow_cr"], end_row["free_cash_flow_cr"], years
    )

    return fcf_cagr_value


def build_company_snapshot(ratios_df: pd.DataFrame) -> pd.DataFrame:
    """
    Reduce the company-year ratio history into a single
    latest-year snapshot per company, with fcf_cagr_5yr
    computed and attached.

    Args:
        ratios_df: Company-year financial ratio history,
            sorted chronologically per company.

    Returns:
        One row per company with the clustering features.
    """

    snapshot_rows = []

    for company_id, company_df in ratios_df.groupby("company_id"):

        latest_row = company_df.iloc[-1]

        snapshot_rows.append(
            {
                "company_id": company_id,
                "return_on_equity_pct": latest_row["return_on_equity_pct"],
                "debt_to_equity": latest_row["debt_to_equity"],
                "revenue_cagr_5yr": latest_row["revenue_cagr_5yr"],
                "operating_profit_margin_pct": latest_row[
                    "operating_profit_margin_pct"
                ],
                "fcf_cagr_5yr": compute_fcf_cagr(company_df),
            }
        )

    return pd.DataFrame(snapshot_rows)


def load_sector_map(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load the broad sector classification for every company.

    Args:
        conn: Open SQLite connection.

    Returns:
        DataFrame with company_id and broad_sector.
    """

    return pd.read_sql(
        """
        SELECT
            company_id,
            broad_sector
        FROM sectors
        """,
        conn,
    )


def impute_by_sector_median(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill missing clustering feature values using the
    median value for the company's sector. Any value that
    is still missing (e.g. an entire sector is null) falls
    back to the global median.

    Args:
        df: Company snapshot including a broad_sector column.

    Returns:
        DataFrame with missing values imputed.
    """

    df = df.copy()

    for feature in CLUSTER_FEATURES:

        sector_median = df.groupby("broad_sector")[feature].transform("median")
        df[feature] = df[feature].fillna(sector_median)

        global_median = df[feature].median()
        df[feature] = df[feature].fillna(global_median)

    return df


def plot_elbow_curve(scaled_features) -> None:
    """
    Fit KMeans for k = 2..10 and save an elbow plot of
    inertia vs. k to help validate the chosen cluster count.

    Args:
        scaled_features: Standardized clustering feature matrix.
    """

    os.makedirs(os.path.dirname(ELBOW_PLOT_FILE), exist_ok=True)

    k_values = range(2, 11)
    inertia_values = []

    for k in k_values:

        model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)

        model.fit(scaled_features)
        inertia_values.append(model.inertia_)

    fig = plt.figure(figsize=(8, 5))

    plt.plot(list(k_values), inertia_values, marker="o")

    plt.axvline(
        x=N_CLUSTERS, color="red", linestyle="--", label=f"Chosen k = {N_CLUSTERS}"
    )

    plt.title("Elbow Method - Optimal Cluster Count")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.xticks(list(k_values))
    plt.legend()
    plt.tight_layout()

    plt.savefig(ELBOW_PLOT_FILE)
    plt.close(fig)

    print(f"✔ Elbow plot saved : {ELBOW_PLOT_FILE}")


def run_clustering(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    """
    Scale the clustering features, fit the final KMeans
    model, and compute each company's distance from its
    assigned cluster centroid.

    Args:
        snapshot_df: Company snapshot with imputed features.

    Returns:
        DataFrame with company_id, cluster_id, cluster_name
        and distance_from_centroid.
    """

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(snapshot_df[CLUSTER_FEATURES])

    plot_elbow_curve(scaled_features)

    model = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)

    cluster_ids = model.fit_predict(scaled_features)

    centroids = model.cluster_centers_

    distances = [
        float(((scaled_features[i] - centroids[cluster_ids[i]]) ** 2).sum() ** 0.5)
        for i in range(len(scaled_features))
    ]

    result = pd.DataFrame(
        {
            "company_id": snapshot_df["company_id"].values,
            "cluster_id": cluster_ids,
            # Day 37 (Cluster Profiling) replaces these generic
            # labels with readable, profile-based cluster names
            # (e.g. "High-Quality Compounders").
            "cluster_name": [f"Cluster {c}" for c in cluster_ids],
            "distance_from_centroid": [round(d, 4) for d in distances],
        }
    )

    return result


def main() -> None:
    """
    Run the full Day 36 clustering pipeline end to end.
    """

    print("=" * 60)
    print("KMeans Clustering Engine")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    ratios_df = load_financial_ratios(conn)
    sector_df = load_sector_map(conn)

    print("✔ financial_ratios rows loaded :", len(ratios_df))
    print("✔ sector records loaded        :", len(sector_df))

    snapshot_df = build_company_snapshot(ratios_df)

    snapshot_df = snapshot_df.merge(sector_df, on="company_id", how="left")

    print("✔ company snapshots built      :", len(snapshot_df))

    snapshot_df = impute_by_sector_median(snapshot_df)

    result_df = run_clustering(snapshot_df)

    os.makedirs(os.path.dirname(CLUSTER_LABELS_FILE), exist_ok=True)

    result_df.to_csv(CLUSTER_LABELS_FILE, index=False)

    print(f"✔ Cluster labels saved : {CLUSTER_LABELS_FILE}")
    print("\nCluster Size Distribution")
    print(result_df["cluster_name"].value_counts())

    conn.close()

    print("\n✅ Day 36 Clustering Complete")


if __name__ == "__main__":
    main()
