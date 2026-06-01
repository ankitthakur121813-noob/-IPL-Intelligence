"""
IPL Analytics — SQLite Setup
=============================
Run once to create ipl.db from your CSVs.

Usage:
    python setup_db.py

Output:
    ipl.db  — SQLite database with 5 tables
"""

import sqlite3
import pandas as pd
import os, sys

CSV_PATH = "IPL.csv"
DB_PATH  = "ipl.db"

if not os.path.exists(CSV_PATH):
    sys.exit(f"ERROR: {CSV_PATH} not found.")

print(f"Loading {CSV_PATH} ...")
D = pd.read_csv(CSV_PATH, low_memory=False)
print(f"  {len(D):,} rows | {D['match_id'].nunique()} matches | {D['year'].nunique()} seasons")

# Derived columns
D['is_six']    = (D['runs_batter'] == 6).astype(int)
D['is_four']   = (D['runs_batter'] == 4).astype(int)
D['is_wicket'] = (
    D['wicket_kind'].notna() &
    (D['wicket_kind'] != '') &
    (D['wicket_kind'].astype(str) != 'nan')
).astype(int)
D['is_legal']  = (D['valid_ball'] == 1).astype(int)

# Normalise winner column (your CSV uses 'match_won_by')
winner_col = 'match_won_by' if 'match_won_by' in D.columns else 'winner'
D['winner'] = D[winner_col]

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# ── TABLE 1: deliveries ───────────────────────────────────────────────────────
print("\nCreating table: deliveries ...")
wanted = [
    'match_id', 'year', 'venue', 'innings', 'over', 'ball',
    'batter', 'bowler', 'player_out', 'batting_team', 'bowling_team',
    'runs_batter', 'runs_extras', 'runs_total', 'runs_bowler',
    'valid_ball', 'wicket_kind', 'winner', 'toss_winner', 'toss_decision',
    'is_six', 'is_four', 'is_wicket', 'is_legal',
]
cols = [c for c in wanted if c in D.columns]
D[cols].to_sql('deliveries', conn, if_exists='replace', index=False)
print(f"  {len(D):,} rows written")

# ── TABLE 2: matches ──────────────────────────────────────────────────────────
print("Creating table: matches ...")
match_cols = ['match_id', 'year', 'venue', 'batting_team', 'bowling_team',
              'toss_winner', 'toss_decision', 'winner']
match_cols = [c for c in match_cols if c in D.columns]
df_matches = (
    D[match_cols]
    .drop_duplicates(subset=['match_id'])
    .sort_values('match_id')
    .reset_index(drop=True)
)
df_matches.to_sql('matches', conn, if_exists='replace', index=False)
print(f"  {len(df_matches):,} rows written")

# ── TABLE 3: batting_stats ────────────────────────────────────────────────────
print("Creating table: batting_stats ...")
cur.executescript("""
DROP TABLE IF EXISTS batting_stats;
CREATE TABLE batting_stats AS
WITH legal_balls AS (
    SELECT * FROM deliveries WHERE is_legal = 1
),
base AS (
    SELECT batter,
           SUM(runs_batter) AS total_runs,
           COUNT(*)         AS balls_faced,
           SUM(is_four)     AS fours,
           SUM(is_six)      AS sixes
    FROM   legal_balls
    GROUP  BY batter
),
innings_scores AS (
    SELECT match_id, innings, batter,
           SUM(runs_batter) AS innings_runs
    FROM   legal_balls
    GROUP  BY match_id, innings, batter
),
inn_agg AS (
    SELECT batter,
           COUNT(*)          AS innings_played,
           MAX(innings_runs) AS highest_score
    FROM   innings_scores
    GROUP  BY batter
),
dismissals AS (
    SELECT player_out AS batter, COUNT(*) AS times_dismissed
    FROM   deliveries
    WHERE  is_wicket  = 1
      AND  player_out IS NOT NULL
      AND  player_out != ''
      AND  player_out != 'nan'
    GROUP  BY player_out
)
SELECT b.batter,
       b.total_runs,
       i.innings_played,
       b.balls_faced,
       b.fours,
       b.sixes,
       i.highest_score,
       COALESCE(d.times_dismissed, 1) AS times_dismissed,
       ROUND(b.total_runs * 1.0 / COALESCE(d.times_dismissed, 1), 1) AS batting_average,
       ROUND(b.total_runs * 100.0 / b.balls_faced, 1)                AS strike_rate
FROM   base b
JOIN   inn_agg  i ON b.batter = i.batter
LEFT JOIN dismissals d ON b.batter = d.batter
ORDER BY total_runs DESC;
""")
conn.commit()
n = cur.execute("SELECT COUNT(*) FROM batting_stats").fetchone()[0]
print(f"  {n:,} players written")

# ── TABLE 4: bowling_stats ────────────────────────────────────────────────────
print("Creating table: bowling_stats ...")
cur.executescript("""
DROP TABLE IF EXISTS bowling_stats;
CREATE TABLE bowling_stats AS
WITH base AS (
    SELECT bowler,
           SUM(is_wicket)   AS wickets,
           SUM(runs_bowler) AS runs_conceded,
           SUM(valid_ball)  AS legal_balls
    FROM   deliveries
    GROUP  BY bowler
),
hauls AS (
    SELECT bowler,
           SUM(CASE WHEN wkts >= 4 THEN 1 ELSE 0 END) AS four_wkt_hauls,
           SUM(CASE WHEN wkts >= 5 THEN 1 ELSE 0 END) AS five_wkt_hauls
    FROM (
        SELECT match_id, innings, bowler,
               SUM(is_wicket) AS wkts
        FROM   deliveries
        WHERE  is_wicket = 1
        GROUP  BY match_id, innings, bowler
    )
    GROUP  BY bowler
)
SELECT b.bowler,
       b.wickets,
       b.runs_conceded,
       b.legal_balls,
       ROUND(b.legal_balls / 6.0, 1)                                    AS overs_bowled,
       ROUND(b.runs_conceded * 6.0 / NULLIF(b.legal_balls, 0), 2)      AS economy_rate,
       ROUND(b.runs_conceded * 1.0 / NULLIF(b.wickets, 0), 2)          AS bowling_average,
       ROUND(b.legal_balls   * 1.0 / NULLIF(b.wickets, 0), 2)          AS bowling_strike_rate,
       COALESCE(h.four_wkt_hauls, 0)                                    AS four_wkt_hauls,
       COALESCE(h.five_wkt_hauls, 0)                                    AS five_wkt_hauls
FROM   base b
LEFT JOIN hauls h ON b.bowler = h.bowler
ORDER BY wickets DESC;
""")
conn.commit()
n = cur.execute("SELECT COUNT(*) FROM bowling_stats").fetchone()[0]
print(f"  {n:,} players written")

# ── TABLE 5: venue_stats ──────────────────────────────────────────────────────
print("Creating table: venue_stats ...")
cur.executescript("""
DROP TABLE IF EXISTS venue_stats;
CREATE TABLE venue_stats AS
WITH match_meta AS (
    SELECT match_id, venue,
           MAX(CASE WHEN innings = 1 THEN batting_team END) AS bat_first_team,
           MAX(winner) AS winner
    FROM   deliveries
    WHERE  venue IS NOT NULL AND venue != ''
    GROUP  BY match_id, venue
),
innings_runs AS (
    SELECT match_id, venue,
           SUM(CASE WHEN innings = 1 THEN runs_total ELSE 0 END) AS first_innings_runs,
           SUM(CASE WHEN innings = 2 THEN runs_total ELSE 0 END) AS second_innings_runs
    FROM   deliveries
    WHERE  venue IS NOT NULL
    GROUP  BY match_id, venue
)
SELECT m.venue,
       COUNT(DISTINCT m.match_id)                                            AS total_matches,
       ROUND(AVG(i.first_innings_runs),  1)                                  AS avg_first_innings,
       ROUND(AVG(i.second_innings_runs), 1)                                  AS avg_second_innings,
       SUM(CASE WHEN m.winner = m.bat_first_team THEN 1 ELSE 0 END)         AS bat_first_wins,
       SUM(CASE WHEN m.winner != m.bat_first_team
                 AND m.winner IS NOT NULL
                 AND m.winner != '' THEN 1 ELSE 0 END)                       AS chase_wins,
       ROUND(
           100.0 * SUM(CASE WHEN m.winner = m.bat_first_team THEN 1 ELSE 0 END)
                 / COUNT(DISTINCT m.match_id), 1
       )                                                                      AS bat_first_win_pct
FROM   match_meta m
JOIN   innings_runs i ON m.match_id = i.match_id
GROUP  BY m.venue
HAVING total_matches >= 10
ORDER  BY total_matches DESC;
""")
conn.commit()
n = cur.execute("SELECT COUNT(*) FROM venue_stats").fetchone()[0]
print(f"  {n:,} venues written")

# ── Indexes ───────────────────────────────────────────────────────────────────
print("\nCreating indexes ...")
for sql in [
    "CREATE INDEX IF NOT EXISTS idx_del_batter  ON deliveries(batter)",
    "CREATE INDEX IF NOT EXISTS idx_del_bowler  ON deliveries(bowler)",
    "CREATE INDEX IF NOT EXISTS idx_del_match   ON deliveries(match_id)",
    "CREATE INDEX IF NOT EXISTS idx_del_year    ON deliveries(year)",
    "CREATE INDEX IF NOT EXISTS idx_del_venue   ON deliveries(venue)",
    "CREATE INDEX IF NOT EXISTS idx_match_year  ON matches(year)",
]:
    cur.execute(sql)
conn.commit()
conn.close()

db_mb = os.path.getsize(DB_PATH) / 1024 / 1024
print(f"\n✅  ipl.db created ({db_mb:.1f} MB)")
print("    Tables: deliveries, matches, batting_stats, bowling_stats, venue_stats")
print("\nNext: run   python queries.py   to test all SQL queries")
