"""Fetch La Liga betting odds from The Odds API.

Saves: data_files/raw/odds.csv

Usage:
    python fetch_odds.py            # skips if odds.csv < MAX_AGE_HOURS old
    python fetch_odds.py --force    # always fetch regardless of cache age

Requires:
    ODDS_API_KEY in .env (free tier: 500 req/month)
    Sign up at https://the-odds-api.com/
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY  = os.getenv("ODDS_API_KEY", "")
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
SPORT_KEY     = "soccer_spain_la_liga"

OUT_PATH = "data_files/raw/odds.csv"

# Skip the API call if the output file is fresher than this many hours.
# One call per day is sufficient; this prevents duplicate burns from manual
# re-runs or workflow_dispatch triggers within the same day.
MAX_AGE_HOURS = 20

# Emit a console warning when monthly quota falls this low.
QUOTA_WARN_THRESHOLD = 50

Path("data_files/raw").mkdir(parents=True, exist_ok=True)


def _is_fresh(path: str = OUT_PATH, max_age_hours: int = MAX_AGE_HOURS) -> bool:
    """Return True if *path* exists and was written within *max_age_hours*."""
    p = Path(path)
    if not p.exists():
        return False
    age_hours = (time.time() - p.stat().st_mtime) / 3600
    return age_hours < max_age_hours


def fetch_upcoming_odds(
    regions: str = "us,eu",
    markets: str = "h2h",
    bookmakers: str = "draftkings,betmgm,pinnacle,bet365",
    force: bool = False,
) -> pd.DataFrame:
    """
    Fetch upcoming La Liga 1X2 (h2h) odds.
    Returns a DataFrame with one row per game per bookmaker.

    Skips the API call and returns the cached CSV when the file is younger
    than MAX_AGE_HOURS, unless *force* is True.
    """
    if not force and _is_fresh():
        age_h = (time.time() - Path(OUT_PATH).stat().st_mtime) / 3600
        print(
            f"  Odds cache is {age_h:.1f}h old (< {MAX_AGE_HOURS}h). "
            "Skipping API call — use --force to refresh."
        )
        return pd.read_csv(OUT_PATH)

    if not ODDS_API_KEY:
        raise EnvironmentError(
            "ODDS_API_KEY not set. Copy .env.example to .env and add your key."
        )

    resp = requests.get(
        f"{ODDS_API_BASE}/sports/{SPORT_KEY}/odds",
        params={
            "apiKey":       ODDS_API_KEY,
            "regions":      regions,
            "markets":      markets,
            "oddsFormat":   "decimal",
            "bookmakers":   bookmakers,
        },
        timeout=20,
    )
    resp.raise_for_status()

    # Log remaining quota from response headers
    remaining_raw = resp.headers.get("x-requests-remaining", "?")
    used = resp.headers.get("x-requests-used", "?")
    print(f"  Odds API quota — used: {used}, remaining: {remaining_raw}")
    try:
        remaining = int(remaining_raw)
        if remaining < QUOTA_WARN_THRESHOLD:
            print(
                f"  ⚠ WARNING: Only {remaining} Odds API requests remaining this month! "
                "Consider running with staleness guard (no --force) until quota resets."
            )
    except (TypeError, ValueError):
        pass

    games = resp.json()
    if not games:
        print("  No upcoming odds returned. Off-season or no active markets.")
        return pd.DataFrame()

    rows = []
    for game in games:
        home = game["home_team"]
        away = game["away_team"]
        date = game["commence_time"][:10]

        for bm in game.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market["key"] != "h2h":
                    continue
                prices = {o["name"]: o["price"] for o in market["outcomes"]}
                rows.append({
                    "Date":         date,
                    "HomeTeam":     home,
                    "AwayTeam":     away,
                    "Bookmaker":    bm["key"],
                    "HomeWinOdds":  prices.get(home),
                    "DrawOdds":     prices.get("Draw"),
                    "AwayWinOdds":  prices.get(away),
                })

    # Keep a stable schema when games exist but the requested bookmakers have
    # no active h2h markets (common during the off-season).  Without explicit
    # columns, an empty ``rows`` list produces a zero-column DataFrame and the
    # implied-probability calculation raises KeyError.
    df = pd.DataFrame(
        rows,
        columns=[
            "Date",
            "HomeTeam",
            "AwayTeam",
            "Bookmaker",
            "HomeWinOdds",
            "DrawOdds",
            "AwayWinOdds",
        ],
    )
    df = _add_implied_probabilities(df)
    df.to_csv(OUT_PATH, index=False)
    print(f"  ✓ Odds for {len(games)} games, {len(df)} bookmaker rows → {OUT_PATH}")
    return df


def _add_implied_probabilities(df: pd.DataFrame) -> pd.DataFrame:
    """Vig-removed implied probabilities from decimal odds."""
    df = df.copy()
    for col in ["HomeWinOdds", "DrawOdds", "AwayWinOdds"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    valid = df["HomeWinOdds"].notna() & df["DrawOdds"].notna() & df["AwayWinOdds"].notna()
    df.loc[valid, "_vig"] = (
        1 / df.loc[valid, "HomeWinOdds"]
        + 1 / df.loc[valid, "DrawOdds"]
        + 1 / df.loc[valid, "AwayWinOdds"]
    )
    df.loc[valid, "ImpliedProb_HomeWin"] = (
        (1 / df.loc[valid, "HomeWinOdds"]) / df.loc[valid, "_vig"]
    ).round(4)
    df.loc[valid, "ImpliedProb_Draw"] = (
        (1 / df.loc[valid, "DrawOdds"]) / df.loc[valid, "_vig"]
    ).round(4)
    df.loc[valid, "ImpliedProb_AwayWin"] = (
        (1 / df.loc[valid, "AwayWinOdds"]) / df.loc[valid, "_vig"]
    ).round(4)
    df.loc[valid, "BookmakerMargin"] = (
        (df.loc[valid, "_vig"] - 1) * 100
    ).round(2)
    df.drop(columns=["_vig"], inplace=True, errors="ignore")
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch La Liga bookmaker odds")
    parser.add_argument(
        "--force",
        action="store_true",
        help=f"Bypass the {MAX_AGE_HOURS}h staleness guard and always call the API",
    )
    args = parser.parse_args()
    fetch_upcoming_odds(force=args.force)
