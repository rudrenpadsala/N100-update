"""
screener.py

Sprint 6
Day 40

Screener API - filters companies on their latest-year
fundamentals, either via an ad-hoc filter set or one of the
named strategies defined in src/config/screener_config.yaml.
"""

import sqlite3

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_db, rows_to_dicts

router = APIRouter(prefix="/screener", tags=["Screener"])

SCREENER_CONFIG_PATH = "src/config/screener_config.yaml"

# Latest-year fundamentals per company, joined once and
# reused for every filter combination.
_LATEST_SNAPSHOT_QUERY = """
    WITH latest_ratio AS (
        SELECT fr.*
        FROM financial_ratios fr
        INNER JOIN (
            SELECT company_id, MAX(id) AS max_id
            FROM financial_ratios
            GROUP BY company_id
        ) latest ON latest.max_id = fr.id
    ),
    latest_market AS (
        SELECT mc.*
        FROM market_cap mc
        INNER JOIN (
            SELECT company_id, MAX(id) AS max_id
            FROM market_cap
            GROUP BY company_id
        ) latest ON latest.max_id = mc.id
    ),
    latest_pl AS (
        SELECT pl.*
        FROM profitandloss pl
        INNER JOIN (
            SELECT company_id, MAX(id) AS max_id
            FROM profitandloss
            GROUP BY company_id
        ) latest ON latest.max_id = pl.id
    )
    SELECT
        c.id AS company_id,
        c.company_name,
        s.broad_sector,
        lr.return_on_equity_pct,
        lr.debt_to_equity,
        lr.free_cash_flow_cr,
        lr.revenue_cagr_5yr,
        lr.pat_cagr_5yr,
        lr.dividend_payout_ratio_pct,
        lm.pe_ratio,
        lm.pb_ratio,
        lm.dividend_yield_pct,
        lp.sales
    FROM companies c
    LEFT JOIN sectors s ON s.company_id = c.id
    LEFT JOIN latest_ratio lr ON lr.company_id = c.id
    LEFT JOIN latest_market lm ON lm.company_id = c.id
    LEFT JOIN latest_pl lp ON lp.company_id = c.id
"""


def _load_strategy_presets() -> dict:
    """
    Load the named screener strategies from
    src/config/screener_config.yaml.

    Returns:
        Dict of strategy name -> filter dict.
    """

    with open(SCREENER_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


@router.get("/strategies")
def list_strategies() -> dict:
    """
    List every named screener strategy and its filter
    thresholds.
    """

    return {"strategies": _load_strategy_presets()}


@router.get("")
def run_screener(
    strategy: str | None = Query(
        None, description="Named strategy from screener_config.yaml"
    ),
    roe_min: float | None = Query(None),
    de_max: float | None = Query(None),
    pe_max: float | None = Query(None),
    pb_max: float | None = Query(None),
    dividend_yield_min: float | None = Query(None),
    revenue_cagr_min: float | None = Query(None),
    pat_cagr_min: float | None = Query(None),
    fcf_min: float | None = Query(None),
    sales_min: float | None = Query(None),
    dividend_payout_max: float | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    """
    Screen companies on their latest-year fundamentals.

    A `strategy` name applies the matching preset from
    screener_config.yaml; any individually supplied filter
    overrides the corresponding preset value.

    Raises:
        HTTPException: 400 if an unknown strategy is given.
    """

    filters = {
        "roe_min": roe_min,
        "de_max": de_max,
        "pe_max": pe_max,
        "pb_max": pb_max,
        "dividend_yield_min": dividend_yield_min,
        "revenue_cagr_min": revenue_cagr_min,
        "pat_cagr_min": pat_cagr_min,
        "fcf_min": fcf_min,
        "sales_min": sales_min,
        "dividend_payout_max": dividend_payout_max,
    }

    if strategy:
        presets = _load_strategy_presets()

        if strategy not in presets:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown strategy '{strategy}'. "
                f"Available: {list(presets.keys())}",
            )

        for key, value in presets[strategy].items():
            if filters.get(key) is None:
                filters[key] = value

    conditions = []
    params: list = []

    condition_map = {
        "roe_min": ("return_on_equity_pct", ">="),
        "de_max": ("debt_to_equity", "<="),
        "pe_max": ("pe_ratio", "<="),
        "pb_max": ("pb_ratio", "<="),
        "dividend_yield_min": ("dividend_yield_pct", ">="),
        "revenue_cagr_min": ("revenue_cagr_5yr", ">="),
        "pat_cagr_min": ("pat_cagr_5yr", ">="),
        "fcf_min": ("free_cash_flow_cr", ">="),
        "sales_min": ("sales", ">="),
        "dividend_payout_max": ("dividend_payout_ratio_pct", "<="),
    }

    for key, value in filters.items():
        if value is None:
            continue
        column, operator = condition_map[key]
        conditions.append(f"{column} {operator} ?")
        params.append(value)

    query = _LATEST_SNAPSHOT_QUERY

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    count_query = f"SELECT COUNT(*) FROM ({query})"
    total = conn.execute(count_query, params).fetchone()[0]

    query += " ORDER BY company_name LIMIT ? OFFSET ?"
    params_paginated = params + [limit, offset]

    rows = conn.execute(query, params_paginated).fetchall()

    return {
        "strategy": strategy,
        "filters_applied": {k: v for k, v in filters.items() if v is not None},
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": rows_to_dicts(rows),
    }
