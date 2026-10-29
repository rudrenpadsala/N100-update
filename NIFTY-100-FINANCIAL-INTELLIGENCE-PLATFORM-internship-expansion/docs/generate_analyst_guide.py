"""
generate_analyst_guide.py

Sprint 6
Day 44

Generates docs/analyst_guide.pdf - a 10+ page reference guide
covering the platform's data pipeline, analytics, screener
strategies, clustering methodology and API layer, for use by
analysts consuming the N100 Financial Platform.
"""

import sqlite3

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PRIMARY = colors.HexColor("#6C63FF")
INK = colors.HexColor("#222222")
GREY = colors.HexColor("#777777")
LIGHT_BG = colors.HexColor("#F5F5FA")

DB_PATH = "db/nifty100.db"
OUTPUT_PATH = "docs/analyst_guide.pdf"


def _styles():
    """
    Build the paragraph style set used across the guide.

    Returns:
        A ReportLab stylesheet with custom guide styles added.
    """

    base = getSampleStyleSheet()

    base.add(
        ParagraphStyle(
            name="GuideTitle", fontSize=26, leading=32, textColor=PRIMARY, spaceAfter=6
        )
    )

    base.add(
        ParagraphStyle(
            name="GuideSubtitle", fontSize=13, leading=18, textColor=GREY, spaceAfter=20
        )
    )

    base.add(
        ParagraphStyle(
            name="H1",
            fontSize=18,
            leading=22,
            textColor=PRIMARY,
            spaceBefore=14,
            spaceAfter=10,
        )
    )

    base.add(
        ParagraphStyle(
            name="H2",
            fontSize=13,
            leading=17,
            textColor=INK,
            spaceBefore=10,
            spaceAfter=6,
        )
    )

    base.add(
        ParagraphStyle(
            name="Body",
            fontSize=10,
            leading=15,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=8,
        )
    )

    base.add(
        ParagraphStyle(
            name="GuideBullet",
            fontSize=10,
            leading=14,
            textColor=INK,
            leftIndent=14,
            spaceAfter=4,
        )
    )

    return base


def _get_db_stats() -> dict:
    """
    Pull live row counts to keep the guide accurate as the
    dataset grows.

    Returns:
        Dict of table name -> row count.
    """

    conn = sqlite3.connect(DB_PATH)

    tables = [
        "companies",
        "sectors",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "financial_ratios",
        "market_cap",
        "peer_groups",
        "documents",
    ]

    stats = {}
    for table in tables:
        stats[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    conn.close()
    return stats


def _table(data, col_widths=None):
    """
    Build a consistently styled ReportLab table.

    Args:
        data: Row-major list of lists, header row first.
        col_widths: Optional explicit column widths.

    Returns:
        A styled ReportLab Table flowable.
    """

    t = Table(data, colWidths=col_widths, repeatRows=1)

    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    return t


def build_story(styles) -> list:
    """
    Assemble every flowable that makes up the guide.

    Args:
        styles: The stylesheet returned by _styles().

    Returns:
        List of ReportLab flowables.
    """

    stats = _get_db_stats()
    story = []

    # ---------------- Cover Page ----------------
    story.append(Spacer(1, 60 * mm))
    story.append(Paragraph("N100 Financial Platform", styles["GuideTitle"]))
    story.append(Paragraph("Analyst Guide — Sprint 6 Release", styles["GuideSubtitle"]))
    story.append(
        Paragraph(
            f"Covers ETL, the ratio &amp; screener engines, KMeans clustering, "
            f"the REST API, and how to interpret every generated report. "
            f"Database snapshot: {stats['companies']} companies, "
            f"{stats['financial_ratios']} financial-ratio records.",
            styles["Body"],
        )
    )
    story.append(PageBreak())

    # ---------------- 1. Platform Overview ----------------
    story.append(Paragraph("1. Platform Overview", styles["H1"]))
    story.append(
        Paragraph(
            "The N100 Financial Platform ingests annual-report-derived "
            "fundamentals for the Nifty 100 universe, computes a standard "
            "set of financial ratios, and layers screening, peer, cash-flow "
            "intelligence, clustering, and reporting modules on top of a "
            "single SQLite database.",
            styles["Body"],
        )
    )
    story.append(Paragraph("Current database volume:", styles["H2"]))

    overview_rows = [["Table", "Row Count"]] + [
        [name, str(count)] for name, count in stats.items()
    ]
    story.append(_table(overview_rows, col_widths=[100 * mm, 40 * mm]))
    story.append(PageBreak())

    # ---------------- 2. ETL & Data Quality ----------------
    story.append(Paragraph("2. ETL &amp; Data Quality", styles["H1"]))
    story.append(
        Paragraph(
            "Source Excel workbooks are loaded, cleaned and normalised into "
            "the SQLite schema by the modules in src/etl/. Every load pass "
            "runs 16 data-quality rules (DQ-01 through DQ-16), covering "
            "primary-key uniqueness, referential integrity to the companies "
            "table, balance-sheet consistency (assets ≈ liabilities), sign "
            "checks on sales/expenses, and completeness checks on year, "
            "website, close price, sector and market cap fields.",
            styles["Body"],
        )
    )
    story.append(Paragraph("Rule severities:", styles["H2"]))
    story.append(
        Paragraph(
            "• <b>CRITICAL</b> — duplicate keys, unknown company_id, duplicate "
            "company name. These block a clean load.<br/>"
            "• <b>WARNING</b> — value-level issues (missing fields, sign "
            "violations, balance-sheet drift) that are logged for manual "
            "review but do not block the load.",
            styles["Body"],
        )
    )
    story.append(PageBreak())

    # ---------------- 3. Ratio Engine & Screener ----------------
    story.append(Paragraph("3. Ratio Engine &amp; Screener", styles["H1"]))
    story.append(
        Paragraph(
            "src/analytics/ratio_engine.py computes profitability, leverage, "
            "efficiency and cash-flow ratios for every company-year. The "
            "screener (src/screener/engine.py) applies threshold-based "
            "strategies defined in src/config/screener_config.yaml. The six "
            "built-in strategies are:",
            styles["Body"],
        )
    )

    strategy_rows = [
        ["Strategy", "Key Thresholds"],
        ["quality_compounder", "ROE ≥ 15%, D/E ≤ 1, FCF ≥ 0, Revenue CAGR ≥ 10%"],
        ["value_pick", "P/E ≤ 15, P/B ≤ 2, ROE ≥ 15%, D/E ≤ 1, Div. Yield ≥ 1%"],
        ["growth_accelerator", "PAT CAGR ≥ 20%, Revenue CAGR ≥ 15%, D/E ≤ 2"],
        ["dividend_champion", "Div. Yield ≥ 2.5%, Payout ≤ 70%, ROE ≥ 10%, FCF ≥ 0"],
        ["debt_free_bluechip", "D/E = 0, ROE ≥ 12%, Sales ≥ ₹5,000 Cr"],
        ["turnaround_watch", "Revenue CAGR ≥ 10%, FCF ≥ 0, D/E ≤ 2"],
    ]
    story.append(_table(strategy_rows, col_widths=[45 * mm, 105 * mm]))
    story.append(PageBreak())

    # ---------------- 4. KMeans Clustering (Sprint 6) ----------------
    story.append(Paragraph("4. KMeans Clustering (Sprint 6)", styles["H1"]))
    story.append(
        Paragraph(
            "src/analytics/clustering.py groups every company into 5 "
            "quantitative clusters using return_on_equity_pct, "
            "debt_to_equity, revenue_cagr_5yr, fcf_cagr_5yr and "
            "operating_profit_margin_pct. Missing values are imputed with "
            "the company's sector median (falling back to the portfolio-wide "
            "median). Features are standardised before fitting "
            "KMeans(n_clusters=5, random_state=42).",
            styles["Body"],
        )
    )
    story.append(
        Paragraph(
            "src/analytics/cluster_profiling.py then profiles each cluster's "
            "mean/median feature values and ranks them on a composite "
            "quality score (ROE + margin − leverage, all z-scored) and a "
            "growth score (revenue + FCF CAGR, z-scored) to assign one of "
            "five readable names:",
            styles["Body"],
        )
    )
    story.append(
        Paragraph(
            "• High-Quality Compounders — best quality score, above-median growth<br/>"
            "• Distressed or Turnaround — worst quality score, below-median growth<br/>"
            "• Emerging Growth — highest growth score among the remainder<br/>"
            "• Defensive Dividend Payers — lowest leverage among the remainder<br/>"
            "• Value Cyclicals — everything left over",
            styles["Body"],
        )
    )
    story.append(
        Paragraph(
            "Outputs: reports/elbow_plot.png (k=2..10 inertia curve), "
            "output/cluster_labels.csv, reports/correlation_heatmap.png, "
            "output/outlier_report.csv (|z-score| &gt; 3), and "
            "output/portfolio_stats.csv (P10-P90, mean, std per feature).",
            styles["Body"],
        )
    )
    story.append(PageBreak())

    # ---------------- 5. REST API ----------------
    story.append(Paragraph("5. REST API", styles["H1"]))
    story.append(
        Paragraph(
            "The FastAPI layer in src/api/ exposes every analytics module "
            "under the /api/v1 prefix, with CORS and request-logging "
            "middleware enabled. Interactive documentation is available at "
            "/docs (Swagger UI) once the service is running:",
            styles["Body"],
        )
    )
    story.append(
        Paragraph(
            "<font face='Courier'>uvicorn src.api.main:app --reload</font>",
            styles["Body"],
        )
    )

    api_rows = [
        ["Router", "Base Path", "Purpose"],
        ["health", "/api/v1/health", "Status, version, uptime, DB row counts"],
        [
            "companies",
            "/api/v1/companies",
            "Profile, P&amp;L, BS, cash flow, ratios, tearsheet",
        ],
        ["screener", "/api/v1/screener", "Named strategies + ad-hoc filters"],
        ["sectors", "/api/v1/sectors", "Sector roll-ups and members"],
        ["peers", "/api/v1/peers", "Peer groups and percentile rankings"],
        ["valuation", "/api/v1/valuation", "Market cap / PE / PB history and rankings"],
        ["portfolio", "/api/v1/portfolio", "Cluster composition, stats, outliers"],
        ["documents", "/api/v1/documents", "Annual report links per company"],
    ]
    story.append(_table(api_rows, col_widths=[28 * mm, 42 * mm, 80 * mm]))
    story.append(PageBreak())

    # ---------------- 6. Reading the Reports ----------------
    story.append(Paragraph("6. Reading the Generated Reports", styles["H1"]))
    story.append(
        Paragraph(
            "• <b>Company Tearsheets</b> (reports/tearsheets/*.pdf) — 2-page "
            "single-company summary: KPI tiles, capital-allocation pattern "
            "badge, revenue/profit charts, ROE/ROCE trend, balance sheet and "
            "cash-flow charts, pros &amp; cons.<br/>"
            "• <b>Sector Reports</b> — sector-level aggregation of the same "
            "KPI set, used to benchmark a company against its sector.<br/>"
            "• <b>Portfolio Report</b> — cross-sector summary for a full "
            "holdings list.<br/>"
            "• <b>Elbow Plot</b> — validates that 5 is a reasonable cluster "
            "count; inertia should visibly bend around k=5.<br/>"
            "• <b>Correlation Heatmap</b> — checks for multicollinearity "
            "among the 5 clustering features before trusting cluster "
            "separations.<br/>"
            "• <b>Outlier Report</b> — companies whose reported ratios are "
            "statistically extreme (|z| &gt; 3) — always sanity-check these "
            "against the source annual report before acting on them.",
            styles["Body"],
        )
    )
    story.append(PageBreak())

    # ---------------- 7. Operational Checklist ----------------
    story.append(Paragraph("7. Operational Checklist", styles["H1"]))
    story.append(
        Paragraph("Before relying on any report for a decision:", styles["Body"])
    )
    story.append(
        Paragraph(
            "1. Confirm the ETL run completed with 0 CRITICAL DQ failures.<br/>"
            "2. Re-run src/analytics/clustering.py and cluster_profiling.py "
            "after any data refresh — cluster assignments are not persisted "
            "across data versions automatically.<br/>"
            "3. Check output/outlier_report.csv for the companies you are "
            "analysing before trusting their ratios at face value.<br/>"
            "4. Confirm docs/openapi.json is regenerated "
            "(python -m src.api.export_api_docs) after any router change.<br/>"
            "5. Run the full test suite (pytest) — 0 failures required before "
            "shipping.",
            styles["Body"],
        )
    )
    story.append(PageBreak())

    # ---------------- 8. Ratio Glossary ----------------
    story.append(Paragraph("8. Ratio Glossary", styles["H1"]))
    story.append(
        Paragraph(
            "Definitions for every ratio referenced in this guide, as "
            "computed by src/analytics/ratio_engine.py:",
            styles["Body"],
        )
    )

    glossary_rows = [
        ["Ratio", "Definition"],
        ["ROE (%)", "Net Profit ÷ Shareholder Equity × 100"],
        ["Debt-to-Equity", "Total Debt ÷ Shareholder Equity"],
        ["Operating Profit Margin (%)", "Operating Profit ÷ Sales × 100"],
        ["Interest Coverage", "Operating Profit ÷ Interest Expense"],
        ["Asset Turnover", "Sales ÷ Total Assets"],
        ["Free Cash Flow (₹ Cr)", "Cash from Operations − Capex"],
        [
            "Revenue / FCF / PAT CAGR (5yr)",
            "Compound annual growth rate between the earliest and latest available reporting periods",
        ],
        ["Dividend Payout Ratio (%)", "Dividends Paid ÷ Net Profit × 100"],
        [
            "Composite Quality Score",
            "Weighted blend of profitability, leverage and growth ratios used for quick ranking",
        ],
    ]
    story.append(_table(glossary_rows, col_widths=[55 * mm, 95 * mm]))
    story.append(PageBreak())

    # ---------------- 9. Appendix: Current Cluster Profile ----------------
    story.append(Paragraph("9. Appendix — Current Cluster Profile", styles["H1"]))
    story.append(
        Paragraph(
            "Snapshot of the live cluster assignment as of the most recent "
            "run of the Day 36/37 pipeline (output/cluster_labels.csv):",
            styles["Body"],
        )
    )

    try:
        import csv as _csv

        with open("output/cluster_labels.csv", newline="") as f:
            cluster_rows = list(_csv.DictReader(f))

        summary: dict = {}
        for row in cluster_rows:
            name = row["cluster_name"]
            summary[name] = summary.get(name, 0) + 1

        cluster_table = [["Cluster Name", "Company Count"]] + [
            [name, str(count)]
            for name, count in sorted(summary.items(), key=lambda x: -x[1])
        ]
        story.append(_table(cluster_table, col_widths=[100 * mm, 50 * mm]))

    except FileNotFoundError:
        story.append(
            Paragraph(
                "Cluster output not found — run "
                "src/analytics/clustering.py and cluster_profiling.py first.",
                styles["Body"],
            )
        )

    story.append(Spacer(1, 8 * mm))
    story.append(
        Paragraph(
            "For per-company cluster assignment and distance-from-centroid, "
            "query GET /api/v1/portfolio/clusters or open "
            "output/cluster_labels.csv directly.",
            styles["Body"],
        )
    )

    return story


def generate_analyst_guide() -> None:
    """
    Build and save the analyst guide PDF.
    """

    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="N100 Financial Platform - Analyst Guide",
    )

    styles = _styles()
    story = build_story(styles)

    doc.build(story)

    print(f"✔ Analyst guide saved : {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_analyst_guide()
