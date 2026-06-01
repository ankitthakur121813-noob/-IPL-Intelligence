import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json, os

st.set_page_config(
    page_title="IPL Intelligence",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif !important; }

[data-testid="stAppViewContainer"] { background: #080c14; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #080c14 100%);
    border-right: 1px solid #1a2332;
}

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* Sidebar text */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label { color: #64748b !important; font-size: 0.8rem !important; }

/* Radio buttons in sidebar */
[data-testid="stSidebar"] .stRadio label { 
    color: #94a3b8 !important; 
    font-size: 0.875rem !important;
    padding: 6px 0 !important;
}

/* Main content */
h1 { color: #f1f5f9 !important; font-weight: 800 !important; font-size: 2rem !important; }
h2 { color: #e2e8f0 !important; font-weight: 700 !important; }
h3 { color: #cbd5e1 !important; font-weight: 600 !important; }
p  { color: #94a3b8 !important; }

/* Stat cards */
.kpi-card {
    background: linear-gradient(135deg, #111827 0%, #1a2332 100%);
    border: 1px solid #1e293b;
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent);
}
.kpi-val  { font-size: 2rem; font-weight: 800; color: var(--accent); line-height: 1.1; }
.kpi-lbl  { font-size: 0.65rem; color: #475569; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }
.kpi-sub  { font-size: 0.72rem; color: #334155; margin-top: 2px; }

/* Insight cards */
.insight {
    background: linear-gradient(135deg, #0f172a 0%, #111827 100%);
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 12px;
    display: flex;
    gap: 14px;
    align-items: flex-start;
}
.insight-icon { font-size: 1.6rem; flex-shrink: 0; }
.insight-body {}
.insight-title { font-weight: 700; color: #f1f5f9; font-size: 0.95rem; margin-bottom: 4px; }
.insight-text  { font-size: 0.82rem; color: #64748b; line-height: 1.5; }
.insight-text b { color: #38bdf8; }

/* Section headers */
.section-head {
    font-size: 1.1rem; font-weight: 700; color: #e2e8f0;
    border-left: 3px solid #38bdf8;
    padding-left: 12px;
    margin: 24px 0 16px 0;
}

/* Tables */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-green  { background: rgba(34,197,94,0.15);  color: #22c55e; }
.badge-orange { background: rgba(249,115,22,0.15); color: #f97316; }
.badge-blue   { background: rgba(56,189,248,0.15); color: #38bdf8; }

/* Logo */
.logo-text {
    font-size: 1.2rem; font-weight: 800; color: #f1f5f9;
    letter-spacing: -0.5px;
}
.logo-accent { color: #38bdf8; }
</style>
""", unsafe_allow_html=True)

# ── Data ─────────────────────────────────────────────────────────────────────
DATA_DIR = "data"

@st.cache_data
def load(key):
    with open(os.path.join(DATA_DIR, f"{key}.json")) as f:
        return json.load(f)

TEAM_CLR = {
    "Mumbai Indians": "#1d4ed8", "Chennai Super Kings": "#eab308",
    "Royal Challengers Bangalore": "#dc2626", "Royal Challengers Bengaluru": "#dc2626",
    "Kolkata Knight Riders": "#7c3aed", "Delhi Capitals": "#3b82f6",
    "Punjab Kings": "#b91c1c", "Kings XI Punjab": "#b91c1c",
    "Rajasthan Royals": "#ec4899", "Sunrisers Hyderabad": "#f97316",
    "Gujarat Titans": "#14b8a6", "Lucknow Super Giants": "#06b6d4",
    "Deccan Chargers": "#64748b", "Delhi Daredevils": "#3b82f6",
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

def dark_fig(fig, h=400):
    fig.update_layout(
        height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", family="Inter, sans-serif"),
        margin=dict(l=10, r=10, t=36, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e293b"),
        xaxis=dict(gridcolor="#1a2332", zerolinecolor="#1a2332", showgrid=True),
        yaxis=dict(gridcolor="#1a2332", zerolinecolor="#1a2332", showgrid=True),
    )
    return fig

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="logo-text">◈ IPL <span class="logo-accent">Intelligence</span></div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#334155;font-size:0.75rem;margin-top:4px;">2008 – 2026 · 19 Seasons</p>', unsafe_allow_html=True)
    st.divider()
    tab = st.radio("", [
        "🏠  Overview", "🏏  Batting", "🎳  Bowling", "🏟️  Venues",
        "🏅  Season Leaders", "📊  Advanced", "💰  Moneyball", "🏆  Records"
    ], label_visibility="collapsed")
    st.divider()
    st.markdown('<p style="color:#1e293b;font-size:0.7rem;">1,193 matches · 19 seasons<br>2008 – 2026 · Real ball-by-ball data</p>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if tab == "🏠  Overview":
    ov = load("overview")
    ss = ov["season_stats"]
    df_ss = pd.DataFrame(ss)

    st.markdown("# 🏏 IPL Intelligence Platform")
    st.markdown('<p style="color:#475569;margin-top:-12px;margin-bottom:24px;">2008–2026 · Complete Statistical Dashboard · Real Ball-by-Ball Data</p>', unsafe_allow_html=True)

    # Insight strip
    six_start = ss[5]["sixes"]
    six_end   = ss[-1]["sixes"]
    six_pct   = round(((six_end - six_start) / six_start) * 100)
    top_team  = max(ov["team_wins"], key=ov["team_wins"].get)
    top_wins  = ov["team_wins"][top_team]
    rpm_last  = round(ss[-1]["runs"] / ss[-1]["matches"])

    c1, c2, c3 = st.columns(3)
    for col, icon, title, text in [
        (c1, "📈", "Sixes Explosion", f"From {six_start} (2013) to {six_end} in {ss[-1]['season']} — a <b>{six_pct}%</b> surge in boundaries hit."),
        (c2, "🏆", "All-Time Leaders", f"<b>{top_team}</b> leads all franchises with <b>{top_wins} wins</b> across 19 seasons."),
        (c3, "⚡", "Scoring Rate", f"{ss[-1]['season']} season averaged <b>{rpm_last} runs/match</b> — highest ever."),
    ]:
        col.markdown(f"""<div class="insight">
            <div class="insight-icon">{icon}</div>
            <div class="insight-body">
                <div class="insight-title">{title}</div>
                <div class="insight-text">{text}</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # KPI Cards
    cols = st.columns(6)
    kpis = [
        ("19",                              "Seasons",      "2008 – 2026",      "#f97316"),
        (f"{ov['total_matches']:,}",        "Matches",      "All matches",      "#38bdf8"),
        (f"{ov['total_runs']//1000}K",      "Total Runs",   "Combined innings", "#eab308"),
        (f"{ov['total_wickets']:,}",        "Wickets",      "All dismissals",   "#a855f7"),
        (f"{ov['total_sixes']:,}",          "Sixes",        "Maximum hits",     "#22c55e"),
        (f"{ov['avg_runs_per_match']}",     "Avg / Match",  "Combined innings", "#ef4444"),
    ]
    for col, (val, lbl, sub, color) in zip(cols, kpis):
        col.markdown(f"""<div class="kpi-card" style="--accent:{color}">
            <div class="kpi-val">{val}</div>
            <div class="kpi-lbl">{lbl}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.divider()

    # Season Trend
    st.markdown('<div class="section-head">Season Trends</div>', unsafe_allow_html=True)
    metric = st.radio("", ["runs", "sixes", "wickets"], horizontal=True, key="ov_m",
                      format_func=lambda x: x.capitalize())
    clr  = {"runs":"#f97316","sixes":"#22c55e","wickets":"#a855f7"}
    fill = {"runs":"rgba(249,115,22,0.15)","sixes":"rgba(34,197,94,0.15)","wickets":"rgba(168,85,247,0.15)"}
    fig = px.area(df_ss, x="season", y=metric, color_discrete_sequence=[clr[metric]])
    fig.update_traces(line_width=2.5, fillcolor=fill[metric])
    dark_fig(fig, 320)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    col_l, col_r = st.columns([1.1, 1])

    with col_l:
        st.markdown('<div class="section-head">All-Time Team Wins</div>', unsafe_allow_html=True)
        tw = [(k,v) for k,v in sorted(ov["team_wins"].items(), key=lambda x:x[1], reverse=True)
              if isinstance(k,str) and k not in ["Unknown","nan",""]][:10]
        df_tw = pd.DataFrame(tw, columns=["Team","Wins"])
        df_tw["Short"] = df_tw["Team"].map(TEAM_SHORT).fillna(df_tw["Team"].str[:3])
        df_tw["Color"] = df_tw["Team"].map(TEAM_CLR).fillna("#64748b")
        fig2 = go.Figure(go.Bar(
            x=df_tw["Wins"], y=df_tw["Short"], orientation="h",
            marker_color=df_tw["Color"].tolist(),
            text=df_tw["Wins"], textposition="outside",
            marker_line_width=0,
        ))
        dark_fig(fig2, 360)
        fig2.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig2, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-head">Head to Head</div>', unsafe_allow_html=True)
        df_h2h = pd.DataFrame(ov["head_to_head"])
        df_h2h["Win %"] = (df_h2h["team1_wins"]/df_h2h["matches"]*100).round(0).astype(int).astype(str)+"%"
        df_h2h = df_h2h.rename(columns={
            "team1":"Team 1","team2":"Team 2","matches":"Matches",
            "team1_wins":"T1 W","team2_wins":"T2 W"
        })
        st.dataframe(df_h2h[["Team 1","Team 2","Matches","T1 W","T2 W","Win %"]],
                     use_container_width=True, hide_index=True, height=360)

# ══════════════════════════════════════════════════════════════════════════════
# BATTING
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "🏏  Batting":
    bat    = load("batting")
    sim    = load("similarity")
    df_bat = pd.DataFrame(bat["leaderboard"])

    st.markdown("# 🏏 Batting Analytics")

    col_f1, col_f2, col_f3 = st.columns([3,1,1])
    search      = col_f1.text_input("", placeholder="🔍  Search player — e.g. Kohli, Gill, Warner", label_visibility="collapsed")
    min_innings = col_f2.number_input("Min Innings", min_value=1, max_value=300, value=1)
    min_runs    = col_f3.number_input("Min Runs", min_value=0, max_value=10000, value=0, step=100)

    df_f = df_bat[(df_bat["innings"]>=min_innings)&(df_bat["total_runs"]>=min_runs)]
    if search.strip():
        df_f = df_f[df_f["batter"].str.contains(search.strip(), case=False, na=False)]

    st.caption(f"Showing **{len(df_f)}** players")
    st.divider()

    st.markdown('<div class="section-head">Batting Leaderboard</div>', unsafe_allow_html=True)
    sort_col = st.selectbox("Sort by", ["total_runs","average","strike_rate","sixes","impact_score"],
                            format_func=lambda x: {
                                "total_runs":"Total Runs","average":"Average",
                                "strike_rate":"Strike Rate","sixes":"Sixes","impact_score":"Impact Score"
                            }[x])
    df_show = df_f.sort_values(sort_col, ascending=False).reset_index(drop=True)
    df_show = df_show.rename(columns={
        "batter":"Player","total_runs":"Runs","innings":"Inn","average":"Avg",
        "strike_rate":"SR","fours":"4s","sixes":"6s","highest":"HS","impact_score":"Impact"
    })
    st.dataframe(df_show, use_container_width=True, hide_index=True, height=360)

    st.divider()
    st.markdown('<div class="section-head">Strike Rate vs Average</div>', unsafe_allow_html=True)
    df_sc = df_bat[df_bat["total_runs"]>=500].copy()
    df_sc["Elite"] = df_sc["total_runs"] >= 4000
    fig_sc = px.scatter(
        df_sc, x="average", y="strike_rate", size="total_runs",
        color="Elite", color_discrete_map={True:"#f97316",False:"#38bdf8"},
        hover_name="batter",
        hover_data={"total_runs":True,"average":True,"strike_rate":True,"Elite":False},
        size_max=45,
        labels={"average":"Batting Average","strike_rate":"Strike Rate"},
    )
    dark_fig(fig_sc, 460)
    fig_sc.update_layout(showlegend=False)
    st.plotly_chart(fig_sc, use_container_width=True)

    st.divider()
    st.markdown('<div class="section-head">Player Similarity Finder</div>', unsafe_allow_html=True)
    selected = st.selectbox("Select player", list(sim.keys()))
    if selected in sim:
        df_sim = pd.DataFrame(sim[selected], columns=["Similar Player","Similarity Score"])
        df_sim["Similarity Score"] = df_sim["Similarity Score"].round(3)
        st.dataframe(df_sim, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# BOWLING
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "🎳  Bowling":
    bowl    = load("bowling")
    df_bowl = pd.DataFrame(bowl["leaderboard"])

    st.markdown("# 🎳 Bowling Analytics")

    col_b1, col_b2 = st.columns([3,1])
    search_b    = col_b1.text_input("", placeholder="🔍  Search bowler — e.g. Bumrah, Chahal, Rashid", label_visibility="collapsed")
    min_wickets = col_b2.number_input("Min Wickets", min_value=1, max_value=300, value=1)

    df_bf = df_bowl[df_bowl["wickets"]>=min_wickets]
    if search_b.strip():
        df_bf = df_bf[df_bf["bowler"].str.contains(search_b.strip(), case=False, na=False)]

    st.caption(f"Showing **{len(df_bf)}** bowlers")
    st.divider()

    st.markdown('<div class="section-head">Bowling Leaderboard</div>', unsafe_allow_html=True)
    sort_b = st.selectbox("Sort by", ["wickets","economy","average","strike_rate"],
                          format_func=lambda x: {
                              "wickets":"Wickets","economy":"Economy",
                              "average":"Average","strike_rate":"Strike Rate"
                          }[x])
    asc   = sort_b in ["economy","average","strike_rate"]
    df_bs = df_bf.sort_values(sort_b, ascending=asc).reset_index(drop=True)
    df_bs = df_bs.rename(columns={
        "bowler":"Player","wickets":"Wkts","economy":"Econ",
        "average":"Avg","strike_rate":"SR",
        "four_wkt_hauls":"4W","five_wkt_hauls":"5W"
    })
    st.dataframe(df_bs, use_container_width=True, hide_index=True, height=360)

    st.divider()
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.markdown('<div class="section-head">Top Wicket Takers</div>', unsafe_allow_html=True)
        df_top = df_bowl.nlargest(12,"wickets")
        fig_wk = px.bar(df_top, x="wickets", y="bowler", orientation="h",
                        color="wickets", color_continuous_scale="Blues", text="wickets")
        fig_wk.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        dark_fig(fig_wk, 400)
        st.plotly_chart(fig_wk, use_container_width=True)

    with col_c2:
        st.markdown('<div class="section-head">Economy vs Wickets</div>', unsafe_allow_html=True)
        fig_ec = px.scatter(df_bowl[df_bowl["wickets"]>=20], x="economy", y="wickets",
                            hover_name="bowler", color="wickets",
                            color_continuous_scale="Oranges", size="wickets", size_max=30)
        fig_ec.update_layout(coloraxis_showscale=False)
        dark_fig(fig_ec, 400)
        st.plotly_chart(fig_ec, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# VENUES
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "🏟️  Venues":
    ven    = load("venues")
    df_ven = pd.DataFrame(ven["venues"])
    df_ven["venue_short"]   = df_ven["venue"].str.split(",").str[0]
    df_ven["chase_win_pct"] = (100 - df_ven["bat_first_win_pct"]).round(1)

    st.markdown("# 🏟️ Venue Intelligence")
    st.divider()

    st.markdown('<div class="section-head">Bat First vs Chase Win %</div>', unsafe_allow_html=True)
    fig_ven = go.Figure()
    fig_ven.add_trace(go.Bar(
        name="Bat First", x=df_ven["venue_short"], y=df_ven["bat_first_win_pct"],
        marker_color="#f97316", marker_line_width=0,
        text=df_ven["bat_first_win_pct"].round(0).astype(int).astype(str)+"%",
        textposition="outside",
    ))
    fig_ven.add_trace(go.Bar(
        name="Chase", x=df_ven["venue_short"], y=df_ven["chase_win_pct"],
        marker_color="#38bdf8", marker_line_width=0,
        text=df_ven["chase_win_pct"].round(0).astype(int).astype(str)+"%",
        textposition="outside",
    ))
    fig_ven.update_layout(barmode="group", xaxis_tickangle=-35)
    dark_fig(fig_ven, 420)
    st.plotly_chart(fig_ven, use_container_width=True)

    st.divider()
    st.markdown('<div class="section-head">Venue Details</div>', unsafe_allow_html=True)
    df_d = df_ven[["venue_short","matches","avg_first_innings","avg_second_innings",
                   "pitch_type","boundary_opportunity","boundary_pct"]].copy()
    df_d.columns = ["Venue","Matches","Avg 1st Inn","Avg 2nd Inn","Pitch Type","Boundary Opp","Boundary %"]
    st.dataframe(df_d, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown('<div class="section-head">Innings Score Comparison</div>', unsafe_allow_html=True)
    fig_inn = px.scatter(
        df_ven, x="avg_first_innings", y="avg_second_innings",
        text="venue_short", color="pitch_type", size="matches", size_max=35,
        labels={"avg_first_innings":"Avg 1st Innings","avg_second_innings":"Avg 2nd Innings"},
    )
    fig_inn.update_traces(textposition="top center")
    dark_fig(fig_inn, 440)
    st.plotly_chart(fig_inn, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# SEASON LEADERS
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "🏅  Season Leaders":
    sl      = load("season_leaders")
    seasons = sl["seasons"]

    st.markdown("# 🏅 Season Leaders")
    st.divider()

    sel = st.select_slider("Season", options=[s["season"] for s in seasons])
    sd  = next(s for s in seasons if s["season"] == sel)

    c1, c2 = st.columns(2)
    c1.markdown(f"""<div class="kpi-card" style="--accent:#f97316">
        <div class="kpi-val" style="font-size:1.4rem">{sd['orange_cap']['player']}</div>
        <div class="kpi-lbl">🟠 Orange Cap</div>
        <div class="kpi-sub">{sd['orange_cap']['runs']} runs</div>
    </div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="kpi-card" style="--accent:#a855f7">
        <div class="kpi-val" style="font-size:1.4rem">{sd['purple_cap']['player']}</div>
        <div class="kpi-lbl">🟣 Purple Cap</div>
        <div class="kpi-sub">{sd['purple_cap']['wickets']} wickets</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("")
    st.divider()
    col_tb, col_tw = st.columns(2)

    with col_tb:
        st.markdown('<div class="section-head">Top Batsmen</div>', unsafe_allow_html=True)
        df_tb  = pd.DataFrame(sd["top_batsmen"])
        fig_tb = px.bar(df_tb, x="runs", y="player", orientation="h",
                        color="runs", color_continuous_scale="Oranges", text="runs")
        fig_tb.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        dark_fig(fig_tb, 280)
        st.plotly_chart(fig_tb, use_container_width=True)

    with col_tw:
        st.markdown('<div class="section-head">Top Bowlers</div>', unsafe_allow_html=True)
        df_tw2 = pd.DataFrame(sd["top_bowlers"])
        fig_tw = px.bar(df_tw2, x="wickets", y="player", orientation="h",
                        color="wickets", color_continuous_scale="Purples", text="wickets")
        fig_tw.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        dark_fig(fig_tw, 280)
        st.plotly_chart(fig_tw, use_container_width=True)

    st.divider()
    st.markdown('<div class="section-head">All Seasons</div>', unsafe_allow_html=True)
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
elif tab == "📊  Advanced":
    adv       = load("advanced")
    df_impact = pd.DataFrame(adv["impact_scores"])

    st.markdown("# 📊 Advanced Analytics")
    st.divider()

    st.markdown('<div class="section-head">Player Impact Leaderboard</div>', unsafe_allow_html=True)
    fig_imp = px.bar(
        df_impact.nlargest(15,"impact_score"),
        x="impact_score", y="player", orientation="h",
        color="impact_score", color_continuous_scale="Plasma", text="impact_score",
    )
    fig_imp.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    fig_imp.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
    dark_fig(fig_imp, 500)
    st.plotly_chart(fig_imp, use_container_width=True)

    st.divider()
    st.markdown('<div class="section-head">SR vs Average — Impact Score</div>', unsafe_allow_html=True)
    fig_adv = px.scatter(
        df_impact, x="avg", y="sr",
        color="impact_score", color_continuous_scale="Plasma",
        hover_name="player", size="runs", size_max=40,
        labels={"avg":"Average","sr":"Strike Rate","impact_score":"Impact"},
    )
    dark_fig(fig_adv, 460)
    st.plotly_chart(fig_adv, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# MONEYBALL
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "💰  Moneyball":
    adv       = load("advanced")
    df_impact = pd.DataFrame(adv["impact_scores"])

    st.markdown("# 💰 Moneyball — Value Analysis")
    st.markdown('<p style="color:#475569;">Finding undervalued players based on impact per run scored</p>', unsafe_allow_html=True)
    st.divider()

    df_impact["Impact/Run"]  = (df_impact["impact_score"] / df_impact["runs"]).round(4)
    df_impact["Value Tier"]  = pd.qcut(df_impact["Impact/Run"], q=3,
                                        labels=["Low Value","Mid Value","High Value"])

    fig_mb = px.scatter(
        df_impact, x="runs", y="impact_score",
        color="Value Tier",
        color_discrete_map={"High Value":"#22c55e","Mid Value":"#eab308","Low Value":"#ef4444"},
        hover_name="player", size="sr", size_max=30,
        labels={"runs":"Total Runs","impact_score":"Impact Score"},
    )
    dark_fig(fig_mb, 460)
    st.plotly_chart(fig_mb, use_container_width=True)

    st.divider()
    st.markdown('<div class="section-head">🟢 Best Value Players</div>', unsafe_allow_html=True)
    df_val = df_impact.sort_values("Impact/Run", ascending=False).head(15)
    df_val = df_val.rename(columns={"player":"Player","runs":"Runs","avg":"Avg","sr":"SR",
                                     "impact_score":"Impact","Impact/Run":"Impact/Run"})
    st.dataframe(df_val[["Player","Runs","Avg","SR","Impact","Impact/Run"]],
                 use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# RECORDS
# ══════════════════════════════════════════════════════════════════════════════
elif tab == "🏆  Records":
    bat     = load("batting")
    bowl    = load("bowling")
    ov      = load("overview")
    df_bat  = pd.DataFrame(bat["leaderboard"])
    df_bowl = pd.DataFrame(bowl["leaderboard"])

    st.markdown("# 🏆 Records & Milestones")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-head">🏏 Batting Records</div>', unsafe_allow_html=True)
        records = [
            ("Most Runs",        "total_runs",   "max", lambda v: f"{int(v):,}"),
            ("Best Average",     "average",      "max", lambda v: f"{v:.1f}"),
            ("Best Strike Rate", "strike_rate",  "max", lambda v: f"{v:.1f}"),
            ("Most Sixes",       "sixes",        "max", lambda v: f"{int(v):,}"),
            ("Highest Score",    "highest",      "max", lambda v: f"{int(v)}"),
        ]
        for rec, col_name, best, fmt in records:
            idx = df_bat[col_name].idxmax()
            row = df_bat.loc[idx]
            st.markdown(f"""<div style="background:#111827;border:1px solid #1e293b;border-radius:10px;padding:12px 16px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#94a3b8;font-size:0.85rem;">{rec}</span>
                <span style="color:#f1f5f9;font-weight:600;">{row['batter']} <span style="color:#38bdf8;margin-left:8px;">{fmt(row[col_name])}</span></span>
            </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-head">🎳 Bowling Records</div>', unsafe_allow_html=True)
        records_b = [
            ("Most Wickets",     "wickets",        "max", lambda v: f"{int(v)}"),
            ("Best Economy",     "economy",        "min", lambda v: f"{v:.2f}"),
            ("Best Average",     "average",        "min", lambda v: f"{v:.2f}"),
            ("Most 4-Wkt Hauls", "four_wkt_hauls", "max", lambda v: f"{int(v)}"),
            ("Most 5-Wkt Hauls", "five_wkt_hauls", "max", lambda v: f"{int(v)}"),
        ]
        for rec, col_name, best, fmt in records_b:
            idx = df_bowl[col_name].idxmax() if best=="max" else df_bowl[col_name].idxmin()
            row = df_bowl.loc[idx]
            st.markdown(f"""<div style="background:#111827;border:1px solid #1e293b;border-radius:10px;padding:12px 16px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
                <span style="color:#94a3b8;font-size:0.85rem;">{rec}</span>
                <span style="color:#f1f5f9;font-weight:600;">{row['bowler']} <span style="color:#a855f7;margin-left:8px;">{fmt(row[col_name])}</span></span>
            </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="section-head">All-Time Team Wins</div>', unsafe_allow_html=True)
    tw = [(k,v) for k,v in sorted(ov["team_wins"].items(), key=lambda x:x[1], reverse=True)
          if isinstance(k,str) and k not in ["Unknown","nan",""]][:12]
    df_tr = pd.DataFrame(tw, columns=["Team","Wins"])
    df_tr["Short"] = df_tr["Team"].map(TEAM_SHORT).fillna(df_tr["Team"].str[:4])
    df_tr["Color"] = df_tr["Team"].map(TEAM_CLR).fillna("#64748b")
    fig_tr = go.Figure(go.Bar(
        x=df_tr["Short"], y=df_tr["Wins"],
        marker_color=df_tr["Color"].tolist(),
        text=df_tr["Wins"], textposition="outside",
        marker_line_width=0,
    ))
    dark_fig(fig_tr, 360)
    st.plotly_chart(fig_tr, use_container_width=True)
