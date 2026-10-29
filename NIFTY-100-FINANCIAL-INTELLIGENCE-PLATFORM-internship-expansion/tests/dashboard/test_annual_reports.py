"""
Unit tests for the Annual Reports and Financial Statements module (FY25 & FY26).
"""

from pathlib import Path
import pytest
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "src" / "dashboard"))

from utils.db import (
    get_companies,
    get_reports,
    get_pl,
    get_bs,
    get_cf,
    get_ratios,
    get_annual_reports_metadata,
)


def test_annual_reports_metadata_coverage():
    """All 92 NIFTY 100 constituent entities must have metadata records."""
    companies = get_companies()
    meta = get_annual_reports_metadata()
    assert not meta.empty
    
    unique_meta_cids = meta["company_id"].unique()
    assert len(unique_meta_cids) >= 91
    
    for cid in companies["id"].dropna().unique():
        assert cid in unique_meta_cids, f"Company {cid} missing from annual_reports_metadata"


def test_fy25_and_fy26_report_statuses():
    """FY 2024-25 has 92/92 available; FY 2025-26 has 91 available and SIEMENS accurately pending."""
    meta = get_annual_reports_metadata()
    fy25 = meta[meta["financial_year"] == 2025]
    fy26 = meta[meta["financial_year"] == 2026]
    
    assert len(fy25) >= 92
    assert len(fy26) >= 92
    
    # Check that all FY25 are AVAILABLE
    assert (fy25["report_status"] == "AVAILABLE").all()
    
    # Check that SIEMENS in FY26 is NOT YET PUBLISHED
    siemens_fy26 = fy26[fy26["company_id"] == "SIEMENS"]
    assert not siemens_fy26.empty
    assert siemens_fy26.iloc[0]["report_status"] == "NOT YET PUBLISHED"
    
    # All other FY26 companies should be AVAILABLE
    other_fy26 = fy26[fy26["company_id"] != "SIEMENS"]
    assert (other_fy26["report_status"] == "AVAILABLE").all()


def test_annual_report_pdfs_exist_on_disk():
    """Every AVAILABLE report must correspond to an actual verified PDF in data/annual_reports."""
    meta = get_annual_reports_metadata()
    available_reports = meta[meta["report_status"] == "AVAILABLE"]
    
    assert len(available_reports) >= 183
    
    missing_pdfs = []
    for _, row in available_reports.iterrows():
        pdf_path = Path(row["local_pdf_path"])
        if not pdf_path.exists() or pdf_path.stat().st_size == 0:
            missing_pdfs.append((row["company_id"], row["financial_year"], str(pdf_path)))
            
    assert len(missing_pdfs) == 0, f"Missing or empty PDFs: {missing_pdfs[:5]}"


def test_financial_statement_updates_contain_2025_and_2026():
    """P&L, Balance Sheet, Cash Flow, and Ratios must contain 2025 and 2026 for sample bellwether companies."""
    for ticker in ["RELIANCE", "TCS", "INFY", "HDFCBANK"]:
        pl = get_pl(ticker)
        bs = get_bs(ticker)
        cf = get_cf(ticker)
        ratios = get_ratios(ticker)
        
        pl_years = [str(y) for y in pl["year"].tolist()]
        assert any("2025" in y for y in pl_years), f"2025 missing in P&L for {ticker}"
        assert any("2026" in y for y in pl_years), f"2026 missing in P&L for {ticker}"
        
        bs_years = [str(y) for y in bs["year"].tolist()]
        assert any("2025" in y for y in bs_years), f"2025 missing in BS for {ticker}"
        assert any("2026" in y for y in bs_years), f"2026 missing in BS for {ticker}"
        
        cf_years = [str(y) for y in cf["year"].tolist()]
        assert any("2025" in y for y in cf_years), f"2025 missing in CF for {ticker}"
        assert any("2026" in y for y in cf_years), f"2026 missing in CF for {ticker}"
        
        ratio_years = [str(y) for y in ratios["year"].tolist()]
        assert any("2025" in y for y in ratio_years), f"2025 missing in ratios for {ticker}"
        assert any("2026" in y for y in ratio_years), f"2026 missing in ratios for {ticker}"
