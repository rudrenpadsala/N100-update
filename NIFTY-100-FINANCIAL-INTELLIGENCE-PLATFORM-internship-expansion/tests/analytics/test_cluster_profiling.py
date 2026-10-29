"""
test_cluster_profiling.py

Sprint 6
Day 41

Unit tests for src/analytics/cluster_profiling.py.
"""

import pandas as pd

from src.analytics.cluster_profiling import (
    CLUSTER_NAME_DISTRESSED,
    CLUSTER_NAME_HIGH_QUALITY,
    assign_readable_names,
    profile_clusters,
)


def _sample_snapshot() -> pd.DataFrame:
    """
    Build a small two-cluster snapshot: one clearly
    high-quality/high-growth cluster and one clearly
    distressed/low-growth cluster.
    """

    return pd.DataFrame(
        {
            "company_id": ["A", "B", "C", "D"],
            "cluster_id": [0, 0, 1, 1],
            "return_on_equity_pct": [30.0, 28.0, 2.0, 1.0],
            "debt_to_equity": [0.2, 0.3, 3.0, 4.0],
            "revenue_cagr_5yr": [20.0, 18.0, -5.0, -6.0],
            "fcf_cagr_5yr": [15.0, 14.0, -10.0, -12.0],
            "operating_profit_margin_pct": [35.0, 33.0, 5.0, 4.0],
        }
    )


def test_profile_clusters_computes_mean_and_median():
    snapshot = _sample_snapshot()
    profile = profile_clusters(snapshot)

    assert "mean_return_on_equity_pct" in profile.columns
    assert "median_return_on_equity_pct" in profile.columns
    assert len(profile) == 2

    cluster_0 = profile[profile["cluster_id"] == 0].iloc[0]
    assert cluster_0["mean_return_on_equity_pct"] == 29.0
    assert cluster_0["company_count"] == 2


def test_assign_readable_names_identifies_best_and_worst_cluster():
    snapshot = _sample_snapshot()
    profile = profile_clusters(snapshot)
    name_map = assign_readable_names(profile)

    assert name_map[0] == CLUSTER_NAME_HIGH_QUALITY
    assert name_map[1] == CLUSTER_NAME_DISTRESSED


def test_assign_readable_names_covers_every_cluster():
    snapshot = _sample_snapshot()
    profile = profile_clusters(snapshot)
    name_map = assign_readable_names(profile)

    assert set(name_map.keys()) == {0, 1}
    assert all(isinstance(name, str) for name in name_map.values())
