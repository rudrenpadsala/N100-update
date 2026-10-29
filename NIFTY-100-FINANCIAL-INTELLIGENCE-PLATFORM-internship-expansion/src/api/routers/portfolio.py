"""
portfolio.py

Sprint 6
Day 40

Portfolio-level endpoints - cluster composition and
portfolio-wide statistics generated on Day 36/37.
"""

import csv
import os

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

CLUSTER_LABELS_FILE = "output/cluster_labels.csv"
PORTFOLIO_STATS_FILE = "output/portfolio_stats.csv"
OUTLIER_REPORT_FILE = "output/outlier_report.csv"


def _read_csv(path: str) -> list:
    """
    Read a CSV file into a list of dicts.

    Args:
        path: Path to the CSV file.

    Returns:
        List of row dicts.

    Raises:
        HTTPException: 404 if the file does not exist yet.
    """

    if not os.path.isfile(path):
        raise HTTPException(
            status_code=404,
            detail=f"'{path}' has not been generated yet. "
            f"Run the Day 36/37 analytics pipeline first.",
        )

    with open(path, newline="") as f:
        return list(csv.DictReader(f))


@router.get("/clusters")
def get_cluster_composition() -> dict:
    """
    Get every company's cluster assignment.
    """

    rows = _read_csv(CLUSTER_LABELS_FILE)
    return {"results": rows}


@router.get("/clusters/summary")
def get_cluster_summary() -> dict:
    """
    Get the company count for each named cluster.
    """

    rows = _read_csv(CLUSTER_LABELS_FILE)

    summary: dict = {}

    for row in rows:
        name = row["cluster_name"]
        summary[name] = summary.get(name, 0) + 1

    return {"results": summary}


@router.get("/stats")
def get_portfolio_stats() -> dict:
    """
    Get portfolio-wide percentile statistics for the
    clustering features (P10-P90, mean, std).
    """

    rows = _read_csv(PORTFOLIO_STATS_FILE)
    return {"results": rows}


@router.get("/outliers")
def get_portfolio_outliers() -> dict:
    """
    Get every flagged statistical outlier (|z-score| > 3).
    """

    rows = _read_csv(OUTLIER_REPORT_FILE)
    return {"results": rows}
