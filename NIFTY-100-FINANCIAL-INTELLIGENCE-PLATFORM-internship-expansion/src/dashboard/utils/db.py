"""
Shared SQLite Data Loader
Used by every Streamlit screen
"""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

# Resolve the DB path relative to this file's location, not the process's
# current working directory. This makes it work regardless of how/where
# Streamlit (locally or on Streamlit Cloud) launches the app from.
# utils/db.py -> utils -> dashboard -> src -> <repo root> -> db/nifty100.db
_REPO_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = str(_REPO_ROOT / "db" / "nifty100.db")


# -----------------------------------------------------
# SQLite Connection
# -----------------------------------------------------

def get_connection():
    if not Path(DB_PATH).exists():
        st.error(
            f"Database file not found at `{DB_PATH}`.\n\n"
            "Make sure `db/nifty100.db` is committed to the repository "
            "(check it isn't excluded by .gitignore) and pushed to GitHub "
            "before deploying to Streamlit Cloud."
        )
        st.stop()
    return sqlite3.connect(DB_PATH)


# -----------------------------------------------------
# Companies
# -----------------------------------------------------

@st.cache_data(ttl=600)
def get_companies():

    conn = get_connection()

    query = """
    SELECT *
    FROM companies
    ORDER BY company_name
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# -----------------------------------------------------
# Financial Ratios
# -----------------------------------------------------

@st.cache_data(ttl=600)
def get_ratios(ticker=None, year=None):

    conn = get_connection()

    query = """
    SELECT *
    FROM financial_ratios
    """

    conditions = []
    params = []

    if ticker is not None:
        conditions.append("company_id = ?")
        params.append(ticker)

    if year is not None:
        conditions.append("year = ?")
        params.append(year)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY company_id, year"

    df = pd.read_sql(
        query,
        conn,
        params=params
    )

    conn.close()

    return df


# -----------------------------------------------------
# Profit & Loss
# -----------------------------------------------------

@st.cache_data(ttl=600)
def get_pl(ticker=None):

    conn = get_connection()

    query = """
    SELECT *
    FROM profitandloss
    """

    params = []

    if ticker is not None:
        query += " WHERE company_id = ?"
        params.append(ticker)

    query += " ORDER BY year"

    df = pd.read_sql(
        query,
        conn,
        params=params,
    )

    conn.close()

    return df




# -----------------------------------------------------
# Balance Sheet
# -----------------------------------------------------

@st.cache_data(ttl=600)
def get_bs(ticker=None):

    conn = get_connection()

    query = """
    SELECT *
    FROM balancesheet
    """

    params = []

    if ticker is not None:
        query += " WHERE company_id = ?"
        params.append(ticker)

    query += " ORDER BY year"

    df = pd.read_sql(
        query,
        conn,
        params=params,
    )

    conn.close()

    return df




# -----------------------------------------------------
# Cash Flow
# -----------------------------------------------------

@st.cache_data(ttl=600)
def get_cf(ticker=None):

    conn = get_connection()

    query = """
    SELECT *
    FROM cashflow
    """

    params = []

    if ticker is not None:
        query += " WHERE company_id = ?"
        params.append(ticker)

    query += " ORDER BY year"

    df = pd.read_sql(
        query,
        conn,
        params=params,
    )

    conn.close()

    return df



# -----------------------------------------------------
# Sector Information
# -----------------------------------------------------

@st.cache_data(ttl=600)
def get_sectors():

    conn = get_connection()

    query = """
    SELECT *
    FROM sectors
    ORDER BY broad_sector, sub_sector
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# -----------------------------------------------------
# Peer Groups
# -----------------------------------------------------

@st.cache_data(ttl=600)
def get_peers(group_name=None):

    conn = get_connection()

    query = """
    SELECT *
    FROM peer_groups
    """

    params = []

    if group_name is not None:
        query += " WHERE peer_group_name = ?"
        params.append(group_name)

    query += """
    ORDER BY
        peer_group_name,
        is_benchmark DESC,
        company_id
    """

    df = pd.read_sql(
        query,
        conn,
        params=params,
    )

    conn.close()

    return df



# -----------------------------------------------------
# Annual Reports
# -----------------------------------------------------

@st.cache_data(ttl=600)
def get_reports(company_id=None):

    conn = get_connection()

    query = """
    SELECT *
    FROM documents
    """

    params = []

    if company_id is not None:
        query += " WHERE company_id = ?"
        params.append(company_id)

    query += " ORDER BY company_id, Year DESC"

    df = pd.read_sql(
        query,
        conn,
        params=params,
    )

    conn.close()

    return df




# -----------------------------------------------------
# Market Cap
# -----------------------------------------------------

@st.cache_data(ttl=600)
def get_market_cap(ticker=None):

    conn = get_connection()

    query = """
    SELECT *
    FROM market_cap
    """

    params = []

    if ticker is not None:
        query += " WHERE company_id = ?"
        params.append(ticker)

    query += " ORDER BY company_id, year"

    df = pd.read_sql(
        query,
        conn,
        params=params
    )

    conn.close()

    return df


@st.cache_data(ttl=600)
def get_market_cap(ticker=None):

    conn = get_connection()

    query = """
    SELECT *
    FROM market_cap
    """

    params = []

    if ticker is not None:
        query += " WHERE company_id = ?"
        params.append(ticker)

    query += " ORDER BY company_id, year"

    df = pd.read_sql(
        query,
        conn,
        params=params,
    )

    conn.close()

    return df



# -----------------------------------------------------
# Valuation
# -----------------------------------------------------

@st.cache_data(ttl=600)
def get_valuation(ticker=None):

    conn = get_connection()

    try:

        query = """
        SELECT *
        FROM valuation_summary
        """

        params = []

        if ticker is not None:
            query += " WHERE company_id = ?"
            params.append(ticker)

        df = pd.read_sql(
            query,
            conn,
            params=params,
        )

    except Exception:

        # Day 23: valuation table may not exist yet.
        # Day 26 will generate it.
        df = pd.DataFrame()

    conn.close()

    return df

# -----------------------------------------------------
# Annual Reports Metadata
# -----------------------------------------------------

@st.cache_data(ttl=600)
def get_annual_reports_metadata(company_id=None):
    """Retrieve verified annual reports metadata, auditor opinions and filing statuses."""
    conn = get_connection()
    query = "SELECT * FROM annual_reports_metadata"
    params = []
    if company_id is not None:
        query += " WHERE company_id = ?"
        params.append(company_id)
    query += " ORDER BY company_id, financial_year DESC"
    try:
        df = pd.read_sql(query, conn, params=params)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

