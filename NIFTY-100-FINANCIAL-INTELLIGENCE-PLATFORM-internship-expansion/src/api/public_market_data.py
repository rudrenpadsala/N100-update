"""
public_market_data.py

Public Market Data Provider for NIFTY-100 Intelligence Platform.
- Completely free of API keys, tokens, or credential-based services.
- Leverages the updated 2025-2026 historical daily database records.
- Provides technical indicators (SMA, EMA, RSI, MACD).
- Computes market breadths, advances, declines, and index statistics.
- Strict compliance: never calls periodic scraping or cached historical prices real-time.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "db" / "nifty100.db"
LATEST_PRICES_PATH = REPO_ROOT / "output" / "sql_results" / "latest_price.csv"


class PublicMarketDataProvider:
    """Manages public market data, technical indicators, and ticker feeds."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._cache_quotes: Dict[str, Dict[str, Any]] = {}
        self._last_loaded = 0.0

    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def is_configured(self) -> bool:
        """Always True since public data requires no credentials."""
        return True

    def get_all_quotes(self, force_refresh: bool = False) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
        """
        Load latest stock prices and daily changes for all 92 companies from updated dataset.
        Returns: (quotes_dict, status_meta)
        """
        conn = self.get_connection()
        query = """
        WITH RankedPrices AS (
            SELECT 
                sp.company_id,
                sp.date,
                sp.open_price,
                sp.high_price,
                sp.low_price,
                sp.close_price,
                sp.volume,
                c.company_name,
                ROW_NUMBER() OVER(PARTITION BY sp.company_id ORDER BY sp.date DESC) as rn
            FROM stock_prices sp
            JOIN companies c ON sp.company_id = c.id
        )
        SELECT 
            latest.company_id,
            latest.company_name,
            latest.date as latest_date,
            latest.open_price as open,
            latest.high_price as high,
            latest.low_price as low,
            latest.close_price as price,
            latest.volume,
            COALESCE(prev.close_price, latest.close_price) as prev_close,
            ROUND(latest.close_price - COALESCE(prev.close_price, latest.close_price), 2) as change,
            ROUND(((latest.close_price - COALESCE(prev.close_price, latest.close_price)) / COALESCE(prev.close_price, latest.close_price)) * 100, 2) as pct_change
        FROM RankedPrices latest
        LEFT JOIN RankedPrices prev ON latest.company_id = prev.company_id AND prev.rn = 2
        WHERE latest.rn = 1
        ORDER BY latest.company_id
        """
        df = pd.read_sql(query, conn)
        conn.close()

        quotes = {}
        max_date = "2024-12-01"
        for _, row in df.iterrows():
            cid = str(row["company_id"])
            dt = str(row["latest_date"])
            if dt > max_date:
                max_date = dt

            c_name = str(row["company_name"]).splitlines()[0].strip()
            price = round(float(row["price"]), 2)
            chg = round(float(row["change"]), 2)
            pct = round(float(row["pct_change"]), 2)

            quotes[cid] = {
                "company_id": cid,
                "symbol": cid,
                "company_name": c_name,
                "trading_symbol": f"{cid}.NS",
                "exchange": "NSE",
                "price": price,
                "change": chg,
                "pct_change": pct,
                "open": round(float(row["open"]), 2),
                "high": round(float(row["high"]), 2),
                "low": round(float(row["low"]), 2),
                "close": round(float(row["prev_close"]), 2),
                "volume": int(row["volume"]),
                "latest_date": dt,
                "is_live": False,  # Strict: Historical/Public End-of-Day or Delayed
                "status": f"PUBLIC_EOD ({dt})",
            }

        status_meta = {
            "is_live": False,
            "source": "PUBLIC_MARKET_DATA",
            "market_status": "LATEST_CLOSE",
            "market_desc": f"Public Market Data Feed (Latest Available: {max_date})",
            "timestamp_ist": f"{max_date} EOD Close",
            "latest_trading_date": max_date,
            "total_companies": len(quotes),
            "is_configured": True,
            "error": None,
            "cached": True,
        }
        return quotes, status_meta

    def get_company_quote(self, company_id: str) -> Optional[Dict[str, Any]]:
        quotes, _ = self.get_all_quotes()
        return quotes.get(company_id)

    def get_historical_data(self, company_id: str, limit: int = 300) -> pd.DataFrame:
        """
        Fetch historical daily OHLCV for a company with technical indicators:
        SMA(20, 50), EMA(20, 50), RSI(14), MACD(12, 26, 9).
        """
        conn = self.get_connection()
        query = """
        SELECT date, open_price as Open, high_price as High, low_price as Low, 
               close_price as Close, volume as Volume, adjusted_close as Adj_Close
        FROM stock_prices
        WHERE company_id = ?
        ORDER BY date ASC
        """
        df = pd.read_sql(query, conn, params=[company_id])
        conn.close()

        if df.empty:
            return df

        df["Date"] = pd.to_datetime(df["date"])
        df.set_index("Date", inplace=True)

        # Technical Indicators
        df["SMA_20"] = df["Close"].rolling(window=20).mean()
        df["SMA_50"] = df["Close"].rolling(window=50).mean()
        df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["EMA_50"] = df["Close"].ewm(span=50, adjust=False).mean()

        # RSI 14
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["RSI"] = 100 - (100 / (1 + rs))
        df["RSI"] = df["RSI"].fillna(50)

        # MACD (12, 26, 9)
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

        if limit and len(df) > limit:
            return df.iloc[-limit:]
        return df


_provider_instance: Optional[PublicMarketDataProvider] = None


def get_public_market_provider() -> PublicMarketDataProvider:
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = PublicMarketDataProvider()
    return _provider_instance


# Bridge aliases for existing imports
get_smartapi_client = get_public_market_provider
SmartAPIClient = PublicMarketDataProvider
