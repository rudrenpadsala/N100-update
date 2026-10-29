"""
benchmarking.py

Internship Expansion - Module 3 (Peer Benchmarking)

Compares one company's indicators with its peers.

Peer set
--------
1. If the company belongs to a curated group in the `peer_groups` table
   (for example "IT Services" or "Private Banks") and that group has at
   least MIN_PEERS members with data, that group is used.
2. Otherwise the company's broad sector (`sectors.broad_sector`) is used.
3. If even the sector has too few members, no benchmark is produced and
   the result says why.

Per metric the table reports
----------------------------
value          the company's own figure
peer_median    median of the OTHER members of the peer set
delta          value - peer_median
percentile     0-100, where 100 means best in the peer set. Direction is
               respected (a low debt-to-equity ranks high). Computed as the
               share of other peers the company beats; ties count half.
rank / n       position in the set, 1 = best
verdict        "Above peers" (percentile >= 66.7), "Below peers" (<= 33.3),
               otherwise "In line"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
import pandas as pd

MIN_PEERS = 3          # total group size, including the company itself
MIN_VALID_VALUES = 3   # companies with a usable value, including the target

# key, label, higher_is_better, unit
BENCHMARK_METRICS = [
    ("health_score", "Health score", True, "pts"),
    ("roe_pct", "Return on equity", True, "%"),
    ("net_margin_pct", "Net profit margin", True, "%"),
    ("operating_margin_pct", "Operating margin", True, "%"),
    ("debt_to_equity", "Debt-to-equity", False, "x"),
    ("interest_coverage", "Interest coverage", True, "x"),
    ("revenue_cagr_pct", "Revenue growth (CAGR)", True, "%"),
    ("profit_cagr_pct", "Profit growth (CAGR)", True, "%"),
    ("cfo_to_pat", "Cash conversion (CFO / PAT)", True, "x"),
    ("pe_ratio", "P/E ratio", None, "x"),          # valuation: shown, never ranked
]

# Metrics that are not meaningful for banks, NBFCs and insurers.
NOT_FOR_FINANCIALS = {"operating_margin_pct", "debt_to_equity", "interest_coverage", "cfo_to_pat"}

# Interest coverage above this is capped for ranking so one outlier cannot
# distort the median (a company with almost no interest cost).
INTEREST_COVERAGE_CAP = 100.0


@dataclass
class PeerSet:
    company_id: str
    basis: str                 # "curated peer group" | "broad sector" | "none"
    group_name: Optional[str]
    members: List[str] = field(default_factory=list)   # includes the company
    note: str = ""


def find_peer_set(company_id: str, metrics: pd.DataFrame, peer_groups: Optional[pd.DataFrame]) -> PeerSet:
    """Choose the peer set for one company (see module docstring)."""

    known = set(metrics["company_id"].astype(str))

    if peer_groups is not None and not peer_groups.empty:
        mine = peer_groups[peer_groups["company_id"].astype(str) == company_id]
        if not mine.empty:
            name = mine.iloc[0]["peer_group_name"]
            members = sorted(
                set(peer_groups.loc[peer_groups["peer_group_name"] == name, "company_id"].astype(str)) & known
            )
            if len(members) >= MIN_PEERS:
                return PeerSet(company_id, "curated peer group", name, members)

    row = metrics[metrics["company_id"].astype(str) == company_id]

    if row.empty:
        return PeerSet(company_id, "none", None, [], "company not found")

    sector = row.iloc[0]["broad_sector"]

    if sector is not None and pd.notna(sector):
        members = sorted(metrics.loc[metrics["broad_sector"] == sector, "company_id"].astype(str))
        if len(members) >= MIN_PEERS:
            note = ""
            if peer_groups is not None and not peer_groups.empty and \
                    (peer_groups["company_id"].astype(str) == company_id).any():
                note = "Curated peer group was too small; broad sector used instead."
            return PeerSet(company_id, "broad sector", sector, members, note)

    return PeerSet(company_id, "none", None, [], "fewer than three companies in the peer set")


def _percentile(value: float, others: np.ndarray, higher_is_better: bool) -> float:
    """Share of the other peers the company beats; ties count half."""

    if len(others) == 0:
        return float("nan")

    if higher_is_better:
        beaten = (value > others).sum() + 0.5 * (value == others).sum()
    else:
        beaten = (value < others).sum() + 0.5 * (value == others).sum()

    return float(100.0 * beaten / len(others))


def benchmark_company(
    company_id: str,
    metrics: pd.DataFrame,
    scores: Optional[pd.DataFrame] = None,
    peer_groups: Optional[pd.DataFrame] = None,
):
    """
    Returns (PeerSet, DataFrame) - the peer set used and the metric table.

    metrics : output of financial_metrics.build_metrics()
    scores  : output of health_score.scores_table() (adds the health score row)
    """

    company_id = str(company_id)
    peer_set = find_peer_set(company_id, metrics, peer_groups)

    columns = [
        "metric", "label", "unit", "value", "peer_median", "delta", "percentile",
        "rank", "n", "verdict", "note",
    ]

    if not peer_set.members:
        return peer_set, pd.DataFrame(columns=columns)

    frame = metrics[metrics["company_id"].astype(str).isin(peer_set.members)].copy()

    if scores is not None and not scores.empty:
        frame = frame.merge(scores[["company_id", "score"]].rename(columns={"score": "health_score"}),
                            on="company_id", how="left")
    else:
        frame["health_score"] = np.nan

    frame["company_id"] = frame["company_id"].astype(str)
    is_financial = bool(frame.loc[frame["company_id"] == company_id, "is_financial"].iloc[0])

    rows = []

    for key, label, higher, unit in BENCHMARK_METRICS:
        record = {"metric": key, "label": label, "unit": unit, "value": np.nan,
                  "peer_median": np.nan, "delta": np.nan, "percentile": np.nan,
                  "rank": np.nan, "n": 0, "verdict": "n/a", "note": ""}

        if is_financial and key in NOT_FOR_FINANCIALS:
            record["note"] = "Not applicable to banks, NBFCs and insurers."
            rows.append(record)
            continue

        series = frame.set_index("company_id")[key] if key in frame.columns else pd.Series(dtype=float)
        series = pd.to_numeric(series, errors="coerce")

        if key == "interest_coverage":
            series = series.clip(upper=INTEREST_COVERAGE_CAP)

        if key in NOT_FOR_FINANCIALS:
            # Peers that are financials do not have a meaningful value either.
            fin = frame.set_index("company_id")["is_financial"]
            series = series[~fin.reindex(series.index).fillna(False).astype(bool)]

        own = series.get(company_id, np.nan)
        record["value"] = own
        valid = series.dropna()
        others = valid.drop(labels=[company_id], errors="ignore").to_numpy(dtype=float)

        record["n"] = int(len(valid))

        if len(others):
            record["peer_median"] = float(np.median(others))

        if pd.isna(own):
            record["note"] = "No usable value for this company."
        else:
            record["delta"] = float(own - record["peer_median"]) if len(others) else np.nan

            if higher is None:
                record["note"] = "Valuation multiple: shown for context, not ranked."
            elif len(valid) < MIN_VALID_VALUES:
                record["note"] = f"Only {len(valid)} companies have a value; not ranked."
            else:
                pct = _percentile(float(own), others, higher)
                record["percentile"] = pct
                ordered = valid.sort_values(ascending=not higher)
                record["rank"] = int(list(ordered.index).index(company_id) + 1)
                record["verdict"] = (
                    "Above peers" if pct >= 66.7 else "Below peers" if pct <= 33.3 else "In line"
                )

        rows.append(record)

    return peer_set, pd.DataFrame(rows, columns=columns)


def sector_summary(metrics: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    """Median indicators and average health score per broad sector."""

    merged = metrics.merge(scores[["company_id", "score"]], on="company_id", how="left")

    cols = ["roe_pct", "net_margin_pct", "operating_margin_pct", "debt_to_equity",
            "revenue_cagr_pct", "profit_cagr_pct", "score"]

    out = merged.groupby("broad_sector").agg(
        companies=("company_id", "count"),
        **{f"median_{c}": (c, "median") for c in cols},
    ).reset_index()

    out = out.rename(columns={"median_score": "median_health_score"})

    # Leverage and operating margin are not meaningful for banks, NBFCs, insurers.
    financials = out["broad_sector"] == "Financials"
    for col in ("median_operating_margin_pct", "median_debt_to_equity"):
        out.loc[financials, col] = np.nan

    return out.sort_values("median_health_score", ascending=False).reset_index(drop=True)
