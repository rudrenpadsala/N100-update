"""
tearsheet.py

Sprint 5
Day 33

Company Tearsheet

Generates a 2-page PDF tearsheet for a single company using
ReportLab, pulling data through src/reports/report_data.py and
rendering charts through src/reports/charts.py.

Page 1 : Header, KPI tiles, Capital Allocation badge,
          Revenue chart, Profit chart
Page 2 : ROE/ROCE chart, Balance Sheet chart, Cash Flow chart,
          Pros, Cons

Usage:
    python -m src.reports.tearsheet TCS
    python -m src.reports.tearsheet TCS HDFCBANK INFY
"""

import os
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, KeepTogether, PageBreak
)
from reportlab.lib.enums import TA_LEFT

from src.reports.report_data import CompanyReportData
from src.reports import charts

PRIMARY = colors.HexColor("#6C63FF")
SECONDARY = colors.HexColor("#FF6B9D")
ACCENT = colors.HexColor("#FFB86C")
SUCCESS = colors.HexColor("#198754")
DANGER = colors.HexColor("#DC3545")
INK = colors.HexColor("#222222")
GREY = colors.HexColor("#777777")
LIGHT_BG = colors.HexColor("#F5F5FA")

OUTPUT_DIR = "reports/tearsheets"

PATTERN_BADGE_COLORS = {
    "Reinvestor": SUCCESS,
    "Cash Accumulator": PRIMARY,
    "Mixed": ACCENT,
    "Liquidating Assets": ACCENT,
    "Growth Funded by Debt": DANGER,
    "Distress Signal": DANGER,
    "Pre-Revenue": GREY,
    "Unknown": GREY,
}

PATTERN_DESCRIPTIONS = {
    "Reinvestor": "Generates operating cash and reinvests it into the business.",
    "Cash Accumulator": "Generates cash from operations, investing and financing alike.",
    "Mixed": "Cash flow signals are mixed across operating, investing and financing activity.",
    "Liquidating Assets": "Positive operating and investing cash flow; funds are being returned to shareholders.",
    "Growth Funded by Debt": "Operating cash flow is negative; growth is being funded through debt.",
    "Distress Signal": "Negative operating cash flow funded by financing or asset sales.",
    "Pre-Revenue": "All three cash flow activities are negative.",
    "Unknown": "Cash flow signature does not match a standard pattern.",
}


# --------------------------------------------------
# Styles
# --------------------------------------------------

def _styles():
    base = getSampleStyleSheet()

    base.add(ParagraphStyle(
        "TSTitle", parent=base["Heading1"], fontSize=20, textColor=INK,
        spaceAfter=2, fontName="Helvetica-Bold"
    ))
    base.add(ParagraphStyle(
        "TSSubtitle", parent=base["Normal"], fontSize=10, textColor=GREY,
        spaceAfter=10
    ))
    base.add(ParagraphStyle(
        "TSSectionHeading", parent=base["Heading2"], fontSize=12, textColor=PRIMARY,
        spaceBefore=10, spaceAfter=6, fontName="Helvetica-Bold"
    ))
    base.add(ParagraphStyle(
        "TSBody", parent=base["Normal"], fontSize=9, textColor=INK, leading=13
    ))
    base.add(ParagraphStyle(
        "TSPro", parent=base["Normal"], fontSize=9, textColor=INK, leading=13,
        leftIndent=2
    ))
    base.add(ParagraphStyle(
        "TSCon", parent=base["Normal"], fontSize=9, textColor=INK, leading=13,
        leftIndent=2
    ))

    return base


# --------------------------------------------------
# KPI Helpers
# --------------------------------------------------

def _fmt(value, suffix="", decimals=1, dash="N/A"):
    if value is None:
        return dash
    try:
        if value != value:  # NaN check without importing pandas here
            return dash
    except TypeError:
        return dash
    return f"{value:.{decimals}f}{suffix}"


def _kpi_tiles(data, styles):
    """Build the top KPI tile row as a ReportLab Table."""

    ratios_latest = data.ratios.iloc[-1] if not data.ratios.empty else None
    mcap = data.market_cap_latest

    roe = ratios_latest.get("return_on_equity_pct") if ratios_latest is not None else None
    roce = data.company.get("roce_percentage") if not data.company.empty else None
    dte = ratios_latest.get("debt_to_equity") if ratios_latest is not None else None
    quality = ratios_latest.get("composite_quality_score") if ratios_latest is not None else None
    pe = mcap.get("pe_ratio") if mcap is not None else None
    div_yield = mcap.get("dividend_yield_pct") if mcap is not None else None

    tiles = [
        ("ROE", _fmt(roe, "%")),
        ("ROCE", _fmt(roce, "%")),
        ("Debt/Equity", _fmt(dte, "x", 2)),
        ("P/E", _fmt(pe, "x", 1)),
        ("Div. Yield", _fmt(div_yield, "%")),
        ("Quality Score", _fmt(quality, "/100", 0)),
    ]

    label_row = [Paragraph(f"<b>{v}</b>", ParagraphStyle(
        "tile_val", fontSize=13, textColor=PRIMARY, alignment=TA_LEFT
    )) for _, v in tiles]

    caption_row = [Paragraph(k, ParagraphStyle(
        "tile_cap", fontSize=8, textColor=GREY, alignment=TA_LEFT
    )) for k, _ in tiles]

    table = Table([label_row, caption_row], colWidths=[28 * mm] * 6)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0EA")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0EA")),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))

    return table


def _capital_allocation_badge(data, styles):

    pattern = data.intelligence.get("capital_allocation_pattern") if not data.intelligence.empty else None

    if not pattern or (isinstance(pattern, float) and pattern != pattern):
        pattern = "Not Available"
        description = "Insufficient cash flow history to classify this company."
        color = GREY
    else:
        description = PATTERN_DESCRIPTIONS.get(pattern, "")
        color = PATTERN_BADGE_COLORS.get(pattern, GREY)

    badge_style = ParagraphStyle(
        "badge", fontSize=11, textColor=colors.white, fontName="Helvetica-Bold",
        alignment=TA_LEFT
    )
    desc_style = ParagraphStyle(
        "badge_desc", fontSize=8, textColor=colors.white, alignment=TA_LEFT, leading=11
    )

    table = Table(
        [[Paragraph(f"CAPITAL ALLOCATION: {pattern.upper()}", badge_style)],
         [Paragraph(description, desc_style)]],
        colWidths=[170 * mm]
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 0),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))

    return table


def _pros_cons_block(items, heading, styles, style_name, bullet, bullet_color):

    story = [Paragraph(heading, styles["TSSectionHeading"])]

    if not items:
        story.append(Paragraph("No items identified.", styles["TSBody"]))
        return story

    for item in items[:6]:
        bullet_style = ParagraphStyle(
            f"{style_name}_item", parent=styles[style_name],
        )
        story.append(Paragraph(
            f'<font color="{bullet_color}"><b>{bullet}</b></font>&nbsp;&nbsp;{item["text"]} '
            f'<font size=7 color="#999999">({item["confidence_pct"]:.0f}% confidence)</font>',
            bullet_style
        ))
        story.append(Spacer(1, 3))

    return story


# --------------------------------------------------
# Chart Assembly
# --------------------------------------------------

def _revenue_profit_charts(data):

    pnl = data.recent(data.pnl)

    years = pnl["year"].tolist() if not pnl.empty else []
    sales = pnl["sales"].tolist() if not pnl.empty else []
    profit = pnl["net_profit"].tolist() if not pnl.empty else []

    revenue_buf = charts.bar_line_chart(years, sales, "Revenue Trend", color=charts.PRIMARY, unit="Rs. Cr")
    profit_buf = charts.bar_line_chart(years, profit, "Net Profit Trend", color=charts.SECONDARY, unit="Rs. Cr")

    return revenue_buf, profit_buf


def _roe_roce_chart(data):

    ratios = data.recent(data.ratios)
    years = ratios["year"].tolist() if not ratios.empty else []
    roe = ratios["return_on_equity_pct"].tolist() if not ratios.empty else []

    roce_current = data.company.get("roce_percentage") if not data.company.empty else None
    roce_series = [roce_current] * len(years) if years and roce_current is not None else []

    return charts.dual_line_chart(
        years, roe, "ROE (trend)", roce_series, "ROCE (current)",
        title="ROE vs ROCE"
    )


def _balance_sheet_chart(data):

    bs = data.recent(data.balance_sheet)
    years = bs["year"].tolist() if not bs.empty else []
    assets = bs["total_assets"].tolist() if not bs.empty else []
    liabilities = bs["total_liabilities"].tolist() if not bs.empty else []

    return charts.stacked_balance_sheet_chart(years, assets, liabilities)


def _cashflow_chart(data):

    cf = data.recent(data.cashflow)
    years = cf["year"].tolist() if not cf.empty else []
    operating = cf["operating_activity"].tolist() if not cf.empty else []
    investing = cf["investing_activity"].tolist() if not cf.empty else []
    financing = cf["financing_activity"].tolist() if not cf.empty else []

    return charts.cashflow_chart(years, operating, investing, financing)


# --------------------------------------------------
# Build Single Company Tearsheet
# --------------------------------------------------

def build_tearsheet_story(data, styles):

    company_name = data.company.get("company_name", data.company_id) if not data.company.empty else data.company_id
    sector = data.sector.get("broad_sector", "Unknown Sector") if not data.sector.empty else "Unknown Sector"
    sub_sector = data.sector.get("sub_sector", "") if not data.sector.empty else ""
    cap_category = data.sector.get("market_cap_category", "") if not data.sector.empty else ""

    story = []

    # ---- Page 1 ----
    story.append(Paragraph(company_name, styles["TSTitle"]))
    subtitle = f"{data.company_id} &nbsp;|&nbsp; {sector}"
    if sub_sector:
        subtitle += f" - {sub_sector}"
    if cap_category:
        subtitle += f" &nbsp;|&nbsp; {cap_category}"
    story.append(Paragraph(subtitle, styles["TSSubtitle"]))

    story.append(_kpi_tiles(data, styles))
    story.append(Spacer(1, 10))
    story.append(_capital_allocation_badge(data, styles))
    story.append(Spacer(1, 10))

    revenue_buf, profit_buf = _revenue_profit_charts(data)
    chart_row = Table(
        [[Image(revenue_buf, width=84 * mm, height=42 * mm),
          Image(profit_buf, width=84 * mm, height=42 * mm)]],
        colWidths=[85 * mm, 85 * mm]
    )
    story.append(chart_row)

    story.append(PageBreak())

    # ---- Page 2 ----
    story.append(Paragraph(f"{company_name} - Financial Trends", styles["TSTitle"]))
    story.append(Spacer(1, 4))

    roe_roce_buf = _roe_roce_chart(data)
    bs_buf = _balance_sheet_chart(data)
    cf_buf = _cashflow_chart(data)

    story.append(Table(
        [[Image(roe_roce_buf, width=84 * mm, height=42 * mm),
          Image(bs_buf, width=84 * mm, height=42 * mm)]],
        colWidths=[85 * mm, 85 * mm]
    ))
    story.append(Spacer(1, 6))
    story.append(Image(cf_buf, width=170 * mm, height=48 * mm))
    story.append(Spacer(1, 6))

    pros_cons_table = Table(
        [[
            _pros_cons_block(data.pros, "Pros", styles, "TSPro", "+", "#198754"),
            _pros_cons_block(data.cons, "Cons", styles, "TSCon", "-", "#DC3545"),
        ]],
        colWidths=[85 * mm, 85 * mm]
    )
    story.append(pros_cons_table)

    return story


def generate_tearsheet(company_id, output_dir=OUTPUT_DIR):
    """
    Generate a single company's 2-page tearsheet PDF.

    Returns the output file path, or None if the company does not
    have sufficient data (see CompanyReportData.has_sufficient_data).
    """

    data = CompanyReportData(company_id)

    if not data.has_sufficient_data():
        return None

    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"{company_id}_tearsheet.pdf")

    styles = _styles()

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=16 * mm, bottomMargin=14 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
        title=f"{company_id} Tearsheet"
    )

    story = build_tearsheet_story(data, styles)
    doc.build(story)

    return output_path


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

def main():

    tickers = sys.argv[1:] if len(sys.argv) > 1 else ["TCS", "HDFCBANK", "INFY"]

    print("=" * 60)
    print("Company Tearsheet Generator (Sprint 5 - Day 33)")
    print("=" * 60)

    for ticker in tickers:
        path = generate_tearsheet(ticker)
        if path:
            print(f"✔ {ticker} -> {path}")
        else:
            print(f"⚠ {ticker} skipped (insufficient data)")


if __name__ == "__main__":
    main()
