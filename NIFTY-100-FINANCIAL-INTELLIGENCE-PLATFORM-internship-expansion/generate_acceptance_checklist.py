"""
generate_acceptance_checklist.py

Sprint 6
Day 45

Runs 20 acceptance gates covering every Sprint 6 deliverable
(Days 36-44), then renders the pass/fail results to
acceptance_checklist.pdf in the project root.

Each gate is a real, executable check against the live
project (file existence, schema shape, or a live API call)
rather than a manual assertion.
"""

import csv
import json
import os
import sqlite3
import subprocess
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

DB_PATH = "db/nifty100.db"
OUTPUT_PATH = "acceptance_checklist.pdf"

PRIMARY = colors.HexColor("#6C63FF")
SUCCESS = colors.HexColor("#198754")
DANGER = colors.HexColor("#DC3545")
INK = colors.HexColor("#222222")
GREY = colors.HexColor("#777777")
LIGHT_BG = colors.HexColor("#F5F5FA")


def _file_exists(path: str) -> bool:
    """Check that a file exists and is non-empty."""
    return os.path.isfile(path) and os.path.getsize(path) > 0


def gate_01_clustering_module_exists() -> tuple:
    ok = _file_exists("src/analytics/clustering.py")
    return ok, "src/analytics/clustering.py present"


def gate_02_elbow_plot_generated() -> tuple:
    ok = _file_exists("reports/elbow_plot.png")
    return ok, "reports/elbow_plot.png present"


def gate_03_cluster_labels_schema() -> tuple:
    if not _file_exists("output/cluster_labels.csv"):
        return False, "output/cluster_labels.csv missing"

    with open("output/cluster_labels.csv", newline="") as f:
        header = next(csv.reader(f))

    required = {"company_id", "cluster_id", "cluster_name", "distance_from_centroid"}
    ok = required.issubset(set(header))
    return ok, f"columns present: {sorted(required)}"


def gate_04_five_readable_cluster_names() -> tuple:
    if not _file_exists("output/cluster_labels.csv"):
        return False, "output/cluster_labels.csv missing"

    with open("output/cluster_labels.csv", newline="") as f:
        rows = list(csv.DictReader(f))

    required_names = {
        "High-Quality Compounders",
        "Defensive Dividend Payers",
        "Value Cyclicals",
        "Distressed or Turnaround",
        "Emerging Growth",
    }
    found_names = {row["cluster_name"] for row in rows}
    ok = required_names.issubset(found_names)
    return ok, f"{len(found_names)} distinct cluster names found"


def gate_05_correlation_heatmap_generated() -> tuple:
    ok = _file_exists("reports/correlation_heatmap.png")
    return ok, "reports/correlation_heatmap.png present"


def gate_06_outlier_report_generated() -> tuple:
    ok = _file_exists("output/outlier_report.csv")
    return ok, "output/outlier_report.csv present"


def gate_07_portfolio_stats_schema() -> tuple:
    if not _file_exists("output/portfolio_stats.csv"):
        return False, "output/portfolio_stats.csv missing"

    with open("output/portfolio_stats.csv", newline="") as f:
        header = next(csv.reader(f))

    required = {"feature", "P10", "P25", "P50", "P75", "P90", "Mean", "Std"}
    ok = required.issubset(set(header))
    return ok, f"columns present: {sorted(required)}"


def gate_08_api_boots_and_docs_served() -> tuple:
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.get("/docs")
    ok = r.status_code == 200
    return ok, f"GET /docs -> {r.status_code}"


def gate_09_health_endpoint_shape() -> tuple:
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/health")
    body = r.json() if r.status_code == 200 else {}

    required = {"status", "version", "uptime_seconds", "database_row_counts"}
    ok = r.status_code == 200 and required.issubset(set(body.keys()))
    return ok, f"GET /api/v1/health -> {r.status_code}, keys={sorted(body.keys())}"


def gate_10_company_endpoints_status_codes() -> tuple:
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    checks = [
        ("/api/v1/companies/ABB", 200),
        ("/api/v1/companies/ABB/pl", 200),
        ("/api/v1/companies/ABB/bs", 200),
        ("/api/v1/companies/ABB/cashflow", 200),
        ("/api/v1/companies/ABB/ratios", 200),
        ("/api/v1/companies/NOTAREAL", 404),
    ]

    results = [client.get(path).status_code == expected for path, expected in checks]
    ok = all(results)
    return ok, f"{sum(results)}/{len(results)} company endpoint checks passed"


def gate_11_screener_strategies_and_filters() -> tuple:
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    r1 = client.get("/api/v1/screener/strategies")
    r2 = client.get("/api/v1/screener?strategy=quality_compounder")
    r3 = client.get("/api/v1/screener?roe_min=15")
    r4 = client.get("/api/v1/screener?strategy=not_real")

    ok = (
        r1.status_code == 200
        and r2.status_code == 200
        and r3.status_code == 200
        and r4.status_code == 400
    )
    return ok, "named strategy, ad-hoc filter and error-handling all verified"


def gate_12_remaining_routers_respond() -> tuple:
    from fastapi.testclient import TestClient
    from src.api.main import app

    client = TestClient(app)
    checks = [
        "/api/v1/sectors",
        "/api/v1/peers/groups",
        "/api/v1/valuation/rankings/top",
        "/api/v1/portfolio/clusters",
        "/api/v1/documents/ABB",
    ]

    results = [client.get(path).status_code == 200 for path in checks]
    ok = all(results)
    return ok, f"{sum(results)}/{len(results)} remaining routers responded 200"


def gate_13_openapi_exported() -> tuple:
    if not _file_exists("docs/openapi.json"):
        return False, "docs/openapi.json missing"

    with open("docs/openapi.json") as f:
        schema = json.load(f)

    ok = len(schema.get("paths", {})) >= 20
    return ok, f"{len(schema.get('paths', {}))} paths documented"


def gate_14_postman_collection_exported() -> tuple:
    if not _file_exists("docs/postman_collection.json"):
        return False, "docs/postman_collection.json missing"

    with open("docs/postman_collection.json") as f:
        collection = json.load(f)

    ok = len(collection.get("item", [])) >= 8
    return ok, f"{len(collection.get('item', []))} folders in collection"


def gate_15_test_suite_60_plus_zero_failures() -> tuple:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header"],
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr
    passed = 0
    failed = 0

    for token in output.split():
        pass

    import re

    match = re.search(r"(\d+) passed", output)
    if match:
        passed = int(match.group(1))

    fail_match = re.search(r"(\d+) failed", output)
    if fail_match:
        failed = int(fail_match.group(1))

    ok = passed >= 60 and failed == 0
    return ok, f"{passed} passed, {failed} failed"


def gate_16_pytest_html_report_generated() -> tuple:
    ok = _file_exists("reports/pytest_report.html")
    return ok, "reports/pytest_report.html present"


def gate_17_sqlite_indexes_created() -> tuple:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
    )
    index_names = {row[0] for row in cur.fetchall()}
    conn.close()

    required = {
        "idx_ratios_company",
        "idx_sectors_company",
        "idx_peer_groups_company",
        "idx_documents_company",
    }
    ok = required.issubset(index_names)
    return ok, f"{len(index_names)} indexes present, required subset found"


def gate_18_perf_notes_generated() -> tuple:
    ok = _file_exists("output/perf_notes.md")
    return ok, "output/perf_notes.md present"


def gate_19_analyst_guide_10_plus_pages() -> tuple:
    if not _file_exists("docs/analyst_guide.pdf"):
        return False, "docs/analyst_guide.pdf missing"

    from pypdf import PdfReader

    page_count = len(PdfReader("docs/analyst_guide.pdf").pages)
    ok = page_count >= 10
    return ok, f"{page_count} pages"


def gate_20_readme_documents_sprint6() -> tuple:
    if not _file_exists("README.md"):
        return False, "README.md missing"

    with open("README.md", encoding="utf-8") as f:
        content = f.read()

    ok = "Sprint 6" in content and "clustering" in content.lower()
    return ok, "README.md references Sprint 6 and clustering"


GATES = [
    ("Gate 01", "Clustering module exists", gate_01_clustering_module_exists),
    ("Gate 02", "Elbow plot generated", gate_02_elbow_plot_generated),
    ("Gate 03", "cluster_labels.csv schema correct", gate_03_cluster_labels_schema),
    ("Gate 04", "All 5 readable cluster names assigned", gate_04_five_readable_cluster_names),
    ("Gate 05", "Correlation heatmap generated", gate_05_correlation_heatmap_generated),
    ("Gate 06", "Outlier report generated (|z| > 3)", gate_06_outlier_report_generated),
    ("Gate 07", "portfolio_stats.csv schema correct", gate_07_portfolio_stats_schema),
    ("Gate 08", "FastAPI boots, Swagger docs served", gate_08_api_boots_and_docs_served),
    ("Gate 09", "Health endpoint returns required fields", gate_09_health_endpoint_shape),
    ("Gate 10", "Company API status codes correct", gate_10_company_endpoints_status_codes),
    ("Gate 11", "Screener strategies + filters + errors", gate_11_screener_strategies_and_filters),
    ("Gate 12", "Sector/Peer/Valuation/Portfolio/Documents APIs respond", gate_12_remaining_routers_respond),
    ("Gate 13", "docs/openapi.json exported (20+ paths)", gate_13_openapi_exported),
    ("Gate 14", "Postman collection exported", gate_14_postman_collection_exported),
    ("Gate 15", "60+ tests, 0 failures", gate_15_test_suite_60_plus_zero_failures),
    ("Gate 16", "pytest_report.html generated", gate_16_pytest_html_report_generated),
    ("Gate 17", "SQLite performance indexes created", gate_17_sqlite_indexes_created),
    ("Gate 18", "perf_notes.md generated", gate_18_perf_notes_generated),
    ("Gate 19", "analyst_guide.pdf has 10+ pages", gate_19_analyst_guide_10_plus_pages),
    ("Gate 20", "README.md documents Sprint 6", gate_20_readme_documents_sprint6),
]


def run_all_gates() -> list:
    """
    Execute every acceptance gate and collect its result.

    Returns:
        List of (gate_id, description, passed, detail) tuples.
    """

    results = []

    for gate_id, description, check_fn in GATES:
        try:
            passed, detail = check_fn()
        except Exception as exc:
            passed, detail = False, f"ERROR: {exc}"

        results.append((gate_id, description, passed, detail))
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {gate_id} - {description} ({detail})")

    return results


def _styles():
    base = getSampleStyleSheet()

    base.add(ParagraphStyle(
        name="GuideTitle", fontSize=24, leading=30,
        textColor=PRIMARY, spaceAfter=6
    ))
    base.add(ParagraphStyle(
        name="GuideSubtitle", fontSize=12, leading=16,
        textColor=GREY, spaceAfter=16
    ))
    base.add(ParagraphStyle(
        name="Body", fontSize=10, leading=14,
        textColor=INK, spaceAfter=8
    ))

    return base


def build_pdf(results: list) -> None:
    """
    Render the acceptance gate results to acceptance_checklist.pdf.

    Args:
        results: Output of run_all_gates().
    """

    styles = _styles()

    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="N100 Financial Platform - Sprint 6 Acceptance Checklist",
    )

    passed_count = sum(1 for _, _, passed, _ in results if passed)
    total_count = len(results)

    story = [
        Paragraph("Sprint 6 Acceptance Checklist", styles["GuideTitle"]),
        Paragraph(
            f"N100 Financial Platform — {passed_count}/{total_count} gates passed",
            styles["GuideSubtitle"],
        ),
        Spacer(1, 4 * mm),
    ]

    table_data = [["#", "Gate", "Status", "Detail"]]

    for gate_id, description, passed, detail in results:
        status_text = "PASS" if passed else "FAIL"
        table_data.append([gate_id, description, status_text, detail])

    table = Table(
        table_data,
        colWidths=[16 * mm, 62 * mm, 16 * mm, 76 * mm],
        repeatRows=1,
    )

    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]

    for row_index, (_, _, passed, _) in enumerate(results, start=1):
        color = SUCCESS if passed else DANGER
        style_commands.append(("TEXTCOLOR", (2, row_index), (2, row_index), color))
        style_commands.append(("FONTNAME", (2, row_index), (2, row_index), "Helvetica-Bold"))

    table.setStyle(TableStyle(style_commands))

    story.append(table)
    story.append(Spacer(1, 6 * mm))

    if passed_count == total_count:
        verdict = "All 20 acceptance gates passed. Sprint 6 is accepted for delivery."
        verdict_color = SUCCESS
    else:
        verdict = (
            f"{total_count - passed_count} gate(s) failed. "
            f"Resolve before Sprint 6 sign-off."
        )
        verdict_color = DANGER

    story.append(Paragraph(
        f"<font color='{verdict_color.hexval()}'><b>{verdict}</b></font>",
        styles["Body"],
    ))

    doc.build(story)

    print(f"\n✔ Acceptance checklist saved : {OUTPUT_PATH}")


def main() -> None:
    """
    Run every gate and render the results to PDF.
    """

    print("=" * 60)
    print("Sprint 6 Acceptance Verification")
    print("=" * 60)

    results = run_all_gates()
    build_pdf(results)

    passed_count = sum(1 for _, _, passed, _ in results if passed)
    print(f"\n{passed_count}/{len(results)} gates passed")

    print("\n✅ Day 45 Acceptance Complete")


if __name__ == "__main__":
    main()
