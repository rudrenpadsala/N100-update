import streamlit as st

from pages import (
    home,
    live_market,
    rl_intelligence,
    profile,
    screener,
    peers,
    trends,
    sectors,
    capital,
    reports,
    health_benchmark,
    data_quality,
)
from utils.theme import apply_global_theme, render_sidebar_nav

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📈",
    layout="wide",
    # "auto": collapsed by default on narrow/mobile screens, expanded on
    # desktop. Using a hardcoded "expanded" forced the sidebar to open as
    # a full-screen overlay on phones every time the app loaded.
    initial_sidebar_state="auto",
)

# -----------------------------------------------------------------
# Hide Streamlit's auto-generated multipage navigation.
#
# Because `pages/` is a real package/folder, Streamlit automatically
# builds its own nav block at the top of the sidebar. That duplicates
# the custom render_sidebar_nav() below it, so we hide the built-in
# one and keep only our own themed nav.
# -----------------------------------------------------------------

st.markdown(
    """
    <style>
    /* Hide Streamlit multipage navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }

    /* Hide the divider below it */
    [data-testid="stSidebarNavSeparator"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Single, shared design system for every page (colors, cards, charts,
# tables, buttons, sidebar, etc.). Individual pages no longer inject
# their own CSS or call st.set_page_config().
apply_global_theme()

PAGES = {
    "home": {"label": "Home", "icon": "🏠", "func": home.show},
    "live_market": {"label": "Market Intelligence", "icon": "⚡", "func": live_market.show},
    "rl": {"label": "RL Intelligence", "icon": "🤖", "func": rl_intelligence.show},
    "profile": {"label": "Company Profile", "icon": "🏢", "func": profile.show},
    "screener": {"label": "Screener", "icon": "🔍", "func": screener.show},
    "peers": {"label": "Peer Comparison", "icon": "👥", "func": peers.show},
    "trends": {"label": "Trend Analysis", "icon": "📈", "func": trends.show},
    "sectors": {"label": "Sector Analysis", "icon": "🏭", "func": sectors.show},
    "capital": {"label": "Capital Allocation", "icon": "💰", "func": capital.show},
    "reports": {"label": "Annual Reports", "icon": "📄", "func": reports.show},
    # Internship expansion modules
    "health": {"label": "Health & Peer Benchmark", "icon": "🩺", "func": health_benchmark.show},
    "quality": {"label": "Data Quality", "icon": "🧪", "func": data_quality.show},
}

# Sync page routing and stock selection from URL query parameters (e.g. from ticker click)
query_params = st.query_params
if "page" in query_params and query_params["page"] in PAGES:
    target_page = query_params["page"]
    target_label = f"{PAGES[target_page]['icon']}  {PAGES[target_page]['label']}"
    if st.session_state.get("n100_nav_radio") != target_label:
        st.session_state["n100_nav_radio"] = target_label

if "symbol" in query_params:
    st.session_state["selected_ticker"] = query_params["symbol"]

selected_key = render_sidebar_nav(PAGES)
PAGES[selected_key]["func"]()