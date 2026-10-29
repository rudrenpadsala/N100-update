"""Period-label parsing, de-duplication and fiscal-year-end detection."""

import pandas as pd
import pytest

from src.quality.periods import (
    annual_rows, add_period_columns, fiscal_year_end_months, parse_period,
)


@pytest.mark.parametrize("label, kind, year, month", [
    ("Mar 2024", "standard", 2024, 3),
    ("Dec 2012", "standard", 2012, 12),
    ("Mar-24", "abbreviated", 2024, 3),
    ("Mar-98", "abbreviated", 1998, 3),
    ("2023", "year_only", 2023, None),
    ("TTM", "ttm", None, None),
    ("2024.5", "malformed", 2024, None),
    ("Mar 2016 9m", "suffixed", 2016, 3),
    ("Mar 2023 15", "suffixed", 2023, 3),
    ("garbage", "unknown", None, None),
    ("Xyz 2020", "unknown", None, None),
])
def test_parse_period(label, kind, year, month):
    p = parse_period(label)
    assert (p.kind, p.year, p.month) == (kind, year, month)


def test_parse_period_handles_missing_values():
    assert parse_period(None).kind == "unknown"
    assert parse_period(float("nan")).kind == "unknown"


def test_only_standard_and_year_labels_are_usable():
    usable = {l: parse_period(l).usable for l in
              ["Mar 2024", "Mar-24", "2024", "TTM", "2024.5", "Mar 2016 9m"]}
    assert usable == {"Mar 2024": True, "Mar-24": True, "2024": True,
                      "TTM": False, "2024.5": False, "Mar 2016 9m": False}


def test_annual_rows_collapses_label_variants_preferring_standard():
    df = pd.DataFrame({
        "company_id": ["A", "A", "A", "A"],
        "year": ["2024", "Mar-24", "Mar 2024", "TTM"],
        "sales": [3, 2, 1, 99],
    })
    out = annual_rows(df)
    assert len(out) == 1
    assert out.iloc[0]["year"] == "Mar 2024"
    assert out.iloc[0]["sales"] == 1


def test_annual_rows_drops_ttm_and_malformed():
    df = pd.DataFrame({
        "company_id": ["A"] * 4,
        "year": ["Mar 2023", "Mar 2024", "TTM", "2024.5"],
        "sales": [1, 2, 3, 4],
    })
    assert list(annual_rows(df)["year"]) == ["Mar 2023", "Mar 2024"]


def test_fiscal_year_end_is_the_most_common_month():
    df = pd.DataFrame({
        "company_id": ["A"] * 5,
        "year": ["Mar 2020", "Mar 2021", "Mar 2022", "Sep 2024", "Dec 2012"],
    })
    assert fiscal_year_end_months([df]) == {"A": 3}


def test_fiscal_year_end_tie_prefers_the_most_recent_period():
    df = pd.DataFrame({"company_id": ["A"] * 4,
                       "year": ["Mar 2014", "Mar 2015", "Dec 2023", "Dec 2024"]})
    assert fiscal_year_end_months([df]) == {"A": 12}


def test_off_cycle_rows_are_dropped_from_annual_rows():
    df = pd.DataFrame({
        "company_id": ["A"] * 4,
        "year": ["Mar 2022", "Mar 2023", "Mar 2024", "Sep 2024"],
        "sales": [1, 2, 3, 99],
    })
    fy = fiscal_year_end_months([df])
    out = annual_rows(df, fy_months=fy)
    assert list(out["sales"]) == [1, 2, 3]


def test_bare_years_are_never_off_cycle():
    df = pd.DataFrame({"company_id": ["A"] * 3, "year": ["Mar 2022", "Mar 2023", "2024"], "v": [1, 2, 3]})
    out = annual_rows(df, fy_months=fiscal_year_end_months([df]))
    assert list(out["v"]) == [1, 2, 3]


def test_add_period_columns_adds_expected_columns():
    out = add_period_columns(pd.DataFrame({"year": ["Mar 2024", "TTM"]}))
    assert {"period_kind", "year_key", "period_month"} <= set(out.columns)
    assert out["year_key"].isna().tolist() == [False, True]
