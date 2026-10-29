"""
documents.py

Sprint 6
Day 40

Company document endpoints (annual report links).
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_db, rows_to_dicts

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/{ticker}")
def get_company_documents(
    ticker: str, conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    """
    Get every annual report link recorded for a company.

    Raises:
        HTTPException: 404 if no documents are found.
    """

    rows = conn.execute(
        """
        SELECT
            id,
            company_id,
            "Year" AS year,
            "Annual_Report" AS annual_report_url
        FROM documents
        WHERE company_id = ?
        ORDER BY "Year" DESC
        """,
        (ticker,),
    ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404, detail=f"No documents found for '{ticker}'"
        )

    return {"company_id": ticker, "results": rows_to_dicts(rows)}
