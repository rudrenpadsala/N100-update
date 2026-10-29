"""
platform_data.py

Internship Expansion - shared data bundle

Loads the database once and computes everything the new modules need:
quality issues, latest-year metrics, health scores and the league table.
The dashboard pages, the PDF report generator and the tests all use this
single entry point so that every screen and every PDF show the same
numbers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from src.analytics.financial_metrics import build_metrics
from src.analytics.health_score import HealthScore, compute_all, scores_table
from src.quality.data_quality import DEFAULT_DB_PATH, load_tables, run_quality_checks


@dataclass
class AnalyticsBundle:
    tables: Dict[str, pd.DataFrame]
    issues: pd.DataFrame
    metrics: pd.DataFrame
    health: Dict[str, HealthScore]
    league: pd.DataFrame

    @property
    def peer_groups(self) -> pd.DataFrame:
        return self.tables["peer_groups"]

    def company_ids(self):
        return list(self.metrics["company_id"].astype(str))


def build_bundle(db_path: Optional[os.PathLike] = None,
                 tables: Optional[Dict[str, pd.DataFrame]] = None) -> AnalyticsBundle:
    """Compute everything from a database path, or from ready-made tables."""

    if tables is None:
        tables = load_tables(db_path)

    issues = run_quality_checks(tables)
    metrics = build_metrics(tables)
    health = compute_all(metrics)
    league = scores_table(health, metrics)

    return AnalyticsBundle(tables, issues, metrics, health, league)


@lru_cache(maxsize=2)
def _cached(path: str, mtime: float) -> AnalyticsBundle:
    return build_bundle(path)


def get_bundle(db_path: Optional[os.PathLike] = None) -> AnalyticsBundle:
    """Cached bundle - recomputed automatically if the database file changes."""

    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    return _cached(str(path), path.stat().st_mtime)
