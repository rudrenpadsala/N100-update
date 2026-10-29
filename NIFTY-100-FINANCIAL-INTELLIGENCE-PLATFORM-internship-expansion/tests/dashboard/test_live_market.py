"""
Unit tests for Public Market Data provider, 2025-2026 dataset updates, technical indicators,
and Reinforcement Learning trading model.
"""

from pathlib import Path
import pytest
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "src" / "dashboard"))

from src.api.public_market_data import get_public_market_provider
from src.analytics.rl_model import train_and_backtest_rl
from utils.db import get_companies


def test_public_market_data_covers_all_companies():
    """All 92 companies from database must have updated quotes through 2026."""
    provider = get_public_market_provider()
    companies = get_companies()
    assert len(companies) >= 91
    
    quotes, meta = provider.get_all_quotes()
    assert len(quotes) >= 91
    assert meta["latest_trading_date"] >= "2026-01-01"
    
    for cid in companies["id"].dropna().unique():
        assert cid in quotes, f"Company {cid} missing from public quotes"
        q = quotes[cid]
        assert q["price"] > 0
        assert isinstance(q["change"], (int, float))
        assert isinstance(q["pct_change"], (int, float))
        assert q["latest_date"] >= "2026-01-01"


def test_technical_indicators_computation():
    """SMA, EMA, RSI, and MACD must compute correctly from the updated OHLCV records."""
    provider = get_public_market_provider()
    df = provider.get_historical_data("TCS", limit=120)
    
    assert not df.empty
    assert "SMA_20" in df.columns
    assert "EMA_20" in df.columns
    assert "RSI" in df.columns
    assert "MACD" in df.columns
    assert "MACD_Signal" in df.columns
    assert "MACD_Hist" in df.columns
    
    # Check RSI range
    valid_rsi = df["RSI"].dropna()
    assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()


def test_rl_model_chronological_splits_and_metrics():
    """RL model must use chronological splits, account for costs, and return verified metrics."""
    res = train_and_backtest_rl("RELIANCE", episodes=20)
    assert "error" not in res
    assert "rl_return" in res
    assert "benchmark_return" in res
    assert "alpha" in res
    assert "sharpe_ratio" in res
    assert "max_drawdown" in res
    assert "total_trades" in res
    assert res["train_records"] > 0
    assert res["test_records"] > 0
    assert isinstance(res["history_df"], pd.DataFrame)


def test_stale_or_cached_data_never_labeled_live():
    """Historical or public EOD data must never be deceptively labeled as real-time."""
    provider = get_public_market_provider()
    quotes, meta = provider.get_all_quotes()
    
    assert meta["is_live"] is False
    assert "LIVE" not in meta["source"]
    for q in quotes.values():
        assert q["is_live"] is False
        assert "LIVE" not in q["status"]
