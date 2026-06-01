"""
queries.py — All IPL analytics queries
========================================
Every function returns a Pandas DataFrame.
Works with SQLite (default) and PostgreSQL — no code changes needed,
just set DB_ENGINE=postgresql (see db.py).

Usage in app.py:
    from queries import top_run_scorers, best_economy, ...
    df = top_run_scorers(20)

Standalone test:
    python queries.py
"""

from db import read_sql


# ══════════════════════════════════════════════════════════════════════════════
# BATTING
# ══════════════════════════════════════════════════════════════════════════════

def top_run_scorers(limit: int = 500):
    """All-time batting leaderboard."""
    return read_sql("""
        SELECT batter,
               total_runs,
               innings_played      AS innings,
               batting_average     AS average,
               strike_rate,
               fours,
               sixes,
               highest_score       AS highest
        FROM   batting_stats
        ORDER  BY total_runs DESC
        LIMIT  :limit
    """, {"limit": limit})


def batting_leaders_by_season(season: int, limit: int = 10):
    """Top run-scorers for one season."""
    return read_sql("""
        SELECT batter,
               SUM(runs_batter)                         AS runs,
               COUNT(DISTINCT match_id)                 AS matches,
               ROUND(SUM(runs_batter)*100.0/COUNT(*),1) AS strike_rate,
               SUM(is_six)                              AS sixes
        FROM   deliveries
        WHERE  year     = :season
          AND  is_legal = 1
        GROUP  BY batter
        ORDER  BY runs DESC
        LIMIT  :limit
    """, {"season": season, "limit": limit})


def player_batting_profile(player_name: str):
    """Season-by-season stats for one batter."""
    return read_sql("""
        SELECT year                                       AS season,
               SUM(runs_batter)                          AS runs,
               COUNT(*)                                  AS balls,
               SUM(is_four)                              AS fours,
               SUM(is_six)                               AS sixes,
               ROUND(SUM(runs_batter)*100.0/COUNT(*),1)  AS strike_rate
        FROM   deliveries
        WHERE  batter   = :player
          AND  is_legal = 1
        GROUP  BY year
        ORDER  BY year
    """, {"player": player_name})


# ══════════════════════════════════════════════════════════════════════════════
# BOWLING
# ══════════════════════════════════════════════════════════════════════════════

def top_wicket_takers(limit: int = 500):
    """All-time bowling leaderboard."""
    return read_sql("""
        SELECT bowler,
               wickets,
               economy_rate        AS economy,
               bowling_average     AS average,
               bowling_strike_rate AS strike_rate,
               four_wkt_hauls,
               five_wkt_hauls
        FROM   bowling_stats
        ORDER  BY wickets DESC
        LIMIT  :limit
    """, {"limit": limit})


def best_economy(min_overs: int = 60, limit: int = 15):
    """Best economy rates (min overs threshold)."""
    return read_sql("""
        SELECT bowler,
               wickets,
               ROUND(legal_balls/6.0,1) AS overs,
               economy_rate,
               bowling_average
        FROM   bowling_stats
        WHERE  legal_balls >= :min_balls
        ORDER  BY economy_rate ASC
        LIMIT  :limit
    """, {"min_balls": min_overs * 6, "limit": limit})


def bowling_leaders_by_season(season: int, limit: int = 10):
    """Top wicket-takers for one season."""
    return read_sql("""
        SELECT bowler,
               SUM(is_wicket)                               AS wickets,
               ROUND(SUM(runs_bowler)*6.0/SUM(valid_ball),2) AS economy,
               SUM(valid_ball)                              AS balls
        FROM   deliveries
        WHERE  year = :season
        GROUP  BY bowler
        HAVING SUM(valid_ball) > 0
        ORDER  BY wickets DESC
        LIMIT  :limit
    """, {"season": season, "limit": limit})


# ══════════════════════════════════════════════════════════════════════════════
# VENUES
# ══════════════════════════════════════════════════════════════════════════════

def venue_win_percentages(min_matches: int = 10):
    """Bat-first vs chase win % per venue."""
    return read_sql("""
        SELECT venue,
               total_matches,
               bat_first_wins,
               chase_wins,
               bat_first_win_pct,
               ROUND(100.0 - bat_first_win_pct, 1) AS chase_win_pct,
               avg_first_innings,
               avg_second_innings
        FROM   venue_stats
        WHERE  total_matches >= :min_matches
        ORDER  BY total_matches DESC
    """, {"min_matches": min_matches})


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW / SEASON
# ══════════════════════════════════════════════════════════════════════════════

def season_trends():
    """Runs, sixes, wickets per season."""
    return read_sql("""
        SELECT year                     AS season,
               COUNT(DISTINCT match_id) AS matches,
               SUM(runs_total)          AS runs,
               SUM(is_six)              AS sixes,
               SUM(is_wicket)           AS wickets
        FROM   deliveries
        GROUP  BY year
        ORDER  BY year
    """)


def team_win_counts():
    """All-time wins per team."""
    return read_sql("""
        SELECT winner                   AS team,
               COUNT(DISTINCT match_id) AS wins
        FROM   matches
        WHERE  winner IS NOT NULL
          AND  winner != ''
          AND  winner != 'nan'
        GROUP  BY winner
        ORDER  BY wins DESC
    """)


def head_to_head_all(min_matches: int = 20):
    """All notable head-to-head records."""
    return read_sql("""
        SELECT batting_team                                          AS team1,
               bowling_team                                         AS team2,
               COUNT(DISTINCT match_id)                             AS matches,
               SUM(CASE WHEN winner=batting_team THEN 1 ELSE 0 END) AS team1_wins,
               SUM(CASE WHEN winner=bowling_team THEN 1 ELSE 0 END) AS team2_wins
        FROM   matches
        WHERE  winner IS NOT NULL AND winner != ''
        GROUP  BY batting_team, bowling_team
        HAVING COUNT(DISTINCT match_id) >= :min_matches
        ORDER  BY matches DESC
        LIMIT  15
    """, {"min_matches": min_matches})


def toss_win_rate() -> float:
    df = read_sql("""
        SELECT ROUND(
            100.0 * SUM(CASE WHEN toss_winner = winner THEN 1 ELSE 0 END)
                  / COUNT(DISTINCT match_id), 1
        ) AS pct
        FROM matches
        WHERE winner IS NOT NULL AND winner != ''
          AND toss_winner IS NOT NULL
    """)
    return float(df["pct"].iloc[0])


def overview_stats() -> dict:
    """Single dict of headline numbers — replaces overview.json."""
    seasons = season_trends()
    teams   = team_win_counts()
    h2h     = head_to_head_all()
    toss    = toss_win_rate()
    return {
        "total_seasons":      int(seasons["season"].nunique()),
        "total_matches":      int(seasons["matches"].sum()),
        "total_runs":         int(seasons["runs"].sum()),
        "total_wickets":      int(seasons["wickets"].sum()),
        "total_sixes":        int(seasons["sixes"].sum()),
        "avg_runs_per_match": round(seasons["runs"].sum() / seasons["matches"].sum(), 1),
        "toss_win_pct":       toss,
        "season_stats":       seasons.to_dict(orient="records"),
        "team_wins":          dict(zip(teams["team"], teams["wins"])),
        "head_to_head":       h2h.to_dict(orient="records"),
    }


def season_leaders() -> dict:
    """Orange Cap + Purple Cap + top 5 per season — replaces season_leaders.json."""
    seasons_df = season_trends()
    result = []
    for season in sorted(seasons_df["season"].tolist()):
        bat = batting_leaders_by_season(season, limit=5)
        bwl = bowling_leaders_by_season(season, limit=5)
        if bat.empty or bwl.empty:
            continue
        result.append({
            "season": season,
            "orange_cap": {"player": bat.iloc[0]["batter"], "runs": int(bat.iloc[0]["runs"])},
            "purple_cap": {"player": bwl.iloc[0]["bowler"], "wickets": int(bwl.iloc[0]["wickets"])},
            "top_batsmen": [{"player": r["batter"], "runs": int(r["runs"])} for _, r in bat.iterrows()],
            "top_bowlers": [{"player": r["bowler"], "wickets": int(r["wickets"])} for _, r in bwl.iterrows()],
        })
    return {"seasons": result}


def advanced_stats() -> dict:
    """Impact scores — replaces advanced.json."""
    df = read_sql("""
        SELECT batter                  AS player,
               total_runs              AS runs,
               batting_average         AS avg,
               strike_rate             AS sr,
               ROUND(
                   total_runs  * 0.4
                 + strike_rate * 0.3
                 + batting_average * 0.3, 1
               )                       AS impact_score
        FROM   batting_stats
        WHERE  innings_played >= 10
        ORDER  BY impact_score DESC
    """)
    return {"impact_scores": df.to_dict(orient="records")}


# ══════════════════════════════════════════════════════════════════════════════
# QUICK TEST
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    from db import current_engine
    print(f"Engine: {current_engine().upper()}\n")
    print("[1] Top 5 run scorers")
    print(top_run_scorers(5).to_string(index=False))
    print("\n[2] Best economy (min 60 overs, top 5)")
    print(best_economy(60, 5).to_string(index=False))
    print("\n[3] Season trends (last 3)")
    print(season_trends().tail(3).to_string(index=False))
    print("\n[4] Toss win rate")
    print(f"  {toss_win_rate()}%")
    print("\n✅ All queries passed.")
