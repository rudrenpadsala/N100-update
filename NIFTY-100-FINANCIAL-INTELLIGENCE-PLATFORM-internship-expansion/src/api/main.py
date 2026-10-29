"""
main.py

Sprint 6
Day 38

FastAPI application entrypoint. Wires up CORS, request
logging middleware, and every /api/v1 router.
"""

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    companies,
    documents,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("n100_api")

API_PREFIX = "/api/v1"

app = FastAPI(
    title="N100 Financial Platform API",
    description="REST API for the N100 Financial Platform - "
    "company fundamentals, screener, sector, peer, "
    "valuation and portfolio analytics.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log every incoming request's method, path, status code
    and duration.

    Args:
        request: The incoming HTTP request.
        call_next: The next handler in the middleware chain.

    Returns:
        The HTTP response, unmodified.
    """

    start_time = time.time()

    response = await call_next(request)

    duration_ms = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} duration_ms={duration_ms}"
    )

    return response


app.include_router(health.router, prefix=API_PREFIX)
app.include_router(companies.router, prefix=API_PREFIX)
app.include_router(screener.router, prefix=API_PREFIX)
app.include_router(sectors.router, prefix=API_PREFIX)
app.include_router(peers.router, prefix=API_PREFIX)
app.include_router(valuation.router, prefix=API_PREFIX)
app.include_router(portfolio.router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)


@app.get("/")
def root() -> dict:
    """
    Root endpoint - points callers to the interactive docs.
    """

    return {
        "service": "N100 Financial Platform API",
        "docs": "/docs",
        "health": f"{API_PREFIX}/health",
    }
