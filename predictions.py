"""La Liga Linea — Streamlit app entry point.

Run with:
    streamlit run predictions.py
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from os import path

import streamlit as st

# ── Page config — must be first Streamlit call ─────────────────────────────
st.set_page_config(
    page_title="La Liga Linea",
    page_icon="🇪🇸",
    layout="wide",
    initial_sidebar_state="expanded",
)

from footer import add_betting_oracle_footer  # noqa: E402
from themes import apply_theme  # noqa: E402
from utils import load_upcoming_fixtures, next_match_countdown  # noqa: E402

# Detect the browser clock through native Streamlit context.
_browser_timezone = getattr(st.context, "timezone", None)
try:
    _theme_hour = datetime.now(ZoneInfo(_browser_timezone)).hour if _browser_timezone else datetime.now().hour
except (ZoneInfoNotFoundError, ValueError):
    _theme_hour = datetime.now().hour
if not st.session_state.get("dark_mode_manual", False):
    st.session_state["dark_mode"] = not (6 <= _theme_hour < 20)

# ── Sidebar ────────────────────────────────────────────────────────────────
_logo = path.join("data_files", "logo.png")
if path.exists(_logo):
    st.sidebar.image(_logo, width=220)
else:
    st.sidebar.markdown("## 🇪🇸 La Liga Linea")

st.sidebar.markdown("**La Liga Predictions & Analysis**")
st.sidebar.divider()

# Next-match countdown
_fix_path = "data_files/upcoming_fixtures.csv"
if path.exists(_fix_path):
    _upcoming = load_upcoming_fixtures(_fix_path)
    _cd = next_match_countdown(_upcoming)
    if _cd:
        st.sidebar.info(_cd)

# Season selector — stored in session state so all pages can read it
_seasons = ["2026-27", "2025-26", "2024-25", "2023-24", "2022-23", "2021-22"]
if "selected_season" not in st.session_state:
    st.session_state["selected_season"] = _seasons[0]

st.session_state["selected_season"] = st.sidebar.selectbox(
    "Season",
    _seasons,
    index=_seasons.index(st.session_state.get("selected_season", _seasons[0])),
)

st.sidebar.divider()

# Night / Day toggle
_mode_label = "☀️ Switch to Day" if st.session_state["dark_mode"] else "🌙 Switch to Night"
if st.sidebar.button(_mode_label, width='stretch'):
    st.session_state["dark_mode"] = not st.session_state["dark_mode"]
    st.session_state["dark_mode_manual"] = True  # suppress auto-override for this session
    st.rerun()

apply_theme()

st.sidebar.divider()

st.sidebar.caption("Data: football-data.org · FBref · The Odds API")
st.sidebar.caption("© Betting Oracle")

# ── Navigation ─────────────────────────────────────────────────────────────
pg = st.navigation(
    {
        "⚽ La Liga": [
            st.Page(
                "pages/predictions_tab.py",
                title="Predictions",
                icon="🎯",
                default=True,
            ),
            st.Page("pages/fixtures.py",       title="Fixtures & Standings", icon="🗓️"),
            st.Page("pages/statistics.py",      title="Statistics",           icon="📊"),
            st.Page("pages/team_deep_dive.py",  title="Team Deep Dive",       icon="🔬"),
            st.Page("pages/raw_data.py",        title="Raw Data",             icon="📁"),
            st.Page("pages/pitchapi_match.py", title="Match analytics", icon=":material/analytics:", url_path="match-analytics"),
            st.Page("pages/pitchapi_team.py", title="Team analytics", icon=":material/shield:", url_path="team-analytics"),
            st.Page("pages/pitchapi_model.py", title="Feature validation", icon=":material/science:", url_path="feature-validation"),
        ],
        "💰 Betting": [
            st.Page("pages/markets.py",     title="Markets",    icon="📈"),
            st.Page("pages/best_bets.py",   title="Best Bets",  icon="💰"),
            st.Page("pages/performance.py", title="Performance", icon="📈"),
        ],
    }
)

pg.run()

add_betting_oracle_footer()
