"""
periods.py

Internship Expansion - Module 1 (Data Quality Monitoring)

One shared, well-tested parser for the financial-period labels that
appear in the database. The raw data mixes several formats:

    "Mar 2024"        standard label
    "Mar-24"          abbreviated label (cashflow table)
    "2024"            bare year (balancesheet table)
    "TTM"             trailing twelve months (not an annual period)
    "Mar 2016 9m"     part-year / suffixed label
    "2024.5"          malformed numeric label

Every analytics module uses this parser so that periods are classified,
de-duplicated and joined across tables in exactly the same way.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import pandas as pd

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_STANDARD = re.compile(r"^([A-Za-z]{3})\s+(\d{4})$")
_ABBREVIATED = re.compile(r"^([A-Za-z]{3})-(\d{2})$")
_YEAR_ONLY = re.compile(r"^(\d{4})$")
_NUMERIC_MALFORMED = re.compile(r"^(\d{4})\.\d+$")
_SUFFIXED = re.compile(r"^([A-Za-z]{3})\s+(\d{4})\s+\S+")

# Kinds that represent a usable full-year period.
USABLE_KINDS = ("standard", "abbreviated", "year_only")

# Preference order when two rows describe the same company-year.
_KIND_PRIORITY = {"standard": 0, "abbreviated": 1, "year_only": 2}


@dataclass(frozen=True)
class Period:
    label: str
    kind: str                    # standard | abbreviated | year_only | ttm | suffixed | malformed | unknown
    year: Optional[int]
    month: Optional[int]

    @property
    def usable(self) -> bool:
        return self.kind in USABLE_KINDS and self.year is not None


def _expand_two_digit_year(yy: int) -> int:
    return 2000 + yy if yy < 50 else 1900 + yy


def parse_period(label) -> Period:
    """Classify one period label."""

    if label is None or (isinstance(label, float) and pd.isna(label)):
        return Period("", "unknown", None, None)

    text = str(label).strip()

    if text.upper() == "TTM":
        return Period(text, "ttm", None, None)

    m = _STANDARD.match(text)
    if m and m.group(1).lower() in MONTHS:
        return Period(text, "standard", int(m.group(2)), MONTHS[m.group(1).lower()])

    m = _ABBREVIATED.match(text)
    if m and m.group(1).lower() in MONTHS:
        return Period(
            text, "abbreviated",
            _expand_two_digit_year(int(m.group(2))), MONTHS[m.group(1).lower()],
        )

    m = _YEAR_ONLY.match(text)
    if m:
        return Period(text, "year_only", int(m.group(1)), None)

    m = _NUMERIC_MALFORMED.match(text)
    if m:
        return Period(text, "malformed", int(m.group(1)), None)

    m = _SUFFIXED.match(text)
    if m and m.group(1).lower() in MONTHS:
        return Period(text, "suffixed", int(m.group(2)), MONTHS[m.group(1).lower()])

    return Period(text, "unknown", None, None)


def add_period_columns(df: pd.DataFrame, column: str = "year") -> pd.DataFrame:
    """
    Return a copy of df with these extra columns:
        period_kind, year_key (Int64), period_month (Int64)
    """

    out = df.copy()
    parsed = [parse_period(v) for v in out[column]]

    out["period_kind"] = [p.kind for p in parsed]
    out["year_key"] = pd.array([p.year for p in parsed], dtype="Int64")
    out["period_month"] = pd.array([p.month for p in parsed], dtype="Int64")

    return out


def fiscal_year_end_months(frames, column: str = "year") -> dict:
    """
    Work out each company's fiscal-year-end month.

    The month that appears most often across all supplied tables wins; if
    two months tie, the month used by the most recent period wins. Rows in
    any other month (for example a "Sep 2024" half-year snapshot stored
    next to "Mar 2024" annual rows, or a long transition period) are
    "off-cycle" and are not full fiscal years.

    frames: iterable of DataFrames that have company_id and a period column.
    """

    counts: dict = {}
    latest: dict = {}

    for df in frames:
        if df is None or df.empty or column not in df.columns:
            continue

        parsed = add_period_columns(df[["company_id", column]], column)
        parsed = parsed[parsed["period_kind"].isin(("standard", "abbreviated"))]

        for company_id, year, month in zip(
            parsed["company_id"], parsed["year_key"], parsed["period_month"]
        ):
            if pd.isna(month) or pd.isna(year):
                continue
            month, year = int(month), int(year)
            counts.setdefault(company_id, {}).setdefault(month, 0)
            counts[company_id][month] += 1
            key = (company_id, month)
            latest[key] = max(latest.get(key, 0), year)

    result = {}

    for company_id, by_month in counts.items():
        top = max(by_month.values())
        tied = [m for m, n in by_month.items() if n == top]
        result[company_id] = max(tied, key=lambda m: latest[(company_id, m)])

    return result


def mark_off_cycle(df: pd.DataFrame, fy_months: dict) -> pd.DataFrame:
    """
    Add a boolean off_cycle column (needs period_month from add_period_columns).
    Rows without a month (bare years) are never off-cycle.
    """

    out = df.copy()
    expected = out["company_id"].map(fy_months)
    month = out["period_month"]

    out["off_cycle"] = (
        month.notna() & expected.notna() & (month.astype("float") != expected.astype("float"))
    ).astype(bool)

    return out


def annual_rows(df: pd.DataFrame, column: str = "year", fy_months: dict | None = None) -> pd.DataFrame:
    """
    Keep only usable full-year rows, collapse duplicates that describe the
    same company-year (preferring the standard "Mon YYYY" label) and sort
    chronologically. Requires a company_id column.

    If fy_months (company -> fiscal-year-end month) is given, off-cycle
    rows such as half-year snapshots are dropped as well.
    """

    out = add_period_columns(df, column)
    out = out[out["period_kind"].isin(USABLE_KINDS)].copy()

    if fy_months:
        out = mark_off_cycle(out, fy_months)
        out = out[~out["off_cycle"]].drop(columns="off_cycle").copy()

    out["_priority"] = out["period_kind"].map(_KIND_PRIORITY)
    out = out.sort_values(["company_id", "year_key", "_priority"], kind="stable")
    out = out.drop_duplicates(subset=["company_id", "year_key"], keep="first")

    return out.drop(columns="_priority").reset_index(drop=True)
