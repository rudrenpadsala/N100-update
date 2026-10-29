"""
Dashboard utility bridge for Public Market Data Provider.
Completely replaces credential-based APIs with public market data.
"""

import sys
from pathlib import Path

_DASHBOARD_DIR = Path(__file__).resolve().parents[1]
_SRC_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[3]

for p in [str(_REPO_ROOT), str(_SRC_DIR), str(_DASHBOARD_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from src.api.public_market_data import (
    PublicMarketDataProvider,
    get_public_market_provider,
    get_smartapi_client,
    SmartAPIClient,
)

__all__ = [
    "PublicMarketDataProvider",
    "get_public_market_provider",
    "get_smartapi_client",
    "SmartAPIClient",
]
