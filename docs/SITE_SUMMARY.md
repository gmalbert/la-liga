> **AI Onboarding Guide** — See also `.github/copilot-instructions.md` for full coding conventions.

# La Liga Linea — Site Summary

## What This App Does

Streamlit multi-page app that predicts La Liga (Spain) match outcomes and surfaces betting market value. It trains a soft-voting ensemble classifier on 10 seasons of historical match data, compares model probabilities against live bookmaker odds, and renders predictions with edge percentages and confidence tiers.

## Quick Start

```bash
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1        # Windows
source .venv/bin/activate           # macOS/Linux

# 2. (Optional) Refresh data
python fetch_historical_csvs.py     # Download SP1.csv for 2015-16 → present
python fetch_upcoming_fixtures.py   # Fetch next scheduled PD fixtures
python fetch_odds.py                # Fetch live La Liga odds

# 3. Run the app
streamlit run predictions.py
```

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit ≥1.36 (`st.navigation` + `st.Page`) |
| ML | VotingClassifier: XGBoost×2, RF×1.5, GB×1, LR×0.5 (soft voting) |
| Data | pandas, NumPy |
| Visualization | Plotly Express |
| Scraping | requests, BeautifulSoup4, lxml |
| Config | python-dotenv (`.env` file) |
| PDF export | fpdf2 |

## Key Files

| File | Purpose |
|---|---|
| `predictions.py` | Entry point — `st.set_page_config`, sidebar, `st.navigation`, theme injection, auto day/night detection |
| `utils.py` | **All** shared functions: data loading, feature engineering, model training, display helpers |
| `pages/*.py` | Individual Streamlit pages — never call `st.set_page_config` here |
| `footer.py` | `add_betting_oracle_footer()` — called in `predictions.py` after `pg.run()` |
| `themes.py` | `apply_theme()` and `plotly_theme()` — called before `pg.run()` |
| `team_name_mapping.py` | `normalize_team_name()` / `normalize_dataframe_teams()` — always use when merging sources |
| `data_files/combined_historical_data.csv` | 10 seasons of SP1.csv from football-data.co.uk |
| `models/ensemble_model.pkl` | Trained VotingClassifier (auto-generated; delete to force retrain) |

## Data Flow

1. **Historical data**: `fetch_historical_csvs.py` downloads `SP1.csv` per season (football-data.co.uk) → `data_files/combined_historical_data.csv`
2. **Upcoming fixtures**: `fetch_upcoming_fixtures.py` hits football-data.org PD endpoint → `data_files/upcoming_fixtures.csv`
3. **Feature engineering**: `calculate_la_liga_features()` in `utils.py` — groupby rolling with `shift(1)` to prevent data leakage
4. **Training**: `VotingClassifier` trained in `utils.py` → saved to `models/ensemble_model.pkl`
5. **Live odds** (optional): `fetch_odds.py` → `data_files/raw/` → edge = model probability vs. implied probability
6. **UI**: Streamlit reads CSVs + loads model → renders predictions, value bets, Copa fixtures context

## Environment Variables

| Variable | Purpose | Required |
|---|---|---|
| `ODDS_API_KEY` | The Odds API — live La Liga odds (`soccer_spain_la_liga`) | Optional |
| `FOOTBALL_DATA_ORG_API_KEY` | football-data.org — upcoming PD fixtures | Optional |

## External APIs & Rate Limits

| API | Notes |
|---|---|
| football-data.co.uk | Static CSV download, no key needed; file is `SP1.csv` |
| football-data.org | Competition code `PD`; 10 req/min free tier |
| The Odds API | `soccer_spain_la_liga`; 500 req/month free tier |
| FBref (comp ID 12) | Scraped — rate-limit cautiously; used by `fetch_fbref_xg.py` |

## Critical Conventions

- **Never** call `st.set_page_config()` in `pages/*.py` — only in `predictions.py`
- **Always** use `render_table(df)` from `utils.py` instead of `st.dataframe()` directly (day-mode rendering fix)
- **Always** call `fig.update_layout(**plotly_theme())` on every Plotly figure
- **Always** use `shift(1)` before `.rolling(n).mean()` in feature engineering to prevent data leakage
- **Always** normalize team names via `team_name_mapping.py` before merging sources
- Target encoding: A=0, D=1, H=2 → `predict_proba` column order is [P(Away), P(Draw), P(Home)]
- All ML logic lives in `utils.py` — pages only display

## Common Gotchas

- Pandas Styler row colors in day mode must use **solid opaque hex** — `rgba` near-transparent renders dark-on-dark on the canvas renderer
- Adding a new model feature: (1) add to `FEATURE_COLS` in `utils.py`, (2) implement in `calculate_la_liga_features()`, (3) delete `models/ensemble_model.pkl` to force retrain, (4) mirror in `_team_stats_for_upcoming()`
- Copa del Rey congestion flag is a La Liga-specific feature — do not remove it
- La Liga goal defaults: home=1.45, away=1.12 — used to fill NaN, **not** 0
- Day/night auto-detection uses a JS snippet injecting `?hour=H` into the URL; manual toggle in sidebar overrides for the session
