"""
companies.py

Sprint 6
Day 38 (scaffold) / Day 39 (full implementation)

Company-level endpoints: profile, P&L, balance sheet,
cash flow, ratios and tearsheet.
"""

import os
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from src.api.dependencies import get_db, rows_to_dicts

router = APIRouter(prefix="/companies", tags=["Companies"])

TEARSHEET_DIR = "reports/tearsheets"


def _get_company_or_404(conn: sqlite3.Connection, ticker: str) -> sqlite3.Row:
    """
    Fetch a single company row or raise a 404.

    Args:
        conn: Open SQLite connection.
        ticker: Company id (ticker symbol).

    Returns:
        The matching company row.

    Raises:
        HTTPException: 404 if the ticker does not exist.
    """

    row = conn.execute("SELECT * FROM companies WHERE id = ?", (ticker,)).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

    return row


@router.get("")
def list_companies(
    sector: str | None = Query(None, description="Filter by broad_sector"),
    market_cap_category: str | None = Query(
        None, description="Filter by market_cap_category"
    ),
    search: str | None = Query(
        None, description="Case-insensitive company name search"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    """
    List companies with optional sector, market cap category
    and name-search filters, plus pagination.

    Returns:
        JSON payload with total count and the paginated
        company list.
    """

    query = """
        SELECT
            c.id,
            c.company_name,
            c.face_value,
            c.book_value,
            c.roce_percentage,
            c.roe_percentage,
            s.broad_sector,
            s.sub_sector,
            s.market_cap_category
        FROM companies c
        LEFT JOIN sectors s ON s.company_id = c.id
        WHERE 1 = 1
    """

    params = []

    if sector:
        query += " AND s.broad_sector = ?"
        params.append(sector)

    if market_cap_category:
        query += " AND s.market_cap_category = ?"
        params.append(market_cap_category)

    if search:
        query += " AND LOWER(c.company_name) LIKE ?"
        params.append(f"%{search.lower()}%")

    count_query = f"SELECT COUNT(*) FROM ({query})"
    total = conn.execute(count_query, params).fetchone()[0]

    query += " ORDER BY c.company_name LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": rows_to_dicts(rows),
    }


@router.get("/{ticker}")
def get_company(ticker: str, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """
    Get a single company's profile.

    Raises:
        HTTPException: 404 if the ticker is unknown.
    """

    company = _get_company_or_404(conn, ticker)

    sector = conn.execute(
        "SELECT * FROM sectors WHERE company_id = ?", (ticker,)
    ).fetchone()

    pros_cons = conn.execute(
        "SELECT * FROM prosandcons WHERE company_id = ?", (ticker,)
    ).fetchone()

    return {
        "company": dict(company),
        "sector": dict(sector) if sector else None,
        "pros_cons": dict(pros_cons) if pros_cons else None,
    }


@router.get("/{ticker}/pl")
def get_profit_and_loss(
    ticker: str, conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    """
    Get the full profit & loss history for a company.

    Raises:
        HTTPException: 404 if the ticker is unknown.
    """

    _get_company_or_404(conn, ticker)

    rows = conn.execute(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year", (ticker,)
    ).fetchall()

    return {"company_id": ticker, "results": rows_to_dicts(rows)}


@router.get("/{ticker}/bs")
def get_balance_sheet(ticker: str, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """
    Get the full balance sheet history for a company.

    Raises:
        HTTPException: 404 if the ticker is unknown.
    """

    _get_company_or_404(conn, ticker)

    rows = conn.execute(
        "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year", (ticker,)
    ).fetchall()

    return {"company_id": ticker, "results": rows_to_dicts(rows)}


@router.get("/{ticker}/cashflow")
def get_cashflow(ticker: str, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """
    Get the full cash flow history for a company.

    Raises:
        HTTPException: 404 if the ticker is unknown.
    """

    _get_company_or_404(conn, ticker)

    rows = conn.execute(
        "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year", (ticker,)
    ).fetchall()

    return {"company_id": ticker, "results": rows_to_dicts(rows)}


@router.get("/{ticker}/ratios")
def get_ratios(ticker: str, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """
    Get the full financial ratio history for a company.

    Raises:
        HTTPException: 404 if the ticker is unknown.
    """

    _get_company_or_404(conn, ticker)

    rows = conn.execute(
        "SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year", (ticker,)
    ).fetchall()

    return {"company_id": ticker, "results": rows_to_dicts(rows)}


@router.get("/{ticker}/tearsheet")
def get_tearsheet(
    ticker: str, conn: sqlite3.Connection = Depends(get_db)
) -> FileResponse:
    """
    Serve the pre-generated PDF tearsheet for a company.

    Raises:
        HTTPException: 404 if the ticker is unknown or no
            tearsheet has been generated for it yet.
    """

    _get_company_or_404(conn, ticker)

    file_path = os.path.join(TEARSHEET_DIR, f"{ticker}_tearsheet.pdf")

    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=404, detail=f"Tearsheet not yet generated for '{ticker}'"
        )

    return FileResponse(
        path=file_path, media_type="application/pdf", filename=f"{ticker}_tearsheet.pdf"
    )
