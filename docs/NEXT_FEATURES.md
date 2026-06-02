# La Liga Linea — Next 5 Features to Implement

> **Based on:** Codebase gap analysis as of July 2025

---

## Feature 1: xG-Based Expected Goals Integration

**Why:** The `fetch_fbref_xg.py` script already exists and targets FBref La Liga (comp ID 12), but xGF/xGA are not yet added to `FEATURE_COLS` in `utils.py`. xG is the most reliable predictor of future performance and would directly improve model accuracy.

**How:**
1. Run `fetch_fbref_xg.py` to verify the FBref scraper works
2. Add `home_xg_l5`, `home_xga_l5`, `away_xg_l5`, `away_xga_l5` to `FEATURE_COLS` in `utils.py`
3. Compute rolling 5-match xG averages in `calculate_la_liga_features()` using `shift(1)` to prevent leakage
4. Add matching computation in `_team_stats_for_upcoming()` for upcoming fixtures
5. Delete `models/ensemble_model.pkl` to force retraining

**Complexity:** Low

---

## Feature 2: Copa del Rey Congestion Page

**Why:** The `fetch_copa_fixtures.py` script exists but there is no UI surfacing which La Liga teams played Copa del Rey ≤4 days before their next La Liga match. The congestion flag already exists as a binary feature — visualizing it gives users betting context.

**How:**
1. Add a new page `pages/copa_congestion.py`
2. Call `fetch_copa_fixtures.py` to load Copa data
3. For each upcoming La Liga fixture, show a table: Home Team | Away Team | Copa ≤4 days? | Days since Copa
4. Highlight rows where congestion flag is 1 (red/orange warning)
5. Wire it into `predictions.py` navigation

**Complexity:** Low

---

## Feature 3: Odds Line Movement Tracker

**Why:** Opening vs closing line movement reveals sharp money and public betting bias. Storing snapshots at T-48h, T-24h, and T-2h before kickoff lets users see whether the model edge is growing or shrinking as game time approaches.

**How:**
1. Add `data_files/raw/odds_snapshots.csv` with columns: `fixture_id`, `snapshot_time`, `home_odds`, `draw_odds`, `away_odds`
2. Add a GitHub Action step that calls `fetch_odds.py` at T-48h, T-24h, and T-2h
3. Add `pages/line_movement.py` showing a Plotly line chart per fixture over the 3 snapshots
4. Include model probability vs each snapshot implied probability

**Complexity:** Medium

---

## Feature 4: Model Calibration Reliability Diagram

**Why:** A reliability diagram (predicted probability decile vs actual win rate) reveals whether the model is overconfident or underconfident in certain probability ranges. This is a one-page addition with high diagnostic value.

**How:**
1. Load `data_files/predictions_log.csv` (already auto-generated)
2. Bin predictions into 10 deciles (0–10%, 10–20%, ... 90–100%)
3. For each bin, compute: mean predicted probability and actual win rate
4. Plot as Plotly scatter with a diagonal reference line
5. Add to existing `pages/model_performance.py` as a new tab or expander

**Complexity:** Low

---

## Feature 5: Matchday PDF Export

**Why:** `fpdf2` is already listed in `requirements.txt`. A one-click PDF export of today's predictions (fixture, model probabilities, market odds, edge, recommendation) would make the app more useful for users who want to reference picks without an internet connection.

**How:**
1. Add `utils/pdf_export.py` using `fpdf2`
2. Design a single-page landscape PDF: fixture table with columns (Home, Away, H%, D%, A%, Market Odds, Edge, Recommendation)
3. Add an `st.download_button` on the Today page that calls `pdf_export.generate()` and returns bytes
4. Follow the existing HTML download button pattern used in other repos (base64 data URI for small files)

**Complexity:** Low
