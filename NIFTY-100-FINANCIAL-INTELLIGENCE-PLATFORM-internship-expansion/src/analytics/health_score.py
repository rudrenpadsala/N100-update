"""
health_score.py

Internship Expansion - Module 2 (Explainable Financial Analytics)

A documented, deterministic 0-100 Financial Health Score.

How it works
------------
1. Each metric is converted to a 0-100 score by straight-line
   interpolation between two documented thresholds
   (`zero_at` -> 0 points, `full_at` -> 100 points, clipped outside).
   This works for "higher is better" and "lower is better" alike.

2. Each metric has a nominal weight (see METRICS). The weights add to 100
   and are grouped in four pillars:

       Profitability   30   ROE, net margin, operating margin
       Leverage        25   debt-to-equity, interest coverage
       Growth          25   revenue CAGR, profit CAGR
       Cash quality    20   cash from operations / net profit

3. A metric that is missing, or excluded because the source value is not
   plausible, is dropped and the remaining weights are re-scaled to 100.
   The result reports `data_coverage_pct` so the reader can see how much of
   the nominal score is actually backed by data. Below MIN_COVERAGE_PCT the
   score is withheld rather than guessed.

4. Banks, NBFCs and insurers (sector "Financials") are not scored on
   leverage, interest coverage, operating margin or CFO/PAT: borrowing is
   their raw material and their cash flows include customer deposits, so
   those ratios are not comparable with industrial companies. They are
   marked "not applicable" and do not count against coverage.

5. Every score comes with a component table: value, points, nominal
   weight, effective weight, contribution and a plain-English note. The
   total is exactly the sum of the contributions - nothing is hidden.

Grades
------
    A  75-100  Strong        B  60-75  Healthy      C  45-60  Moderate
    D  30-45   Weak          E   0-30  Distressed

Limitations
-----------
* Scores of Financials rest on fewer metrics than industrial companies, so
  compare a bank with other banks (peer benchmarking), not with a steel mill.
* The score uses reported figures for the latest full fiscal year plus a
  growth history; it does not look at prices and does not predict them.
* It is an analytical summary, not investment advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

MIN_COVERAGE_PCT = 50.0


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    pillar: str
    weight: float
    zero_at: float          # value that earns 0 points
    full_at: float          # value that earns 100 points
    unit: str               # "%", "x"
    rationale: str
    applies_to_financials: bool = True


METRICS: List[MetricSpec] = [
    MetricSpec("roe_pct", "Return on equity", "Profitability", 12.0, 0.0, 20.0, "%",
               "Profit earned per rupee of shareholder capital; 20% or more earns full marks, 0% or less earns none."),
    MetricSpec("net_margin_pct", "Net profit margin", "Profitability", 9.0, 0.0, 20.0, "%",
               "Share of sales kept as profit; 20% or more earns full marks."),
    MetricSpec("operating_margin_pct", "Operating margin", "Profitability", 9.0, 0.0, 25.0, "%",
               "Core operating profit as a share of sales; 25% or more earns full marks.",
               applies_to_financials=False),
    MetricSpec("debt_to_equity", "Debt-to-equity", "Leverage", 15.0, 2.0, 0.3, "x",
               "Borrowings per rupee of net worth; 0.3x or lower earns full marks, 2.0x or higher earns none.",
               applies_to_financials=False),
    MetricSpec("interest_coverage", "Interest coverage", "Leverage", 10.0, 1.0, 8.0, "x",
               "Operating earnings relative to interest; 8x or more earns full marks, 1x or less earns none.",
               applies_to_financials=False),
    MetricSpec("revenue_cagr_pct", "Revenue growth (CAGR)", "Growth", 12.5, 0.0, 15.0, "%",
               "Compound annual sales growth over up to 5 years; 15% or more earns full marks."),
    MetricSpec("profit_cagr_pct", "Profit growth (CAGR)", "Growth", 12.5, 0.0, 20.0, "%",
               "Compound annual net-profit growth over up to 5 years; 20% or more earns full marks."),
    MetricSpec("cfo_to_pat", "Cash conversion (CFO / PAT)", "Cash quality", 20.0, 0.3, 1.0, "x",
               "Operating cash flow per rupee of reported profit; 1.0x or more earns full marks, 0.3x or less earns none.",
               applies_to_financials=False),
]

METRIC_BY_KEY = {m.key: m for m in METRICS}
PILLARS = ["Profitability", "Leverage", "Growth", "Cash quality"]

GRADE_BANDS = [
    (75.0, "A", "Strong"),
    (60.0, "B", "Healthy"),
    (45.0, "C", "Moderate"),
    (30.0, "D", "Weak"),
    (0.0, "E", "Distressed"),
]

assert abs(sum(m.weight for m in METRICS) - 100.0) < 1e-9


# =====================================================================
# Scoring primitives
# =====================================================================

def score_metric(value: float, zero_at: float, full_at: float) -> float:
    """Straight-line 0-100 score between the two thresholds, clipped."""

    if value is None or pd.isna(value):
        return float("nan")

    fraction = (value - zero_at) / (full_at - zero_at)

    return float(min(1.0, max(0.0, fraction)) * 100.0)


def grade_for(score: Optional[float]):
    """Returns (letter, label) for a 0-100 score."""

    if score is None or pd.isna(score):
        return "N/A", "Insufficient data"

    for lower, letter, label in GRADE_BANDS:
        if score >= lower:
            return letter, label

    return "E", "Distressed"


def _fmt_value(value: float, unit: str) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value:,.2f}{unit}"


# =====================================================================
# Result object
# =====================================================================

@dataclass
class HealthScore:
    company_id: str
    company_name: str
    score: Optional[float]
    grade: str
    grade_label: str
    data_coverage_pct: float
    as_of_year: Optional[int]
    is_financial: bool
    components: pd.DataFrame
    pillars: pd.DataFrame
    strengths: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "score": self.score,
            "grade": self.grade,
            "grade_label": self.grade_label,
            "data_coverage_pct": self.data_coverage_pct,
            "as_of_year": self.as_of_year,
        }


# =====================================================================
# Main entry point
# =====================================================================

def compute_health_score(metrics_row: pd.Series, reference_year: Optional[int] = None) -> HealthScore:
    """
    Score one company from one row of financial_metrics.build_metrics().

    reference_year: the most recent year in the universe; if this company's
    latest data is older, a staleness caveat is added.
    """

    is_financial = bool(metrics_row.get("is_financial", False))
    notes = metrics_row.get("metric_notes")
    notes = notes if isinstance(notes, dict) else {}
    interest_free = bool(metrics_row.get("interest_free", False))

    records = []

    for spec in METRICS:
        value = metrics_row.get(spec.key, np.nan)
        value = float(value) if value is not None and pd.notna(value) else np.nan

        record = {
            "pillar": spec.pillar,
            "metric": spec.key,
            "label": spec.label,
            "value": value,
            "unit": spec.unit,
            "points": np.nan,
            "nominal_weight": spec.weight,
            "effective_weight": 0.0,
            "contribution": 0.0,
            "status": "scored",
            "note": "",
        }

        if is_financial and not spec.applies_to_financials:
            record["status"] = "not_applicable"
            record["note"] = "Not applicable to banks, NBFCs and insurers (borrowing is their business model)."

        elif spec.key == "interest_coverage" and np.isnan(value) and interest_free:
            record["points"] = 100.0
            record["note"] = "No interest expense reported - treated as full marks."

        elif np.isnan(value):
            record["status"] = "missing"
            record["note"] = notes.get(spec.key, "No data available.")

        else:
            record["points"] = score_metric(value, spec.zero_at, spec.full_at)
            record["note"] = spec.rationale

        records.append(record)

    comp = pd.DataFrame(records)

    applicable_weight = comp.loc[comp["status"] != "not_applicable", "nominal_weight"].sum()
    scored_mask = comp["points"].notna() & (comp["status"] == "scored")
    scored_weight = comp.loc[scored_mask, "nominal_weight"].sum()

    coverage = 100.0 * scored_weight / applicable_weight if applicable_weight else 0.0

    if scored_weight > 0:
        comp.loc[scored_mask, "effective_weight"] = (
            comp.loc[scored_mask, "nominal_weight"] / scored_weight * 100.0
        )
        comp.loc[scored_mask, "contribution"] = (
            comp.loc[scored_mask, "points"] * comp.loc[scored_mask, "effective_weight"] / 100.0
        )

    total = float(comp["contribution"].sum()) if scored_weight > 0 else float("nan")

    if coverage < MIN_COVERAGE_PCT:
        score = None
    else:
        score = round(total, 1)

    letter, label = grade_for(score)

    # ---- pillar roll-up -------------------------------------------------
    pillar_rows = []
    for pillar in PILLARS:
        part = comp[(comp["pillar"] == pillar)]
        applicable = part[part["status"] != "not_applicable"]
        scored = part[part["points"].notna() & (part["status"] == "scored")]

        if applicable.empty:
            pillar_rows.append({
                "pillar": pillar, "pillar_score": np.nan, "contribution": 0.0,
                "effective_weight": 0.0, "status": "not_applicable",
            })
            continue

        if scored.empty:
            pillar_rows.append({
                "pillar": pillar, "pillar_score": np.nan, "contribution": 0.0,
                "effective_weight": 0.0, "status": "missing",
            })
            continue

        w = scored["nominal_weight"]
        pillar_rows.append({
            "pillar": pillar,
            "pillar_score": float((scored["points"] * w).sum() / w.sum()),
            "contribution": float(scored["contribution"].sum()),
            "effective_weight": float(scored["effective_weight"].sum()),
            "status": "scored",
        })

    pillars = pd.DataFrame(pillar_rows)

    # ---- plain-English drivers -------------------------------------------
    scored_rows = comp[scored_mask]
    strengths = [
        f"{r.label}: {_fmt_value(r.value, r.unit)} ({r.points:.0f}/100 points)"
        for r in scored_rows.sort_values("points", ascending=False).itertuples()
        if r.points >= 75
    ][:3]
    concerns = [
        f"{r.label}: {_fmt_value(r.value, r.unit)} ({r.points:.0f}/100 points)"
        for r in scored_rows.sort_values("points").itertuples()
        if r.points < 40
    ][:3]

    caveats: List[str] = []
    if is_financial:
        caveats.append(
            "Bank / NBFC / insurer: leverage, interest coverage, operating margin and "
            "cash conversion are not scored."
        )
    missing = comp[comp["status"] == "missing"]
    for r in missing.itertuples():
        caveats.append(f"{r.label} excluded: {r.note}")
    if score is None:
        caveats.append(
            f"Score withheld: only {coverage:.0f}% of the applicable weight has usable data "
            f"(minimum {MIN_COVERAGE_PCT:.0f}%)."
        )

    as_of = metrics_row.get("as_of_year")

    if reference_year is not None and as_of is not None and pd.notna(as_of) and int(as_of) < int(reference_year):
        caveats.append(
            f"Latest available financial year is {int(as_of)}, older than the {int(reference_year)} "
            "used for most companies; compare with care."
        )

    return HealthScore(
        company_id=str(metrics_row.get("company_id")),
        company_name=str(metrics_row.get("company_name")),
        score=score,
        grade=letter,
        grade_label=label,
        data_coverage_pct=round(coverage, 1),
        as_of_year=int(as_of) if as_of is not None and pd.notna(as_of) else None,
        is_financial=is_financial,
        components=comp,
        pillars=pillars,
        strengths=strengths,
        concerns=concerns,
        caveats=caveats,
    )


def compute_all(metrics: pd.DataFrame) -> Dict[str, HealthScore]:
    reference = metrics["as_of_year"].max() if "as_of_year" in metrics.columns else None
    reference = int(reference) if reference is not None and pd.notna(reference) else None

    return {
        str(row["company_id"]): compute_health_score(row, reference_year=reference)
        for _, row in metrics.iterrows()
    }


def scores_table(scores: Dict[str, HealthScore], metrics: pd.DataFrame) -> pd.DataFrame:
    """Flat league table: one row per company, sorted by score."""

    sector = metrics.set_index("company_id")["broad_sector"].to_dict()
    rows = []

    for cid, hs in scores.items():
        row = {
            "company_id": cid,
            "company_name": hs.company_name,
            "broad_sector": sector.get(cid),
            "score": hs.score,
            "grade": hs.grade,
            "grade_label": hs.grade_label,
            "data_coverage_pct": hs.data_coverage_pct,
            "as_of_year": hs.as_of_year,
        }
        for p in hs.pillars.itertuples():
            row[f"{p.pillar.lower().replace(' ', '_')}_score"] = p.pillar_score
        rows.append(row)

    df = pd.DataFrame(rows)

    return df.sort_values("score", ascending=False, na_position="last").reset_index(drop=True)
