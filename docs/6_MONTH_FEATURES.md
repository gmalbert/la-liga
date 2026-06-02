# La Liga Linea — 6-Month Feature Roadmap

## Month 1: Match Day Experience

- **Today's fixtures card** — Quick view of all La Liga fixtures this weekend with model predictions.
- **Live score widget** — Auto-refreshing scoreboard for in-play La Liga matches via ESPN API.
- **Pre-match summary** — For each fixture: last 5 results, top scorer, injury report (if available).
- **Upcoming form badges** — "Won last 4" / "No win in 5" badge on each team card.

## Month 2: Team Pages

- **Team profile** — Season stats, xG trend, form chart, Copa del Rey fixture overlap.
- **Squad depth indicator** — Simple flag for teams with key players absent.
- **Home/away split** — Teams that massively outperform at home vs. away.

## Month 3: Betting Tools

- **Value bet finder** — Filter matches where model edge vs. B365/Bet365 exceeds 3%.
- **Draw specialist dashboard** — Highlight historically draw-heavy fixtures.
- **Odds comparison table** — B365, BF exchange, and no-vig model probability side by side.

## Month 4: Historical Analytics

- **Season-by-season accuracy report** — Model accuracy broken down by team and outcome class.
- **Referee stats page** — Booking rates, penalty rates, red cards per referee.
- **El Clásico & top-fixture deep-dive** — Historical model vs. result for marquee matches.

## Month 5: PDF & Export

- **Matchday PDF export** — One-click PDF of all weekend predictions with odds.
- **Fixture calendar export** — Download `.ics` file of La Liga schedule.

## Month 6: Automation

- **Nightly fixture fetch** — GitHub Action runs `fetch_upcoming_fixtures.py` and `fetch_odds.py` Monday–Friday.
- **Friday email** — Weekly predictions email with weekend fixtures.
- **Model retraining Action** — Monthly retraining trigger on new-season data.
