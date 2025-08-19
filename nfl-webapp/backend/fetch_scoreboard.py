# fetch_scoreboard.py
#
# Uses ESPN’s unofficial scoreboard API to collect NFL games for a single week.
# You can loop through weekly dates to build a season’s dataset.
import requests
import pandas as pd
from datetime import datetime

def fetch_scoreboard(date_str: str) -> pd.DataFrame:
    """
    Fetch ESPN scoreboard for a specific date (YYYY-MM-DD).
    Returns a DataFrame with columns: date, home_team, away_team, home_score, away_score.
    """
    url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    params = {"dates": date_str.replace("-", "")}  # ESPN expects YYYYMMDD
    resp = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"})
    print("Request URL:", resp.url)
    if not resp.ok:
        print("Response text:", resp.text)
    resp.raise_for_status()
    data = resp.json()

    records = []
    for event in data.get("events", []):
        competition = event["competitions"][0]
        home = next(team for team in competition["competitors"] if team["homeAway"] == "home")
        away = next(team for team in competition["competitors"] if team["homeAway"] == "away")
        records.append({
            "date": datetime.fromisoformat(event["date"]).date(),
            "home_team": home["team"]["abbreviation"],
            "away_team": away["team"]["abbreviation"],
            "home_score": int(home["score"]),
            "away_score": int(away["score"]),
        })
    return pd.DataFrame.from_records(records)

if __name__ == "__main__":
    # example usage: fetch games from Week 1 of 2024 (adjust date as needed)
    df_week1 = fetch_scoreboard("2024-09-10")
    print(df_week1)
