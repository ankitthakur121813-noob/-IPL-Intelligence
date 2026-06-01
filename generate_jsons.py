"""
IPL JSON Generator
------------------
Run this script in the same folder as IPL.csv
Output: 7 JSON files in a /data folder

Usage:
    python generate_jsons.py

Requirements:
    pip install pandas numpy scikit-learn
"""

import pandas as pd
import numpy as np
import json, os, warnings
warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
INPUT_FILE    = "IPL.csv"               # main ball-by-ball dataset
BATTING_2026  = "ipl_2026_batting.csv"  # 2026 batting summary (optional)
BOWLING_2026  = "ipl_2026_bowling.csv"  # 2026 bowling summary (optional)
OUTPUT_DIR    = "data"                  # JSONs will be saved here
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save(obj, name):
    path = f"{OUTPUT_DIR}/{name}.json"
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"  ✓ {name}.json saved")

# ── Load data ─────────────────────────────────────────────────────────────────
print(f"\nLoading {INPUT_FILE} ...")
D = pd.read_csv(INPUT_FILE, low_memory=False)
print(f"  Loaded {len(D):,} rows | {D['match_id'].nunique()} matches | {D['year'].nunique()} seasons")

# ── Derived columns ───────────────────────────────────────────────────────────
D['is_six']     = (D['runs_batter'] == 6).astype(int)
D['is_four']    = (D['runs_batter'] == 4).astype(int)
D['is_wicket']  = D['wicket_kind'].notna() & (D['wicket_kind'] != '') & (D['wicket_kind'].astype(str) != 'nan')
D['is_legal']   = (D['valid_ball'] == 1)

print("\nGenerating JSONs...\n")

# ══════════════════════════════════════════════════════════════════════════════
# 1. OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
season_g = D.groupby('year').agg(
    runs    =('runs_total', 'sum'),
    sixes   =('is_six', 'sum'),
    wickets =('is_wicket', 'sum'),
).reset_index()

match_counts = D.groupby('year')['match_id'].nunique().reset_index(name='matches')
season_g = season_g.merge(match_counts, on='year')
season_g = season_g.sort_values('year')

season_stats = []
for _, r in season_g.iterrows():
    season_stats.append({
        'season':  int(r['year']),
        'matches': int(r['matches']),
        'runs':    int(r['runs']),
        'sixes':   int(r['sixes']),
        'wickets': int(r['wickets']),
    })

# team wins
match_level = D.drop_duplicates('match_id')[['match_id','match_won_by','toss_winner','toss_decision']].copy()
team_wins = match_level['match_won_by'].value_counts().head(15).to_dict()
team_wins = {k: int(v) for k, v in team_wins.items() if isinstance(k, str) and k not in ['NA','nan','']}

# toss advantage
toss_won_match = (match_level['toss_winner'] == match_level['match_won_by']).mean()

# head to head top pairs
pairs_raw = D.drop_duplicates('match_id')[['match_id','batting_team','bowling_team','match_won_by']].copy()
h2h_list = []
top_teams = list(team_wins.keys())[:8]
done = set()
for t1 in top_teams:
    for t2 in top_teams:
        if t1 >= t2 or (t1,t2) in done: continue
        sub = pairs_raw[
            ((pairs_raw['batting_team']==t1)|(pairs_raw['bowling_team']==t1)) &
            ((pairs_raw['batting_team']==t2)|(pairs_raw['bowling_team']==t2))
        ]
        if len(sub) < 5: continue
        t1w = int((sub['match_won_by']==t1).sum())
        t2w = int((sub['match_won_by']==t2).sum())
        h2h_list.append({'team1':t1,'team2':t2,'matches':int(len(sub)),'team1_wins':t1w,'team2_wins':t2w})
        done.add((t1,t2))
h2h_list = sorted(h2h_list, key=lambda x: x['matches'], reverse=True)[:10]

total_runs    = int(D['runs_total'].sum())
total_wickets = int(D['is_wicket'].sum())
total_matches = int(D['match_id'].nunique())
total_sixes   = int(D['is_six'].sum())
total_fours   = int(D['is_four'].sum())

save({
    'total_matches':     total_matches,
    'total_seasons':     int(D['year'].nunique()),
    'total_runs':        total_runs,
    'total_wickets':     total_wickets,
    'total_sixes':       total_sixes,
    'total_fours':       total_fours,
    'avg_runs_per_match': round(total_runs / total_matches, 1),
    'toss_win_pct':      round(toss_won_match * 100, 1),
    'season_stats':      season_stats,
    'team_wins':         team_wins,
    'head_to_head':      h2h_list,
}, 'overview')

# ══════════════════════════════════════════════════════════════════════════════
# 2. BATTING
# ══════════════════════════════════════════════════════════════════════════════
legal = D[D['is_legal'] == True].copy()

bat = legal.groupby('batter').agg(
    total_runs  =('runs_batter', 'sum'),
    balls       =('runs_batter', 'count'),
    fours       =('is_four', 'sum'),
    sixes       =('is_six', 'sum'),
).reset_index()

# innings count
inn = legal.groupby(['match_id','innings','batter'])['runs_batter'].sum().reset_index()
inn_count = inn.groupby('batter').size().reset_index(name='innings')
bat = bat.merge(inn_count, on='batter', how='left')

# dismissals
dismissed = legal[D['is_wicket'] & legal['player_out'].notna()].groupby('player_out').size().reset_index(name='dismissals')
dismissed.columns = ['batter', 'dismissals']
bat = bat.merge(dismissed, on='batter', how='left')
bat['dismissals'] = bat['dismissals'].fillna(1)

# highest score per innings
hs = inn.groupby('batter')['runs_batter'].max().reset_index(name='highest')
bat = bat.merge(hs, on='batter', how='left')

bat['average']      = (bat['total_runs'] / bat['dismissals']).round(1)
bat['strike_rate']  = (bat['total_runs'] / bat['balls'] * 100).round(1)
bat['impact_score'] = (bat['total_runs']*0.4 + bat['strike_rate']*0.3 + bat['average']*0.3).round(1)

bat = bat[bat["innings"] >= 1].sort_values("total_runs", ascending=False)

leaderboard = []
for _, r in bat.iterrows():
    leaderboard.append({
        'batter':       str(r['batter']),
        'total_runs':   int(r['total_runs']),
        'innings':      int(r['innings']),
        'average':      float(r['average']),
        'strike_rate':  float(r['strike_rate']),
        'fours':        int(r['fours']),
        'sixes':        int(r['sixes']),
        'highest':      int(r['highest']),
        'impact_score': float(r['impact_score']),
    })
# ── Merge 2026 batting CSV if available ──────────────────────────────────────
if os.path.exists(BATTING_2026):
    b26 = pd.read_csv(BATTING_2026)
    b26 = b26.rename(columns={'player':'batter','runs':'total_runs','inns':'innings',
                               'avg':'average','sr':'strike_rate','4s':'fours','6s':'sixes','hs':'highest_str'})
    b26['highest'] = b26['highest_str'].astype(str).str.replace('*','').apply(
        lambda x: int(x) if x.replace('.','').isdigit() else 0)
    b26['impact_score'] = (b26['total_runs']*0.4 + b26['strike_rate']*0.3 + b26['average']*0.3).round(1)
    b26 = b26[['batter','total_runs','innings','average','strike_rate','fours','sixes','highest','impact_score']]
    # update existing players, add new ones
    existing = {r['batter']: i for i, r in enumerate(leaderboard)}
    for _, r in b26.iterrows():
        name = str(r['batter'])
        entry = {
            'batter': name, 'total_runs': int(r['total_runs']), 'innings': int(r['innings']),
            'average': float(r['average']), 'strike_rate': float(r['strike_rate']),
            'fours': int(r['fours']), 'sixes': int(r['sixes']),
            'highest': int(r['highest']), 'impact_score': float(r['impact_score']),
        }
        if name in existing:
            leaderboard[existing[name]] = entry
        else:
            leaderboard.append(entry)
    leaderboard = sorted(leaderboard, key=lambda x: x['total_runs'], reverse=True)[:50]
    print("  ✓ 2026 batting data merged")

save({'leaderboard': leaderboard}, 'batting')

# ══════════════════════════════════════════════════════════════════════════════
# 3. BOWLING
# ══════════════════════════════════════════════════════════════════════════════
bowl = D.groupby('bowler').agg(
    wickets       =('is_wicket', 'sum'),
    runs_conceded =('runs_bowler', 'sum'),
    balls         =('valid_ball', 'sum'),
).reset_index()

bowl['overs']       = bowl['balls'] / 6
bowl['economy']     = (bowl['runs_conceded'] / bowl['overs'].replace(0, np.nan)).round(2).fillna(0)
bowl['average']     = (bowl['runs_conceded'] / bowl['wickets'].replace(0, np.nan)).round(2).fillna(0)
bowl['strike_rate'] = (bowl['balls'] / bowl['wickets'].replace(0, np.nan)).round(2).fillna(0)

# 4wkt / 5wkt hauls
wi = D[D['is_wicket']].groupby(['match_id','innings','bowler'])['is_wicket'].sum().reset_index(name='wkts')
bowl4 = wi[wi['wkts'] >= 4].groupby('bowler').size().reset_index(name='four_wkt_hauls')
bowl5 = wi[wi['wkts'] >= 5].groupby('bowler').size().reset_index(name='five_wkt_hauls')
bowl = bowl.merge(bowl4, on='bowler', how='left').merge(bowl5, on='bowler', how='left')
bowl[['four_wkt_hauls','five_wkt_hauls']] = bowl[['four_wkt_hauls','five_wkt_hauls']].fillna(0)

bowl = bowl[bowl["wickets"] >= 1].sort_values("wickets", ascending=False)

bl = []
for _, r in bowl.iterrows():
    bl.append({
        'bowler':          str(r['bowler']),
        'wickets':         int(r['wickets']),
        'economy':         float(r['economy']),
        'average':         float(r['average']),
        'strike_rate':     float(r['strike_rate']),
        'four_wkt_hauls':  int(r['four_wkt_hauls']),
        'five_wkt_hauls':  int(r['five_wkt_hauls']),
    })
# ── Merge 2026 bowling CSV if available ──────────────────────────────────────
if os.path.exists(BOWLING_2026):
    bw26 = pd.read_csv(BOWLING_2026)
    bw26 = bw26.rename(columns={'player':'bowler','wkts':'wickets','econ':'economy',
                                  'avg':'average','sr':'strike_rate','4w':'four_wkt_hauls','5w':'five_wkt_hauls'})
    bw26['impact_score'] = 0
    bw26 = bw26[['bowler','wickets','economy','average','strike_rate','four_wkt_hauls','five_wkt_hauls']]
    existing_b = {r['bowler']: i for i, r in enumerate(bl)}
    for _, r in bw26.iterrows():
        name = str(r['bowler'])
        entry = {
            'bowler': name, 'wickets': int(r['wickets']),
            'economy': float(r['economy']), 'average': float(r['average']),
            'strike_rate': float(r['strike_rate']),
            'four_wkt_hauls': int(r['four_wkt_hauls']),
            'five_wkt_hauls': int(r['five_wkt_hauls']),
        }
        if name in existing_b:
            bl[existing_b[name]] = entry
        else:
            bl.append(entry)
    bl = sorted(bl, key=lambda x: x['wickets'], reverse=True)[:50]
    print("  ✓ 2026 bowling data merged")

save({'leaderboard': bl}, 'bowling')

# ══════════════════════════════════════════════════════════════════════════════
# 4. VENUES
# ══════════════════════════════════════════════════════════════════════════════
match_info = D.drop_duplicates('match_id')[['match_id','venue','toss_decision','toss_winner','match_won_by']].copy()

# innings scores
inn_scores = D.groupby(['match_id','innings'])['runs_total'].sum().reset_index()
inn1 = inn_scores[inn_scores['innings']==1].rename(columns={'runs_total':'inn1_score'})
inn2 = inn_scores[inn_scores['innings']==2].rename(columns={'runs_total':'inn2_score'})
match_scores = match_info.merge(inn1[['match_id','inn1_score']], on='match_id', how='left')
match_scores = match_scores.merge(inn2[['match_id','inn2_score']], on='match_id', how='left')

match_scores['bat_first_won'] = (
    ((match_scores['toss_decision']=='bat') & (match_scores['toss_winner']==match_scores['match_won_by'])) |
    ((match_scores['toss_decision']=='field') & (match_scores['toss_winner']!=match_scores['match_won_by']))
)

vg = match_scores.groupby('venue').agg(
    matches        =('match_id','count'),
    bat_first_wins =('bat_first_won','sum'),
    avg_first      =('inn1_score','mean'),
    avg_second     =('inn2_score','mean'),
).reset_index()

# boundary % from deliveries
b_pct = D.groupby('venue').apply(
    lambda x: round((x['is_six'].sum() + x['is_four'].sum()) / max(len(x),1) * 100, 1)
).reset_index(name='boundary_pct')
vg = vg.merge(b_pct, on='venue', how='left')

vg['chase_wins']        = vg['matches'] - vg['bat_first_wins']
vg['bat_first_win_pct'] = (vg['bat_first_wins'] / vg['matches'] * 100).round(1)
vg = vg[vg['matches'] >= 5].sort_values('matches', ascending=False).head(14)

def pitch_type(row):
    pct = row['bat_first_win_pct']
    avg = (row['avg_first'] + row['avg_second']) / 2
    if pct > 56: return 'Bat First Venue'
    if pct < 44: return 'Chase Friendly'
    if avg > 175: return 'Batting Paradise'
    if avg > 168: return 'Batting Friendly'
    return 'Balanced'

def boundary_opp(pct):
    if pct > 50: return 'Very High'
    if pct > 45: return 'High'
    if pct > 38: return 'Medium'
    return 'Low'

venues = []
for _, r in vg.iterrows():
    bp = float(r['boundary_pct']) if pd.notna(r['boundary_pct']) else 44.0
    venues.append({
        'venue':               str(r['venue']),
        'matches':             int(r['matches']),
        'bat_first_wins':      int(r['bat_first_wins']),
        'chase_wins':          int(r['chase_wins']),
        'bat_first_win_pct':   float(r['bat_first_win_pct']),
        'avg_first_innings':   round(float(r['avg_first']) if pd.notna(r['avg_first']) else 160, 1),
        'avg_second_innings':  round(float(r['avg_second']) if pd.notna(r['avg_second']) else 155, 1),
        'pitch_type':          pitch_type(r),
        'boundary_opportunity': boundary_opp(bp),
        'boundary_pct':        bp,
    })
save({'venues': venues, 'toss_win_pct': round(toss_won_match * 100, 1)}, 'venues')

# ══════════════════════════════════════════════════════════════════════════════
# 5. SEASON LEADERS
# ══════════════════════════════════════════════════════════════════════════════
seasons_out = []
for season in sorted(D['year'].unique()):
    sd  = D[D['year'] == season]
    sl  = legal[legal['year'] == season]

    # top 5 batsmen
    tb = sl.groupby('batter')['runs_batter'].sum().nlargest(5).reset_index()
    tb.columns = ['player', 'runs']

    # top 5 bowlers
    tw = sd[sd['is_wicket']].groupby('bowler')['is_wicket'].sum().nlargest(5).reset_index()
    tw.columns = ['player', 'wickets']

    if tb.empty or tw.empty: continue

    seasons_out.append({
        'season':      int(season),
        'orange_cap':  {'player': str(tb.iloc[0]['player']), 'runs': int(tb.iloc[0]['runs'])},
        'purple_cap':  {'player': str(tw.iloc[0]['player']), 'wickets': int(tw.iloc[0]['wickets'])},
        'top_batsmen': [{'player': str(r['player']), 'runs': int(r['runs'])} for _, r in tb.iterrows()],
        'top_bowlers': [{'player': str(r['player']), 'wickets': int(r['wickets'])} for _, r in tw.iterrows()],
    })
save({'seasons': seasons_out}, 'season_leaders')

# ══════════════════════════════════════════════════════════════════════════════
# 6. ADVANCED (impact scores)
# ══════════════════════════════════════════════════════════════════════════════
adv_list = []
for _, r in bat.iterrows():
    adv_list.append({
        'player':       str(r['batter']),
        'runs':         int(r['total_runs']),
        'avg':          float(r['average']),
        'sr':           float(r['strike_rate']),
        'innings':      int(r['innings']),
        'sixes':        int(r['sixes']),
        'impact_score': float(r['impact_score']),
    })
save({'impact_scores': adv_list}, 'advanced')

# ══════════════════════════════════════════════════════════════════════════════
# 7. SIMILARITY
# ══════════════════════════════════════════════════════════════════════════════
try:
    from sklearn.preprocessing import MinMaxScaler
    bat_feat = bat[['batter','total_runs','average','strike_rate','sixes']].dropna()
    bat_feat = bat_feat[bat_feat['total_runs'] > 500].reset_index(drop=True)

    scaler      = MinMaxScaler()
    feat_scaled = scaler.fit_transform(bat_feat[['total_runs','average','strike_rate','sixes']])

    sim_out  = {}
    players  = bat_feat['batter'].tolist()
    for i, p in enumerate(players[:25]):
        dists   = np.sqrt(((feat_scaled - feat_scaled[i])**2).sum(axis=1))
        top5    = np.argsort(dists)[1:6]
        sim_out[p] = [[players[j], round(max(0, 1 - float(dists[j])), 3)] for j in top5]
    save(sim_out, 'similarity')
except ImportError:
    print("  ⚠ sklearn not found — install with: pip install scikit-learn")
    save({}, 'similarity')

# ══════════════════════════════════════════════════════════════════════════════
print("\n✅ Done! All 7 JSONs saved in /data folder")
print(f"   Total matches processed : {total_matches:,}")
print(f"   Total runs               : {total_runs:,}")
print(f"   Total wickets            : {total_wickets:,}")
print(f"   Seasons covered          : {D['year'].min()} – {D['year'].max()}")
