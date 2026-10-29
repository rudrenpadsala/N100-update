"""
sector_report.py

Sprint 5
Day 33/34

Sector Report

Generates one PDF per broad sector, summarizing the companies
within it: sector-level averages, a capital allocation pattern
mix, a ROE leaderboard, and any distress alerts within the sector.

Usage:
    python -m src.reports.sector_report
    python -m src.reports.sector_report "Information Technology"
"""

import os
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.enums import TA_LEFT

import pandas as pd

from src.reports.report_data import get_master_companies, load_cashflow_intelligence, get_connection
from src.reports import charts

PRIMARY = colors.HexColor("#6C63FF")
GREY = colors.HexColor("#777777")
INK = colors.HexColor("#222222")
LIGHT_BG = colors.HexColor("#F5F5FA")
DANGER = colors.HexColor("#DC3545")

OUTPUT_DIR = "reports/sector"


def _styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle("SRTitle", parent=base["Heading1"], fontSize=20, textColor=INK, fontName="Helvetica-Bold"))
    base.add(ParagraphStyle("SRSubtitle", parent=base["Normal"], fontSize=10, textColor=GREY, spaceAfter=10))
    base.add(ParagraphStyle("SRHeading", parent=base["Heading2"], fontSize=12, textColor=PRIMARY, spaceBefore=10, spaceAfter=6, fontName="Helvetica-Bold"))
    base.add(ParagraphStyle("SRBody", parent=base["Normal"], fontSize=9, textColor=INK, leading=13))
    return base


def _load_sector_financials(company_ids):
    """Latest financial_ratios + market_cap row per company in the sector."""

    conn = get_connection()

    placeholders = ",".join("?" for _ in company_ids)

    ratios = pd.read_sql(
        f"SELECT * FROM financial_ratios WHERE company_id IN ({placeholders})",
        conn, params=company_ids
    )

    conn.close()

    if ratios.empty:
        return ratios

    return (
        ratios.sort_values(["company_id", "year"])
        .drop_duplicates(subset=["company_id"], keep="last")
    )


def _kpi_summary_table(sector_ratios, sector_name, company_count):

    avg_roe = sector_ratios["return_on_equity_pct"].mean() if not sector_ratios.empty else None
    avg_rev_cagr = sector_ratios["revenue_cagr_5yr"].mean() if not sector_ratios.empty else None
    avg_dte = sector_ratios["debt_to_equity"].mean() if not sector_ratios.empty else None
    avg_quality = sector_ratios["composite_quality_score"].mean() if not sector_ratios.empty else None

    def fmt(v, suffix=""):
        return f"{v:.1f}{suffix}" if v is not None and pd.notna(v) else "N/A"

    tiles = [
        ("Companies", str(company_count)),
        ("Avg ROE", fmt(avg_roe, "%")),
        ("Avg Revenue CAGR", fmt(avg_rev_cagr, "%")),
        ("Avg Debt/Equity", fmt(avg_dte, "x")),
        ("Avg Quality Score", fmt(avg_quality, "/100")),
    ]

    label_row = [Paragraph(f"<b>{v}</b>", ParagraphStyle("t", fontSize=13, textColor=PRIMARY)) for _, v in tiles]
    caption_row = [Paragraph(k, ParagraphStyle("c", fontSize=8, textColor=GREY)) for k, _ in tiles]

    table = Table([label_row, caption_row], colWidths=[34 * mm] * 5)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0EA")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0EA")),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))

    return table


def _leaderboard_table(sector_ratios, company_names, styles, top_n=10):

    if sector_ratios.empty:
        return Paragraph("No ratio data available for this sector.", styles["SRBody"])

    ranked = sector_ratios.sort_values("return_on_equity_pct", ascending=False).head(top_n)

    header = ["Company", "ROE %", "Rev CAGR %", "Debt/Equity", "Quality"]
    rows = [header]

    for _, row in ranked.iterrows():
        name = company_names.get(row["company_id"], row["company_id"])
        rows.append([
            name,
            f"{row['return_on_equity_pct']:.1f}" if pd.notna(row["return_on_equity_pct"]) else "N/A",
            f"{row['revenue_cagr_5yr']:.1f}" if pd.notna(row["revenue_cagr_5yr"]) else "N/A",
            f"{row['debt_to_equity']:.2f}" if pd.notna(row["debt_to_equity"]) else "N/A",
            f"{row['composite_quality_score']:.0f}" if pd.notna(row["composite_quality_score"]) else "N/A",
        ])

    table = Table(rows, colWidths=[62 * mm, 25 * mm, 28 * mm, 27 * mm, 24 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E0E0EA")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    return table


def generate_sector_report(sector_name, output_dir=OUTPUT_DIR):

    companies = get_master_companies()
    sector_companies = companies[companies["broad_sector"] == sector_name]

    if sector_companies.empty:
        return None

    company_ids = sector_companies["id"].tolist()
    company_names = dict(zip(sector_companies["id"], sector_companies["company_name"]))

    sector_ratios = _load_sector_financials(company_ids)

    intelligence = load_cashflow_intelligence()
    sector_intel = intelligence[intelligence.index.isin(company_ids)] if not intelligence.empty else intelligence

    styles = _styles()
    story = []

    story.append(Paragraph(sector_name, styles["SRTitle"]))
    story.append(Paragraph(f"Sector Report &nbsp;|&nbsp; {len(company_ids)} companies", styles["SRSubtitle"]))

    story.append(_kpi_summary_table(sector_ratios, sector_name, len(company_ids)))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Top Companies by ROE", styles["SRHeading"]))
    story.append(_leaderboard_table(sector_ratios, company_names, styles))
    story.append(Spacer(1, 10))

    # Capital allocation pattern mix + ROE ranking chart, side by side
    if not sector_intel.empty and "capital_allocation_pattern" in sector_intel.columns:
        pattern_counts = sector_intel["capital_allocation_pattern"].value_counts()
        pattern_buf = charts.pattern_pie_chart(
            pattern_counts.index.tolist(), pattern_counts.values.tolist(),
            title="Capital Allocation Mix"
        )
    else:
        pattern_buf = charts.pattern_pie_chart([], [], title="Capital Allocation Mix")

    if not sector_ratios.empty:
        ranked = sector_ratios.sort_values("return_on_equity_pct", ascending=False).head(10)
        labels = [company_names.get(cid, cid) for cid in ranked["company_id"]]
        values = ranked["return_on_equity_pct"].tolist()
        roe_buf = charts.sector_bar_chart(labels, values, "ROE Ranking (%)", color=charts.PRIMARY, figsize=(5.8, 4.0))
    else:
        roe_buf = charts.sector_bar_chart([], [], "ROE Ranking (%)")

    story.append(Table(
        [[Image(pattern_buf, width=75 * mm, height=68 * mm),
          Image(roe_buf, width=95 * mm, height=68 * mm)]],
        colWidths=[80 * mm, 95 * mm]
    ))
    story.append(Spacer(1, 10))

    # Distress alerts within sector
    if not sector_intel.empty and "is_distressed" in sector_intel.columns:
        distressed = sector_intel[sector_intel["is_distressed"] == True]  # noqa: E712
    else:
        distressed = pd.DataFrame()

    story.append(Paragraph("Distress Alerts in Sector", styles["SRHeading"]))

    if distressed.empty:
        story.append(Paragraph("No companies in this sector are currently flagged as distressed.", styles["SRBody"]))
    else:
        for company_id, row in distressed.iterrows():
            name = company_names.get(company_id, company_id)
            reason = row.get("distress_reason", "")
            story.append(Paragraph(
                f'<font color="#DC3545"><b>{name}</b></font> - {reason}', styles["SRBody"]
            ))

    os.makedirs(output_dir, exist_ok=True)
    safe_name = sector_name.replace(" ", "_").replace("/", "-")
    output_path = os.path.join(output_dir, f"{safe_name}_sector_report.pdf")

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=16 * mm, bottomMargin=14 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
        title=f"{sector_name} Sector Report"
    )
    doc.build(story)

    return output_path


def generate_all_sector_reports(output_dir=OUTPUT_DIR):

    companies = get_master_companies()
    sectors = sorted(companies["broad_sector"].dropna().unique())

    results = []

    for sector_name in sectors:
        path = generate_sector_report(sector_name, output_dir)
        results.append((sector_name, path))

    return results


def main():

    print("=" * 60)
    print("Sector Report Generator (Sprint 5 - Day 33/34)")
    print("=" * 60)

    if len(sys.argv) > 1:
        sector_name = " ".join(sys.argv[1:])
        path = generate_sector_report(sector_name)
        print(f"✔ {sector_name} -> {path}" if path else f"⚠ No companies found for sector '{sector_name}'")
        return

    results = generate_all_sector_reports()

    for sector_name, path in results:
        print(f"✔ {sector_name} -> {path}")

    print(f"\n✔ Generated {len(results)} sector reports in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
