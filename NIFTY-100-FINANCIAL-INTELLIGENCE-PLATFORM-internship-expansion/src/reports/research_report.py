"""
research_report.py

Internship Expansion - Module 4
Automated PDF Company Research Report

Builds a multi-page PDF for one company with:

    1. Snapshot            key figures for the latest fiscal year
    2. Financial health    score, grade, pillar roll-up and the full
                           component table (value, points, weight, contribution)
    3. Trend charts        sales and net profit over the last years
    4. Peer benchmark      company vs. peer median, percentile and rank
    5. Data-quality notes  reliability rating and every recent warning
    6. Methodology         formulas, thresholds, weights and limitations

Every number comes from the same bundle (src/analytics/platform_data.py)
that the dashboard uses, so a PDF can never disagree with the screen.

Usage:
    python -m src.reports.research_report TCS
    python -m src.reports.research_report TCS INFY HDFCBANK
    python -m src.reports.research_report --all
"""

from __future__ import annotations

import io
import sys
from datetime import date
from pathlib import Path
from typing import List, Optional, Union
from xml.sax.saxutils import escape

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from src.analytics.benchmarking import benchmark_company
from src.analytics.health_score import (
    GRADE_BANDS, METRICS, MIN_COVERAGE_PCT, PILLARS, HealthScore,
)
from src.analytics.platform_data import AnalyticsBundle, get_bundle
from src.quality.data_quality import company_reliability, company_warnings
from src.quality.periods import annual_rows, fiscal_year_end_months

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "reports" / "research"

PRIMARY = colors.HexColor("#6C63FF")
INK = colors.HexColor("#222222")
GREY = colors.HexColor("#777777")
LIGHT_BG = colors.HexColor("#F5F5FA")
GRID = colors.HexColor("#DDDDE8")
GREEN = colors.HexColor("#198754")
AMBER = colors.HexColor("#E08A00")
RED = colors.HexColor("#DC3545")

HEX = {"green": "#198754", "amber": "#E08A00", "red": "#DC3545", "primary": "#6C63FF"}

PAGE_W, PAGE_H = A4
MARGIN = 16 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

DISCLAIMER = (
    "Analytical summary of reported figures from the project database. Not investment "
    "advice; it does not predict prices."
)

TREND_YEARS = 8
RECENT_YEARS_FOR_WARNINGS = 3


# =====================================================================
# Formatting helpers
# =====================================================================

def _num(value, decimals: int = 1, suffix: str = "") -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)) or pd.isna(value):
        return "n/a"
    return f"{value:,.{decimals}f}{suffix}"


def _crore(value) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"Rs {value:,.0f} cr"


def _p(text, style) -> Paragraph:
    return Paragraph(escape(str(text)), style)


def _grade_color(grade: str):
    return {"A": GREEN, "B": GREEN, "C": AMBER, "D": RED, "E": RED}.get(grade, GREY)


def _points_color_hex(points: float) -> str:
    if points >= 75:
        return HEX["green"]
    if points >= 40:
        return HEX["amber"]
    return HEX["red"]


def _styles():
    base = getSampleStyleSheet()
    s = {}
    s["title"] = ParagraphStyle("title", parent=base["Title"], fontName="Helvetica-Bold",
                                fontSize=20, leading=24, textColor=INK, alignment=TA_LEFT, spaceAfter=2)
    s["subtitle"] = ParagraphStyle("subtitle", parent=base["Normal"], fontSize=9.5, leading=13,
                                   textColor=GREY)
    s["h1"] = ParagraphStyle("h1", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=13,
                             leading=16, textColor=PRIMARY, spaceBefore=10, spaceAfter=5)
    s["h2"] = ParagraphStyle("h2", parent=base["Heading3"], fontName="Helvetica-Bold", fontSize=10,
                             leading=13, textColor=INK, spaceBefore=6, spaceAfter=3)
    s["body"] = ParagraphStyle("body", parent=base["Normal"], fontSize=9, leading=12.5, textColor=INK)
    s["small"] = ParagraphStyle("small", parent=base["Normal"], fontSize=7.5, leading=10, textColor=INK)
    s["small_grey"] = ParagraphStyle("small_grey", parent=s["small"], textColor=GREY)
    s["cell"] = ParagraphStyle("cell", parent=base["Normal"], fontSize=8, leading=10.5, textColor=INK)
    s["cell_head"] = ParagraphStyle("cell_head", parent=s["cell"], fontName="Helvetica-Bold",
                                    textColor=colors.white)
    s["kpi_value"] = ParagraphStyle("kpi_value", parent=base["Normal"], fontName="Helvetica-Bold",
                                    fontSize=13, leading=16, alignment=TA_CENTER, textColor=INK)
    s["kpi_label"] = ParagraphStyle("kpi_label", parent=base["Normal"], fontSize=7.5, leading=9.5,
                                    alignment=TA_CENTER, textColor=GREY)
    s["bullet"] = ParagraphStyle("bullet", parent=s["body"], leftIndent=10, bulletIndent=0, spaceAfter=1.5)
    s["score"] = ParagraphStyle("score", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=30,
                                leading=34, alignment=TA_CENTER)
    return s


# =====================================================================
# Context (everything the PDF shows, computed once)
# =====================================================================

def _company_trend(bundle: AnalyticsBundle, company_id: str) -> pd.DataFrame:
    tables = bundle.tables
    subset = [
        tables[t][tables[t]["company_id"] == company_id]
        for t in ("profitandloss", "balancesheet", "cashflow", "financial_ratios")
        if t in tables
    ]
    fy = fiscal_year_end_months(subset)
    pl = annual_rows(subset[0], fy_months=fy)

    if pl.empty:
        return pl

    return pl[["year_key", "year", "sales", "net_profit"]].tail(TREND_YEARS).reset_index(drop=True)


def build_report_context(company_id: str, bundle: Optional[AnalyticsBundle] = None) -> dict:
    """Collect all figures for one company's report."""

    bundle = bundle or get_bundle()
    company_id = str(company_id)

    row = bundle.metrics[bundle.metrics["company_id"].astype(str) == company_id]
    if row.empty:
        raise ValueError(f"Unknown company: {company_id}")

    row = row.iloc[0]
    health: HealthScore = bundle.health[company_id]

    peer_set, benchmark = benchmark_company(
        company_id, bundle.metrics, bundle.league, bundle.peer_groups
    )

    as_of = health.as_of_year
    recent_from = (as_of - RECENT_YEARS_FOR_WARNINGS + 1) if as_of else None

    return {
        "company_id": company_id,
        "row": row,
        "health": health,
        "peer_set": peer_set,
        "benchmark": benchmark,
        "trend": _company_trend(bundle, company_id),
        "reliability": company_reliability(bundle.issues, company_id, recent_from),
        "warnings": company_warnings(bundle.issues, company_id, recent_from),
        "league_rank": _league_rank(bundle, company_id),
        "generated_on": date.today().isoformat(),
    }


def _league_rank(bundle: AnalyticsBundle, company_id: str):
    ranked = bundle.league.dropna(subset=["score"]).reset_index(drop=True)
    match = ranked.index[ranked["company_id"] == company_id]
    if len(match) == 0:
        return None
    return int(match[0]) + 1, int(len(ranked))


# =====================================================================
# Charts
# =====================================================================

def _png(fig, width_mm: float, height_mm: float) -> Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=width_mm * mm, height=height_mm * mm)


def _style_axes(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#BBBBBB")
    ax.spines["bottom"].set_color("#BBBBBB")
    ax.tick_params(colors="#444444", labelsize=7)
    ax.grid(axis="y", color="#EEEEEE", linewidth=0.7)
    ax.set_axisbelow(True)


def chart_trend(trend: pd.DataFrame) -> Optional[Image]:
    if trend.empty:
        return None

    labels = [str(int(y)) for y in trend["year_key"]]
    x = np.arange(len(labels))
    w = 0.38

    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    ax.bar(x - w / 2, trend["sales"], w, label="Sales", color=HEX["primary"])
    ax.bar(x + w / 2, trend["net_profit"], w, label="Net profit", color="#FF6B9D")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Rs crore", fontsize=7)
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    ax.set_title("Sales and net profit by fiscal year", fontsize=9, loc="left", color="#222222")
    _style_axes(ax)

    return _png(fig, 170, 170 * 2.7 / 7.2)


def chart_metric_points(health: HealthScore) -> Optional[Image]:
    comp = health.components
    scored = comp[comp["points"].notna() & (comp["status"] == "scored")]

    if scored.empty:
        return None

    scored = scored.iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 0.45 * len(scored) + 0.9))
    ax.barh(scored["label"], scored["points"], color=[_points_color_hex(v) for v in scored["points"]])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Points earned (0-100)", fontsize=7)
    ax.set_title("What drives the score: points per metric", fontsize=9, loc="left", color="#222222")
    for i, v in enumerate(scored["points"]):
        if v >= 12:
            ax.text(v - 1.5, i, f"{v:.0f}", va="center", ha="right", fontsize=7, color="white")
        else:
            ax.text(v + 1.5, i, f"{v:.0f}", va="center", ha="left", fontsize=7, color="#333333")
    _style_axes(ax)
    ax.grid(axis="x", color="#EEEEEE", linewidth=0.7)
    ax.grid(axis="y", visible=False)

    return _png(fig, 170, 170 * (0.45 * len(scored) + 0.9) / 7.2)


def chart_percentiles(benchmark: pd.DataFrame) -> Optional[Image]:
    ranked = benchmark[benchmark["percentile"].notna()]

    if ranked.empty:
        return None

    ranked = ranked.iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 0.42 * len(ranked) + 0.9))
    ax.barh(ranked["label"], ranked["percentile"],
            color=[_points_color_hex(v * 0.75 + 12) for v in ranked["percentile"]])
    ax.axvline(50, color="#888888", linewidth=0.9, linestyle="--")
    ax.set_xlim(0, 100)
    for i, v in enumerate(ranked["percentile"]):
        if v >= 12:
            ax.text(v - 1.5, i, f"{v:.0f}", va="center", ha="right", fontsize=7, color="white")
        else:
            ax.text(v + 1.5, i, f"{v:.0f}", va="center", ha="left", fontsize=7, color="#333333")
    ax.set_xlabel("Percentile in peer set (100 = best)", fontsize=7)
    ax.set_title("Position versus peers", fontsize=9, loc="left", color="#222222")
    _style_axes(ax)
    ax.grid(axis="x", color="#EEEEEE", linewidth=0.7)
    ax.grid(axis="y", visible=False)

    return _png(fig, 170, 170 * (0.42 * len(ranked) + 0.9) / 7.2)


# =====================================================================
# Page furniture
# =====================================================================

def _footer(company_name: str):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(GRID)
        canvas.line(MARGIN, 14 * mm, PAGE_W - MARGIN, 14 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GREY)
        canvas.drawString(MARGIN, 10.5 * mm, f"{company_name} - Research report")
        canvas.drawRightString(PAGE_W - MARGIN, 10.5 * mm, f"Page {doc.page}")
        canvas.setFont("Helvetica", 6.5)
        canvas.drawCentredString(PAGE_W / 2, 6.8 * mm, DISCLAIMER)
        canvas.restoreState()
    return draw


def _table(data, col_widths, header=True, zebra=True, extra=None):
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, GRID),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), PRIMARY)]
    if zebra:
        for r in range(1, len(data)):
            if r % 2 == 0:
                style.append(("BACKGROUND", (0, r), (-1, r), LIGHT_BG))
    if extra:
        style += extra
    t.setStyle(TableStyle(style))
    return t


# =====================================================================
# Sections
# =====================================================================

def _section_header(ctx, st):
    row, health, peer_set = ctx["row"], ctx["health"], ctx["peer_set"]

    peer_text = (
        f"{peer_set.group_name} ({peer_set.basis}, {len(peer_set.members)} companies)"
        if peer_set.members else "no peer set available"
    )

    return [
        _p(row["company_name"], st["title"]),
        _p(f"{ctx['company_id']}  |  {row['broad_sector']} - {row['sub_sector']}  |  "
           f"{row['market_cap_category']}", st["subtitle"]),
        _p(f"Latest fiscal year: {health.as_of_year or 'n/a'}  |  Peer set: {peer_text}  |  "
           f"Generated: {ctx['generated_on']}", st["subtitle"]),
        Spacer(1, 6),
    ]


def _section_snapshot(ctx, st):
    row = ctx["row"]

    kpis = [
        ("Sales", _crore(row.get("sales"))),
        ("Net profit", _crore(row.get("net_profit"))),
        ("Return on equity", _num(row.get("roe_pct"), 1, "%")),
        ("Net profit margin", _num(row.get("net_margin_pct"), 1, "%")),
        ("Debt-to-equity", _num(row.get("debt_to_equity"), 2, "x")),
        ("Revenue CAGR", _num(row.get("revenue_cagr_pct"), 1, "%")),
        ("P/E ratio", _num(row.get("pe_ratio"), 1, "x")),
        ("Market cap", _crore(row.get("market_cap_crore"))),
    ]

    cells = [
        [[_p(v, st["kpi_value"]), _p(k, st["kpi_label"])] for k, v in kpis[:4]],
        [[_p(v, st["kpi_value"]), _p(k, st["kpi_label"])] for k, v in kpis[4:]],
    ]

    w = CONTENT_W / 4
    t = Table(cells, colWidths=[w] * 4)
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, GRID),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    return [_p("1. Snapshot", st["h1"]), t]


def _section_health(ctx, st):
    health: HealthScore = ctx["health"]
    out = [_p("2. Financial health score", st["h1"])]

    score_text = _num(health.score, 1) if health.score is not None else "N/A"
    gc = _grade_color(health.grade)

    rank = ctx["league_rank"]
    rank_text = f"Ranked {rank[0]} of {rank[1]} companies by score" if rank else "Not ranked (score withheld)"

    left = [
        Paragraph(f'<font color="{gc.hexval()}">{escape(score_text)}</font>', st["score"]),
        _p(f"Grade {health.grade} - {health.grade_label}", st["kpi_value"]),
        _p(f"out of 100  |  data coverage {health.data_coverage_pct:.0f}%", st["kpi_label"]),
        _p(rank_text, st["kpi_label"]),
    ]

    pillar_rows = [[_p("Pillar", st["cell_head"]), _p("Score (0-100)", st["cell_head"]),
                    _p("Weight used", st["cell_head"]), _p("Points added", st["cell_head"])]]
    for p in health.pillars.itertuples():
        if p.status == "not_applicable":
            pillar_rows.append([_p(p.pillar, st["cell"]), _p("n/a", st["cell"]),
                                _p("not applicable", st["cell"]), _p("-", st["cell"])])
        elif p.status == "missing":
            pillar_rows.append([_p(p.pillar, st["cell"]), _p("no data", st["cell"]),
                                _p("0%", st["cell"]), _p("0.0", st["cell"])])
        else:
            pillar_rows.append([_p(p.pillar, st["cell"]), _p(_num(p.pillar_score, 0), st["cell"]),
                                _p(f"{p.effective_weight:.1f}%", st["cell"]),
                                _p(f"{p.contribution:.1f}", st["cell"])])

    right = _table(pillar_rows, [34 * mm, 24 * mm, 26 * mm, 24 * mm])

    box = Table([[left, right]], colWidths=[CONTENT_W * 0.36, CONTENT_W * 0.64])
    box.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                             ("BOX", (0, 0), (-1, -1), 0.5, GRID)]))
    out += [box, Spacer(1, 6)]

    # ---- component table ---------------------------------------------------
    out.append(_p("How the score is built", st["h2"]))
    rows = [[_p(h, st["cell_head"]) for h in
             ("Metric", "Value", "Points", "Nominal weight", "Weight used", "Contribution", "Note")]]

    for r in health.components.itertuples():
        if r.status == "not_applicable":
            value, points, used, contrib = "n/a", "n/a", "-", "-"
        elif r.status == "missing":
            value, points, used, contrib = _num(r.value, 2, r.unit if r.unit == "%" else r.unit), "-", "0%", "0.0"
            value = "n/a"
        else:
            value = _num(r.value, 2, r.unit) if not pd.isna(r.value) else "none reported"
            points = _num(r.points, 0)
            used = f"{r.effective_weight:.1f}%"
            contrib = f"{r.contribution:.1f}"
        rows.append([
            _p(r.label, st["cell"]), _p(value, st["cell"]), _p(points, st["cell"]),
            _p(f"{r.nominal_weight:g}", st["cell"]), _p(used, st["cell"]), _p(contrib, st["cell"]),
            _p(r.note, st["small_grey"]),
        ])

    rows.append([_p("Total", st["cell"]), "", "", _p("100", st["cell"]), _p("100%", st["cell"]),
                 _p(score_text, st["cell"]), _p("Sum of the contributions above.", st["small_grey"])])

    out.append(_table(
        rows,
        [30 * mm, 20 * mm, 12 * mm, 16 * mm, 16 * mm, 22 * mm, CONTENT_W - 116 * mm],
        extra=[("FONTNAME", (0, len(rows) - 1), (-1, len(rows) - 1), "Helvetica-Bold"),
               ("LINEABOVE", (0, len(rows) - 1), (-1, len(rows) - 1), 0.8, INK)],
    ))
    out.append(Spacer(1, 4))

    for title, items in (("Strengths", health.strengths), ("Concerns", health.concerns),
                         ("Caveats", health.caveats)):
        if items:
            out.append(_p(title, st["h2"]))
            for item in items:
                out.append(Paragraph(escape(item), st["bullet"], bulletText="-"))

    chart = chart_metric_points(health)
    if chart:
        out += [Spacer(1, 4), chart]

    return out


def _section_trend(ctx, st):
    chart = chart_trend(ctx["trend"])
    out = [_p("3. Sales and profit trend", st["h1"])]

    if chart is None:
        out.append(_p("No annual profit & loss history is available.", st["body"]))
    else:
        out.append(chart)

    return [KeepTogether(out)]


def _section_peers(ctx, st):
    peer_set, bench = ctx["peer_set"], ctx["benchmark"]
    out = [_p("4. Peer benchmarking", st["h1"])]

    if not peer_set.members:
        out.append(_p(f"No benchmark available: {peer_set.note or 'peer set too small'}.", st["body"]))
        return out

    others = [m for m in peer_set.members if m != ctx["company_id"]]
    out.append(_p(
        f"Compared with {len(others)} peers in the {peer_set.basis} '{peer_set.group_name}': "
        + ", ".join(others[:14]) + (" ..." if len(others) > 14 else "") + ".",
        st["body"],
    ))
    if peer_set.note:
        out.append(_p(peer_set.note, st["small_grey"]))
    out.append(Spacer(1, 4))

    rows = [[_p(h, st["cell_head"]) for h in
             ("Metric", "Company", "Peer median", "Difference", "Percentile", "Rank", "Verdict")]]

    for r in bench.itertuples():
        if pd.isna(r.value) and not r.note:
            continue
        if r.note.startswith("Not applicable"):
            rows.append([_p(r.label, st["cell"]), _p("n/a", st["cell"]), _p("n/a", st["cell"]),
                         _p("-", st["cell"]), _p("-", st["cell"]), _p("-", st["cell"]),
                         _p("not applicable", st["cell"])])
            continue
        unit = "" if r.unit == "pts" else r.unit
        rank = f"{int(r.rank)} of {int(r.n)}" if not pd.isna(r.rank) else "-"
        rows.append([
            _p(r.label, st["cell"]), _p(_num(r.value, 2, unit), st["cell"]),
            _p(_num(r.peer_median, 2, unit), st["cell"]),
            _p(_num(r.delta, 2, unit), st["cell"]),
            _p(_num(r.percentile, 0), st["cell"]), _p(rank, st["cell"]),
            _p(r.verdict if r.verdict != "n/a" else (r.note or "n/a"), st["cell"]),
        ])

    out.append(_table(rows, [38 * mm, 22 * mm, 22 * mm, 22 * mm, 20 * mm, 18 * mm, CONTENT_W - 142 * mm]))
    out.append(_p(
        "Percentile = share of other peers the company beats (100 = best; for debt-to-equity "
        "lower is better). P/E is shown for context and is not ranked.", st["small_grey"]))

    chart = chart_percentiles(bench)
    if chart:
        out += [Spacer(1, 4), chart]

    return out


def _section_quality(ctx, st):
    rel = ctx["reliability"]
    out = [_p("5. Data-quality warnings", st["h1"])]

    colour = {"High": GREEN, "Medium": AMBER, "Low": RED}[rel["rating"]]
    out.append(Paragraph(
        f'Data reliability: <font color="{colour.hexval()}"><b>{rel["rating"]}</b></font> '
        f'({rel["errors"]} errors, {rel["warnings"]} warnings in the most recent '
        f'{RECENT_YEARS_FOR_WARNINGS} fiscal years and any undated checks). '
        "Rating rules: Low = at least one error, Medium = at least one warning, High = none.",
        st["body"],
    ))
    out.append(Spacer(1, 3))

    if ctx["warnings"]:
        for line in ctx["warnings"]:
            out.append(Paragraph(escape(line), st["bullet"], bulletText="-"))
    else:
        out.append(_p("No data-quality errors or warnings were found for this company.", st["body"]))

    return out


def _section_methodology(ctx, st):
    out = [_p("6. Methodology", st["h1"])]

    out.append(_p(
        "All figures are taken from the latest full fiscal year in the project database "
        "(db/nifty100.db). Half-year rows, TTM rows and rows with malformed period labels are "
        "excluded; duplicate rows describing the same fiscal year are collapsed.", st["body"]))

    out.append(_p("Indicator formulas", st["h2"]))
    formulas = [
        ("Return on equity", "net profit / (equity capital + reserves) x 100"),
        ("Net profit margin", "net profit / sales x 100"),
        ("Operating margin", "operating profit / sales x 100"),
        ("Debt-to-equity", "borrowings / (equity capital + reserves)"),
        ("Interest coverage", "(profit before tax + interest) / interest"),
        ("Revenue / profit CAGR", "(end / start)^(1 / years) - 1 over up to 5 years (minimum 3); "
                                  "profit CAGR only when both ends are positive"),
        ("Cash conversion", "cash from operations / net profit (only when profit is positive)"),
    ]
    rows = [[_p("Indicator", st["cell_head"]), _p("Formula", st["cell_head"])]]
    rows += [[_p(a, st["cell"]), _p(b, st["cell"])] for a, b in formulas]
    out.append(_table(rows, [42 * mm, CONTENT_W - 42 * mm]))

    out.append(_p("Scoring thresholds and weights", st["h2"]))
    rows = [[_p(h, st["cell_head"]) for h in ("Pillar", "Metric", "0 points at", "100 points at", "Weight")]]
    for m in METRICS:
        rows.append([_p(m.pillar, st["cell"]), _p(m.label, st["cell"]),
                     _p(f"{m.zero_at:g}{m.unit}", st["cell"]), _p(f"{m.full_at:g}{m.unit}", st["cell"]),
                     _p(f"{m.weight:g}", st["cell"])])
    out.append(_table(rows, [30 * mm, 52 * mm, 28 * mm, 28 * mm, CONTENT_W - 138 * mm]))

    bands = ", ".join(f"{g} ({lo:g}+, {label})" for lo, g, label in GRADE_BANDS)
    for text in (
        "Points between the two thresholds are interpolated in a straight line and clipped to 0-100. "
        f"Grades: {bands}.",
        "A missing metric, or one excluded because the computed value is outside a plausible range "
        "(a sign of bad source data), is dropped and the remaining weights are re-scaled to 100. "
        f"If less than {MIN_COVERAGE_PCT:.0f}% of the applicable weight has data, the score is withheld.",
        "Banks, NBFCs and insurers are not scored on leverage, interest coverage, operating margin or "
        "cash conversion, because those ratios are not comparable with industrial companies. Their score "
        "rests on fewer metrics, so compare them with their own peer group.",
        "Peer set: the curated peer group from the database if it has at least 3 members, otherwise the "
        "broad sector. Percentile is the share of the other peers the company beats, with ties counted "
        "half; interest coverage is capped at 100x for ranking.",
        "Data reliability is derived from the data-quality monitor: missing values, duplicate periods, "
        "inconsistent period labels and implausible metrics.",
        DISCLAIMER,
    ):
        out.append(Paragraph(escape(text), st["bullet"], bulletText="-"))

    return out


# =====================================================================
# Rendering
# =====================================================================

def render_report(ctx: dict, destination: Union[str, Path, io.BytesIO], compress: bool = True) -> None:
    """Write the PDF for a prepared context to a path or buffer."""

    st = _styles()
    name = str(ctx["row"]["company_name"])

    doc = SimpleDocTemplate(
        destination if isinstance(destination, io.BytesIO) else str(destination),
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=14 * mm, bottomMargin=20 * mm,
        title=f"{name} - Research report",
        author="NIFTY 100 Financial Intelligence Platform",
        subject="Explainable financial analytics, peer benchmarking and data quality",
        pageCompression=1 if compress else 0,
    )

    story: List = []
    story += _section_header(ctx, st)
    story += _section_snapshot(ctx, st)
    story += _section_health(ctx, st)
    story += _section_trend(ctx, st)
    story += _section_peers(ctx, st)
    story += _section_quality(ctx, st)
    story += _section_methodology(ctx, st)

    footer = _footer(name)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def generate_report_bytes(company_id: str, bundle: Optional[AnalyticsBundle] = None,
                          compress: bool = True) -> bytes:
    ctx = build_report_context(company_id, bundle)
    buf = io.BytesIO()
    render_report(ctx, buf, compress=compress)
    return buf.getvalue()


def generate_research_report(company_id: str, output_dir: Optional[Union[str, Path]] = None,
                             bundle: Optional[AnalyticsBundle] = None) -> Path:
    out_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    ctx = build_report_context(company_id, bundle)
    safe = str(company_id).replace("&", "and").replace("/", "_")
    path = out_dir / f"{safe}_research_report.pdf"
    render_report(ctx, path)

    return path


def generate_all(output_dir: Optional[Union[str, Path]] = None,
                 bundle: Optional[AnalyticsBundle] = None) -> List[Path]:
    bundle = bundle or get_bundle()
    return [generate_research_report(cid, output_dir, bundle) for cid in bundle.company_ids()]


def main(argv: List[str]) -> None:
    if not argv:
        print(__doc__)
        return

    bundle = get_bundle()

    if argv == ["--all"]:
        paths = generate_all(bundle=bundle)
        print(f"Generated {len(paths)} reports in {OUTPUT_DIR}")
        return

    for cid in argv:
        print(generate_research_report(cid, bundle=bundle))


if __name__ == "__main__":
    main(sys.argv[1:])
