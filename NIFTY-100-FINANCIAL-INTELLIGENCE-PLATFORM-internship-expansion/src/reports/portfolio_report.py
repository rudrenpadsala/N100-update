"""
portfolio_report.py

Sprint 5
Day 35

Portfolio Report

Generates a single portfolio-wide PDF with one page per company,
showing the company name, sector, its top 6 KPIs, and a trend arrow
for each KPI (comparing the latest reported year to the previous
one).

Trend arrows show direction only (up / down / flat), not a
"good"/"bad" judgement, since the desirable direction differs by
KPI (e.g. rising Debt/Equity is unfavourable while rising ROE is
favourable) - documented assumption.

Output:
    reports/portfolio/portfolio_summary.pdf
"""

import os

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

from src.reports.report_data import CompanyReportData, get_master_companies

PRIMARY = colors.HexColor("#6C63FF")
GREY = colors.HexColor("#777777")
INK = colors.HexColor("#222222")
LIGHT_BG = colors.HexColor("#F5F5FA")
SUCCESS = colors.HexColor("#198754")
DANGER = colors.HexColor("#DC3545")

OUTPUT_DIR = "reports/portfolio"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "portfolio_summary.pdf")

UP_ARROW = "\u25B2"
DOWN_ARROW = "\u25BC"
FLAT_ARROW = "\u25AC"


def _styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle("PRTitle", parent=base["Heading1"], fontSize=20, textColor=INK, fontName="Helvetica-Bold"))
    base.add(ParagraphStyle("PRSubtitle", parent=base["Normal"], fontSize=10, textColor=GREY, spaceAfter=12))
    base.add(ParagraphStyle("PRCover", parent=base["Normal"], fontSize=11, textColor=INK, leading=16))
    return base


def _trend(current, previous):
    """Returns (formatted_arrow_text, color) for current vs previous."""

    if current is None or previous is None or pd.isna(current) or pd.isna(previous):
        return "N/A", GREY

    if previous == 0:
        return "N/A", GREY

    change_pct = (current - previous) / abs(previous) * 100

    if change_pct > 1:
        return f"{UP_ARROW} {change_pct:+.1f}%", SUCCESS

    if change_pct < -1:
        return f"{DOWN_ARROW} {change_pct:+.1f}%", DANGER

    return f"{FLAT_ARROW} {change_pct:+.1f}%", GREY


def _kpi_rows(data):
    """
    Build the Top 6 KPI rows: (label, current_value_text, trend_text, trend_color)
    """

    ratios = data.ratios
    pnl = data.pnl

    def latest_prev(df, col):
        if df is None or df.empty or col not in df.columns:
            return None, None
        vals = df[col].tolist()
        current = vals[-1] if len(vals) >= 1 else None
        previous = vals[-2] if len(vals) >= 2 else None
        return current, previous

    roe_cur, roe_prev = latest_prev(ratios, "return_on_equity_pct")
    dte_cur, dte_prev = latest_prev(ratios, "debt_to_equity")
    quality_cur, quality_prev = latest_prev(ratios, "composite_quality_score")
    payout_cur, payout_prev = latest_prev(ratios, "dividend_payout_ratio_pct")
    sales_cur, sales_prev = latest_prev(pnl, "sales")
    profit_cur, profit_prev = latest_prev(pnl, "net_profit")

    def fmt(v, suffix="", decimals=1):
        return f"{v:.{decimals}f}{suffix}" if v is not None and pd.notna(v) else "N/A"

    rows = [
        ("Revenue (Rs. Cr)", fmt(sales_cur, "", 0), *_trend(sales_cur, sales_prev)),
        ("Net Profit (Rs. Cr)", fmt(profit_cur, "", 0), *_trend(profit_cur, profit_prev)),
        ("ROE", fmt(roe_cur, "%"), *_trend(roe_cur, roe_prev)),
        ("Debt / Equity", fmt(dte_cur, "x", 2), *_trend(dte_cur, dte_prev)),
        ("Dividend Payout", fmt(payout_cur, "%"), *_trend(payout_cur, payout_prev)),
        ("Quality Score", fmt(quality_cur, "/100", 0), *_trend(quality_cur, quality_prev)),
    ]

    return rows


def _company_page(data, styles):

    company_name = data.company.get("company_name", data.company_id) if not data.company.empty else data.company_id
    sector = data.sector.get("broad_sector", "Unknown Sector") if not data.sector.empty else "Unknown Sector"
    sub_sector = data.sector.get("sub_sector", "") if not data.sector.empty else ""
    cap_category = data.sector.get("market_cap_category", "") if not data.sector.empty else ""

    story = []

    story.append(Paragraph(company_name, styles["PRTitle"]))

    subtitle = f"{data.company_id} &nbsp;|&nbsp; {sector}"
    if sub_sector:
        subtitle += f" - {sub_sector}"
    if cap_category:
        subtitle += f" &nbsp;|&nbsp; {cap_category}"

    story.append(Paragraph(subtitle, styles["PRSubtitle"]))

    rows = _kpi_rows(data)

    header = ["KPI", "Latest Value", "YoY Trend"]
    table_data = [header]

    for label, value, trend_text, trend_color in rows:
        table_data.append([label, value, trend_text])

    table = Table(table_data, colWidths=[60 * mm, 50 * mm, 60 * mm])

    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E0E0EA")),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]

    for i, (_, _, _, trend_color) in enumerate(rows, start=1):
        style_commands.append(("TEXTCOLOR", (2, i), (2, i), trend_color))
        style_commands.append(("FONTNAME", (2, i), (2, i), "Helvetica-Bold"))

    table.setStyle(TableStyle(style_commands))

    story.append(table)

    # Capital allocation pattern footer
    pattern = data.intelligence.get("capital_allocation_pattern") if not data.intelligence.empty else None
    if pattern and not (isinstance(pattern, float) and pd.isna(pattern)):
        story.append(Spacer(1, 14))
        story.append(Paragraph(
            f'<font color="#777777">Capital Allocation Pattern:</font> <b>{pattern}</b>',
            styles["PRCover"]
        ))

    story.append(PageBreak())

    return story


def generate_portfolio_summary(output_path=OUTPUT_PATH):

    companies = get_master_companies().sort_values(["broad_sector", "id"])

    styles = _styles()
    story = []

    for _, row in companies.iterrows():

        data = CompanyReportData(row["id"])

        if not data.has_sufficient_data():
            continue

        story.extend(_company_page(data, styles))

    # Remove the trailing PageBreak after the last company
    if story and isinstance(story[-1], PageBreak):
        story = story[:-1]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=18 * mm, bottomMargin=16 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title="Nifty 100 Portfolio Summary"
    )
    doc.build(story)

    return output_path


def main():

    print("=" * 60)
    print("Portfolio Summary Report (Sprint 5 - Day 35)")
    print("=" * 60)

    path = generate_portfolio_summary()

    print(f"✔ Saved: {path}")


if __name__ == "__main__":
    main()
