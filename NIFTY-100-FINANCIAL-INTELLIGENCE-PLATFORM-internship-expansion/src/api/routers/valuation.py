"""
valuation.py

Sprint 6
Day 40

Valuation and market-cap endpoints.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_db, rows_to_dicts

router = APIRouter(prefix="/valuation", tags=["Valuation"])

_RANKABLE_METRICS = {
    "market_cap_crore",
    "enterprise_value_crore",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
}


@router.get("/{ticker}")
def get_valuation_history(
    ticker: str, conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    """
    Get the full market-cap / valuation history for a company.

    Raises:
        HTTPException: 404 if the ticker has no valuation data.
    """

    rows = conn.execute(
        "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year", (ticker,)
    ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404, detail=f"No valuation data found for '{ticker}'"
        )

    return {"company_id": ticker, "results": rows_to_dicts(rows)}


@router.get("/rankings/top")
def get_valuation_rankings(
    metric: str = Query(
        "market_cap_crore",
        description="One of: " + ", ".join(sorted(_RANKABLE_METRICS)),
    ),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(20, ge=1, le=100),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    """
    Rank companies by their latest-year value for a given
    valuation metric.

    Raises:
        HTTPException: 400 if an unsupported metric is given.
    """

    if metric not in _RANKABLE_METRICS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported metric '{metric}'. "
            f"Choose from: {sorted(_RANKABLE_METRICS)}",
        )

    direction = "ASC" if order == "asc" else "DESC"

    query = f"""
        WITH latest_market AS (
            SELECT mc.*
            FROM market_cap mc
            INNER JOIN (
                SELECT company_id, MAX(id) AS max_id
                FROM market_cap
                GROUP BY company_id
            ) latest ON latest.max_id = mc.id
        )
        SELECT
            c.id AS company_id,
            c.company_name,
            lm.{metric} AS value,
            lm.year
        FROM latest_market lm
        INNER JOIN companies c ON c.id = lm.company_id
        WHERE lm.{metric} IS NOT NULL
        ORDER BY lm.{metric} {direction}
        LIMIT ?
    """

    rows = conn.execute(query, (limit,)).fetchall()

    return {"metric": metric, "order": order, "results": rows_to_dicts(rows)}
