# La Liga Linea — Architecture

## Overview
Streamlit multi-page app predicting La Liga match outcomes and surfacing betting market value. Part of the Betting Oracle football suite.

## Data Flow
```
football-data.co.uk (SP1.csv)   FBref (xG)   The Odds API   Copa del Rey fixtures
        ↓                           ↓               ↓               ↓
fetch_historical_csvs.py     fetch_fbref_xg.py  fetch_odds.py  fetch_copa_fixtures.py
        ↓
data_files/combined_historical_data.csv
        ↓
utils.py → calculate_la_liga_features() [13 features, shift(1)]
        ↓
VotingClassifier (XGBoost×2 + RF×1.5 + GB×1 + LR×0.5, soft voting)
        ↓
models/ensemble_model.pkl
        ↓
predictions.py (entry) → pages/*.py
        ↓
data_files/best_bets_today.json
```

## ML Model
- **Target encoding**: A=0, D=1, H=2 (alphabetical, scikit-learn LabelEncoder)
- **`predict_proba` column order**: [P(Away), P(Draw), P(Home)]
- **Features** (`FEATURE_COLS` in `utils.py`): 13 features, all `shift(1)` leakage prevention
- **La Liga avg goals** (defaults): home=1.45, away=1.12

## La Liga-Specific Features
- `copa_congestion_flag` — binary: 1 if team played Copa del Rey ≤4 days prior
- No referee feature (sparse English data for La Liga)
- No surface flag (all 20 stadiums: natural grass)
- No travel-distance feature

## API Integrations
| Source | Purpose | Key |
|--------|---------|-----|
| football-data.co.uk | SP1.csv per season | None (download) |
| football-data.org | Fixtures (PD competition) | `FOOTBALL_DATA_API_KEY` |
| FBref | xG stats (comp ID 12) | None (scraped) |
| The Odds API | `soccer_spain_la_liga` | `ODDS_API_KEY` |
| ESPN API | `esp.1` scoreboard | None (public) |

## Theming System
`themes.py` provides `apply_theme()` + `plotly_theme()`. Auto-detects day/night from browser hour via `?hour=` query param. Manual sidebar toggle overrides session.
- **Table rendering**: Use `render_table()` from `utils.py` — never `st.dataframe()` directly
- **Day mode**: Solid opaque hex colours in Pandas Styler (rgba is unreadable on light canvas)
- **Charts**: Always call `fig.update_layout(**plotly_theme())` on every Plotly figure

## Key Components
- `predictions.py` — entry, `st.set_page_config`, sidebar, `st.navigation`, theme init
- `utils.py` — ALL shared functions (data, features, models, display)
- `themes.py` — `apply_theme()`, `plotly_theme()`
- `team_name_mapping.py` — normalises team names across sources
- `pages/*.py` — individual pages (no `st.set_page_config`)

## Storage
- `data_files/combined_historical_data.csv` — 10 seasons SP1.csv
- `data_files/upcoming_fixtures.csv` — scheduled fixtures
- `data_files/predictions_log.csv` — rolling predictions log
- `data_files/raw/` — raw scraped data
- `models/ensemble_model.pkl` — trained VotingClassifier (gitignored)
