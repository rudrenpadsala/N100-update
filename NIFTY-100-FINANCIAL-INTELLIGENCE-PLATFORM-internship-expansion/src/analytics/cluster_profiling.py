"""
cluster_profiling.py

Sprint 6
Day 37

Cluster Profiling

Builds on the Day 36 clustering output (output/cluster_labels.csv)
to:
    - Profile each cluster (mean / median of every feature)
    - Replace the generic "Cluster N" labels with readable
      names (High-Quality Compounders, Defensive Dividend
      Payers, Value Cyclicals, Distressed or Turnaround,
      Emerging Growth)
    - Generate a feature correlation heatmap
    - Flag statistical outliers (|z-score| > 3)
    - Generate portfolio-wide percentile statistics
"""

import os
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.analytics.clustering import (
    CLUSTER_FEATURES,
    CLUSTER_LABELS_FILE,
    DB_PATH,
    build_company_snapshot,
    impute_by_sector_median,
    load_financial_ratios,
    load_sector_map,
)

CORRELATION_HEATMAP_FILE = "reports/correlation_heatmap.png"
OUTLIER_REPORT_FILE = "output/outlier_report.csv"
PORTFOLIO_STATS_FILE = "output/portfolio_stats.csv"

OUTLIER_Z_THRESHOLD = 3.0

# Readable names required by the Sprint 6 specification.
CLUSTER_NAME_HIGH_QUALITY = "High-Quality Compounders"
CLUSTER_NAME_DEFENSIVE = "Defensive Dividend Payers"
CLUSTER_NAME_VALUE_CYCLICAL = "Value Cyclicals"
CLUSTER_NAME_DISTRESSED = "Distressed or Turnaround"
CLUSTER_NAME_EMERGING_GROWTH = "Emerging Growth"


def build_labelled_snapshot() -> pd.DataFrame:
    """
    Rebuild the same imputed company snapshot used on Day 36
    and attach each company's assigned cluster_id.

    Returns:
        DataFrame with one row per company: clustering
        features plus cluster_id.
    """

    conn = sqlite3.connect(DB_PATH)

    ratios_df = load_financial_ratios(conn)
    sector_df = load_sector_map(conn)

    conn.close()

    snapshot_df = build_company_snapshot(ratios_df)

    snapshot_df = snapshot_df.merge(sector_df, on="company_id", how="left")

    snapshot_df = impute_by_sector_median(snapshot_df)

    labels_df = pd.read_csv(CLUSTER_LABELS_FILE)[["company_id", "cluster_id"]]

    snapshot_df = snapshot_df.merge(labels_df, on="company_id", how="inner")

    return snapshot_df


def profile_clusters(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the mean and median of every clustering feature
    for each cluster.

    Args:
        snapshot_df: Labelled company snapshot.

    Returns:
        One row per cluster_id with mean_/median_ columns
        for each feature, plus company_count.
    """

    grouped = snapshot_df.groupby("cluster_id")

    profile = grouped[CLUSTER_FEATURES].agg(["mean", "median"])
    profile.columns = [f"{stat}_{feature}" for feature, stat in profile.columns]
    profile["company_count"] = grouped.size()

    return profile.reset_index()


def assign_readable_names(profile_df: pd.DataFrame) -> dict:
    """
    Rank cluster centroids on quality (ROE, low leverage,
    margin) and growth (revenue/FCF CAGR) to assign each
    cluster one of the five required readable names.

    Ranking logic:
        1. quality_score  = z(mean ROE) + z(mean OPM) - z(mean D/E)
        2. growth_score   = z(mean revenue_cagr) + z(mean fcf_cagr)
        3. Highest quality_score with above-median growth
           -> High-Quality Compounders
        4. Lowest quality_score with below-median growth
           -> Distressed or Turnaround
        5. Highest remaining growth_score
           -> Emerging Growth
        6. Remaining cluster with lowest leverage
           -> Defensive Dividend Payers
        7. Any cluster still unassigned
           -> Value Cyclicals

    Args:
        profile_df: Output of profile_clusters().

    Returns:
        Dict mapping cluster_id -> readable cluster name.
    """

    df = profile_df.copy()

    def zscore(series: pd.Series) -> pd.Series:
        std = series.std(ddof=0)
        if std == 0 or pd.isna(std):
            return series * 0
        return (series - series.mean()) / std

    df["quality_score"] = (
        zscore(df["mean_return_on_equity_pct"])
        + zscore(df["mean_operating_profit_margin_pct"])
        - zscore(df["mean_debt_to_equity"])
    )

    df["growth_score"] = zscore(df["mean_revenue_cagr_5yr"]) + zscore(
        df["mean_fcf_cagr_5yr"]
    )

    growth_median = df["growth_score"].median()

    unassigned = set(df["cluster_id"])
    names = {}

    # 1. High-Quality Compounders: best quality, above-median growth
    candidates = df[
        df["cluster_id"].isin(unassigned) & (df["growth_score"] >= growth_median)
    ]
    if not candidates.empty:
        winner = candidates.loc[candidates["quality_score"].idxmax(), "cluster_id"]
        names[winner] = CLUSTER_NAME_HIGH_QUALITY
        unassigned.discard(winner)

    # 2. Distressed or Turnaround: worst quality, below-median growth
    candidates = df[
        df["cluster_id"].isin(unassigned) & (df["growth_score"] < growth_median)
    ]
    if not candidates.empty:
        loser = candidates.loc[candidates["quality_score"].idxmin(), "cluster_id"]
        names[loser] = CLUSTER_NAME_DISTRESSED
        unassigned.discard(loser)

    # 3. Emerging Growth: highest remaining growth score
    candidates = df[df["cluster_id"].isin(unassigned)]
    if not candidates.empty:
        grower = candidates.loc[candidates["growth_score"].idxmax(), "cluster_id"]
        names[grower] = CLUSTER_NAME_EMERGING_GROWTH
        unassigned.discard(grower)

    # 4. Defensive Dividend Payers: lowest remaining leverage
    candidates = df[df["cluster_id"].isin(unassigned)]
    if not candidates.empty:
        defensive = candidates.loc[
            candidates["mean_debt_to_equity"].idxmin(), "cluster_id"
        ]
        names[defensive] = CLUSTER_NAME_DEFENSIVE
        unassigned.discard(defensive)

    # 5. Anything left over -> Value Cyclicals
    for cluster_id in unassigned:
        names[cluster_id] = CLUSTER_NAME_VALUE_CYCLICAL

    return names


def update_cluster_labels(name_map: dict) -> pd.DataFrame:
    """
    Overwrite the cluster_name column in cluster_labels.csv
    with the readable names assigned on Day 37.

    Args:
        name_map: Dict mapping cluster_id -> readable name.

    Returns:
        The updated labels DataFrame.
    """

    labels_df = pd.read_csv(CLUSTER_LABELS_FILE)

    labels_df["cluster_name"] = labels_df["cluster_id"].map(name_map)

    labels_df.to_csv(CLUSTER_LABELS_FILE, index=False)

    return labels_df


def plot_correlation_heatmap(snapshot_df: pd.DataFrame) -> None:
    """
    Save a correlation heatmap of the clustering features.

    Args:
        snapshot_df: Labelled company snapshot.
    """

    os.makedirs(os.path.dirname(CORRELATION_HEATMAP_FILE), exist_ok=True)

    corr = snapshot_df[CLUSTER_FEATURES].corr()

    fig, ax = plt.subplots(figsize=(7, 6))

    image = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)

    ax.set_xticks(range(len(CLUSTER_FEATURES)))
    ax.set_yticks(range(len(CLUSTER_FEATURES)))
    ax.set_xticklabels(CLUSTER_FEATURES, rotation=45, ha="right")
    ax.set_yticklabels(CLUSTER_FEATURES)

    for i in range(len(CLUSTER_FEATURES)):
        for j in range(len(CLUSTER_FEATURES)):
            ax.text(
                j,
                i,
                f"{corr.iloc[i, j]:.2f}",
                ha="center",
                va="center",
                color="black",
                fontsize=8,
            )

    ax.set_title("Feature Correlation Heatmap")
    fig.colorbar(image, ax=ax, shrink=0.8)
    fig.tight_layout()

    fig.savefig(CORRELATION_HEATMAP_FILE)
    plt.close(fig)

    print(f"✔ Correlation heatmap saved : {CORRELATION_HEATMAP_FILE}")


def generate_outlier_report(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag every company-feature combination whose z-score
    exceeds the outlier threshold (|z| > 3).

    Args:
        snapshot_df: Labelled company snapshot.

    Returns:
        DataFrame of outlier records.
    """

    records = []

    for feature in CLUSTER_FEATURES:

        series = snapshot_df[feature]
        std = series.std(ddof=0)

        if std == 0 or pd.isna(std):
            continue

        z_scores = (series - series.mean()) / std

        flagged = snapshot_df.loc[z_scores.abs() > OUTLIER_Z_THRESHOLD]
        flagged_z = z_scores.loc[z_scores.abs() > OUTLIER_Z_THRESHOLD]

        for (idx, row), z_value in zip(flagged.iterrows(), flagged_z):
            records.append(
                {
                    "company_id": row["company_id"],
                    "feature": feature,
                    "value": row[feature],
                    "z_score": round(float(z_value), 4),
                }
            )

    outlier_df = pd.DataFrame(
        records, columns=["company_id", "feature", "value", "z_score"]
    )

    os.makedirs(os.path.dirname(OUTLIER_REPORT_FILE), exist_ok=True)
    outlier_df.to_csv(OUTLIER_REPORT_FILE, index=False)

    print(f"✔ Outlier report saved : {OUTLIER_REPORT_FILE}")
    print(f"  Outliers flagged : {len(outlier_df)}")

    return outlier_df


def generate_portfolio_stats(snapshot_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute portfolio-wide percentile statistics for every
    clustering feature.

    Args:
        snapshot_df: Labelled company snapshot.

    Returns:
        DataFrame with one row per feature and columns
        P10, P25, P50, P75, P90, Mean, Std.
    """

    rows = []

    for feature in CLUSTER_FEATURES:

        series = snapshot_df[feature].dropna()

        rows.append(
            {
                "feature": feature,
                "P10": round(np.percentile(series, 10), 4),
                "P25": round(np.percentile(series, 25), 4),
                "P50": round(np.percentile(series, 50), 4),
                "P75": round(np.percentile(series, 75), 4),
                "P90": round(np.percentile(series, 90), 4),
                "Mean": round(series.mean(), 4),
                "Std": round(series.std(ddof=0), 4),
            }
        )

    stats_df = pd.DataFrame(rows)

    os.makedirs(os.path.dirname(PORTFOLIO_STATS_FILE), exist_ok=True)
    stats_df.to_csv(PORTFOLIO_STATS_FILE, index=False)

    print(f"✔ Portfolio stats saved : {PORTFOLIO_STATS_FILE}")

    return stats_df


def main() -> None:
    """
    Run the full Day 37 cluster profiling pipeline.
    """

    print("=" * 60)
    print("Cluster Profiling Engine")
    print("=" * 60)

    snapshot_df = build_labelled_snapshot()
    print("✔ Labelled snapshot built :", len(snapshot_df))

    profile_df = profile_clusters(snapshot_df)
    name_map = assign_readable_names(profile_df)

    print("\nCluster Name Assignment:")
    for cluster_id, name in sorted(name_map.items()):
        count = int(
            profile_df.loc[
                profile_df["cluster_id"] == cluster_id, "company_count"
            ].iloc[0]
        )
        print(f"  Cluster {cluster_id} -> {name} ({count} companies)")

    update_cluster_labels(name_map)
    print(f"\n✔ cluster_labels.csv updated with readable names : {CLUSTER_LABELS_FILE}")

    plot_correlation_heatmap(snapshot_df)
    generate_outlier_report(snapshot_df)
    generate_portfolio_stats(snapshot_df)

    print("\n✅ Day 37 Cluster Profiling Complete")


if __name__ == "__main__":
    main()
