# pfr_schedule.py
from __future__ import annotations
from datetime import datetime, date, time
from typing import Optional, Any

import pandas as pd
import numpy as np
import requests

def get_regular_season_schedule(year: int) -> pd.DataFrame:
    """
    Return a clean, ML-ready NFL regular-season schedule for `year` from Pro-Football-Reference.
    Columns:
      ['season','week','game_date','kickoff_et','away_team','home_team','away_pts','home_pts','ot','game_id']
    Types:
      season:int, week:int, game_date:date, kickoff_et:Optional[time], teams:str, pts:float (NaN before played), ot:bool
    """
    url = f"https://www.pro-football-reference.com/years/{year}/games.htm"
    html = requests.get(url, timeout=20).text

    # PFR tables are often inside HTML comments; read_html handles that.
    tables = pd.read_html(html, attrs={"id": "games"})
    if not tables:
        raise RuntimeError("Could not find games table on the page.")

    df = tables[0]

    # Keep essential columns (they’re stable across seasons)
    keep = ["Week", "Day", "Date", "Time", "Winner/tie", "PtsW", "Loser/tie", "PtsL", "OT"]
    df = df.loc[:, [c for c in keep if c in df.columns]].copy()

    # Drop header repeats / blanks
    df = df[df["Week"].astype(str).str.strip().ne("Week")]

    # Filter regular-season only: numeric weeks; exclude 'Pre', 'WildCard', 'Division', etc.
    is_numeric_week = df["Week"].astype(str).str.fullmatch(r"\d+")
    df = df[is_numeric_week].copy()
    df["Week"] = df["Week"].astype(int)

    # Parse date (PFR omits year in cell; add it explicitly)
    # Examples like "September 7"
    df["game_date"] = pd.to_datetime(df["Date"].astype(str) + f" {year}", errors="coerce").dt.date

    # Parse kickoff time (ET). Some rows are NaN (flexed/TBD).
    def _parse_time(s: Any) -> Optional[time]:
        if pd.isna(s):
            return None
        s = str(s).strip()
        # e.g., "1:00PM"
        try:
            return datetime.strptime(s, "%I:%M%p").time()
        except ValueError:
            return None

    df["kickoff_et"] = df["Time"].map(_parse_time)

    # Rename for clarity
    df = df.rename(
        columns={
            "Winner/tie": "home_team",  # On PFR, the listed "Winner/tie" can be home or away depending on '@' column,
            "Loser/tie": "away_team",   # but in this 'games' table it’s ordered by home/away columns hidden.
        }
    )

    # The above rename is NOT always correct if you rely on Winner/Loser. Safer approach:
    # Use the '@' indicator if present; rebuild home/away deterministically.
    if "Unnamed: 5" in tables[0].columns or "Unnamed: 6" in tables[0].columns or "@" in tables[0].columns:
        # If a column named '@' exists, it marks the away team (row uses 'Winner/tie'/'Loser/tie').
        # Reload with explicit columns so we can derive home/away correctly.
        raw = tables[0].copy()
        # Normalize column names
        raw.columns = [c.replace("@", "@").strip() for c in raw.columns]
        # Try to find the at-marker col
        at_col = [c for c in raw.columns if c in {"@", "Unnamed: 5", "Unnamed: 6"}]
        at_col = at_col[0] if at_col else None

        # Build deterministic home/away:
        # If '@' == '@' then Winner/tie is AWAY and Loser/tie is HOME.
        # Else Winner/tie is HOME and Loser/tie is AWAY.
        work = raw.loc[df.index, ["Week", "Winner/tie", "Loser/tie", "PtsW", "PtsL", "OT"] + ([at_col] if at_col else [])].copy()
        is_at = (work[at_col] == "@") if at_col else pd.Series(False, index=work.index)

        away_team = np.where(is_at, work["Winner/tie"], work["Loser/tie"])
        home_team = np.where(is_at, work["Loser/tie"], work["Winner/tie"])
        away_pts  = np.where(is_at, work["PtsW"], work["PtsL"])
        home_pts  = np.where(is_at, work["PtsL"], work["PtsW"])

        df["away_team"] = away_team
        df["home_team"] = home_team
        df["away_pts"]  = pd.to_numeric(away_pts, errors="coerce")
        df["home_pts"]  = pd.to_numeric(home_pts, errors="coerce")
        df["ot"]        = work["OT"].fillna("").astype(str).str.upper().eq("OT")
    else:
        # Fallback (rare pages). Keep previous rename but ensure numeric types exist.
        df["away_team"] = df["Loser/tie"]
        df["home_team"] = df["Winner/tie"]
        df["away_pts"]  = pd.to_numeric(df["PtsL"], errors="coerce")
        df["home_pts"]  = pd.to_numeric(df["PtsW"], errors="coerce")
        df["ot"]        = df["OT"].fillna("").astype(str).str.upper().eq("OT")

    # Build a stable game_id (season-week-away@home)
    slug = lambda s: str(s).lower().replace(" ", "_").replace("&", "and")
    df["game_id"] = (
        df["Week"].astype(int).astype(str)
        + "-"
        + pd.Series(df["away_team"]).map(slug)
        + "@"
        + pd.Series(df["home_team"]).map(slug)
    )

    # Final select & order
    out = df.assign(season=year)[
        ["season", "week", "game_date", "kickoff_et", "away_team", "home_team", "away_pts", "home_pts", "ot", "game_id"]
    ].sort_values(["week", "home_team", "away_team"], kind="stable").reset_index(drop=True)

    # Types: ensure clean dtypes
    out["season"] = out["season"].astype(int)
    out["week"]   = out["week"].astype(int)
    # game_date already date; kickoff_et is time or NaT
    # points are float (NaN for unplayed); ot is bool

    return out

# Example:
    df = get_regular_season_schedule(2025)
    print(f"Retrieved {len(df)} games for 2025 regular season.{df.shape}")
    df.to_csv("schedule_regular_2025_clean.csv", index=False)