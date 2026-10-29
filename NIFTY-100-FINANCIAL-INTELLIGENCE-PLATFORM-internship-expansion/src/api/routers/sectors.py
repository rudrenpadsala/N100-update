"""
sectors.py

Sprint 6
Day 40

Sector-level endpoints.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_db, rows_to_dicts

router = APIRouter(prefix="/sectors", tags=["Sectors"])


@router.get("")
def list_sectors(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """
    List every broad sector along with its company count and
    average ROE / ROCE.

    Returns:
        JSON payload with one row per broad sector.
    """

    rows = conn.execute("""
        SELECT
            s.broad_sector,
            COUNT(*) AS company_count,
            ROUND(AVG(c.roe_percentage), 2) AS avg_roe_percentage,
            ROUND(AVG(c.roce_percentage), 2) AS avg_roce_percentage
        FROM sectors s
        LEFT JOIN companies c ON c.id = s.company_id
        GROUP BY s.broad_sector
        ORDER BY s.broad_sector
        """).fetchall()

    return {"results": rows_to_dicts(rows)}


@router.get("/{sector_name}/companies")
def get_sector_companies(
    sector_name: str,
    sub_sector: str | None = Query(None, description="Filter by sub_sector"),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    """
    List every company within a broad sector, optionally
    filtered to a sub-sector.

    Raises:
        HTTPException: 404 if the sector has no companies.
    """

    query = """
        SELECT
            c.id,
            c.company_name,
            s.sub_sector,
            s.market_cap_category,
            s.index_weight_pct,
            c.roe_percentage,
            c.roce_percentage
        FROM sectors s
        INNER JOIN companies c ON c.id = s.company_id
        WHERE s.broad_sector = ?
    """

    params = [sector_name]

    if sub_sector:
        query += " AND s.sub_sector = ?"
        params.append(sub_sector)

    query += " ORDER BY c.company_name"

    rows = conn.execute(query, params).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404, detail=f"No companies found for sector '{sector_name}'"
        )

    return {"broad_sector": sector_name, "results": rows_to_dicts(rows)}
