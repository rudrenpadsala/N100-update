"""Module 4 - automated PDF research reports."""

import re

import pytest

from src.analytics.platform_data import build_bundle
from src.reports.research_report import (
    build_report_context, generate_all, generate_report_bytes, generate_research_report,
)


@pytest.fixture
def bundle(synthetic_tables):
    return build_bundle(tables=synthetic_tables)


def pages(pdf: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page\b", pdf))


def text_of(pdf_bytes_uncompressed: bytes) -> str:
    """Text drawn by ReportLab in an uncompressed PDF (string operands of Tj/TJ)."""
    chunks = re.findall(rb"\((.*?)(?<!\\)\)\s*Tj", pdf_bytes_uncompressed, flags=re.S)
    return " ".join(c.decode("latin-1") for c in chunks)


# --------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------

def test_report_is_a_valid_multi_page_pdf(bundle):
    pdf = generate_report_bytes("A", bundle)
    assert pdf.startswith(b"%PDF") and pdf.rstrip().endswith(b"%%EOF")
    assert pages(pdf) >= 3


def test_report_contains_every_required_section(bundle):
    text = text_of(generate_report_bytes("A", bundle, compress=False))
    for heading in ("1. Snapshot", "2. Financial health score", "How the score is built",
                    "3. Sales and profit trend", "4. Peer benchmarking",
                    "5. Data-quality warnings", "6. Methodology",
                    "Indicator formulas", "Scoring thresholds and weights"):
        assert heading in text, heading


def test_report_contains_charts(bundle):
    pdf = generate_report_bytes("A", bundle, compress=False)
    assert len(re.findall(rb"/Subtype\s*/Image", pdf)) >= 3     # trend, points, peer percentiles


def test_report_states_the_disclaimer(bundle):
    assert "Not investment" in text_of(generate_report_bytes("A", bundle, compress=False))


# --------------------------------------------------------------------------
# Consistency with the analytics modules
# --------------------------------------------------------------------------

def test_score_in_pdf_equals_score_from_the_module(bundle):
    for cid in ("A", "B", "C", "F1"):
        text = text_of(generate_report_bytes(cid, bundle, compress=False))
        score = bundle.health[cid].score
        assert f"{score:.1f}" in text, cid
        assert f"Grade {bundle.health[cid].grade}" in text


def test_every_component_row_appears_in_the_pdf(bundle):
    text = text_of(generate_report_bytes("B", bundle, compress=False))
    for label in bundle.health["B"].components["label"]:
        assert label.split(" (")[0] in text, label


def test_context_matches_the_bundle(bundle):
    ctx = build_report_context("A", bundle)
    assert ctx["health"] is bundle.health["A"]
    assert ctx["peer_set"].group_name == "Tech"
    assert ctx["league_rank"][1] == int(bundle.league["score"].notna().sum())
    assert len(ctx["trend"]) == 6 and ctx["trend"]["year_key"].tolist()[-1] == 2024


def test_data_quality_warnings_are_carried_into_the_pdf(synthetic_tables):
    tables = {k: v.copy() for k, v in synthetic_tables.items()}
    mask = (tables["financial_ratios"].company_id == "B") & (tables["financial_ratios"].year == "Mar 2024")
    tables["financial_ratios"].loc[mask, "return_on_equity_pct"] = 15000.0
    bundle = build_bundle(tables=tables)

    text = text_of(generate_report_bytes("B", bundle, compress=False))
    assert "ROE of 15,000.00% is implausible" in text
    assert "Data reliability" in text and "Low" in text

    clean = text_of(generate_report_bytes("A", bundle, compress=False))
    assert "No data-quality errors or warnings" in clean


def test_methodology_lists_every_threshold(bundle):
    from src.analytics.health_score import METRICS
    text = text_of(generate_report_bytes("A", bundle, compress=False))
    for m in METRICS:
        assert m.label.split(" (")[0] in text        # table cells may wrap after the bracket


# --------------------------------------------------------------------------
# Edge cases
# --------------------------------------------------------------------------

def test_bank_report_marks_leverage_not_applicable(bundle):
    text = text_of(generate_report_bytes("F1", bundle, compress=False))
    assert "not applicable" in text.lower() and "Bank" in text


def test_company_without_peers_still_gets_a_report(bundle):
    text = text_of(generate_report_bytes("Z", bundle, compress=False))
    assert "No benchmark available" in text


def test_company_with_withheld_score_still_gets_a_report(synthetic_tables):
    tables = {k: v.copy() for k, v in synthetic_tables.items()}
    tables["balancesheet"] = tables["balancesheet"].query("company_id != 'D'")
    tables["cashflow"] = tables["cashflow"].query("company_id != 'D'")
    bundle = build_bundle(tables=tables)
    assert bundle.health["D"].score is None or bundle.health["D"].data_coverage_pct < 100
    pdf = generate_report_bytes("D", bundle)
    assert pdf.startswith(b"%PDF")


def test_unknown_company_raises(bundle):
    with pytest.raises(ValueError, match="Unknown company"):
        generate_report_bytes("NOPE", bundle)


def test_ticker_with_special_characters_is_written_safely(tmp_path, real_bundle):
    path = generate_research_report("M&M", tmp_path, real_bundle)
    assert path.name == "MandM_research_report.pdf" and path.read_bytes().startswith(b"%PDF")


def test_generate_all_writes_one_file_per_company(tmp_path, bundle):
    paths = generate_all(tmp_path, bundle)
    assert len(paths) == len(bundle.company_ids()) == len(list(tmp_path.glob("*.pdf")))


def test_report_generation_is_repeatable(bundle):
    first = text_of(generate_report_bytes("A", bundle, compress=False))
    second = text_of(generate_report_bytes("A", bundle, compress=False))
    def body(t):
        # drop volatile PDF metadata (creation date, document id) and the generated-on date
        t = re.sub(r"/CreationDate \(.*?\)|/ModDate \(.*?\)|/ID \[.*?\]", "", t, flags=re.S)
        return re.sub(r"Generated: \S+", "", t)

    assert body(first) == body(second)


# --------------------------------------------------------------------------
# Real database
# --------------------------------------------------------------------------

@pytest.mark.parametrize("cid", ["TCS", "HDFCBANK", "BEL", "JIOFIN", "RELIANCE"])
def test_real_company_reports_build(real_bundle, cid):
    pdf = generate_report_bytes(cid, real_bundle)
    assert pdf.startswith(b"%PDF") and 3 <= pages(pdf) <= 6


def test_real_bel_report_shows_its_bad_roe_as_a_warning(real_bundle):
    text = text_of(generate_report_bytes("BEL", real_bundle, compress=False))
    assert "plausible range" in text and "implausible" in text
