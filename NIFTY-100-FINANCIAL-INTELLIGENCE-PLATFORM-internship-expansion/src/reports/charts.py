"""
charts.py

Sprint 5
Day 33 support module

Matplotlib chart generation for PDF reports (tearsheets, sector
reports, portfolio summary). Charts are rendered to PNG in-memory
and returned as ReportLab Image-ready BytesIO buffers.

Colors match the existing Streamlit dashboard brand palette
(src/dashboard/utils/theme.py) so the PDF outputs feel consistent
with the rest of the platform.
"""

import io

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

PRIMARY = "#6C63FF"
SECONDARY = "#FF6B9D"
ACCENT = "#FFB86C"
SUCCESS = "#198754"
DANGER = "#DC3545"
GREY = "#8A8A99"

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.edgecolor"] = "#DDDDDD"
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.color"] = "#EEEEEE"
plt.rcParams["grid.linewidth"] = 0.6


def _empty_chart(title, figsize=(5.2, 2.6)):
    """Placeholder chart used when a company has no data for a metric."""

    fig, ax = plt.subplots(figsize=figsize, dpi=170)
    ax.text(
        0.5, 0.5, "No data available",
        ha="center", va="center", fontsize=11, color=GREY
    )
    ax.set_title(title, fontsize=11, fontweight="bold", loc="left", color="#222222")
    ax.axis("off")
    return _to_buffer(fig)


def _to_buffer(fig):
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf


def _short_year(year_label):
    """'Mar 2024' -> '2024', 'Sep 2021' -> "S'21" kept compact for x-axis labels."""

    if year_label is None:
        return ""
    digits = "".join(ch for ch in str(year_label) if ch.isdigit())
    return digits[-4:] if len(digits) >= 4 else str(year_label)


def bar_line_chart(years, values, title, color=PRIMARY, unit="", figsize=(5.2, 2.6)):
    """Simple bar chart used for Revenue / Profit trends."""

    if values is None or len(values) == 0 or all(v is None for v in values):
        return _empty_chart(title, figsize)

    fig, ax = plt.subplots(figsize=figsize, dpi=170)

    labels = [_short_year(y) for y in years]
    ax.bar(labels, values, color=color, width=0.55, zorder=3)

    ax.set_title(title, fontsize=11, fontweight="bold", loc="left", color="#222222")
    ax.tick_params(axis="both", labelsize=8, colors="#555555")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.set_ylabel(unit, fontsize=8, color="#777777")

    return _to_buffer(fig)


def dual_line_chart(years, series_a, label_a, series_b, label_b, title,
                     color_a=PRIMARY, color_b=SECONDARY, unit="%", figsize=(5.2, 2.6)):
    """Two-line trend chart, used for ROE/ROCE and similar comparisons."""

    if (not series_a and not series_b) or (all(v is None for v in series_a) and all(v is None for v in series_b)):
        return _empty_chart(title, figsize)

    fig, ax = plt.subplots(figsize=figsize, dpi=170)

    labels = [_short_year(y) for y in years]

    if series_a and any(v is not None for v in series_a):
        ax.plot(labels, series_a, marker="o", markersize=3, linewidth=2,
                color=color_a, label=label_a, zorder=3)

    if series_b and any(v is not None for v in series_b):
        ax.plot(labels, series_b, marker="o", markersize=3, linewidth=2,
                color=color_b, label=label_b, zorder=3)

    ax.set_title(title, fontsize=11, fontweight="bold", loc="left", color="#222222")
    ax.tick_params(axis="both", labelsize=8, colors="#555555")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.set_ylabel(unit, fontsize=8, color="#777777")
    ax.legend(fontsize=7, frameon=False, loc="upper left")

    return _to_buffer(fig)


def stacked_balance_sheet_chart(years, assets, liabilities, title="Balance Sheet", figsize=(5.2, 2.6)):
    """Assets vs Liabilities grouped bar chart."""

    if not assets and not liabilities:
        return _empty_chart(title, figsize)

    fig, ax = plt.subplots(figsize=figsize, dpi=170)

    labels = [_short_year(y) for y in years]
    x = range(len(labels))
    width = 0.35

    ax.bar([i - width / 2 for i in x], assets, width, color=PRIMARY, label="Total Assets", zorder=3)
    ax.bar([i + width / 2 for i in x], liabilities, width, color=ACCENT, label="Total Liabilities", zorder=3)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_title(title, fontsize=11, fontweight="bold", loc="left", color="#222222")
    ax.tick_params(axis="both", labelsize=8, colors="#555555")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.set_ylabel("Rs. Cr", fontsize=8, color="#777777")
    ax.legend(fontsize=7, frameon=False, loc="upper left")

    return _to_buffer(fig)


def cashflow_chart(years, operating, investing, financing, title="Cash Flow", figsize=(5.2, 2.6)):
    """Grouped bar chart for CFO / CFI / CFF across years."""

    if not operating and not investing and not financing:
        return _empty_chart(title, figsize)

    fig, ax = plt.subplots(figsize=figsize, dpi=170)

    labels = [_short_year(y) for y in years]
    x = range(len(labels))
    width = 0.26

    ax.bar([i - width for i in x], operating, width, color=SUCCESS, label="Operating", zorder=3)
    ax.bar(list(x), investing, width, color=DANGER, label="Investing", zorder=3)
    ax.bar([i + width for i in x], financing, width, color=PRIMARY, label="Financing", zorder=3)

    ax.axhline(0, color="#AAAAAA", linewidth=0.8, zorder=2)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_title(title, fontsize=11, fontweight="bold", loc="left", color="#222222")
    ax.tick_params(axis="both", labelsize=8, colors="#555555")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.set_ylabel("Rs. Cr", fontsize=8, color="#777777")
    ax.legend(fontsize=7, frameon=False, loc="upper left")

    return _to_buffer(fig)


def sector_bar_chart(labels, values, title, color=PRIMARY, unit="", horizontal=True, figsize=(6.0, 3.6)):
    """Horizontal ranking bar chart, used in sector reports."""

    if values is None or len(values) == 0:
        return _empty_chart(title, figsize)

    fig, ax = plt.subplots(figsize=figsize, dpi=170)

    if horizontal:
        ax.barh(labels, values, color=color, zorder=3)
        ax.invert_yaxis()
    else:
        ax.bar(labels, values, color=color, zorder=3)

    ax.set_title(title, fontsize=12, fontweight="bold", loc="left", color="#222222")
    ax.tick_params(axis="both", labelsize=8, colors="#555555")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.set_xlabel(unit, fontsize=8, color="#777777")

    return _to_buffer(fig)


def pattern_pie_chart(labels, values, title="Capital Allocation Mix", figsize=(4.4, 4.0)):
    """Pie/donut chart used in sector and portfolio reports."""

    if not values:
        return _empty_chart(title, figsize)

    palette = [PRIMARY, SECONDARY, ACCENT, SUCCESS, DANGER, GREY, "#4A90D9"]
    colors = [palette[i % len(palette)] for i in range(len(labels))]

    fig, ax = plt.subplots(figsize=figsize, dpi=170)
    ax.pie(
        values, labels=labels, colors=colors, autopct="%1.0f%%",
        textprops={"fontsize": 8}, wedgeprops={"width": 0.42}
    )
    ax.set_title(title, fontsize=11, fontweight="bold", color="#222222")

    return _to_buffer(fig)
