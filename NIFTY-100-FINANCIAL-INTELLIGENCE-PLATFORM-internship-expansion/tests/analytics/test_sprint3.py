import sqlite3
import pandas as pd

DB = "db/nifty100.db"


def test_financial_ratios_exists():

    conn = sqlite3.connect(DB)

    df = pd.read_sql(
        "SELECT * FROM financial_ratios LIMIT 5",
        conn
    )

    conn.close()

    assert len(df) > 0


def test_peer_percentiles_exists():

    conn = sqlite3.connect(DB)

    df = pd.read_sql(
        "SELECT * FROM peer_percentiles LIMIT 5",
        conn
    )

    conn.close()

    assert len(df) > 0


def test_peer_groups_exists():

    conn = sqlite3.connect(DB)

    df = pd.read_sql(
        "SELECT * FROM peer_groups LIMIT 5",
        conn
    )

    conn.close()

    assert len(df) > 0