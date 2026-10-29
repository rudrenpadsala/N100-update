"""
parser.py

Sprint 5
Day 29

NLP Analysis Parser

Parses the free-text "period: value%" fields that come from
data/raw/analysis.xlsx (screener.in style growth/return commentary)
into structured numeric records, and cross-checks the parsed CAGR
values against the Ratio Engine output (financial_ratios /
output/company_cagr.csv) to flag divergence.

Outputs:
    output/analysis_parsed.csv
    output/parse_failures.csv
"""

import os
import re
import sqlite3

import pandas as pd

DB_PATH = "db/nifty100.db"
RAW_ANALYSIS_PATH = "data/raw/analysis.xlsx"
OUTPUT_DIR = "output"

# --------------------------------------------------
# Regex Patterns
# --------------------------------------------------

# Primary pattern required by the Sprint 5 spec:
#   "10 Years: 21%", "5 Years   14%", "3 Years:9%"
YEARS_PATTERN = re.compile(
    r"(\d+)\s*Years?:?\s*([\d.]+)\s*%"
)

# The raw data also contains a few other screener.in style periods
# that do not fit the "N Years" shape (TTM, 1 Year, Last Year).
# These are handled as a documented extension of the spec so that
# real rows are not silently dropped as failures.
TTM_PATTERN = re.compile(
    r"TTM:?\s*([\-\d.]+)\s*%"
)

SINGLE_YEAR_PATTERN = re.compile(
    r"(?:1\s*Year|Last\s*Year):?\s*([\-\d.]+)\s*%",
    re.IGNORECASE
)

FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe"
]

# Maps a parsed field + period to the closest available Ratio Engine
# column so the two can be cross-checked. Only 5-year periods have a
# direct match today (revenue_cagr_5yr / pat_cagr_5yr); other periods
# are parsed but not cross-checked (documented assumption below).
RATIO_ENGINE_MATCH = {
    ("compounded_sales_growth", "5"): "revenue_cagr_5yr",
    ("compounded_profit_growth", "5"): "pat_cagr_5yr",
}

DIVERGENCE_THRESHOLD_PCT = 5.0


# --------------------------------------------------
# Field Parsing
# --------------------------------------------------

def parse_field(raw_text):
    """
    Parse a single free-text field such as "10 Years: 21%".

    Returns:
        (period_label, value, status)

        period_label : "10", "5", "3", "TTM", "1", None
        value        : float or None
        status       : "OK" or "PARSE_FAILED"
    """

    if raw_text is None or (isinstance(raw_text, float) and pd.isna(raw_text)):
        return None, None, "PARSE_FAILED"

    text = str(raw_text).strip()

    if text == "" or text.lower() == "nan":
        return None, None, "PARSE_FAILED"

    match = YEARS_PATTERN.search(text)

    if match:
        period = match.group(1)
        value = float(match.group(2))
        return period, value, "OK"

    match = TTM_PATTERN.search(text)

    if match:
        value = float(match.group(1))
        return "TTM", value, "OK"

    match = SINGLE_YEAR_PATTERN.search(text)

    if match:
        value = float(match.group(1))
        return "1", value, "OK"

    return None, None, "PARSE_FAILED"


# --------------------------------------------------
# Ratio Engine Cross Check
# --------------------------------------------------

def load_ratio_engine_lookup():
    """
    Build a {company_id: latest_row} lookup from financial_ratios so
    parsed CAGR values can be cross-checked against the Ratio Engine.
    """

    conn = sqlite3.connect(DB_PATH)

    ratios = pd.read_sql(
        """
        SELECT
            company_id,
            year,
            revenue_cagr_5yr,
            pat_cagr_5yr,
            return_on_equity_pct
        FROM financial_ratios
        """,
        conn
    )

    conn.close()

    # Keep only the latest reported year per company for the check.
    ratios = ratios.sort_values(["company_id", "year"])
    latest = ratios.drop_duplicates(subset=["company_id"], keep="last")

    return latest.set_index("company_id")


def cross_check(field, period, parsed_value, company_id, ratio_lookup):
    """
    Compare a parsed value against the Ratio Engine and return:
        (ratio_engine_value, divergence_pct, divergence_flag)
    """

    ratio_col = RATIO_ENGINE_MATCH.get((field, period))

    if ratio_col is None:
        return None, None, "NOT_CHECKED"

    if company_id not in ratio_lookup.index:
        return None, None, "NOT_CHECKED"

    ratio_value = ratio_lookup.loc[company_id, ratio_col]

    if pd.isna(ratio_value) or parsed_value is None:
        return None, None, "NOT_CHECKED"

    divergence = round(abs(parsed_value - ratio_value), 2)

    flag = "DIVERGENT" if divergence > DIVERGENCE_THRESHOLD_PCT else "OK"

    return round(float(ratio_value), 2), divergence, flag


# --------------------------------------------------
# Main Parse Routine
# --------------------------------------------------

def parse_analysis(raw_path=RAW_ANALYSIS_PATH):
    """
    Parse data/raw/analysis.xlsx into a tidy long-format DataFrame,
    one row per (company_id, field, period).

    Returns:
        (parsed_df, failures_df)
    """

    raw = pd.read_excel(raw_path, header=1)

    ratio_lookup = load_ratio_engine_lookup()

    parsed_rows = []
    failure_rows = []

    for _, row in raw.iterrows():

        company_id = row.get("company_id")

        for field in FIELDS:

            raw_text = row.get(field)

            period, value, status = parse_field(raw_text)

            if status == "PARSE_FAILED":
                failure_rows.append({
                    "row_id": row.get("id"),
                    "company_id": company_id,
                    "field": field,
                    "raw_text": raw_text,
                    "reason": "REGEX_NO_MATCH"
                })
                continue

            ratio_value, divergence_pct, divergence_flag = cross_check(
                field, period, value, company_id, ratio_lookup
            )

            parsed_rows.append({
                "row_id": row.get("id"),
                "company_id": company_id,
                "field": field,
                "period": period,
                "parsed_value_pct": value,
                "ratio_engine_value_pct": ratio_value,
                "divergence_pct": divergence_pct,
                "divergence_flag": divergence_flag
            })

    parsed_df = pd.DataFrame(parsed_rows)
    failures_df = pd.DataFrame(failure_rows)

    return parsed_df, failures_df


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

def main():

    print("=" * 60)
    print("NLP Analysis Parser (Sprint 5 - Day 29)")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    parsed_df, failures_df = parse_analysis()

    parsed_path = os.path.join(OUTPUT_DIR, "analysis_parsed.csv")
    failures_path = os.path.join(OUTPUT_DIR, "parse_failures.csv")

    parsed_df.to_csv(parsed_path, index=False)
    failures_df.to_csv(failures_path, index=False)

    divergent = 0

    if not parsed_df.empty:
        divergent = int((parsed_df["divergence_flag"] == "DIVERGENT").sum())

    print(f"✔ Parsed rows        : {len(parsed_df)}")
    print(f"✔ Parse failures     : {len(failures_df)}")
    print(f"✔ Divergent (>{DIVERGENCE_THRESHOLD_PCT}%) : {divergent}")
    print(f"✔ Saved: {parsed_path}")
    print(f"✔ Saved: {failures_path}")


if __name__ == "__main__":
    main()
