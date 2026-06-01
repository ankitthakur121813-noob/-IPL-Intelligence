import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

st.set_page_config(
    page_title="IPL Intelligence Platform",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  /* ── Base ── */
  [data-testid="stAppViewContainer"] { background: #0f1117; }
  [data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #1e293b; }
  [data-testid="stSidebar"] * { color: #94a3b8 !important; }

  /* ── Stat cards ── */
  .stat-card {
    background: #1e293b; border-radius: 12px; padding: 16px;
    border-left: 4px solid var(--accent); margin-bottom: 12px;
  }
  .stat-value { font-size: 1.6rem; font-weight: 700; color: #f1f5f9; }
  .stat-label { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }
  .stat-sub   { font-size: 0.7rem; color: #475569; margin-top: 4px; }

  /* ── Insight cards ── */
  .insight-card {
    background: #1e293b; border-radius: 10px; padding: 16px;
    margin-bottom: 10px; border: 1px solid #334155;
  }
  .insight-icon  { font-size: 1.4rem; }
  .insight-title { font-weight: 600; color: #f1f5f9; margin: 6px 0 4px; font-size: 0.95rem; }
  .insight-text  { font-size: 0.82rem; color: #94a3b8; }

  /* ── Typography ── */
  h1, h2, h3 { color: #f1f5f9 !important; }
  p, li, label { color: #94a3b8 !important; }

  /* ── Responsive tables ── */
  [data-testid="stDataFrame"] { width: 100% !important; }

  /* ── Mobile: hide sidebar by default ── */
  @media (max-width: 768px) {
    .stat-value { font-size: 1.2rem; }
    .stat-card  { padding: 12px; }
  }
</style>
""", unsafe_allow_html=True)

# ── Data ─────────────────────────────────────────────────────────────────────
DATA_DIR = "data"

@st.cache_data
def load(key):
    path = os.path.join(DATA_DIR, f"{key}.json")
    with open(path, "r") as f:
        return json.load(f)

TEAM_CLR = {
    "Mumbai Indians": "#1d4ed8", "Chennai Super Kings": "#ca8a04",
    "Royal Challengers Bangalore": "#dc2626", "Royal Challengers Bengaluru": "#dc2626",
    "Kolkata Knight Riders": "#7c3aed", "Delhi Capitals": "#2563eb",
    "Punjab Kings": "#b91c1c", "Kings XI Punjab": "#b91c1c",
    "Rajasthan Royals": "#db2777", "Sunrisers Hyderabad": "#ea580c",
    "Gujarat Titans": "#0d9488", "Lucknow Super Giants": "#0ea5e9",
    "Deccan Chargers": "#64748b", "Delhi Daredevils": "#2563eb",
}
TEAM_SHORT = {
    "Mumbai Indians": "MI", "Chennai Super Kings": "CSK",
    "Royal Challengers Bangalore": "RCB", "Royal Challengers Bengaluru": "RCB",
    "Kolkata Knight Riders": "KKR", "Delhi Capitals": "DC",
    "Punjab Kings": "PBKS", "Kings XI Punjab": "PBKS",
    "Rajasthan Royals": "RR", "Sunrisers Hyderabad": "SRH",
    "Gujarat Titans": "GT", "Lucknow Super Giants": "LSG",
    "Deccan Chargers": "DC-old", "Delhi Daredevils": "DD",
}

def dark_layout(fig, height=400):
    fig.update_layout(
        height=height,
        paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
        font=dict(color="#94a3b8", family="sans-serif"),
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#334155"),
        xaxis=dict(gridcolor="#1e293b", zerolinecolor="#1e293b"),
        yaxis=dict(gridcolor="#1e293b", zerolinecolor="#1e293b"),
    )
    return fig

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ◈ IPL *Intelligence*")
    st.caption("2008 – 2026 · 19 Seasons")
    st.divider()
    tab = st.radio("Navigate", [
        "Overview", "Batting", "Bowling", "Venues",
        "Season Leaders", "Advanced", "Moneyball", "Records"
    ], label_visibility="collapsed")
    st.divider()
    st.caption("Data: 1,193 matches · 19 seasons · 2008–2026")

# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if tab == "Overview":
    ov    = load("overview")
    ss    = ov["season_stats"]
    df_ss = pd.DataFrame(ss)

    st.title("🏏 IPL Intelligence Platform")
    st.caption("2008–2026 · Complete Statistical Dashboard")

    six_start = ss[5]["sixes"]
    six_end   = ss[-1]["sixes"]
    six_pct   = round(((six_end - six_start) / six_start) * 100)
    top_team  = max(ov["team_wins"], key=ov["team_wins"].get)
    top_wins  = ov["team_wins"][top_team]
    rpm_last  = round(ss[-1]["runs"] / ss[-1]["matches"])

    c1, c2, c3 = st.columns(3)
    for col, icon, title, text in [
        (c1, "📈", "Sixes Explosion",
         f"From {six_start} (2013) to {six_end} in {ss[-1]['season']} — a **{six_pct}%** surge."),
        (c2, "🏆", "All-Time Leaders",
         f"**{top_team}** leads with **{top_wins} wins**."),
        (c3, "⚡", "Scoring Rate",
         f"{ss[-1]['season']} season averaged **{rpm_last} runs/match**."),
    ]:
        col.markdown(f"""<div class="insight-card">
            <div class="insight-icon">{icon}</div>
            <div class="insight-title">{title}</div>
            <div class="insight-text">{text}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    sc = st.columns(6)
    stats = [
        ("Seasons",    ov["total_seasons"],              "2008–2026",         "#f97316"),
        ("Matches",    ov["total_matches"],              "all matches",       "#3b82f6"),
        ("Total Runs", f"{ov['total_runs']/1000:.0f}K", "combined runs",     "#eab308"),
        ("Wickets",    ov["total_wickets"],              "all dismissals",    "#a855f7"),
        ("Sixes",      ov["total_sixes"],                "maximum hits",      "#14b8a6"),
        ("Avg/Match",  ov["avg_runs_per_match"],         "combined innings",  "#ef4444"),
    ]
    for col, (label, val, sub, color) in zip(sc, stats):
        col.markdown(f"""<div class="stat-card" style="--accent:{color}">
            <div class="stat-label">{label}</div>
            <div class="stat-value" style="color:{color}">{val}</div>
            <div class="stat-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.subheader("Season Trends")
    metric   = st.radio("Metric", ["runs","sixes","wickets"], horizontal=True, key="ov_m")
    color_map = {"runs":"#f97316","sixes":"#14b8a6","wickets":"#a855f7"}
    fill_map  = {"runs":"rgba(249,115,22,0.2)","sixes":"rgba(20,184,166,0.2)","wickets":"rgba(168,85,247,0.2)"}
    fig = px.area(df_ss, x="season", y=metric, color_discrete_sequence=[color_map[metric]])
    fig.update_traces(line_width=2, fillcolor=fill_map[metric])
    dark_layout(fig, 350)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("All-Time Team Wins")
        sorted_teams = sorted(ov["team_wins"].items(), key=lambda x: x[1], reverse=True)
        # filter out noise
        sorted_teams = [(k,v) for k,v in sorted_teams if k not in ["Unknown","nan",""] and isinstance(k,str)][:12]
        df_tw = pd.DataFrame(sorted_teams, columns=["Team","Wins"])
        df_tw["Short"] = df_tw["Team"].map(TEAM_SHORT).fillna(df_tw["Team"].str[:3])
        df_tw["Color"] = df_tw["Team"].map(TEAM_CLR).fillna("#64748b")
        fig2 = go.Figure(go.Bar(
            x=df_tw["Wins"], y=df_tw["Short"], orientation="h",
            marker_color=df_tw["Color"].tolist(),
            text=df_tw["Wins"], textposition="outside",
        ))
        dark_layout(fig2, 380)
        fig2.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig2, use_container_width=True)

    with col_r:
        st.subheader("Head to Head")
        df_h2h = pd.DataFrame(ov["head_to_head"])
        df_h2h["T1 Win%"] = (df_h2h["team1_wins"]/df_h2h["matches"]*100).round(0).astype(int).astype(str)+"%"
        df_h2h.columns = ["Team 1","Team 2","Matches","T1 Wins","T2 Wins","T1 Win%"]
        st.dataframe(df_h2h, use_container_width=True, hide_index=True, height=380)

# ══════════════════════════════════════════════════════════════════════════════
# BATTING
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "Batting":
    bat    = load("batting")
    sim    = load("similarity")
    df_bat = pd.DataFrame(bat["leaderboard"])

    st.title("🏏 Batting Analytics")

    col_f1, col_f2, col_f3 = st.columns([3, 1, 1])
    search      = col_f1.text_input("🔍 Search player", placeholder="e.g. Kohli, Gill, Sharma")
    min_innings = col_f2.number_input("Min innings", min_value=1, max_value=300, value=1)
    min_runs    = col_f3.number_input("Min runs", min_value=0, max_value=10000, value=0, step=100)

    df_filtered = df_bat[
        (df_bat["innings"] >= min_innings) &
        (df_bat["total_runs"] >= min_runs)
    ]
    if search.strip():
        df_filtered = df_filtered[
            df_filtered["batter"].str.contains(search.strip(), case=False, na=False)
        ]

    st.caption(f"Showing {len(df_filtered)} players")
    st.divider()

    st.subheader("Batting Leaderboard")
    sort_col = st.selectbox("Sort by", ["total_runs","average","strike_rate","sixes","impact_score"])
    df_sorted = df_filtered.sort_values(sort_col, ascending=False).reset_index(drop=True)
    st.dataframe(df_sorted, use_container_width=True, hide_index=True, height=350)

    st.divider()
    st.subheader("Strike Rate vs Average")
    df_scatter = df_bat[df_bat["total_runs"] >= 500].copy()
    df_scatter["elite"] = df_scatter["total_runs"] >= 4000
    fig_sc = px.scatter(
        df_scatter, x="average", y="strike_rate",
        size="total_runs", color="elite",
        color_discrete_map={True:"#f97316", False:"#3b82f6"},
        hover_name="batter",
        hover_data={"total_runs":True,"average":True,"strike_rate":True,"elite":False},
        size_max=40,
        labels={"average":"Batting Average","strike_rate":"Strike Rate"},
    )
    dark_layout(fig_sc, 450)
    fig_sc.update_layout(showlegend=False)
    st.plotly_chart(fig_sc, use_container_width=True)

    st.divider()
    st.subheader("Player Similarity Finder")
    players  = list(sim.keys())
    selected = st.selectbox("Select player", players)
    if selected and selected in sim:
        df_sim = pd.DataFrame(sim[selected], columns=["Similar Player","Similarity Score"])
        st.dataframe(df_sim, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# BOWLING
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "Bowling":
    bowl    = load("bowling")
    df_bowl = pd.DataFrame(bowl["leaderboard"])

    st.title("🎳 Bowling Analytics")

    col_b1, col_b2 = st.columns([3,1])
    search_b   = col_b1.text_input("🔍 Search bowler", placeholder="e.g. Bumrah, Chahal, Rashid")
    min_wickets = col_b2.number_input("Min wickets", min_value=1, max_value=300, value=1)

    df_bf = df_bowl[df_bowl["wickets"] >= min_wickets].copy()
    if search_b.strip():
        df_bf = df_bf[df_bf["bowler"].str.contains(search_b.strip(), case=False, na=False)]

    st.caption(f"Showing {len(df_bf)} bowlers")
    st.divider()

    st.subheader("Bowling Leaderboard")
    sort_b = st.selectbox("Sort by", ["wickets","economy","average","strike_rate"])
    asc    = sort_b in ["economy","average","strike_rate"]
    df_bs  = df_bf.sort_values(sort_b, ascending=asc).reset_index(drop=True)
    st.dataframe(df_bs, use_container_width=True, hide_index=True, height=350)

    st.divider()
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.subheader("Top Wicket Takers")
        df_top = df_bowl.nlargest(10,"wickets")
        fig_wk = px.bar(df_top, x="wickets", y="bowler", orientation="h",
                        color="wickets", color_continuous_scale="Blues", text="wickets")
        fig_wk.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        dark_layout(fig_wk, 380)
        st.plotly_chart(fig_wk, use_container_width=True)

    with col_c2:
        st.subheader("Economy vs Wickets")
        fig_ec = px.scatter(df_bowl, x="economy", y="wickets",
                            hover_name="bowler",
                            color="wickets", color_continuous_scale="Oranges",
                            size="wickets", size_max=30)
        fig_ec.update_layout(coloraxis_showscale=False)
        dark_layout(fig_ec, 380)
        st.plotly_chart(fig_ec, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# VENUES
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "Venues":
    ven    = load("venues")
    df_ven = pd.DataFrame(ven["venues"])
    df_ven["venue_short"]   = df_ven["venue"].str.split(",").str[0]
    df_ven["chase_win_pct"] = (100 - df_ven["bat_first_win_pct"]).round(1)

    st.title("🏟️ Venue Analysis")
    st.divider()

    st.subheader("Bat First vs Chase Win %")
    fig_ven = go.Figure()
    fig_ven.add_trace(go.Bar(
        name="Bat First Win%", x=df_ven["venue_short"], y=df_ven["bat_first_win_pct"],
        marker_color="#f97316",
        text=df_ven["bat_first_win_pct"].round(0).astype(int).astype(str)+"%",
        textposition="outside",
    ))
    fig_ven.add_trace(go.Bar(
        name="Chase Win%", x=df_ven["venue_short"], y=df_ven["chase_win_pct"],
        marker_color="#3b82f6",
        text=df_ven["chase_win_pct"].round(0).astype(int).astype(str)+"%",
        textposition="outside",
    ))
    fig_ven.update_layout(barmode="group", xaxis_tickangle=-45)
    dark_layout(fig_ven, 420)
    st.plotly_chart(fig_ven, use_container_width=True)

    st.divider()
    st.subheader("Venue Details")
    df_display = df_ven[["venue_short","matches","avg_first_innings",
                          "avg_second_innings","pitch_type","boundary_opportunity","boundary_pct"]].copy()
    df_display.columns = ["Venue","Matches","Avg 1st Inn","Avg 2nd Inn","Pitch Type","Boundary Opp","Boundary %"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Avg First vs Second Innings")
    fig_inn = px.scatter(
        df_ven, x="avg_first_innings", y="avg_second_innings",
        text="venue_short", color="pitch_type", size="matches", size_max=30,
        labels={"avg_first_innings":"Avg First Innings","avg_second_innings":"Avg Second Innings"},
    )
    fig_inn.update_traces(textposition="top center")
    dark_layout(fig_inn, 420)
    st.plotly_chart(fig_inn, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# SEASON LEADERS
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "Season Leaders":
    sl      = load("season_leaders")
    seasons = sl["seasons"]

    st.title("🏅 Season Leaders")
    st.divider()

    selected_season = st.select_slider("Select Season", options=[s["season"] for s in seasons])
    season_data     = next(s for s in seasons if s["season"] == selected_season)

    col_o, col_p = st.columns(2)
    col_o.metric("🟠 Orange Cap", season_data["orange_cap"]["player"],
                 f"{season_data['orange_cap']['runs']} runs")
    col_p.metric("🟣 Purple Cap", season_data["purple_cap"]["player"],
                 f"{season_data['purple_cap']['wickets']} wickets")

    st.divider()
    col_tb, col_tw = st.columns(2)

    with col_tb:
        st.subheader("Top Batsmen")
        df_tb  = pd.DataFrame(season_data["top_batsmen"])
        fig_tb = px.bar(df_tb, x="runs", y="player", orientation="h",
                        color="runs", color_continuous_scale="Oranges", text="runs")
        fig_tb.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        dark_layout(fig_tb, 280)
        st.plotly_chart(fig_tb, use_container_width=True)

    with col_tw:
        st.subheader("Top Bowlers")
        df_tw_bowl = pd.DataFrame(season_data["top_bowlers"])
        fig_tw     = px.bar(df_tw_bowl, x="wickets", y="player", orientation="h",
                            color="wickets", color_continuous_scale="Purples", text="wickets")
        fig_tw.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        dark_layout(fig_tw, 280)
        st.plotly_chart(fig_tw, use_container_width=True)

    st.divider()
    st.subheader("All Season Caps")
    df_all = pd.DataFrame([{
        "Season": s["season"],
        "Orange Cap": s["orange_cap"]["player"],
        "Runs": s["orange_cap"]["runs"],
        "Purple Cap": s["purple_cap"]["player"],
        "Wickets": s["purple_cap"]["wickets"],
    } for s in seasons])
    st.dataframe(df_all, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# ADVANCED
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "Advanced":
    adv       = load("advanced")
    df_impact = pd.DataFrame(adv["impact_scores"])

    st.title("📊 Advanced Analytics")
    st.divider()

    st.subheader("Player Impact Scores")
    fig_imp = px.bar(
        df_impact.nlargest(15,"impact_score"),
        x="impact_score", y="player", orientation="h",
        color="impact_score", color_continuous_scale="Plasma", text="impact_score",
    )
    fig_imp.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_imp.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
    dark_layout(fig_imp, 480)
    st.plotly_chart(fig_imp, use_container_width=True)

    st.divider()
    st.subheader("SR vs Average — colored by Impact Score")
    fig_adv = px.scatter(
        df_impact, x="avg", y="sr",
        color="impact_score", color_continuous_scale="Plasma",
        hover_name="player", size="runs", size_max=35,
        labels={"avg":"Average","sr":"Strike Rate","impact_score":"Impact"},
    )
    dark_layout(fig_adv, 450)
    st.plotly_chart(fig_adv, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# MONEYBALL
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "Moneyball":
    adv       = load("advanced")
    df_impact = pd.DataFrame(adv["impact_scores"])

    st.title("💰 Moneyball — Value Analysis")
    st.caption("Undervalued players based on impact vs runs scored")
    st.divider()

    df_impact["impact_per_run"] = (df_impact["impact_score"] / df_impact["runs"]).round(4)
    df_impact["value_tier"]     = pd.qcut(df_impact["impact_per_run"], q=3,
                                           labels=["Low Value","Mid Value","High Value"])

    fig_mb = px.scatter(
        df_impact, x="runs", y="impact_score",
        color="value_tier",
        color_discrete_map={"High Value":"#22c55e","Mid Value":"#eab308","Low Value":"#ef4444"},
        hover_name="player", size="sr", size_max=30,
        labels={"runs":"Total Runs","impact_score":"Impact Score"},
    )
    dark_layout(fig_mb, 450)
    st.plotly_chart(fig_mb, use_container_width=True)

    st.divider()
    st.subheader("🟢 Best Value Players (Impact per Run)")
    df_val = df_impact.sort_values("impact_per_run", ascending=False).head(15)
    st.dataframe(df_val[["player","runs","avg","sr","impact_score","impact_per_run"]],
                 use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# RECORDS
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "Records":
    bat    = load("batting")
    bowl   = load("bowling")
    ov     = load("overview")
    df_bat  = pd.DataFrame(bat["leaderboard"])
    df_bowl = pd.DataFrame(bowl["leaderboard"])

    st.title("🏆 Records & Milestones")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏏 Batting Records")
        for rec, col_name, fmt in [
            ("Most Runs",        "total_runs",   lambda v: f"{v:,}"),
            ("Best Average",     "average",      lambda v: f"{v:.1f}"),
            ("Best Strike Rate", "strike_rate",  lambda v: f"{v:.1f}"),
            ("Most Sixes",       "sixes",        lambda v: f"{v:,}"),
            ("Highest Score",    "highest",      lambda v: f"{v}"),
        ]:
            asc   = False
            idx   = df_bat[col_name].idxmax() if not asc else df_bat[col_name].idxmin()
            row   = df_bat.loc[idx]
            st.markdown(f"**{rec}** — {row['batter']} `{fmt(row[col_name])}`")

    with col2:
        st.subheader("🎳 Bowling Records")
        for rec, col_name, best in [
            ("Most Wickets",    "wickets",        "max"),
            ("Best Economy",    "economy",        "min"),
            ("Best Average",    "average",        "min"),
            ("Most 4-Wkt Hauls","four_wkt_hauls", "max"),
            ("Most 5-Wkt Hauls","five_wkt_hauls", "max"),
        ]:
            idx = df_bowl[col_name].idxmax() if best=="max" else df_bowl[col_name].idxmin()
            row = df_bowl.loc[idx]
            st.markdown(f"**{rec}** — {row['bowler']} `{row[col_name]}`")

    st.divider()
    st.subheader("🏟️ All-Time Team Wins")
    sorted_teams = [(k,v) for k,v in sorted(ov["team_wins"].items(), key=lambda x:x[1], reverse=True)
                    if isinstance(k,str) and k not in ["Unknown","nan",""]][:12]
    df_tr = pd.DataFrame(sorted_teams, columns=["Team","Wins"])
    df_tr["Short"] = df_tr["Team"].map(TEAM_SHORT).fillna(df_tr["Team"].str[:4])
    fig_tr = px.bar(df_tr, x="Short", y="Wins",
                    color="Wins", color_continuous_scale="Blues", text="Wins")
    fig_tr.update_traces(textposition="outside")
    fig_tr.update_layout(coloraxis_showscale=False)
    dark_layout(fig_tr, 360)
    st.plotly_chart(fig_tr, use_container_width=True)
