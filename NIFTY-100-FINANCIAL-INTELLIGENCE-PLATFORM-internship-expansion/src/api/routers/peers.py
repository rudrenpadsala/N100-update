"""
peers.py

Sprint 6
Day 40

Peer group and peer percentile endpoints.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_db, rows_to_dicts

router = APIRouter(prefix="/peers", tags=["Peers"])


@router.get("/groups")
def list_peer_groups(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """
    List every peer group and its member count.
    """

    rows = conn.execute("""
        SELECT
            peer_group_name,
            COUNT(*) AS company_count
        FROM peer_groups
        GROUP BY peer_group_name
        ORDER BY peer_group_name
        """).fetchall()

    return {"results": rows_to_dicts(rows)}


@router.get("/groups/{peer_group_name}")
def get_peer_group_members(
    peer_group_name: str, conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    """
    List every company in a peer group, flagging the
    benchmark company if one is set.

    Raises:
        HTTPException: 404 if the peer group does not exist.
    """

    rows = conn.execute(
        """
        SELECT
            pg.company_id,
            c.company_name,
            pg.is_benchmark
        FROM peer_groups pg
        LEFT JOIN companies c ON c.id = pg.company_id
        WHERE pg.peer_group_name = ?
        ORDER BY pg.is_benchmark DESC, c.company_name
        """,
        (peer_group_name,),
    ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404, detail=f"Peer group '{peer_group_name}' not found"
        )

    return {"peer_group_name": peer_group_name, "results": rows_to_dicts(rows)}


@router.get("/{ticker}/percentiles")
def get_company_percentiles(
    ticker: str, conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    """
    Get every peer-percentile ranking recorded for a company.

    Raises:
        HTTPException: 404 if no percentile data exists.
    """

    rows = conn.execute(
        """
        SELECT
            peer_group_name,
            metric,
            value,
            percentile_rank,
            year
        FROM peer_percentiles
        WHERE company_id = ?
        ORDER BY year DESC, metric
        """,
        (ticker,),
    ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404, detail=f"No peer percentile data found for '{ticker}'"
        )

    return {"company_id": ticker, "results": rows_to_dicts(rows)}
