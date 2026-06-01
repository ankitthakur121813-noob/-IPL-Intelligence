import pandas as pd, json

df = pd.read_csv('IPL.csv', low_memory=False)
legal = df[df['valid_ball']==1]
bat = legal.groupby('batter')['runs_batter'].sum().reset_index()
bat.columns = ['batter','runs']
bat = bat.sort_values('runs', ascending=False)
print('Total batters in IPL.csv:', len(bat))
print('\nTop 10:')
print(bat.head(10).to_string())

# Check current batting.json
with open('data/batting.json') as f:
    bj = json.load(f)
print(f'\nPlayers in batting.json: {len(bj["leaderboard"])}')
print('First 5:', [x["batter"] for x in bj["leaderboard"][:5]])
