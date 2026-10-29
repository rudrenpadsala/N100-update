"""Module 2 - explainable financial health score."""

import numpy as np
import pandas as pd
import pytest

from src.analytics.financial_metrics import build_metrics
from src.analytics.health_score import (
    GRADE_BANDS, METRICS, MIN_COVERAGE_PCT, PILLARS, compute_all, compute_health_score,
    grade_for, score_metric, scores_table,
)


def metrics_row(**overrides):
    base = dict(
        company_id="X", company_name="X Ltd", broad_sector="Industrials", is_financial=False,
        as_of_year=2024, interest_free=False, metric_notes={},
        roe_pct=20.0, net_margin_pct=20.0, operating_margin_pct=25.0, debt_to_equity=0.3,
        interest_coverage=8.0, revenue_cagr_pct=15.0, profit_cagr_pct=20.0, cfo_to_pat=1.0,
    )
    base.update(overrides)
    return pd.Series(base)


# --------------------------------------------------------------------------
# Scoring primitives
# --------------------------------------------------------------------------

@pytest.mark.parametrize("value, zero, full, expected", [
    (0.0, 0.0, 20.0, 0.0),
    (10.0, 0.0, 20.0, 50.0),
    (20.0, 0.0, 20.0, 100.0),
    (-5.0, 0.0, 20.0, 0.0),        # clipped below
    (45.0, 0.0, 20.0, 100.0),      # clipped above
    (0.3, 2.0, 0.3, 100.0),        # lower is better
    (2.0, 2.0, 0.3, 0.0),
    (1.15, 2.0, 0.3, 50.0),
    (5.0, 2.0, 0.3, 0.0),
])
def test_score_metric(value, zero, full, expected):
    assert score_metric(value, zero, full) == pytest.approx(expected)


def test_score_metric_missing_value_is_nan():
    assert np.isnan(score_metric(None, 0, 1)) and np.isnan(score_metric(float("nan"), 0, 1))


@pytest.mark.parametrize("score, grade", [
    (100, "A"), (75.0, "A"), (74.9, "B"), (60.0, "B"), (59.9, "C"), (45.0, "C"),
    (44.9, "D"), (30.0, "D"), (29.9, "E"), (0.0, "E"),
])
def test_grade_bands(score, grade):
    assert grade_for(score)[0] == grade


def test_grade_for_missing_score():
    assert grade_for(None) == ("N/A", "Insufficient data")


def test_documented_weights_add_to_100_and_cover_every_pillar():
    assert sum(m.weight for m in METRICS) == pytest.approx(100.0)
    assert {m.pillar for m in METRICS} == set(PILLARS)
    assert [lo for lo, _, _ in GRADE_BANDS] == sorted((lo for lo, _, _ in GRADE_BANDS), reverse=True)


# --------------------------------------------------------------------------
# Explainability: the parts add up to the whole
# --------------------------------------------------------------------------

def test_perfect_company_scores_100():
    hs = compute_health_score(metrics_row())
    assert hs.score == 100.0 and hs.grade == "A" and hs.data_coverage_pct == 100.0


def test_worst_company_scores_zero():
    hs = compute_health_score(metrics_row(
        roe_pct=0, net_margin_pct=0, operating_margin_pct=0, debt_to_equity=5.0,
        interest_coverage=0.5, revenue_cagr_pct=-3, profit_cagr_pct=-9, cfo_to_pat=0.0))
    assert hs.score == 0.0 and hs.grade == "E"


def test_contributions_add_up_to_the_score():
    hs = compute_health_score(metrics_row(roe_pct=11.0, debt_to_equity=1.1, cfo_to_pat=0.7))
    assert hs.components["contribution"].sum() == pytest.approx(hs.score, abs=0.06)


def test_each_contribution_is_points_times_effective_weight():
    hs = compute_health_score(metrics_row(roe_pct=7.0, net_margin_pct=4.0))
    for r in hs.components[hs.components.status == "scored"].itertuples():
        assert r.contribution == pytest.approx(r.points * r.effective_weight / 100)


def test_pillar_contributions_add_up_to_the_score():
    hs = compute_health_score(metrics_row(roe_pct=11.0, revenue_cagr_pct=4.0))
    assert hs.pillars["contribution"].sum() == pytest.approx(hs.score, abs=0.06)


def test_effective_weights_always_add_to_100():
    hs = compute_health_score(metrics_row(roe_pct=np.nan, profit_cagr_pct=np.nan))
    assert hs.components["effective_weight"].sum() == pytest.approx(100.0)


def test_strengths_and_concerns_are_listed():
    hs = compute_health_score(metrics_row(roe_pct=30.0, debt_to_equity=3.0))
    assert any("Return on equity" in s for s in hs.strengths)
    assert any("Debt-to-equity" in c for c in hs.concerns)


def test_scoring_is_deterministic():
    row = metrics_row(roe_pct=13.3, net_margin_pct=7.7)
    a, b = compute_health_score(row), compute_health_score(row)
    assert a.score == b.score
    pd.testing.assert_frame_equal(a.components, b.components)


# --------------------------------------------------------------------------
# Missing, excluded and not-applicable metrics
# --------------------------------------------------------------------------

def test_missing_metric_reduces_coverage_and_is_explained():
    hs = compute_health_score(metrics_row(
        profit_cagr_pct=np.nan, metric_notes={"profit_cagr_pct": "net profit negative"}))
    assert hs.data_coverage_pct == pytest.approx(87.5)
    comp = hs.components.set_index("metric").loc["profit_cagr_pct"]
    assert comp.status == "missing" and comp.contribution == 0 and "negative" in comp.note
    assert any("Profit growth" in c for c in hs.caveats)


def test_score_is_withheld_when_coverage_is_too_low():
    hs = compute_health_score(metrics_row(
        roe_pct=np.nan, net_margin_pct=np.nan, operating_margin_pct=np.nan,
        debt_to_equity=np.nan, interest_coverage=np.nan))
    assert hs.data_coverage_pct < MIN_COVERAGE_PCT
    assert hs.score is None and hs.grade == "N/A"
    assert any("withheld" in c for c in hs.caveats)


def test_interest_free_company_gets_full_marks_on_coverage():
    hs = compute_health_score(metrics_row(interest_coverage=np.nan, interest_free=True))
    row = hs.components.set_index("metric").loc["interest_coverage"]
    assert row.points == 100 and row.status == "scored" and "No interest" in row.note


def test_financials_are_not_scored_on_leverage_or_cash_conversion():
    hs = compute_health_score(metrics_row(is_financial=True, debt_to_equity=9.0, interest_coverage=1.0))
    comp = hs.components.set_index("metric")
    for key in ("operating_margin_pct", "debt_to_equity", "interest_coverage", "cfo_to_pat"):
        assert comp.loc[key, "status"] == "not_applicable"
        assert comp.loc[key, "contribution"] == 0
    assert hs.data_coverage_pct == 100.0        # not-applicable never counts as missing
    assert hs.score == 100.0                    # leverage of 9x does not hurt a bank
    assert hs.pillars.set_index("pillar").loc["Leverage", "status"] == "not_applicable"
    assert any("Bank" in c for c in hs.caveats)


def test_stale_company_gets_a_caveat():
    hs = compute_health_score(metrics_row(as_of_year=2021), reference_year=2024)
    assert any("2021" in c and "2024" in c for c in hs.caveats)
    assert not compute_health_score(metrics_row(), reference_year=2024).caveats


# --------------------------------------------------------------------------
# Full pipeline on synthetic data, ordering sanity
# --------------------------------------------------------------------------

def test_better_fundamentals_score_higher(synthetic_tables):
    scores = compute_all(build_metrics(synthetic_tables))
    assert scores["A"].score > scores["B"].score > scores["C"].score


def test_league_table_is_sorted_and_complete(synthetic_tables):
    metrics = build_metrics(synthetic_tables)
    league = scores_table(compute_all(metrics), metrics)
    assert len(league) == len(metrics)
    assert league["score"].is_monotonic_decreasing
    assert {"profitability_score", "leverage_score", "growth_score", "cash_quality_score"} <= set(league.columns)


# --------------------------------------------------------------------------
# Real database
# --------------------------------------------------------------------------

def test_every_real_company_has_a_valid_result(real_bundle):
    assert len(real_bundle.health) == 92
    for cid, hs in real_bundle.health.items():
        if hs.score is not None:
            assert 0 <= hs.score <= 100
            assert hs.components["contribution"].sum() == pytest.approx(hs.score, abs=0.06)
            assert hs.grade in {"A", "B", "C", "D", "E"}
        assert 0 <= hs.data_coverage_pct <= 100
        assert hs.components["effective_weight"].sum() in (pytest.approx(100.0), pytest.approx(0.0))


def test_real_data_bad_roe_is_excluded_not_scored(real_bundle):
    hal = real_bundle.health["HAL"].components.set_index("metric").loc["roe_pct"]
    assert hal.status == "missing" and "plausible range" in hal.note


def test_real_banks_and_insurers_are_not_scored_on_leverage(real_bundle):
    status = real_bundle.health["HDFCBANK"].components.set_index("metric")["status"]
    assert status["debt_to_equity"] == "not_applicable"


def test_few_real_companies_lack_a_score(real_bundle):
    withheld = [c for c, h in real_bundle.health.items() if h.score is None]
    assert len(withheld) <= 3
