"""
Module 1 - data-quality monitoring.

Each test starts from the CLEAN synthetic database, breaks exactly one
thing and checks that exactly that thing is reported.
"""

import numpy as np
import pandas as pd
import pytest

from src.quality.data_quality import (
    DataQualityMonitor, ISSUE_COLUMNS, company_reliability, company_warnings,
    run_quality_checks, summarize,
)


def checks(issues, name=None, severity=None, company=None, table=None):
    out = issues
    if name is not None:
        out = out[out["check"] == name]
    if severity is not None:
        out = out[out["severity"] == severity]
    if company is not None:
        out = out[out["company_id"] == company]
    if table is not None:
        out = out[out["table"] == table]
    return out


def edit(tables, table, where, **changes):
    """Return a copy of tables with `changes` applied to rows matching `where`."""
    out = {k: v.copy() for k, v in tables.items()}
    mask = where(out[table])
    for col, value in changes.items():
        out[table].loc[mask, col] = value
    return out


# --------------------------------------------------------------------------
# Baseline
# --------------------------------------------------------------------------

def test_clean_data_produces_no_errors_or_warnings(synthetic_tables):
    issues = run_quality_checks(synthetic_tables)
    assert issues[issues["severity"].isin(["error", "warning"])].empty


def test_result_has_the_documented_columns(synthetic_tables):
    assert list(run_quality_checks(synthetic_tables).columns) == ISSUE_COLUMNS


def test_results_are_deterministic(synthetic_tables):
    tables = edit(synthetic_tables, "profitandloss",
                  lambda d: (d.company_id == "A") & (d.year == "Mar 2022"), sales=np.nan)
    first = run_quality_checks(tables)
    second = run_quality_checks(tables)
    pd.testing.assert_frame_equal(first, second)


# --------------------------------------------------------------------------
# 1. Missing values
# --------------------------------------------------------------------------

def test_missing_critical_value_is_an_error(synthetic_tables):
    tables = edit(synthetic_tables, "profitandloss",
                  lambda d: (d.company_id == "A") & (d.year == "Mar 2022"), sales=np.nan)
    hit = checks(run_quality_checks(tables), "null_value", "error", "A")
    assert len(hit) == 1
    assert hit.iloc[0]["column"] == "sales" and hit.iloc[0]["period"] == "Mar 2022"


def test_missing_expected_value_is_only_info(synthetic_tables):
    tables = edit(synthetic_tables, "profitandloss",
                  lambda d: d.company_id == "A", dividend_payout=np.nan)
    issues = run_quality_checks(tables)
    assert issues[issues["severity"].isin(["error", "warning"])].empty
    assert len(checks(issues, "null_value", "info", "A")) == 6     # one per fiscal year


def test_company_missing_from_a_table_is_reported(synthetic_tables):
    tables = dict(synthetic_tables)
    tables["cashflow"] = tables["cashflow"][tables["cashflow"].company_id != "D"]
    hit = checks(run_quality_checks(tables), "company_missing_from_table", "warning", "D")
    assert len(hit) == 1 and hit.iloc[0]["table"] == "cashflow"


# --------------------------------------------------------------------------
# 2. Duplicates
# --------------------------------------------------------------------------

def test_identical_duplicate_period_is_a_warning(synthetic_tables):
    tables = dict(synthetic_tables)
    dup = tables["profitandloss"].query("company_id == 'A' and year == 'Mar 2023'")
    tables["profitandloss"] = pd.concat([tables["profitandloss"], dup], ignore_index=True)
    issues = run_quality_checks(tables)
    hit = checks(issues, "duplicate_period_identical", "warning", "A")
    assert len(hit) == 1
    assert checks(issues, "duplicate_period_conflicting").empty


def test_conflicting_duplicate_period_is_an_error(synthetic_tables):
    tables = dict(synthetic_tables)
    dup = tables["profitandloss"].query("company_id == 'A' and year == 'Mar 2023'").copy()
    dup["sales"] = dup["sales"] + 500
    tables["profitandloss"] = pd.concat([tables["profitandloss"], dup], ignore_index=True)
    hit = checks(run_quality_checks(tables), "duplicate_period_conflicting", "error", "A")
    assert len(hit) == 1


def test_label_variant_duplicate_is_detected(synthetic_tables):
    tables = dict(synthetic_tables)
    dup = tables["cashflow"].query("company_id == 'B' and year == 'Mar 2022'").copy()
    dup["year"] = "Mar-22"
    tables["cashflow"] = pd.concat([tables["cashflow"], dup], ignore_index=True)
    issues = run_quality_checks(tables)
    hit = checks(issues, "duplicate_period_identical", None, "B", "cashflow")
    assert len(hit) == 1 and "Mar-22" in hit.iloc[0]["detail"]
    assert len(checks(issues, "non_standard_period_label", "warning", "B")) == 1


def test_company_in_two_peer_groups_is_flagged(synthetic_tables):
    tables = dict(synthetic_tables)
    extra = pd.DataFrame({"peer_group_name": ["Other"], "company_id": ["A"], "is_benchmark": [0]})
    tables["peer_groups"] = pd.concat([tables["peer_groups"], extra], ignore_index=True)
    assert len(checks(run_quality_checks(tables), "multiple_peer_groups", "warning", "A")) == 1


# --------------------------------------------------------------------------
# 3. Inconsistent periods
# --------------------------------------------------------------------------

@pytest.mark.parametrize("label, check, severity", [
    ("TTM", "ttm_row", "info"),
    ("2024.5", "unusable_period_label", "warning"),
    ("Mar 2024 9m", "unusable_period_label", "warning"),
])
def test_period_label_problems(synthetic_tables, label, check, severity):
    tables = dict(synthetic_tables)
    extra = tables["profitandloss"].query("company_id == 'A' and year == 'Mar 2024'").copy()
    extra["year"] = label
    tables["profitandloss"] = pd.concat([tables["profitandloss"], extra], ignore_index=True)
    assert len(checks(run_quality_checks(tables), check, severity, "A")) == 1


def test_abbreviated_label_is_flagged_but_still_usable(synthetic_tables):
    tables = edit(synthetic_tables, "cashflow",
                  lambda d: (d.company_id == "C") & (d.year == "Mar 2021"), year="Mar-21")
    issues = run_quality_checks(tables)
    assert len(checks(issues, "non_standard_period_label", "warning", "C")) == 1
    assert checks(issues, "gap_in_years").empty     # Mar-21 still counts as 2021


def test_half_year_row_is_off_cycle_not_a_duplicate(synthetic_tables):
    tables = dict(synthetic_tables)
    half = tables["balancesheet"].query("company_id == 'A' and year == 'Mar 2024'").copy()
    half["year"] = "Sep 2024"
    half["total_assets"] += 77
    half["total_liabilities"] += 77
    tables["balancesheet"] = pd.concat([tables["balancesheet"], half], ignore_index=True)
    issues = run_quality_checks(tables)
    assert len(checks(issues, "off_cycle_period", "warning", "A", "balancesheet")) == 1
    assert checks(issues, "duplicate_period_conflicting").empty


def test_gap_in_years_is_reported(synthetic_tables):
    tables = dict(synthetic_tables)
    tables["profitandloss"] = tables["profitandloss"].query(
        "not (company_id == 'A' and year == 'Mar 2021')")
    hit = checks(run_quality_checks(tables), "gap_in_years", "warning", "A", "profitandloss")
    assert len(hit) == 1 and "2021" in hit.iloc[0]["detail"]


def test_statements_ending_in_different_years_are_flagged(synthetic_tables):
    tables = dict(synthetic_tables)
    tables["cashflow"] = tables["cashflow"].query("not (company_id == 'D' and year == 'Mar 2024')")
    hit = checks(run_quality_checks(tables), "latest_year_mismatch", "warning", "D")
    assert len(hit) == 1 and "cashflow=2023" in hit.iloc[0]["detail"]


# --------------------------------------------------------------------------
# 4. Invalid metrics
# --------------------------------------------------------------------------

def test_unbalanced_balance_sheet_is_an_error(synthetic_tables):
    tables = edit(synthetic_tables, "balancesheet",
                  lambda d: (d.company_id == "B") & (d.year == "Mar 2024"), total_assets=1.0)
    assert len(checks(run_quality_checks(tables), "balance_sheet_not_balanced", "error", "B")) == 1


def test_balance_sheet_rounding_difference_is_tolerated(synthetic_tables):
    tables = synthetic_tables["balancesheet"].copy()
    tables.loc[(tables.company_id == "B") & (tables.year == "Mar 2024"), "total_assets"] += 0.5
    tables = {**synthetic_tables, "balancesheet": tables}
    assert checks(run_quality_checks(tables), "balance_sheet_not_balanced").empty


def test_negative_sales_is_an_error(synthetic_tables):
    tables = edit(synthetic_tables, "profitandloss",
                  lambda d: (d.company_id == "A") & (d.year == "Mar 2024"), sales=-10.0)
    assert len(checks(run_quality_checks(tables), "negative_sales", "error", "A")) == 1


def test_implausible_roe_is_an_error_and_extreme_roe_a_warning(synthetic_tables):
    tables = edit(synthetic_tables, "financial_ratios",
                  lambda d: (d.company_id == "A") & (d.year == "Mar 2024"), return_on_equity_pct=15000.0)
    tables = edit(tables, "financial_ratios",
                  lambda d: (d.company_id == "B") & (d.year == "Mar 2024"), return_on_equity_pct=250.0)
    issues = run_quality_checks(tables)
    assert len(checks(issues, "roe_implausible", "error", "A")) == 1
    assert len(checks(issues, "roe_extreme", "warning", "B")) == 1


def test_cashflow_that_does_not_add_up_is_a_warning(synthetic_tables):
    tables = edit(synthetic_tables, "cashflow",
                  lambda d: (d.company_id == "C") & (d.year == "Mar 2024"), net_cash_flow=9999.0)
    assert len(checks(run_quality_checks(tables), "cashflow_does_not_add_up", "warning", "C")) == 1


def test_negative_net_worth_is_a_warning(synthetic_tables):
    tables = edit(synthetic_tables, "balancesheet",
                  lambda d: (d.company_id == "D") & (d.year == "Mar 2024"), reserves=-500.0)
    assert len(checks(run_quality_checks(tables), "negative_net_worth", "warning", "D")) == 1


def test_expenses_implausibly_low_applies_to_industrials_only(synthetic_tables):
    tables = edit(synthetic_tables, "profitandloss",
                  lambda d: (d.company_id.isin(["A", "F1"])) & (d.year == "Mar 2024"), expenses=5.0)
    issues = run_quality_checks(tables)
    assert len(checks(issues, "expenses_implausibly_low", "warning", "A")) == 1
    assert checks(issues, "expenses_implausibly_low", company="F1").empty


def test_stock_price_checks(synthetic_tables):
    tables = dict(synthetic_tables)
    tables["stock_prices"] = pd.DataFrame({
        "company_id": ["A", "A"], "date": ["2024-01-01", "2024-01-02"],
        "open_price": [10, 10], "high_price": [9, 12], "low_price": [11, 9],
        "close_price": [10, -1], "volume": [1, 1], "adjusted_close": [10, -1],
    })
    issues = run_quality_checks(tables)
    assert len(checks(issues, "high_below_low", "error")) == 1
    assert len(checks(issues, "invalid_close_price", "error")) == 1


def test_orphan_company_ids_are_reported(synthetic_tables):
    tables = dict(synthetic_tables)
    ghost = tables["profitandloss"].query("company_id == 'A'").copy()
    ghost["company_id"] = "GHOST"
    tables["profitandloss"] = pd.concat([tables["profitandloss"], ghost], ignore_index=True)
    hit = checks(run_quality_checks(tables), "orphan_company_id", "error", "GHOST")
    assert len(hit) == 1 and hit.iloc[0]["value"] == 6


# --------------------------------------------------------------------------
# Summaries used by the dashboard and PDF
# --------------------------------------------------------------------------

def test_summarize_counts_by_severity(synthetic_tables):
    tables = edit(synthetic_tables, "profitandloss",
                  lambda d: (d.company_id == "A") & (d.year == "Mar 2024"), sales=-10.0)
    issues = run_quality_checks(tables)
    s = summarize(issues, tables)
    assert s["errors"] == int((issues.severity == "error").sum()) >= 1
    assert s["total_issues"] == len(issues)
    assert 0 < s["clean_record_pct"] < 100


def test_reliability_rating_rules(synthetic_tables):
    tables = edit(synthetic_tables, "financial_ratios",
                  lambda d: (d.company_id == "A") & (d.year == "Mar 2024"), return_on_equity_pct=15000.0)
    tables = edit(tables, "profitandloss",
                  lambda d: (d.company_id == "B") & (d.year == "Mar 2024"), opm_percentage=300.0)
    issues = run_quality_checks(tables)
    assert company_reliability(issues, "A", 2022)["rating"] == "Low"
    assert company_reliability(issues, "B", 2022)["rating"] == "Medium"
    assert company_reliability(issues, "C", 2022)["rating"] == "High"


def test_old_issues_do_not_affect_recent_reliability(synthetic_tables):
    tables = edit(synthetic_tables, "financial_ratios",
                  lambda d: (d.company_id == "A") & (d.year == "Mar 2019"), return_on_equity_pct=15000.0)
    issues = run_quality_checks(tables)
    assert company_reliability(issues, "A", 2022)["rating"] == "High"
    assert company_reliability(issues, "A")["rating"] == "Low"


def test_company_warnings_are_readable_and_errors_come_first(synthetic_tables):
    tables = edit(synthetic_tables, "profitandloss",
                  lambda d: (d.company_id == "A") & (d.year == "Mar 2024"), opm_percentage=300.0)
    tables = edit(tables, "financial_ratios",
                  lambda d: (d.company_id == "A") & (d.year == "Mar 2024"), return_on_equity_pct=15000.0)
    lines = company_warnings(run_quality_checks(tables), "A", 2022)
    assert lines[0].startswith("[ERROR]") and any(l.startswith("[WARNING]") for l in lines)
    assert company_warnings(run_quality_checks(tables), "C", 2022) == []


# --------------------------------------------------------------------------
# The real database
# --------------------------------------------------------------------------

def test_real_database_known_problems_are_found(real_bundle):
    issues = real_bundle.issues
    assert not issues.empty
    assert set(issues["severity"]) <= {"error", "warning", "info"}
    # BEL's stored ROE is thousands of percent: must be an error.
    assert len(checks(issues, "roe_implausible", "error", "BEL")) >= 1
    # Statements contain company ids that are not in the master list.
    assert len(checks(issues, "orphan_company_id", "error")) >= 5
    # Mixed period labels exist in cashflow and balancesheet.
    assert len(checks(issues, "non_standard_period_label", "warning")) > 0
    assert len(checks(issues, "ttm_row", "info")) > 0


def test_real_database_every_company_gets_a_rating(real_bundle):
    for cid in real_bundle.company_ids():
        assert company_reliability(real_bundle.issues, cid, 2022)["rating"] in {"High", "Medium", "Low"}
