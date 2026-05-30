"use strict";
const BASE="./", TABS=["overview","batting","bowling","venues","leaders","advanced","moneyball","gallery"];
const cache={}, charts={};
Chart.defaults.color="#94a3b8"; Chart.defaults.borderColor="rgba(255,255,255,0.06)";
Chart.defaults.font.family="'DM Sans',sans-serif"; Chart.defaults.font.size=12;

const P={orange:"#f97316",blue:"#3b82f6",purple:"#a855f7",gold:"#eab308",teal:"#14b8a6",red:"#ef4444",green:"#22c55e",muted:"#475569"};
const TEAM_CLR={"Mumbai Indians":"#1d4ed8","Chennai Super Kings":"#ca8a04","Royal Challengers Bangalore":"#dc2626","Kolkata Knight Riders":"#7c3aed","Delhi Capitals":"#2563eb","Punjab Kings":"#b91c1c","Rajasthan Royals":"#db2777","Sunrisers Hyderabad":"#ea580c","Gujarat Titans":"#0d9488","Lucknow Super Giants":"#0ea5e9"};
const TEAM_SHORT={"Mumbai Indians":"MI","Chennai Super Kings":"CSK","Royal Challengers Bangalore":"RCB","Kolkata Knight Riders":"KKR","Delhi Capitals":"DC","Punjab Kings":"PBKS","Rajasthan Royals":"RR","Sunrisers Hyderabad":"SRH","Gujarat Titans":"GT","Lucknow Super Giants":"LSG"};

const $=id=>document.getElementById(id);
const dc=id=>{if(charts[id]){charts[id].destroy();delete charts[id];}};
function tbl(heads,rows){return`<table><thead><tr>${heads.map(h=>`<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;}
function countUp(el,t,d=1100,s=""){const n=parseFloat(t),isF=!Number.isInteger(n),start=performance.now();(function f(now){const p=Math.min((now-start)/d,1),e=1-Math.pow(1-p,3);el.textContent=(isF?(n*e).toFixed(1):Math.round(n*e).toLocaleString())+s;if(p<1)requestAnimationFrame(f);})(performance.now());}
let _dbt; function debounce(fn,ms=260){clearTimeout(_dbt);_dbt=setTimeout(fn,ms);}

async function load(key){
  if(cache[key])return cache[key];
  const r=await fetch(`${BASE}data/${key}.json`);
  if(!r.ok)throw new Error(`HTTP ${r.status} loading ${key}`);
  cache[key]=await r.json(); return cache[key];
}

let _retryFn=null;
$("error-retry").onclick=()=>{$("error-toast").classList.add("hidden");_retryFn?.();};
function showError(m,fn){$("error-msg").textContent=m;$("error-toast").classList.remove("hidden");_retryFn=fn;}

function activeTab(){const h=location.hash.replace("#","");return TABS.includes(h)?h:"overview";}
function switchTab(tab){
  document.querySelectorAll(".nav-link").forEach(l=>l.classList.toggle("active",l.dataset.tab===tab));
  TABS.forEach(t=>{const el=$(`tab-${t}`);if(el)el.classList.toggle("hidden",t!==tab);});
  $("sidebar").classList.remove("open");
}
const loaded=new Set();
async function navigate(tab){location.hash=tab;switchTab(tab);if(loaded.has(tab))return;loaded.add(tab);try{await loadTab(tab);}catch(e){loaded.delete(tab);showError(e.message,()=>navigate(tab));}}
async function loadTab(t){const m={overview:renderOverview,batting:renderBatting,bowling:renderBowling,venues:renderVenues,leaders:renderLeaders,advanced:renderAdvanced,moneyball:renderMoneyball,gallery:renderGallery};await m[t]?.();}
document.querySelectorAll(".nav-link").forEach(l=>l.addEventListener("click",e=>{e.preventDefault();navigate(l.dataset.tab);}));
$("hamburger").addEventListener("click",()=>$("sidebar").classList.toggle("open"));

// ═══ OVERVIEW ═════════════════════════════════════════════════════════════════
async function renderOverview(){
  const ov=await load("overview"), ss=ov.season_stats;
  const sixStart=ss[5]?.sixes||300, sixEnd=ss[ss.length-1].sixes;
  const sixPct=Math.round(((sixEnd-sixStart)/sixStart)*100);
  const topTeam=Object.entries(ov.team_wins).sort((a,b)=>b[1]-a[1])[0];
  const rpmLast=Math.round(ss[ss.length-1].runs/ss[ss.length-1].matches);

  $("insight-strip").innerHTML=[
    {icon:"📈",title:"Sixes Explosion",text:`From ${sixStart} sixes in the 2013 season to ${sixEnd} in ${ss[ss.length-1].season} — a <strong>${sixPct}%</strong> surge. T20 batting has been completely transformed.`},
    {icon:"🏆",title:"All-Time Leaders",text:`<strong>${topTeam[0]}</strong> leads all franchises with <strong>${topTeam[1]} wins</strong> — the most dominant franchise in IPL history.`},
    {icon:"⚡",title:"Scoring Rate",text:`The ${ss[ss.length-1].season} season averaged <strong>${rpmLast} runs/match</strong> — teams now regularly post 200+ totals in T20s.`},
  ].map(i=>`<div class="insight-card"><div class="insight-icon">${i.icon}</div><div class="insight-title">${i.title}</div><div class="insight-text">${i.text}</div></div>`).join("");

  const stats=[
    {l:"Seasons",v:ov.total_seasons,s:"2008–2025",c:P.orange},
    {l:"Matches",v:ov.total_matches,s:"league + playoffs",c:P.blue},
    {l:"Total Runs",v:+(ov.total_runs/1000).toFixed(1),s:"thousands of runs",c:P.gold,x:"K"},
    {l:"Wickets",v:ov.total_wickets,s:"all dismissals",c:P.purple},
    {l:"Sixes",v:ov.total_sixes,s:"maximum hits",c:P.teal},
    {l:"Avg/Match",v:ov.avg_runs_per_match,s:"combined innings",c:P.red},
  ];
  $("stat-grid").innerHTML=stats.map(s=>`<div class="stat-card" style="--accent-color:${s.c}"><div class="stat-label">${s.l}</div><div class="stat-value" data-t="${s.v}" data-s="${s.x||''}">0</div><div class="stat-sub">${s.s}</div></div>`).join("");
  $("stat-grid").querySelectorAll(".stat-value").forEach(el=>countUp(el,el.dataset.t,1100,el.dataset.s));

  function drawSeason(metric){
    dc("season-chart");
    const clrs={runs:P.orange,sixes:P.teal,wickets:P.purple}, col=clrs[metric];
    charts["season-chart"]=new Chart($("season-chart").getContext("2d"),{type:"line",data:{labels:ss.map(s=>s.season),datasets:[{label:metric,data:ss.map(s=>s[metric]),borderColor:col,backgroundColor:c=>{const g=c.chart.ctx.createLinearGradient(0,0,0,220);g.addColorStop(0,col+"55");g.addColorStop(1,col+"00");return g;},fill:true,tension:0.4,pointRadius:4,pointBackgroundColor:col}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false}},y:{grid:{color:"rgba(255,255,255,0.04)"}}}}});
  }
  drawSeason("runs");
  $("season-toggle").querySelectorAll(".toggle-btn").forEach(btn=>btn.addEventListener("click",()=>{$("season-toggle").querySelectorAll(".toggle-btn").forEach(b=>b.classList.remove("active"));btn.classList.add("active");drawSeason(btn.dataset.metric);}));

  const sortedTeams=Object.entries(ov.team_wins).sort((a,b)=>b[1]-a[1]);
  dc("team-wins-chart");
  charts["team-wins-chart"]=new Chart($("team-wins-chart").getContext("2d"),{type:"bar",data:{labels:sortedTeams.map(([t])=>TEAM_SHORT[t]||t.split(" ").pop()),datasets:[{label:"Wins",data:sortedTeams.map(([,v])=>v),backgroundColor:sortedTeams.map(([t])=>TEAM_CLR[t]||P.muted),borderRadius:5,borderSkipped:false}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{title:i=>`${sortedTeams[i[0].dataIndex][0]}`}}},scales:{x:{grid:{color:"rgba(255,255,255,0.04)"}},y:{grid:{display:false},ticks:{font:{size:11}}}}}});

  $("h2h-table-wrap").innerHTML=tbl(["Team 1","Team 2","Matches","T1 Wins","T2 Wins","T1 Win%"],ov.head_to_head.slice(0,12).map(r=>[`<b>${r.team1}</b>`,r.team2,r.matches,`<span class="badge badge-blue">${r.team1_wins}</span>`,`<span class="badge badge-orange">${r.team2_wins}</span>`,`${((r.team1_wins/r.matches)*100).toFixed(0)}%`]));
}

// ═══ BATTING ══════════════════════════════════════════════════════════════════
let batData=null, batCol="total_runs", batQ="";
let simData=null;

async function renderBatting(){
  batData=await load("batting"); simData=await load("similarity");
  renderBatTable();

  // Scatter: SR vs Average with quadrant labels
  const top=batData.leaderboard.filter(r=>r.innings>=5);
  const maxR=Math.max(...top.map(r=>r.total_runs));
  dc("scatter-chart");
  const sctx=$("scatter-chart").getContext("2d");
  charts["scatter-chart"]=new Chart(sctx,{type:"bubble",data:{datasets:[{label:"Batters",data:top.map(r=>({x:+r.average.toFixed(1),y:+r.strike_rate.toFixed(1),r:Math.max(5,(r.total_runs/maxR)*28),name:r.batter,runs:r.total_runs})),backgroundColor:top.map(r=>r.total_runs>=5000?"rgba(249,115,22,0.75)":"rgba(59,130,246,0.5)"),borderColor:top.map(r=>r.total_runs>=5000?P.orange:P.blue),borderWidth:1}]},options:{responsive:true,maintainAspectRatio:false,onClick:(e,els)=>{if(els.length)openPlayerDetail(top[els[0].index].batter);},plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.raw.name}  Avg:${c.raw.x}  SR:${c.raw.y}  Runs:${c.raw.runs.toLocaleString()}`}}},scales:{x:{title:{display:true,text:"Batting Average",color:"#64748b"},grid:{color:"rgba(255,255,255,0.04)"}},y:{title:{display:true,text:"Strike Rate",color:"#64748b"},grid:{color:"rgba(255,255,255,0.04)"}}}}}); 

  // Season runs chart
  const sr=batData.season_runs, players=Object.keys(sr).slice(0,5);
  const seasons=Array.from({length:18},(_,i)=>2008+i);
  const pal=[P.orange,P.blue,P.purple,P.gold,P.teal];
  dc("season-runs-chart");
  charts["season-runs-chart"]=new Chart($("season-runs-chart").getContext("2d"),{type:"line",data:{labels:seasons,datasets:players.map((p,i)=>({label:p.split(" ").pop(),data:seasons.map(s=>sr[p]?.[s]||null),borderColor:pal[i],backgroundColor:"transparent",tension:0.3,pointRadius:3,spanGaps:true}))},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:"index",intersect:false},plugins:{legend:{position:"top",labels:{boxWidth:10,padding:8,font:{size:10}}}},scales:{x:{grid:{display:false}},y:{grid:{color:"rgba(255,255,255,0.04)"}}}}});

  // Partnerships
  const pairs=batData.partnerships.slice(0,10);
  dc("partnership-chart");
  charts["partnership-chart"]=new Chart($("partnership-chart").getContext("2d"),{type:"bar",data:{labels:pairs.map(p=>p.pair.split(" & ").map(n=>n.split(" ").pop()).join(" & ")),datasets:[{label:"Runs",data:pairs.map(p=>p.total_runs),backgroundColor:pairs.map((_,i)=>i===0?P.orange:P.blue),borderRadius:5,borderSkipped:false}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{color:"rgba(255,255,255,0.04)"}},y:{grid:{display:false},ticks:{font:{size:10}}}}}});

  // Boundary breakdown
  const bTop=[...batData.leaderboard].sort((a,b)=>(b.fours+b.sixes)-(a.fours+a.sixes)).slice(0,10);
  dc("boundary-chart");
  charts["boundary-chart"]=new Chart($("boundary-chart").getContext("2d"),{type:"bar",data:{labels:bTop.map(r=>r.batter.split(" ").pop()),datasets:[{label:"Fours",data:bTop.map(r=>r.fours),backgroundColor:"rgba(234,179,8,0.8)",borderRadius:4},{label:"Sixes",data:bTop.map(r=>r.sixes),backgroundColor:"rgba(249,115,22,0.85)",borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top",labels:{boxWidth:10,padding:8}}},scales:{x:{grid:{display:false},ticks:{font:{size:10}}},y:{grid:{color:"rgba(255,255,255,0.04)"}}}}});

  $("bat-sort-btns").querySelectorAll(".sort-btn").forEach(btn=>btn.addEventListener("click",()=>{$("bat-sort-btns").querySelectorAll(".sort-btn").forEach(b=>b.classList.remove("active"));btn.classList.add("active");batCol=btn.dataset.col;renderBatTable();}));
  $("bat-search").addEventListener("input",e=>debounce(()=>{batQ=e.target.value.toLowerCase();renderBatTable();}));
  $("pd-close").addEventListener("click",()=>$("player-detail").classList.add("hidden"));
}

function renderBatTable(){
  if(!batData)return;
  let rows=[...batData.leaderboard];
  if(batQ)rows=rows.filter(r=>r.batter.toLowerCase().includes(batQ));
  rows.sort((a,b)=>b[batCol]-a[batCol]);
  const empty=$("bat-empty"),wrap=$("bat-table-wrap");
  if(!rows.length){wrap.innerHTML="";empty.classList.remove("hidden");return;}
  empty.classList.add("hidden");
  const topR=rows[0].total_runs;
  wrap.innerHTML=tbl(["#","Batter","Runs","Inns","Avg","SR","4s","6s","Impact"],
    rows.map((r,i)=>{
      const pct=Math.round((r.total_runs/topR)*80);
      const badge=r.total_runs>=7000?'<span class="badge badge-orange">Elite</span>':r.sixes>=200?'<span class="badge badge-gold">6s Machine</span>':"";
      return[`<span class="rank-num">${i+1}</span>`,
        `<span class="player-link" data-name="${r.batter}">${r.batter}${badge}</span>`,
        `<div style="display:flex;align-items:center;gap:6px"><div style="width:${pct}px;height:4px;background:${P.orange};border-radius:2px;opacity:.65;min-width:4px"></div><strong>${r.total_runs.toLocaleString()}</strong></div>`,
        r.innings,r.average.toFixed(1),r.strike_rate.toFixed(1),r.fours,r.sixes,
        `<span class="impact-pill">${r.impact_score||"-"}</span>`
      ];
    })
  );
  wrap.querySelectorAll(".player-link").forEach(el=>el.addEventListener("click",()=>openPlayerDetail(el.dataset.name)));
}

function openPlayerDetail(name){
  if(!batData||!simData)return;
  const r=batData.leaderboard.find(x=>x.batter===name); if(!r)return;
  const similar=simData[name]||[];
  $("pd-name").textContent=name;
  $("pd-stats").innerHTML=`
    <div class="pd-stat"><div class="pd-stat-val">${r.total_runs.toLocaleString()}</div><div class="pd-stat-label">Runs</div></div>
    <div class="pd-stat"><div class="pd-stat-val">${r.average.toFixed(1)}</div><div class="pd-stat-label">Average</div></div>
    <div class="pd-stat"><div class="pd-stat-val">${r.strike_rate.toFixed(1)}</div><div class="pd-stat-label">Strike Rate</div></div>
    <div class="pd-stat"><div class="pd-stat-val">${r.sixes}</div><div class="pd-stat-label">Sixes</div></div>
    <div class="pd-stat"><div class="pd-stat-val">${r.impact_score||"-"}</div><div class="pd-stat-label">Impact Score</div></div>`;
  $("pd-similar").innerHTML=`<div class="pd-similar-title">Similar Players</div>${similar.slice(0,4).map(([p,score])=>`<div class="pd-sim-row"><span>${p}</span><span class="pd-sim-score">${(score*100).toFixed(0)}% match</span></div>`).join("")}`;
  
  // Radar chart
  const allBat=batData.leaderboard.filter(x=>x.innings>=5);
  const maxAvg=Math.max(...allBat.map(x=>x.average));
  const maxSR=Math.max(...allBat.map(x=>x.strike_rate));
  const maxSix=Math.max(...allBat.map(x=>x.sixes));
  const maxRuns=Math.max(...allBat.map(x=>x.total_runs));
  const maxImp=Math.max(...allBat.map(x=>x.impact_score||0));
  dc("pd-radar-chart");
  charts["pd-radar-chart"]=new Chart($("pd-radar-chart").getContext("2d"),{type:"radar",data:{labels:["Average","Strike Rate","Sixes","Runs","Impact"],datasets:[{label:name,data:[r.average/maxAvg*100,r.strike_rate/maxSR*100,(r.sixes/maxSix)*100,r.total_runs/maxRuns*100,(r.impact_score||0)/maxImp*100],borderColor:P.orange,backgroundColor:"rgba(249,115,22,0.15)",pointBackgroundColor:P.orange,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{r:{grid:{color:"rgba(255,255,255,0.08)"},angleLines:{color:"rgba(255,255,255,0.08)"},ticks:{backdropColor:"transparent",font:{size:8},stepSize:20},pointLabels:{font:{size:10},color:"#94a3b8"},min:0,max:100}}}});
  $("player-detail").classList.remove("hidden");
  $("player-detail").scrollIntoView({behavior:"smooth",block:"nearest"});
}

// ═══ BOWLING ══════════════════════════════════════════════════════════════════
let bowlData=null,bowlQ="";
async function renderBowling(){
  bowlData=await load("bowling"); renderBowlTable();

  const top20=[...bowlData.leaderboard].slice(0,25);
  dc("bowl-scatter-chart");
  charts["bowl-scatter-chart"]=new Chart($("bowl-scatter-chart").getContext("2d"),{type:"bubble",data:{datasets:[{label:"Bowlers",data:top20.map(r=>({x:+r.economy.toFixed(2),y:r.wickets,r:Math.max(5,r.wickets/15),name:r.bowler})),backgroundColor:top20.map(r=>r.economy<7.5?"rgba(20,184,166,0.75)":"rgba(168,85,247,0.55)"),borderColor:top20.map(r=>r.economy<7.5?P.teal:P.purple),borderWidth:1}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.raw.name}  Econ:${c.raw.x}  Wkts:${c.raw.y}`}}},scales:{x:{title:{display:true,text:"Economy Rate",color:"#64748b"},grid:{color:"rgba(255,255,255,0.04)"}},y:{title:{display:true,text:"Total Wickets",color:"#64748b"},grid:{color:"rgba(255,255,255,0.04)"}}}}});

  const figs=bowlData.best_figures.slice(0,12);
  dc("figures-chart");
  charts["figures-chart"]=new Chart($("figures-chart").getContext("2d"),{type:"bar",data:{labels:figs.map(f=>`${f.bowler.split(" ").pop()} ${f.figure}`),datasets:[{label:"Wickets",data:figs.map(f=>f.wkts),backgroundColor:figs.map((_,i)=>i===0?P.orange:P.purple),borderRadius:5,borderSkipped:false}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{color:"rgba(255,255,255,0.04)"}},y:{grid:{display:false},ticks:{font:{size:10}}}}}});

  const byEcon=[...bowlData.leaderboard].filter(r=>r.wickets>=50).sort((a,b)=>a.economy-b.economy).slice(0,15);
  dc("economy-chart");
  charts["economy-chart"]=new Chart($("economy-chart").getContext("2d"),{type:"bar",data:{labels:byEcon.map(r=>r.bowler.split(" ").pop()),datasets:[{label:"Economy",data:byEcon.map(r=>r.economy),backgroundColor:byEcon.map(r=>r.economy<7.5?P.teal:r.economy<8.5?P.blue:P.purple),borderRadius:5,borderSkipped:false}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${byEcon[c.dataIndex].bowler}: ${c.parsed.y}`}}},scales:{x:{grid:{display:false},ticks:{font:{size:10}}},y:{grid:{color:"rgba(255,255,255,0.04)"},min:5,ticks:{stepSize:0.5}}}}});

  $("bowl-search").addEventListener("input",e=>debounce(()=>{bowlQ=e.target.value.toLowerCase();renderBowlTable();}));
}

function renderBowlTable(){
  if(!bowlData)return;
  let rows=[...bowlData.leaderboard];
  if(bowlQ)rows=rows.filter(r=>r.bowler.toLowerCase().includes(bowlQ));
  const empty=$("bowl-empty"),wrap=$("bowl-table-wrap");
  if(!rows.length){wrap.innerHTML="";empty.classList.remove("hidden");return;}
  empty.classList.add("hidden");
  wrap.innerHTML=tbl(["#","Bowler","Wickets","Economy","Avg","SR","4W","5W"],
    rows.slice(0,25).map((r,i)=>[
      `<span class="rank-num">${i+1}</span>`,
      `${r.bowler}${r.economy<7.5?'<span class="badge badge-blue">Elite</span>':""}`,
      `<strong>${r.wickets}</strong>`,
      `<span style="color:${r.economy<7.5?P.teal:r.economy<8.5?P.orange:P.muted}">${r.economy.toFixed(2)}</span>`,
      r.average.toFixed(1), r.strike_rate.toFixed(1),
      r.four_wkt_hauls||0, r.five_wkt_hauls||0
    ])
  );
}

// ═══ VENUES ═══════════════════════════════════════════════════════════════════
async function renderVenues(){
  const data=await load("venues");
  $("toss-value").textContent=`${data.toss_win_pct}%`;
  const avgF=(data.venues.reduce((s,v)=>s+v.avg_first_innings,0)/data.venues.length).toFixed(1);
  const avgS=(data.venues.reduce((s,v)=>s+v.avg_second_innings,0)/data.venues.length).toFixed(1);
  $("avg-first-val").textContent=avgF; $("avg-second-val").textContent=avgS;

  // Venue profile cards
  $("venue-cards-grid").innerHTML=data.venues.slice(0,6).map(v=>{
    const name=v.venue.split(",")[0];
    const pitchClr={"Batting Paradise":"#f97316","Chase Friendly":"#3b82f6","Spin Friendly":"#a855f7","Balanced":"#14b8a6","Bat First Venue":"#eab308","Run Fest":"#ef4444"}[v.pitch_type]||"#475569";
    return`<div class="venue-profile-card">
      <div class="vpc-header" style="border-color:${pitchClr}">
        <div class="vpc-name">${name}</div>
        <div class="vpc-tag" style="background:${pitchClr}22;color:${pitchClr};border:1px solid ${pitchClr}44">${v.pitch_type}</div>
      </div>
      <div class="vpc-stats">
        <div class="vpc-stat"><span class="vpc-val">${v.bat_first_win_pct}%</span><span class="vpc-lbl">Bat First Win</span></div>
        <div class="vpc-stat"><span class="vpc-val">${v.avg_first_innings}</span><span class="vpc-lbl">Avg 1st Inn</span></div>
        <div class="vpc-stat"><span class="vpc-val">${v.matches}</span><span class="vpc-lbl">Matches</span></div>
        <div class="vpc-stat"><span class="vpc-val">${v.boundary_opportunity}</span><span class="vpc-lbl">Boundary Opp</span></div>
      </div>
    </div>`;
  }).join("");

  const top10=data.venues.slice(0,10);
  dc("venue-chart");
  charts["venue-chart"]=new Chart($("venue-chart").getContext("2d"),{type:"bar",data:{labels:top10.map(v=>v.venue.split(",")[0].replace("Stadium","Stad.").replace(" Cricket","").replace(" Ground","")),datasets:[{label:"Bat First Win %",data:top10.map(v=>v.bat_first_win_pct),backgroundColor:P.orange,borderRadius:{topLeft:4,topRight:4}},{label:"Chase Win %",data:top10.map(v=>+(100-v.bat_first_win_pct).toFixed(1)),backgroundColor:P.blue,borderRadius:{topLeft:4,topRight:4}}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top"},tooltip:{callbacks:{label:c=>` ${c.dataset.label}: ${c.parsed.y.toFixed(1)}%`,afterBody:i=>{const v=top10[i[0].dataIndex];return[`Matches: ${v.matches}`,`Avg 1st Inn: ${v.avg_first_innings}`,`Avg 2nd Inn: ${v.avg_second_innings}`];}}}},scales:{x:{grid:{display:false},ticks:{font:{size:10},maxRotation:30}},y:{grid:{color:"rgba(255,255,255,0.04)"},min:0,max:100,ticks:{callback:v=>v+"%"}}}}});

  const byScore=[...data.venues].sort((a,b)=>b.avg_first_innings-a.avg_first_innings).slice(0,10);
  dc("venue-score-chart");
  charts["venue-score-chart"]=new Chart($("venue-score-chart").getContext("2d"),{type:"bar",data:{labels:byScore.map(v=>v.venue.split(",")[0].split(" ").slice(0,2).join(" ")),datasets:[{label:"Avg 1st Inn",data:byScore.map(v=>v.avg_first_innings),backgroundColor:P.orange,borderRadius:4},{label:"Avg 2nd Inn",data:byScore.map(v=>v.avg_second_innings),backgroundColor:P.blue,borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top",labels:{boxWidth:10,padding:8}}},scales:{x:{grid:{display:false},ticks:{font:{size:9},maxRotation:30}},y:{grid:{color:"rgba(255,255,255,0.04)"}}}}});

  const sel=$("venue-select");
  if(!sel.options.length){data.venues.forEach(v=>sel.appendChild(new Option(v.venue.split(",")[0],v.venue)));sel.addEventListener("change",()=>drawVenueRadar(sel.value,data.venues));}
  drawVenueRadar(data.venues[0].venue,data.venues);

  $("venue-table-wrap").innerHTML=tbl(["Venue","Matches","Bat 1st%","Avg 1st","Avg 2nd","Pitch Type"],data.venues.map(v=>[v.venue.split(",")[0],v.matches,`<span style="color:${v.bat_first_win_pct>50?P.orange:P.blue}">${v.bat_first_win_pct}%</span>`,v.avg_first_innings,v.avg_second_innings,`<span class="badge" style="background:rgba(20,184,166,0.15);color:#14b8a6;border:1px solid rgba(20,184,166,0.3)">${v.pitch_type}</span>`]));
}

function drawVenueRadar(name,venues){
  const v=venues.find(x=>x.venue===name);if(!v)return;
  const n=(val,arr)=>Math.round((val-Math.min(...arr))/(Math.max(...arr)-Math.min(...arr))*100);
  const aF=venues.map(x=>x.avg_first_innings),aS=venues.map(x=>x.avg_second_innings),bF=venues.map(x=>x.bat_first_win_pct),mC=venues.map(x=>x.matches);
  dc("venue-radar-chart");
  charts["venue-radar-chart"]=new Chart($("venue-radar-chart").getContext("2d"),{type:"radar",data:{labels:["High Scoring","Good Chase","Bat-First Friendly","Chase Friendly","High Traffic"],datasets:[{label:v.venue.split(",")[0],data:[n(v.avg_first_innings,aF),n(v.avg_second_innings,aS),v.bat_first_win_pct,100-v.bat_first_win_pct,n(v.matches,mC)],borderColor:P.orange,backgroundColor:"rgba(249,115,22,0.15)",pointBackgroundColor:P.orange,borderWidth:2,pointRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{r:{grid:{color:"rgba(255,255,255,0.08)"},angleLines:{color:"rgba(255,255,255,0.08)"},ticks:{backdropColor:"transparent",font:{size:9},stepSize:20},pointLabels:{font:{size:10},color:"#94a3b8"},min:0,max:100}}}});
}

// ═══ SEASON LEADERS ═══════════════════════════════════════════════════════════
let leadData=null,sliderIdx=0;
async function renderLeaders(){
  leadData=await load("season_leaders"); sliderIdx=leadData.seasons.length-1;
  buildSlider(); renderLeaderCard(sliderIdx); renderCapCharts();
}
function buildSlider(){
  const wrap=$("leaders-slider-wrap");if(!wrap||wrap.dataset.built)return;wrap.dataset.built="1";
  const S=leadData.seasons;
  wrap.innerHTML=`<div class="slider-track-wrap"><button class="slider-arrow" id="slider-prev">&#8592;</button><div class="slider-track" id="slider-track">${S.map((s,i)=>`<div class="slider-pip${i===sliderIdx?" active":""}" data-i="${i}">${s.season}</div>`).join("")}</div><button class="slider-arrow" id="slider-next">&#8594;</button></div><input type="range" id="season-range" class="season-range" min="0" max="${S.length-1}" value="${sliderIdx}" step="1">`;
  $("season-range").addEventListener("input",e=>{sliderIdx=+e.target.value;syncSlider();renderLeaderCard(sliderIdx);});
  $("slider-prev").addEventListener("click",()=>{if(sliderIdx>0){sliderIdx--;syncSlider();renderLeaderCard(sliderIdx);}});
  $("slider-next").addEventListener("click",()=>{if(sliderIdx<leadData.seasons.length-1){sliderIdx++;syncSlider();renderLeaderCard(sliderIdx);}});
  wrap.querySelectorAll(".slider-pip").forEach(p=>p.addEventListener("click",()=>{sliderIdx=+p.dataset.i;syncSlider();renderLeaderCard(sliderIdx);}));
}
function syncSlider(){
  const range=$("season-range");if(range)range.value=sliderIdx;
  document.querySelectorAll(".slider-pip").forEach(p=>p.classList.toggle("active",+p.dataset.i===sliderIdx));
  document.querySelector(".slider-pip.active")?.scrollIntoView({behavior:"smooth",block:"nearest",inline:"center"});
  ["orange-chart","purple-chart"].forEach((id,ci)=>{const c=charts[id];if(!c)return;c.data.datasets[0].backgroundColor=leadData.seasons.map((_,i)=>ci===0?(i===sliderIdx?P.orange:"rgba(249,115,22,0.22)"):(i===sliderIdx?P.purple:"rgba(168,85,247,0.22)"));c.update("none");});
}
function renderLeaderCard(idx){
  const s=leadData.seasons[idx];if(!s)return;syncSlider();
  $("leader-grid").innerHTML=`
    <div class="leader-card orange-card"><div class="leader-cap">🟠 Orange Cap</div><div class="leader-name">${s.orange_cap.player}</div><div class="leader-stat">${s.orange_cap.runs.toLocaleString()}</div><div class="leader-stat-label">runs · IPL ${s.season}</div><div class="leader-bg-icon">🏏</div><div class="leader-top5"><div class="top5-title">Top Run Scorers</div>${s.top_batsmen.map((p,i)=>`<div class="top5-row${i===0?" top5-winner":""}"><span class="top5-rank">${i+1}</span><span class="top5-name">${p.player}</span><span class="top5-val">${p.runs} runs</span></div>`).join("")}</div></div>
    <div class="leader-card purple-card"><div class="leader-cap">🟣 Purple Cap</div><div class="leader-name">${s.purple_cap.player}</div><div class="leader-stat">${s.purple_cap.wickets}</div><div class="leader-stat-label">wickets · IPL ${s.season}</div><div class="leader-bg-icon">🎳</div><div class="leader-top5"><div class="top5-title">Top Wicket Takers</div>${s.top_bowlers.map((p,i)=>`<div class="top5-row${i===0?" top5-winner":""}"><span class="top5-rank">${i+1}</span><span class="top5-name">${p.player}</span><span class="top5-val">${p.wickets} wkts</span></div>`).join("")}</div></div>`;
}
function renderCapCharts(){
  const seasons=leadData.seasons.map(s=>s.season);
  [["orange-chart",leadData.seasons.map(s=>s.orange_cap.runs),P.orange,"rgba(249,115,22,0.22)"],["purple-chart",leadData.seasons.map(s=>s.purple_cap.wickets),P.purple,"rgba(168,85,247,0.22)"]].forEach(([id,data,clr,dim])=>{dc(id);charts[id]=new Chart($(id).getContext("2d"),{type:"bar",data:{labels:seasons,datasets:[{data,borderRadius:5,backgroundColor:seasons.map((_,i)=>i===sliderIdx?clr:dim)}]},options:{responsive:true,maintainAspectRatio:false,onClick:(e,els)=>{if(els.length){sliderIdx=els[0].index;syncSlider();renderLeaderCard(sliderIdx);}},plugins:{legend:{display:false},tooltip:{callbacks:{title:i=>`IPL ${i[0].label}`}}},scales:{x:{grid:{display:false},ticks:{font:{size:9},maxRotation:45}},y:{grid:{color:"rgba(255,255,255,0.04)"}}}}});});
}

// ═══ ADVANCED ANALYTICS ═══════════════════════════════════════════════════════
async function renderAdvanced(){
  const adv=await load("advanced"), bat=await load("batting");

  // KPI strip
  const topImpact=adv.impact_scores[0];
  const topBat=bat.leaderboard[0];
  const topAvg=[...bat.leaderboard].filter(r=>r.innings>=8).sort((a,b)=>b.average-a.average)[0];
  const topSR=[...bat.leaderboard].filter(r=>r.innings>=5).sort((a,b)=>b.strike_rate-a.strike_rate)[0];
  $("kpi-strip").innerHTML=[
    {icon:"🏆",label:"Most Runs",name:topBat.batter,val:`${topBat.total_runs.toLocaleString()} runs`,clr:P.orange},
    {icon:"⚡",label:"Highest Impact",name:topImpact.player,val:`${topImpact.impact_score} score`,clr:P.gold},
    {icon:"📊",label:"Best Average",name:topAvg.batter,val:`${topAvg.average.toFixed(1)} avg`,clr:P.blue},
    {icon:"🚀",label:"Best Strike Rate",name:topSR.batter,val:`${topSR.strike_rate.toFixed(1)} SR`,clr:P.teal},
  ].map(k=>`<div class="kpi-card" style="--kc:${k.clr}"><div class="kpi-icon">${k.icon}</div><div class="kpi-label">${k.label}</div><div class="kpi-name">${k.name}</div><div class="kpi-val">${k.val}</div></div>`).join("");

  // Impact score chart
  const top15=adv.impact_scores.slice(0,15);
  dc("impact-chart");
  charts["impact-chart"]=new Chart($("impact-chart").getContext("2d"),{type:"bar",data:{labels:top15.map(r=>r.player.split(" ").pop()),datasets:[{label:"Impact Score",data:top15.map(r=>r.impact_score),backgroundColor:top15.map((_,i)=>i===0?P.orange:i<3?P.gold:"rgba(59,130,246,0.7)"),borderRadius:5,borderSkipped:false}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{title:i=>`${top15[i[0].dataIndex].player}`,label:c=>`Impact: ${c.parsed.x}  Runs: ${top15[c.dataIndex].runs.toLocaleString()}`}}},scales:{x:{grid:{color:"rgba(255,255,255,0.04)"}},y:{grid:{display:false},ticks:{font:{size:10}}}}}});

  // Phase analysis
  const phase=adv.phase_analysis;
  dc("phase-chart");
  charts["phase-chart"]=new Chart($("phase-chart").getContext("2d"),{type:"bar",data:{labels:phase.map(p=>p.phase),datasets:[{label:"Run Rate",data:phase.map(p=>p.avg_rr),backgroundColor:[P.blue,P.teal,P.orange],borderRadius:5,borderSkipped:false,yAxisID:"y"},{label:"Boundary%",data:phase.map(p=>p.boundary_pct),type:"line",borderColor:P.gold,backgroundColor:"transparent",pointBackgroundColor:P.gold,tension:0.3,yAxisID:"y2"}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top",labels:{boxWidth:10,padding:8}}},scales:{y:{grid:{color:"rgba(255,255,255,0.04)"},title:{display:true,text:"Run Rate",color:"#64748b"}},y2:{position:"right",grid:{display:false},title:{display:true,text:"Boundary %",color:"#64748b"},ticks:{callback:v=>v+"%"}}}}});

  // Heatmap
  buildHeatmap(adv.heatmap);

  // Toss chart
  const t=adv.toss_analysis;
  dc("toss-chart");
  charts["toss-chart"]=new Chart($("toss-chart").getContext("2d"),{type:"doughnut",data:{labels:["Toss Winner → Win","Toss Winner → Lose"],datasets:[{data:[t.overall_win_pct,100-t.overall_win_pct],backgroundColor:[P.orange,"rgba(255,255,255,0.08)"],borderWidth:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom"},tooltip:{callbacks:{label:c=>`${c.label}: ${c.parsed}%`}}}},cutout:"65%"});

  // Similarity search
  $("sim-btn").addEventListener("click",()=>runSimilarity());
  $("sim-search").addEventListener("keydown",e=>{ if(e.key==="Enter") runSimilarity(); });

  // Compare radar
  await setupCompareRadar(bat);
}

function buildHeatmap(hm){
  const {players,seasons,matrix}=hm;
  const allVals=players.flatMap(p=>seasons.map(s=>matrix[p][s]||0));
  const maxVal=Math.max(...allVals)||1;
  let html=`<div class="hm-wrap"><div class="hm-corner"></div>${seasons.map(s=>`<div class="hm-col-head">'${String(s).slice(2)}</div>`).join("")}</div>`;
  players.forEach(p=>{
    html+=`<div class="hm-row"><div class="hm-player">${p.split(" ").pop()}</div>`;
    seasons.forEach(s=>{
      const v=matrix[p][s]||0;
      const pct=v/maxVal;
      const alpha=v>0?0.15+pct*0.75:0.03;
      const textClr=pct>0.5?"#fff":"#94a3b8";
      html+=`<div class="hm-cell" title="${p} in ${s}: ${v||'—'} runs" style="background:rgba(249,115,22,${alpha.toFixed(2)});color:${textClr}">${v||""}</div>`;
    });
    html+="</div>";
  });
  const wrap=document.getElementById("heatmap-container");
  if(wrap) wrap.innerHTML=html;
}

async function runSimilarity(){
  const q=$("sim-search").value.trim().toLowerCase(); if(!q)return;
  if(!simData)simData=await load("similarity");
  const key=Object.keys(simData).find(k=>k.toLowerCase().includes(q));
  const res=$("sim-results");
  if(!key){res.innerHTML=`<div class="sim-not-found">Player not found. Try "Kohli", "Rohit", "Bumrah"…</div>`;return;}
  const similar=simData[key];
  res.innerHTML=`<div class="sim-title">Players similar to <strong>${key}</strong>:</div>${similar.map(([p,sc],i)=>`<div class="sim-row"><span class="sim-rank">${i+1}</span><span class="sim-name">${p}</span><div class="sim-bar-wrap"><div class="sim-bar" style="width:${(sc*100).toFixed(0)}%"></div></div><span class="sim-pct">${(sc*100).toFixed(0)}%</span></div>`).join("")}`;
}

async function setupCompareRadar(bat){
  const players=bat.leaderboard.filter(r=>r.innings>=5);
  const names=players.map(r=>r.batter);
  ["cmp1","cmp2","cmp3"].forEach((id,idx)=>{
    const sel=$(id); sel.innerHTML="";
    names.forEach(n=>sel.appendChild(new Option(n,n)));
    sel.value=names[idx]||names[0];
    sel.addEventListener("change",()=>drawCompareRadar(players));
  });
  drawCompareRadar(players);
}

function drawCompareRadar(players){
  const sel1=$("cmp1").value,sel2=$("cmp2").value,sel3=$("cmp3").value;
  const maxAvg=Math.max(...players.map(x=>x.average));
  const maxSR=Math.max(...players.map(x=>x.strike_rate));
  const maxSix=Math.max(...players.map(x=>x.sixes));
  const maxRuns=Math.max(...players.map(x=>x.total_runs));
  const maxImp=Math.max(...players.map(x=>x.impact_score||0));
  function norm(r){return[r.average/maxAvg*100,r.strike_rate/maxSR*100,(r.sixes/maxSix)*100,r.total_runs/maxRuns*100,(r.impact_score||0)/maxImp*100];}
  const pal=[[P.orange,"rgba(249,115,22,0.15)"],[P.blue,"rgba(59,130,246,0.15)"],[P.purple,"rgba(168,85,247,0.15)"]];
  const selected=[sel1,sel2,sel3];
  dc("compare-radar-chart");
  charts["compare-radar-chart"]=new Chart($("compare-radar-chart").getContext("2d"),{type:"radar",data:{labels:["Average","Strike Rate","Sixes","Total Runs","Impact Score"],datasets:selected.map((name,i)=>{const r=players.find(x=>x.batter===name);if(!r)return null;return{label:name,data:norm(r),borderColor:pal[i][0],backgroundColor:pal[i][1],pointBackgroundColor:pal[i][0],borderWidth:2};}).filter(Boolean)},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"top",labels:{boxWidth:10,padding:8}}},scales:{r:{grid:{color:"rgba(255,255,255,0.08)"},angleLines:{color:"rgba(255,255,255,0.08)"},ticks:{backdropColor:"transparent",font:{size:9},stepSize:20},pointLabels:{font:{size:11},color:"#94a3b8"},min:0,max:100}}}});
}

// ═══ MONEYBALL ════════════════════════════════════════════════════════════════
async function renderMoneyball(){
  const adv=await load("advanced");
  const mb=adv.moneyball_batting, mbb=adv.moneyball_bowling;

  // Insights
  const bestBatVal=mb[0], bestBowlVal=mbb[0];
  const mostExpBat=[...mb].sort((a,b)=>b.price_cr-a.price_cr)[0];
  $("money-insight-strip").innerHTML=[
    {icon:"💎",title:"Best Batting Value",text:`<strong>${bestBatVal.player}</strong> delivers <strong>${bestBatVal.runs_per_cr} runs/crore</strong> — the most cost-efficient batter in IPL auction history.`},
    {icon:"🎳",title:"Best Bowling Value",text:`<strong>${bestBowlVal.player}</strong> takes <strong>${bestBowlVal.wkts_per_cr} wickets/crore</strong> — exceptional return on investment for any franchise.`},
    {icon:"💰",title:"Premium Pricing",text:`<strong>${mostExpBat.player}</strong> commands ₹${mostExpBat.price_cr}Cr — top auction price. Does the performance justify the spend?`},
  ].map(i=>`<div class="insight-card"><div class="insight-icon">${i.icon}</div><div class="insight-title">${i.title}</div><div class="insight-text">${i.text}</div></div>`).join("");

  // Runs per crore chart
  const top12bat=mb.slice(0,12);
  dc("money-bat-chart");
  charts["money-bat-chart"]=new Chart($("money-bat-chart").getContext("2d"),{type:"bar",data:{labels:top12bat.map(r=>r.player.split(" ").pop()),datasets:[{label:"Runs per ₹Crore",data:top12bat.map(r=>r.runs_per_cr),backgroundColor:top12bat.map((_,i)=>i===0?P.gold:i<3?"rgba(234,179,8,0.6)":"rgba(234,179,8,0.35)"),borderRadius:5,borderSkipped:false}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{title:i=>`${top12bat[i[0].dataIndex].player}`,label:c=>`${c.parsed.x} runs/₹Cr  |  ₹${top12bat[c.dataIndex].price_cr}Cr  |  ${top12bat[c.dataIndex].runs.toLocaleString()} runs`}}},scales:{x:{grid:{color:"rgba(255,255,255,0.04)"}},y:{grid:{display:false},ticks:{font:{size:10}}}}}});

  const top12bowl=mbb.slice(0,12);
  dc("money-bowl-chart");
  charts["money-bowl-chart"]=new Chart($("money-bowl-chart").getContext("2d"),{type:"bar",data:{labels:top12bowl.map(r=>r.player.split(" ").pop()),datasets:[{label:"Wickets per ₹Crore",data:top12bowl.map(r=>r.wkts_per_cr),backgroundColor:top12bowl.map((_,i)=>i===0?P.teal:i<3?"rgba(20,184,166,0.6)":"rgba(20,184,166,0.35)"),borderRadius:5,borderSkipped:false}]},options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{title:i=>`${top12bowl[i[0].dataIndex].player}`,label:c=>`${c.parsed.x} wkts/₹Cr  |  ₹${top12bowl[c.dataIndex].price_cr}Cr  |  ${top12bowl[c.dataIndex].wickets} wickets`}}},scales:{x:{grid:{color:"rgba(255,255,255,0.04)"}},y:{grid:{display:false},ticks:{font:{size:10}}}}}});

  const tierClr={"Elite Value":"#22c55e","Good Value":"#3b82f6","Premium Price":"#f97316"};
  $("money-bat-table").innerHTML=tbl(["#","Batter","Runs","₹Crore","Runs/Cr","SR","Value Tier"],
    mb.slice(0,20).map((r,i)=>[`<span class="rank-num">${i+1}</span>`,`<b>${r.player}</b>`,r.runs.toLocaleString(),`₹${r.price_cr}Cr`,`<strong style="color:${P.gold}">${r.runs_per_cr}</strong>`,r.sr,`<span class="badge" style="background:${tierClr[r.value_tier]}22;color:${tierClr[r.value_tier]};border:1px solid ${tierClr[r.value_tier]}44">${r.value_tier}</span>`]));

  $("money-bowl-table").innerHTML=tbl(["#","Bowler","Wickets","₹Crore","Wkts/Cr","Economy","Value Tier"],
    mbb.slice(0,20).map((r,i)=>[`<span class="rank-num">${i+1}</span>`,`<b>${r.player}</b>`,r.wickets,`₹${r.price_cr}Cr`,`<strong style="color:${P.teal}">${r.wkts_per_cr}</strong>`,r.economy,`<span class="badge" style="background:${tierClr[r.value_tier]}22;color:${tierClr[r.value_tier]};border:1px solid ${tierClr[r.value_tier]}44">${r.value_tier}</span>`]));
}

// ═══ GALLERY ══════════════════════════════════════════════════════════════════
async function renderGallery(){
  const [bat,bowl,ov,venues]=await Promise.all([load("batting"),load("bowling"),load("overview"),load("venues")]);
  const topBat=[...bat.leaderboard].sort((a,b)=>b.total_runs-a.total_runs)[0];
  const topSix=[...bat.leaderboard].sort((a,b)=>b.sixes-a.sixes)[0];
  const topWkt=[...bowl.leaderboard].sort((a,b)=>b.wickets-a.wickets)[0];
  const bestEco=[...bowl.leaderboard].filter(r=>r.wickets>=50).sort((a,b)=>a.economy-b.economy)[0];
  const bestV=[...venues.venues].sort((a,b)=>b.avg_first_innings-a.avg_first_innings)[0];
  const bestFig=bowl.best_figures[0];

  $("records-grid").innerHTML=[
    {icon:"🏆",label:"Most Runs (Career)",name:topBat.batter,stat:`${topBat.total_runs.toLocaleString()} runs`,sub:`Avg ${topBat.average.toFixed(1)} · SR ${topBat.strike_rate.toFixed(1)}`,clr:P.orange},
    {icon:"💥",label:"Most Sixes (Career)",name:topSix.batter,stat:`${topSix.sixes} sixes`,sub:`${topSix.total_runs.toLocaleString()} total runs`,clr:P.gold},
    {icon:"🎳",label:"Most Wickets (Career)",name:topWkt.bowler,stat:`${topWkt.wickets} wickets`,sub:`Economy ${topWkt.economy.toFixed(2)}`,clr:P.purple},
    {icon:"💰",label:"Best Economy (50+ wkts)",name:bestEco.bowler,stat:`${bestEco.economy.toFixed(2)} econ`,sub:`${bestEco.wickets} wickets`,clr:P.teal},
    {icon:"🏟️",label:"Highest Scoring Venue",name:bestV.venue.split(",")[0],stat:`${bestV.avg_first_innings} avg`,sub:`${bestV.matches} matches played`,clr:P.blue},
    {icon:"🔥",label:"Best Match Figures",name:bestFig.bowler,stat:bestFig.figure,sub:"Best single-match spell",clr:P.red},
  ].map(r=>`<div class="record-card" style="--rc:${r.clr}"><div class="record-icon">${r.icon}</div><div class="record-label">${r.label}</div><div class="record-name">${r.name}</div><div class="record-stat">${r.stat}</div><div class="record-sub">${r.sub}</div></div>`).join("");

  const ss=ov.season_stats;
  $("ipl-timeline").innerHTML=[
    {year:2008,icon:"🎉",title:"IPL is Born",text:"First edition with 8 teams. Rajasthan Royals stun the world. Shane Warne leads the underdogs to the title in a remarkable debut season."},
    {year:2010,icon:"🏏",title:"MS Dhoni Era",text:"Chennai Super Kings become the team to beat. Dhoni's calm leadership and CSK's consistency set the template for franchise cricket success."},
    {year:2012,icon:"💥",title:"Chris Gayle Effect",text:"Gayle smashes 733 runs including the first IPL century in just 30 balls. His impact redefines what's possible in T20 power hitting."},
    {year:2016,icon:"🌟",title:"Kohli's Historic Season",text:"Virat Kohli scores 973 runs — the all-time IPL record. Four half centuries and four centuries in a single season. Never replicated since."},
    {year:2020,icon:"🌍",title:"UAE Edition",text:"COVID-19 moves the tournament to UAE. Mumbai Indians win their 5th title. KL Rahul wins Orange Cap with 670 runs in the unique bubble environment."},
    {year:2022,icon:"⚡",title:"10-Team Era",text:`IPL expands to Gujarat Titans and Lucknow Super Giants. ${ss.find(s=>s.season===2022)?.sixes||730} sixes hit across 74 matches. GT win the title on debut.`},
    {year:2025,icon:"🚀",title:"Peak T20 Era",text:`${ss[ss.length-1].sixes} sixes in ${ss[ss.length-1].season}. Virat Kohli continues to accumulate — now the all-time run-scorer in IPL history with 8,661 runs.`},
  ].map((e,i)=>`<div class="tl-item ${i%2===0?"tl-left":"tl-right"}"><div class="tl-dot">${e.icon}</div><div class="tl-card"><div class="tl-year">${e.year}</div><div class="tl-title">${e.title}</div><div class="tl-text">${e.text}</div></div></div>`).join("");

  document.querySelectorAll(".gallery-card").forEach(c=>c.addEventListener("click",()=>openLightbox(c.dataset.img,c.dataset.title,c.dataset.caption)));
}

function openLightbox(src,title,caption){$("lightbox-img").src=src;$("lightbox-title").textContent=title;$("lightbox-caption-text").textContent=caption;$("lightbox").classList.remove("hidden");document.body.style.overflow="hidden";}
function closeLightbox(){$("lightbox").classList.add("hidden");document.body.style.overflow="";}
$("lightbox-close").onclick=closeLightbox; $("lightbox-backdrop").onclick=closeLightbox;
document.addEventListener("keydown",e=>{if(e.key==="Escape")closeLightbox();});

// ═══ AI CHATBOT ════════════════════════════════════════════════════════════════
(function(){
  const fab=$("chat-fab"),panel=$("chat-panel"),msgs=$("chat-messages"),inp=$("chat-input");
  fab.onclick=()=>{panel.classList.remove("hidden");inp.focus();};
  $("chat-close").onclick=()=>panel.classList.add("hidden");
  $("chat-send").onclick=send; inp.addEventListener("keydown",e=>{if(e.key==="Enter")send();});
  document.querySelectorAll(".chip").forEach(c=>c.onclick=()=>ask(c.dataset.q));
  function send(){const q=inp.value.trim();if(!q)return;inp.value="";ask(q);}
  function ask(q){addMsg("user",q);const t=addTyping();setTimeout(async()=>{const a=await reply(q);t.remove();addMsg("bot",a);msgs.scrollTop=9999;},420);}
  function addMsg(role,html){const d=document.createElement("div");d.className=`chat-msg ${role==="bot"?"bot-msg":"user-msg"}`;d.innerHTML=`<span class="msg-avatar">${role==="bot"?"🏏":"👤"}</span><div class="msg-bubble">${html}</div>`;msgs.appendChild(d);msgs.scrollTop=9999;return d;}
  function addTyping(){const d=document.createElement("div");d.className="chat-msg bot-msg";d.innerHTML=`<span class="msg-avatar">🏏</span><div class="msg-bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>`;msgs.appendChild(d);msgs.scrollTop=9999;return d;}
  function row(l,v){return`<div class="stat-line"><span>${l}</span><span class="val">${v}</span></div>`;}

  async function reply(q){
    const ql=q.toLowerCase();
    let bat,bowl,ov,venues,leaders,adv;
    try{[bat,bowl,ov,venues,leaders,adv]=await Promise.all([load("batting"),load("bowling"),load("overview"),load("venues"),load("season_leaders"),load("advanced")]);}
    catch(e){return"⚠️ Couldn't load data.";}
    const yr=ql.match(/\b(20\d{2})\b/);const cy=yr?+yr[1]:null;

    if(/(orange cap)/.test(ql)){if(cy){const s=leaders.seasons.find(x=>x.season===cy);return s?`🟠 <strong>Orange Cap ${cy}</strong><br>${row(s.orange_cap.player,s.orange_cap.runs+" runs")}`:`No data for ${cy}.`;}const all=leaders.seasons.map(s=>({y:s.season,p:s.orange_cap.player,r:s.orange_cap.runs})).sort((a,b)=>b.r-a.r);return`🟠 <strong>Top Orange Cap Seasons:</strong><br>${all.slice(0,5).map((x,i)=>row(`${i+1}. ${x.p} (${x.y})`,x.r+" runs")).join("")}`;}
    if(/(purple cap)/.test(ql)){if(cy){const s=leaders.seasons.find(x=>x.season===cy);return s?`🟣 <strong>Purple Cap ${cy}</strong><br>${row(s.purple_cap.player,s.purple_cap.wickets+" wkts")}`:`No data for ${cy}.`;}const all=leaders.seasons.map(s=>({y:s.season,p:s.purple_cap.player,w:s.purple_cap.wickets})).sort((a,b)=>b.w-a.w);return`🟣 <strong>Top Purple Cap Seasons:</strong><br>${all.slice(0,5).map((x,i)=>row(`${i+1}. ${x.p} (${x.y})`,x.w+" wkts")).join("")}`;}

    const bp=bat.leaderboard.find(r=>r.batter.toLowerCase().split(" ").some(w=>w.length>3&&ql.includes(w)));
    if(bp)return`🏏 <strong>${bp.batter}</strong><br>${row("Runs",bp.total_runs.toLocaleString())}${row("Innings",bp.innings)}${row("Average",bp.average.toFixed(1))}${row("Strike Rate",bp.strike_rate.toFixed(1))}${row("Sixes",bp.sixes)}${row("Impact Score",bp.impact_score||"-")}`;
    const bwp=bowl.leaderboard.find(r=>r.bowler.toLowerCase().split(" ").some(w=>w.length>3&&ql.includes(w)));
    if(bwp)return`🎳 <strong>${bwp.bowler}</strong><br>${row("Wickets",bwp.wickets)}${row("Economy",bwp.economy.toFixed(2))}${row("Average",bwp.average.toFixed(1))}${row("Strike Rate",bwp.strike_rate.toFixed(1))}`;

    if(/(most run|top batter|run scorer)/.test(ql)){const t=[...bat.leaderboard].sort((a,b)=>b.total_runs-a.total_runs).slice(0,5);return`🏏 <strong>Top Run Scorers:</strong><br>${t.map((r,i)=>row(`${i+1}. ${r.batter}`,r.total_runs.toLocaleString()+" runs")).join("")}`;}
    if(/(most six|six machine)/.test(ql)){const t=[...bat.leaderboard].sort((a,b)=>b.sixes-a.sixes).slice(0,5);return`💥 <strong>Most Sixes:</strong><br>${t.map((r,i)=>row(`${i+1}. ${r.batter}`,r.sixes+" sixes")).join("")}`;}
    if(/(impact score|best impact)/.test(ql)){return`⚡ <strong>Top Impact Scores:</strong><br>${adv.impact_scores.slice(0,5).map((r,i)=>row(`${i+1}. ${r.player}`,r.impact_score+" score")).join("")}`;}
    if(/(best value|auction value|moneyball|runs per crore)/.test(ql)){const t=adv.moneyball_batting.slice(0,5);return`💎 <strong>Best Batting Value (Runs/Crore):</strong><br>${t.map((r,i)=>row(`${i+1}. ${r.player}`,r.runs_per_cr+" runs/₹Cr")).join("")}`;}
    if(/(most wicket|top bowler)/.test(ql)&&!/(economy)/.test(ql)){const t=[...bowl.leaderboard].sort((a,b)=>b.wickets-a.wickets).slice(0,5);return`🎳 <strong>Most Wickets:</strong><br>${t.map((r,i)=>row(`${i+1}. ${r.bowler}`,r.wickets+" wkts")).join("")}`;}
    if(/(economy|economical|cheap)/.test(ql)){const t=[...bowl.leaderboard].filter(r=>r.wickets>=50).sort((a,b)=>a.economy-b.economy).slice(0,5);return`💰 <strong>Best Economy Rates:</strong><br>${t.map((r,i)=>row(`${i+1}. ${r.bowler}`,r.economy.toFixed(2)+" econ")).join("")}`;}
    if(/(best figure|best spell)/.test(ql)){const t=bowl.best_figures.slice(0,5);return`🔥 <strong>Best Bowling Figures:</strong><br>${t.map((r,i)=>row(`${i+1}. ${r.bowler}`,r.figure)).join("")}`;}
    if(/(similar|like|plays like)/.test(ql)){const nm=bat.leaderboard.find(r=>r.batter.toLowerCase().split(" ").some(w=>w.length>3&&ql.includes(w)));if(nm){const sim=(await load("similarity"))[nm.batter]||[];return`🔍 <strong>Similar to ${nm.batter}:</strong><br>${sim.slice(0,4).map((([p,s])=>row(p,`${(s*100).toFixed(0)}% match`))).join("")}`;}return"Type a player name to find similar batters.";}
    if(/(compare|vs|versus)/.test(ql)){const ps=bat.leaderboard.filter(r=>r.batter.toLowerCase().split(" ").some(w=>w.length>3&&ql.includes(w)));if(ps.length>=2){const [a,b]=ps;return`⚔️ <strong>${a.batter} vs ${b.batter}</strong><br><div style="display:grid;grid-template-columns:1fr auto 1fr;gap:4px;font-size:12px;margin-top:8px;text-align:center"><b style="color:#f97316">${a.total_runs.toLocaleString()}</b><span style="color:#475569">Runs</span><b style="color:#3b82f6">${b.total_runs.toLocaleString()}</b><b style="color:#f97316">${a.average.toFixed(1)}</b><span style="color:#475569">Avg</span><b style="color:#3b82f6">${b.average.toFixed(1)}</b><b style="color:#f97316">${a.strike_rate.toFixed(1)}</b><span style="color:#475569">SR</span><b style="color:#3b82f6">${b.strike_rate.toFixed(1)}</b><b style="color:#f97316">${a.sixes}</b><span style="color:#475569">6s</span><b style="color:#3b82f6">${b.sixes}</b></div>`;}}
    if(/(most win|best team)/.test(ql)){const t=Object.entries(ov.team_wins).sort((a,b)=>b[1]-a[1]).slice(0,5);return`🏆 <strong>Most Wins:</strong><br>${t.map((e,i)=>row(`${i+1}. ${e[0]}`,e[1]+" wins")).join("")}`;}
    if(/(toss)/.test(ql))return`🪙 <strong>Toss Impact:</strong><br>${row("Toss winner wins match",ov.toss_win_pct+"% of the time")}<small style="display:block;color:#64748b;margin-top:4px">Across ${ov.total_matches} matches — a slight but real advantage.</small>`;
    if(/(best venue|highest scoring)/.test(ql)){const t=[...venues.venues].sort((a,b)=>b.avg_first_innings-a.avg_first_innings).slice(0,5);return`🏟️ <strong>Highest Scoring Venues:</strong><br>${t.map((v,i)=>row(`${i+1}. ${v.venue.split(",")[0]}`,v.avg_first_innings+" avg")).join("")}`;}
    const vm=venues.venues.find(v=>v.venue.toLowerCase().split(/[\s,]+/).some(p=>p.length>4&&ql.includes(p)));
    if(vm)return`🏟️ <strong>${vm.venue.split(",")[0]}</strong><br>${row("Matches",vm.matches)}${row("Avg 1st Inn",vm.avg_first_innings)}${row("Bat First Win",vm.bat_first_win_pct+"%")}${row("Pitch Type",vm.pitch_type)}`;
    return`Hmm, couldn't find that. Try:<br><span style="color:#94a3b8">• "Kohli stats" · "Bumrah economy"</span><br><span style="color:#94a3b8">• "Orange Cap 2022?" · "Purple Cap 2016?"</span><br><span style="color:#94a3b8">• "Best auction value?" · "Impact score?"</span><br><span style="color:#94a3b8">• "Similar to Rohit?" · "Compare Kohli vs Rohit"</span>`;
  }
})();

// ═══ BOOT ══════════════════════════════════════════════════════════════════════
(async()=>{
  const tab=activeTab(); switchTab(tab); await navigate(tab);
  window.addEventListener("hashchange",async()=>{const t=activeTab();switchTab(t);await navigate(t);});
})();
