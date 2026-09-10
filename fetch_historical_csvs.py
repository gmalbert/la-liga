"""Download SP1.csv files for every La Liga season from football-data.co.uk
and merge them into data_files/combined_historical_data.csv.

Usage:
    python fetch_historical_csvs.py
"""

from __future__ import annotations

import io
from pathlib import Path
import time
from urllib.parse import urlsplit, urlunsplit

import pandas as pd
import requests

# ── Seasons to download ────────────────────────────────────────────────────

SEASONS: dict[str, str] = {
    "1516": "2015-16",
    "1617": "2016-17",
    "1718": "2017-18",
    "1819": "2018-19",
    "1920": "2019-20",
    "2021": "2020-21",
    "2122": "2021-22",
    "2223": "2022-23",
    "2324": "2023-24",
    "2425": "2024-25",
    "2526": "2025-26",
}

BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/SP1.csv"
FOOTBALL_DATA_HOSTS = ("football-data.co.uk", "www.football-data.co.uk")

COLUMN_MAP: dict[str, str] = {
    "Date":   "MatchDate",
    "HomeTeam": "HomeTeam",
    "AwayTeam": "AwayTeam",
    "FTHG":   "FullTimeHomeGoals",
    "FTAG":   "FullTimeAwayGoals",
    "FTR":    "FullTimeResult",
    "HTHG":   "HalfTimeHomeGoals",
    "HTAG":   "HalfTimeAwayGoals",
    "HTR":    "HalfTimeResult",
    "Referee": "Referee",
    "HS":     "HomeShots",
    "AS":     "AwayShots",
    "HST":    "HomeShotsOnTarget",
    "AST":    "AwayShotsOnTarget",
    "HF":     "HomeFouls",
    "AF":     "AwayFouls",
    "HC":     "HomeCorners",
    "AC":     "AwayCorners",
    "HY":     "HomeYellowCards",
    "AY":     "AwayYellowCards",
    "HR":     "HomeRedCards",
    "AR":     "AwayRedCards",
    # Bet365 odds
    "B365H":  "Bet365_HomeWinOdds",
    "B365D":  "Bet365_DrawOdds",
    "B365A":  "Bet365_AwayWinOdds",
    # BetWin
    "BWH":    "BW_HomeWinOdds",
    "BWD":    "BW_DrawOdds",
    "BWA":    "BW_AwayWinOdds",
    # Pinnacle
    "PSH":    "Pinnacle_HomeWinOdds",
    "PSD":    "Pinnacle_DrawOdds",
    "PSA":    "Pinnacle_AwayWinOdds",
}


def _download_csv_text(url: str) -> str:
    errors = []
    for host in FOOTBALL_DATA_HOSTS:
        parsed = urlsplit(url)
        candidate = urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))
        for attempt in range(3):
            try:
                resp = requests.get(
                    candidate,
                    headers={"Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1"},
                    timeout=20,
                )
                if 500 <= resp.status_code < 600 and attempt < 2:
                    try:
                        delay = min(max(float(resp.headers.get("Retry-After", "0.5")), 0), 5)
                    except ValueError:
                        delay = 0.5
                    time.sleep(delay)
                    continue
                resp.raise_for_status()
                try:
                    text = resp.content.decode("utf-8-sig")
                except UnicodeDecodeError:
                    text = resp.content.decode("cp1252")
                preview = text[:160].replace("\n", " ").strip()
                if "<html" in preview.lower() or "<!doctype" in preview.lower():
                    raise ValueError(f"HTML response: {preview!r}")
                return text
            except (requests.RequestException, UnicodeDecodeError, ValueError) as exc:
                errors.append(f"{candidate} [attempt {attempt + 1}]: {exc}")
                break
    raise RuntimeError("Football-Data download failed: " + " | ".join(errors))


def download_season(season_code: str, season_label: str) -> pd.DataFrame:
    """Download one season CSV and return a normalised DataFrame."""
    url = BASE_URL.format(code=season_code)
    try:
        df = pd.read_csv(
            io.StringIO(_download_csv_text(url)),
            on_bad_lines="skip",
        )
        df = df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in df.columns}).copy()
        df["Season"] = season_label
        df["MatchDate"] = pd.to_datetime(df["MatchDate"], format="mixed", dayfirst=True, errors="coerce")
        # Drop completely empty rows
        df = df.dropna(subset=["HomeTeam", "AwayTeam"])
        print(f"  ✓ {season_label}: {len(df)} matches")
        return df
    except Exception as exc:
        print(f"  ✗ {season_label}: {exc}")
        return pd.DataFrame()


def build_historical_dataset() -> pd.DataFrame:
    """Download all seasons, combine, and save to CSV."""
    Path("data_files/raw").mkdir(parents=True, exist_ok=True)

    frames: list[pd.DataFrame] = []
    for code, label in SEASONS.items():
        print(f"Downloading {label}…")
        df = download_season(code, label)
        if not df.empty:
            raw_path = f"data_files/raw/SP1_{code}.csv"
            df.to_csv(raw_path, index=False)
            frames.append(df)

    if not frames:
        print("No data downloaded. Check your internet connection.")
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values("MatchDate").reset_index(drop=True)

    out_path = "data_files/combined_historical_data.csv"
    combined.to_csv(out_path, index=False)
    print(f"\n✓ Combined: {len(combined)} matches across {len(frames)} seasons → {out_path}")
    return combined


if __name__ == "__main__":
    build_historical_dataset()
