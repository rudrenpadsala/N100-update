"""
Shared design system for the N100 Analytics dashboard.

Layout : horizontal - a navy header with the page menu across the top
         (no left sidebar menu). Page-specific filters that pages put in
         st.sidebar still work and appear in a slim white sidebar.
Palette: white, navy blue, blue and dark brown only (plus pale tints of
         the blue for borders / zebra rows, and red/amber/green kept
         purely as status colours in charts).

Public API (unchanged, so no page needs editing):
    apply_global_theme()   -> inject CSS, register the Plotly colour theme
    render_sidebar_nav()   -> render the horizontal menu, return page key
    page_header()          -> page title + subtitle
    metric_card()          -> KPI card
    style_plot()           -> apply the palette to a Plotly figure
"""

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# =====================================================
# 1. Colour palette  (edit here to re-theme everything)
# =====================================================
WHITE = "#FFFFFF"
NAVY = "#0B1F4B"          # headers, text, primary buttons
BLUE = "#1E63D6"          # links, highlights, charts
BROWN = "#4B2E1E"         # dark brown accent
BLUE_SOFT = "#EAF1FD"     # pale tint of blue: card / zebra backgrounds
BORDER = "#D3DEF2"        # pale blue-grey borders
MUTED = "#5B6B8C"         # secondary text
BLUE_LIGHT = "#6F9BE8"    # lighter blue for extra chart series
BROWN_LIGHT = "#8A5A3C"   # lighter brown for extra chart series

# Kept names used elsewhere in the code base
PRIMARY = BLUE
SECONDARY = NAVY
DEEP = NAVY
LAVENDER = BLUE_LIGHT
ACCENT = BROWN

# Status colours (only for good / warning / bad meaning)
SUCCESS = "#10B981"
WARNING = "#F59E0B"
ERROR = "#EF4444"

CHART_COLORS = [NAVY, BLUE, BROWN, BLUE_LIGHT, BROWN_LIGHT, "#9DB4DD"]

# Plotly: every chart in the app (including px.* charts) uses this palette.
pio.templates["n100"] = go.layout.Template(
    layout=dict(
        colorway=CHART_COLORS,
        font=dict(family="Inter, sans-serif", color=NAVY),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER),
        title=dict(font=dict(color=NAVY)),
    )
)
pio.templates.default = "plotly_white+n100"


def apply_global_theme() -> None:
    """Inject the shared CSS design system into the app."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {{
            --navy: {NAVY};
            --blue: {BLUE};
            --brown: {BROWN};
            --soft: {BLUE_SOFT};
            --border: {BORDER};
            --muted: {MUTED};
        }}

        html, body, [class*="stAppViewContainer"], .stApp {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: {WHITE} !important;
            color: {NAVY} !important;
        }}

        /* hide Streamlit's own top bar so the navy header is the top of the page */
        header[data-testid="stHeader"] {{ background: transparent !important; height: 0 !important; }}
        div[data-testid="stToolbar"], div[data-testid="stDecoration"] {{ display: none !important; }}

        .main .block-container, .block-container {{
            padding-top: 1rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }}

        p, span, label, li, .stMarkdown {{ color: {NAVY}; }}
        .stCaption, [data-testid="stCaptionContainer"], small {{ color: {MUTED} !important; }}

        /* =====================================================
           Horizontal header + menu
           ===================================================== */
        .st-key-n100_nav {{
            background: {NAVY};
            border-radius: 16px;
            padding: 14px 20px 10px 20px;
            margin-bottom: 1.4rem;
            border-bottom: 4px solid {BROWN};
            box-shadow: 0 8px 24px rgba(11, 31, 75, 0.18);
        }}

        .n100-brand {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding-bottom: 6px;
        }}
        .n100-brand-left {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .n100-brand-logo {{ font-size: 1.7rem; line-height: 1; }}
        .n100-brand-title {{
            font-weight: 800; font-size: 1.25rem; color: {WHITE} !important; letter-spacing: -0.01em;
        }}
        .n100-brand-sub {{
            font-size: 0.7rem; font-weight: 600; color: {BLUE_LIGHT} !important;
            text-transform: uppercase; letter-spacing: 0.08em;
        }}

        /* =====================================================
           Horizontally Scrolling Stock Ticker (Angel One SmartAPI)
           ===================================================== */
        .n100-ticker-bar {{
            margin: 8px 0 12px 0;
            overflow: hidden;
            position: relative;
            background: rgba(4, 15, 38, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 10px;
            padding: 7px 0;
            box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.3);
        }}
        .n100-ticker-bar:hover .n100-ticker-track {{
            animation-play-state: paused;
        }}
        .n100-ticker-track {{
            display: inline-flex;
            white-space: nowrap;
            animation: n100-marquee 130s linear infinite;
            will-change: transform;
        }}
        @keyframes n100-marquee {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}
        .n100-ticker-item {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 4px 11px;
            margin: 0 4px;
            border-radius: 7px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.10);
            text-decoration: none !important;
            transition: all 0.15s ease;
            cursor: pointer;
        }}
        .n100-ticker-item:hover {{
            background: rgba(30, 99, 214, 0.6) !important;
            border-color: {BLUE_LIGHT} !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        .n100-ticker-sym {{
            color: {WHITE} !important;
            font-weight: 800;
            font-size: 0.84rem;
            letter-spacing: 0.02em;
        }}
        .n100-ticker-price {{
            color: #E2E8F0 !important;
            font-weight: 600;
            font-size: 0.82rem;
        }}
        .n100-ticker-chg-pos {{
            color: #10B981 !important;
            font-weight: 700;
            font-size: 0.80rem;
        }}
        .n100-ticker-chg-neg {{
            color: #EF4444 !important;
            font-weight: 700;
            font-size: 0.80rem;
        }}
        .n100-ticker-status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        /* menu row: works for both old (baseweb) and new (stRadioOption) Streamlit */
        .st-key-n100_nav [role="radiogroup"] {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 6px !important;
            align-items: center !important;
            margin-top: 4px !important;
        }}

        .st-key-n100_nav label[data-testid="stRadioOption"],
        .st-key-n100_nav [data-testid="stRadioOption"],
        .st-key-n100_nav label[data-baseweb="radio"] {{
            background: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.16) !important;
            border-radius: 8px !important;
            padding: 6px 14px !important;
            margin: 0 !important;
            cursor: pointer !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: background 0.15s ease, border-color 0.15s ease !important;
        }}

        /* Ensure inner flex containers are visible and inline-flex */
        .st-key-n100_nav [data-testid="stRadioOption"] > div,
        .st-key-n100_nav [data-testid="stRadioOption"] > div > div {{
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            visibility: visible !important;
            opacity: 1 !important;
        }}

        /* Guarantee button label text is ALWAYS visible, white, and bold */
        .st-key-n100_nav [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"],
        .st-key-n100_nav [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] p,
        .st-key-n100_nav [data-testid="stRadioOption"] [data-testid="stMarkdownContainer"] span,
        .st-key-n100_nav [data-testid="stRadioOption"] p,
        .st-key-n100_nav [data-testid="stRadioOption"] span,
        .st-key-n100_nav label[data-baseweb="radio"] [data-testid="stMarkdownContainer"],
        .st-key-n100_nav label[data-baseweb="radio"] [data-testid="stMarkdownContainer"] p,
        .st-key-n100_nav label[data-baseweb="radio"] p,
        .st-key-n100_nav label[data-baseweb="radio"] span {{
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 0.85rem !important;
            visibility: visible !important;
            opacity: 1 !important;
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.3 !important;
            white-space: nowrap !important;
            display: inline-block !important;
        }}

        /* Hide the native radio circle cleanly without ever hiding the text container */
        .st-key-n100_nav input[type="radio"] {{
            display: none !important;
            width: 0 !important;
            height: 0 !important;
        }}
        .st-key-n100_nav [data-testid="stRadioOption"] div:has(+ [data-testid="stMarkdownContainer"]) {{
            display: none !important;
        }}
        .st-key-n100_nav label[data-baseweb="radio"] > div:first-child:not(:has(p)) {{
            display: none !important;
        }}

        .st-key-n100_nav [data-testid="stRadioOption"]:hover,
        .st-key-n100_nav label[data-testid="stRadioOption"]:hover,
        .st-key-n100_nav label[data-baseweb="radio"]:hover {{
            background: rgba(30, 99, 214, 0.55) !important;
            border-color: {BLUE_LIGHT} !important;
        }}

        .st-key-n100_nav [data-testid="stRadioOption"]:has(input:checked),
        .st-key-n100_nav [data-testid="stRadioOption"][data-selected="true"],
        .st-key-n100_nav label[data-testid="stRadioOption"]:has(input:checked),
        .st-key-n100_nav label[data-testid="stRadioOption"][data-selected="true"],
        .st-key-n100_nav label[data-baseweb="radio"]:has(input:checked) {{
            background: {BLUE} !important;
            border-color: {WHITE} !important;
            box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.25) !important;
        }}

        /* =====================================================
           Headings
           ===================================================== */
        h1 {{ color: {NAVY} !important; font-weight: 800 !important; letter-spacing: -0.02em; }}
        h2, h3 {{
            color: {NAVY} !important;
            font-weight: 700 !important;
            border-left: 4px solid {BROWN};
            padding-left: 0.7rem;
        }}
        h4, h5 {{ color: {NAVY} !important; font-weight: 700 !important; }}
        .n100-page-subtitle {{
            color: {MUTED} !important; font-size: 0.98rem; margin-top: -0.4rem;
            margin-bottom: 1.3rem; font-weight: 500;
        }}

        /* =====================================================
           Cards
           ===================================================== */
        .glass-card-3d,
        div[data-testid="stMetric"] {{
            background: {WHITE} !important;
            border: 1px solid {BORDER} !important;
            border-left: 5px solid {BLUE} !important;
            border-radius: 14px !important;
            padding: 1rem 1.2rem !important;
            box-shadow: 0 4px 14px rgba(11, 31, 75, 0.08) !important;
            transition: box-shadow 0.2s ease, border-color 0.2s ease;
        }}
        .glass-card-3d:hover,
        div[data-testid="stMetric"]:hover {{
            border-left-color: {BROWN} !important;
            box-shadow: 0 8px 22px rgba(11, 31, 75, 0.16) !important;
        }}
        .glass-card-title,
        div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] * {{
            color: {MUTED} !important; font-size: 0.78rem !important; font-weight: 700 !important;
            text-transform: uppercase; letter-spacing: 0.06em;
        }}
        .glass-card-value,
        div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * {{
            color: {NAVY} !important; font-size: 1.7rem !important; font-weight: 800 !important;
            letter-spacing: -0.02em;
        }}
        .glass-card-value {{ margin-top: 4px; }}

        /* =====================================================
           Inputs
           ===================================================== */
        div[data-testid="stSelectbox"] label, div[data-testid="stMultiSelect"] label,
        div[data-testid="stTextInput"] label, div[data-testid="stNumberInput"] label,
        div[data-testid="stDateInput"] label, div[data-testid="stSlider"] label {{
            color: {NAVY} !important; font-weight: 700; font-size: 0.8rem;
            text-transform: uppercase; letter-spacing: 0.05em;
        }}
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {{
            background: {WHITE} !important;
            border: 1px solid {BORDER} !important;
            border-radius: 10px !important;
            color: {NAVY} !important;
        }}
        div[data-baseweb="select"] span, div[data-baseweb="input"] input {{
            color: {NAVY} !important; font-weight: 600 !important;
        }}
        div[data-baseweb="select"]:hover > div, div[data-baseweb="input"]:hover > div {{
            border-color: {BLUE} !important;
        }}
        div[data-baseweb="select"]:focus-within > div, div[data-baseweb="input"]:focus-within > div {{
            border-color: {NAVY} !important; box-shadow: 0 0 0 2px rgba(30, 99, 214, 0.25) !important;
        }}
        ul[data-baseweb="menu"] {{ background: {WHITE} !important; border: 1px solid {BORDER} !important; border-radius: 10px !important; }}
        li[data-baseweb="option"] {{ color: {NAVY} !important; }}
        li[data-baseweb="option"]:hover {{ background: {BLUE_SOFT} !important; }}
        span[data-baseweb="tag"] {{ background: {NAVY} !important; border-radius: 8px !important; }}
        span[data-baseweb="tag"] span {{ color: {WHITE} !important; font-weight: 600 !important; }}
        div[data-testid="stSlider"] div[role="slider"] {{ background-color: {BROWN} !important; border: 2px solid {WHITE} !important; }}
        div[data-testid="stSlider"] div[data-baseweb="slider"] div {{ background-color: {BLUE} !important; }}

        /* =====================================================
           Charts, tables
           ===================================================== */
        div[data-testid="stPlotlyChart"] {{
            background: {WHITE} !important;
            border: 1px solid {BORDER};
            border-radius: 14px;
            padding: 0.8rem;
            box-shadow: 0 4px 14px rgba(11, 31, 75, 0.06);
        }}
        div[data-testid="stDataFrame"] {{
            border: 1px solid {BORDER};
            border-radius: 12px;
            overflow: hidden;
        }}
        div[data-testid="stExpander"] {{ border: 1px solid {BORDER} !important; border-radius: 12px !important; background: {WHITE}; }}
        div[data-testid="stExpander"] summary {{ color: {NAVY} !important; font-weight: 600; }}
        div[data-testid="stAlert"] {{ border-radius: 12px; }}

        /* =====================================================
           Buttons and tabs
           ===================================================== */
        div[data-testid="stDownloadButton"] button, div[data-testid="stButton"] button {{
            background: {NAVY}; color: {WHITE} !important; border: 1px solid {NAVY};
            border-radius: 10px; font-weight: 700; padding: 0.55rem 1.3rem;
            transition: background 0.2s ease, border-color 0.2s ease;
        }}
        div[data-testid="stDownloadButton"] button:hover, div[data-testid="stButton"] button:hover {{
            background: {BROWN}; border-color: {BROWN}; color: {WHITE} !important;
        }}
        div[data-testid="stDownloadButton"] button p, div[data-testid="stButton"] button p {{ color: {WHITE} !important; }}

        button[data-baseweb="tab"] {{ font-weight: 600; color: {MUTED} !important; padding: 0.7rem 1.2rem !important; }}
        button[data-baseweb="tab"][aria-selected="true"] {{ color: {NAVY} !important; }}
        button[data-baseweb="tab"]:hover {{ color: {BLUE} !important; }}
        div[data-baseweb="tab-highlight"] {{ background: {BROWN} !important; height: 3px !important; }}
        div[data-baseweb="tab-border"] {{ background: {BORDER} !important; }}

        hr {{ border: none; height: 1px; background: {BORDER}; margin: 1.3rem 0; }}

        /* =====================================================
           Slim white sidebar (only appears if a page puts filters in it)
           ===================================================== */
        section[data-testid="stSidebar"] {{
            background: {BLUE_SOFT} !important;
            border-right: 1px solid {BORDER} !important;
        }}
        section[data-testid="stSidebar"] * {{ color: {NAVY}; }}
        /* no filters on this page -> hide the empty sidebar */
        section[data-testid="stSidebar"]:not(:has([data-testid="stSidebarUserContent"] [data-testid="stElementContainer"])) {{
            display: none !important;
        }}
        div[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =====================================================
# Helper functions
# =====================================================
def page_header(icon: str, title: str, subtitle: str | None = None) -> None:
    """Render a consistent page title and subtitle."""
    st.title(f"{icon} {title}")
    if subtitle:
        st.markdown(
            f'<div class="n100-page-subtitle">{subtitle}</div>',
            unsafe_allow_html=True,
        )


def metric_card(title: str, value: str, change: str | None = None, is_positive: bool = True) -> None:
    """KPI card: white, navy value, blue left edge."""
    change_html = ""
    if change:
        color = SUCCESS if is_positive else ERROR
        arrow = "▲" if is_positive else "▼"
        change_html = (
            f'<div style="color: {color}; font-weight: 700; font-size: 0.85rem; '
            f'margin-top: 6px;">{arrow} {change}</div>'
        )

    st.markdown(
        f"""
        <div class="glass-card-3d">
            <div class="glass-card-title">{title}</div>
            <div class="glass-card-value">{value}</div>
            {change_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_plot(fig: go.Figure) -> go.Figure:
    """Apply the navy / blue / brown palette to a Plotly figure."""

    for i, trace in enumerate(fig.data):
        color = CHART_COLORS[i % len(CHART_COLORS)]

        if trace.type == "bar":
            trace.marker.color = color
            trace.marker.line = dict(color=WHITE, width=1)

        elif trace.type in ("scatter", "lines"):
            if hasattr(trace, "line") and trace.line.color is None:
                trace.line.color = color
                trace.line.width = 3

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=NAVY),
        margin=dict(l=25, r=25, t=45, b=25),
        colorway=CHART_COLORS,
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, showgrid=True),
        yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, showgrid=True),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER, borderwidth=1),
    )
    return fig


def render_sidebar_nav(pages: dict) -> str:
    """
    Render the horizontal header + menu with live Angel One stock ticker
    and return the selected page key.
    """
    from utils.smartapi_client import get_smartapi_client

    options = list(pages.keys())
    labels = {key: f"{meta['icon']}  {meta['label']}" for key, meta in pages.items()}

    # Fetch quotes for ticker (cached and rate-limit safe)
    client = get_smartapi_client()
    quotes, meta = client.get_all_quotes()

    # Build ticker items for all 92 companies
    ticker_items = []
    for cid in sorted(quotes.keys()):
        q = quotes[cid]
        sym = q.get("company_id", cid)
        price = q.get("price", 0.0)
        chg = q.get("change", 0.0)
        pct = q.get("pct_change", 0.0)
        is_pos = chg >= 0
        cls = "n100-ticker-chg-pos" if is_pos else "n100-ticker-chg-neg"
        arrow = "▲" if is_pos else "▼"
        sign = "+" if is_pos else ""
        c_title = q.get("company_name", sym)
        item_html = (
            f'<a href="?page=live_market&symbol={sym}" target="_self" class="n100-ticker-item" title="{c_title}">'
            f'<span class="n100-ticker-sym">{sym}</span>'
            f'<span class="n100-ticker-price">₹{price:,.2f}</span>'
            f'<span class="{cls}">{arrow} {sign}{chg:,.2f} ({sign}{pct:.2f}%)</span>'
            f'</a>'
        )
        ticker_items.append(item_html)

    track_single = "".join(ticker_items)
    # Duplicate track for continuous loop
    full_track = track_single + track_single

    # Determine status badge - clearly label source and date, never mislabel as real-time
    latest_dt = meta.get("latest_trading_date", "2026-10-29")
    status_badge = (
        f'<span class="n100-ticker-status-badge" style="background: rgba(16, 185, 129, 0.18); color: #10B981; border: 1px solid #10B981;">'
        f'● NSE MARKET DATA ({latest_dt})</span>'
    )

    with st.container(key="n100_nav"):
        st.markdown(
            f"""
            <div class="n100-brand">
                <div class="n100-brand-left">
                    <div class="n100-brand-logo">📊</div>
                    <div>
                        <div class="n100-brand-title">N100 Analytics</div>
                        <div class="n100-brand-sub">Nifty 100 Financial Intelligence</div>
                    </div>
                </div>
                <div>
                    {status_badge}
                </div>
            </div>
            <div class="n100-ticker-bar">
                <div class="n100-ticker-track">
                    {full_track}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        choice_label = st.radio(
            "Navigation",
            options=[labels[key] for key in options],
            horizontal=True,
            label_visibility="collapsed",
            key="n100_nav_radio",
        )

    for key in options:
        if labels[key] == choice_label:
            return key
    return options[0]
