import pandas as pd
import numpy as np
import json
import os

print("Loading IPL.csv...")
D = pd.read_csv('IPL.csv', low_memory=False)
print(f"Loaded {len(D):,} rows")

D['is_six']    = (D['runs_batter'] == 6).astype(int)
D['is_four']   = (D['runs_batter'] == 4).astype(int)
D['is_wicket'] = D['wicket_kind'].notna() & (D['wicket_kind'].astype(str) != 'nan')
D['is_legal']  = (D['valid_ball'] == 1)

legal = D[D['is_legal'] == True].copy()

# ── BATTING ───────────────────────────────────────────────────────────────────
print("Building batting data...")
bat = legal.groupby('batter').agg(
    total_runs =('runs_batter', 'sum'),
    balls      =('runs_batter', 'count'),
    fours      =('is_four', 'sum'),
    sixes      =('is_six', 'sum'),
).reset_index()

inn = legal.groupby(['match_id','innings','batter'])['runs_batter'].sum().reset_index()
inn_count = inn.groupby('batter').size().reset_index(name='innings')
bat = bat.merge(inn_count, on='batter', how='left')

dismissed = D[D['is_wicket'] & D['player_out'].notna()].groupby('player_out').size().reset_index(name='dismissals')
dismissed.columns = ['batter','dismissals']
bat = bat.merge(dismissed, on='batter', how='left')
bat['dismissals'] = bat['dismissals'].fillna(1)

hs = inn.groupby('batter')['runs_batter'].max().reset_index(name='highest')
bat = bat.merge(hs, on='batter', how='left')

bat['average']      = (bat['total_runs'] / bat['dismissals']).round(1)
bat['strike_rate']  = (bat['total_runs'] / bat['balls'] * 100).round(1)
bat['impact_score'] = (bat['total_runs']*0.4 + bat['strike_rate']*0.3 + bat['average']*0.3).round(1)

# NO FILTER — all players
bat = bat.sort_values('total_runs', ascending=False)
print(f"Total batters: {len(bat)}")

# Merge 2026 batting CSV
if os.path.exists('ipl_2026_batting.csv'):
    b26 = pd.read_csv('ipl_2026_batting.csv')
    b26 = b26.rename(columns={'player':'batter','runs':'total_runs','inns':'innings',
                               'avg':'average','sr':'strike_rate','4s':'fours','6s':'sixes','hs':'highest_str'})
    b26['highest'] = b26['highest_str'].astype(str).str.replace('*','',regex=False)
    b26['highest'] = pd.to_numeric(b26['highest'], errors='coerce').fillna(0).astype(int)
    b26['impact_score'] = (b26['total_runs']*0.4 + b26['strike_rate']*0.3 + b26['average']*0.3).round(1)
    print(f"2026 batting players: {len(b26)}")

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
        'highest':      int(r['highest']) if pd.notna(r['highest']) else 0,
        'impact_score': float(r['impact_score']),
    })

# Merge 2026
if os.path.exists('ipl_2026_batting.csv'):
    existing = {r['batter']: i for i, r in enumerate(leaderboard)}
    for _, r in b26.iterrows():
        name = str(r['batter'])
        entry = {
            'batter': name, 'total_runs': int(r['total_runs']),
            'innings': int(r['innings']), 'average': float(r['average']),
            'strike_rate': float(r['strike_rate']), 'fours': int(r['fours']),
            'sixes': int(r['sixes']), 'highest': int(r['highest']),
            'impact_score': float(r['impact_score']),
        }
        if name in existing:
            leaderboard[existing[name]] = entry
        else:
            leaderboard.append(entry)
    leaderboard = sorted(leaderboard, key=lambda x: x['total_runs'], reverse=True)
    print(f"After 2026 merge: {len(leaderboard)} players")

with open('data/batting.json', 'w') as f:
    json.dump({'leaderboard': leaderboard}, f, indent=2)
print(f"✓ batting.json saved — {len(leaderboard)} players")

# ── BOWLING ───────────────────────────────────────────────────────────────────
print("\nBuilding bowling data...")
bowl = D.groupby('bowler').agg(
    wickets       =('is_wicket', 'sum'),
    runs_conceded =('runs_bowler', 'sum'),
    balls         =('valid_ball', 'sum'),
).reset_index()

bowl['overs']       = bowl['balls'] / 6
bowl['economy']     = (bowl['runs_conceded'] / bowl['overs'].replace(0, np.nan)).round(2).fillna(0)
bowl['average']     = (bowl['runs_conceded'] / bowl['wickets'].replace(0, np.nan)).round(2).fillna(0)
bowl['strike_rate'] = (bowl['balls'] / bowl['wickets'].replace(0, np.nan)).round(2).fillna(0)

wi    = D[D['is_wicket']].groupby(['match_id','innings','bowler'])['is_wicket'].sum().reset_index(name='wkts')
bowl4 = wi[wi['wkts']>=4].groupby('bowler').size().reset_index(name='four_wkt_hauls')
bowl5 = wi[wi['wkts']>=5].groupby('bowler').size().reset_index(name='five_wkt_hauls')
bowl  = bowl.merge(bowl4, on='bowler', how='left').merge(bowl5, on='bowler', how='left')
bowl[['four_wkt_hauls','five_wkt_hauls']] = bowl[['four_wkt_hauls','five_wkt_hauls']].fillna(0)

# NO FILTER — all bowlers
bowl = bowl.sort_values('wickets', ascending=False)
print(f"Total bowlers: {len(bowl)}")

bl = []
for _, r in bowl.iterrows():
    bl.append({
        'bowler':         str(r['bowler']),
        'wickets':        int(r['wickets']),
        'economy':        float(r['economy']),
        'average':        float(r['average']),
        'strike_rate':    float(r['strike_rate']),
        'four_wkt_hauls': int(r['four_wkt_hauls']),
        'five_wkt_hauls': int(r['five_wkt_hauls']),
    })

# Merge 2026 bowling
if os.path.exists('ipl_2026_bowling.csv'):
    bw26 = pd.read_csv('ipl_2026_bowling.csv')
    bw26 = bw26.rename(columns={'player':'bowler','wkts':'wickets','econ':'economy',
                                  'avg':'average','sr':'strike_rate','4w':'four_wkt_hauls','5w':'five_wkt_hauls'})
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
    bl = sorted(bl, key=lambda x: x['wickets'], reverse=True)
    print(f"After 2026 merge: {len(bl)} bowlers")

with open('data/bowling.json', 'w') as f:
    json.dump({'leaderboard': bl}, f, indent=2)
print(f"✓ bowling.json saved — {len(bl)} bowlers")

print("\n✅ Done! All players included.")
