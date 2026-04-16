#\!/usr/bin/env python3
"""
TOSM Install Dashboard Generator
Reads TOSM_AppsFlyer_Install.csv and generates an HTML dashboard.
Run this script whenever the CSV is updated.
"""
import os, json, re
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH   = os.path.join(SCRIPT_DIR, "TOSM_AppsFlyer_Install.csv")
HTML_PATH  = os.path.join(SCRIPT_DIR, "TOSM_Dashboard.html")

# ── Parse CSV ──────────────────────────────────────────────────────────────
def parse_num(x):
    if not x: return 0
    s = re.sub(r'[,\s]', '', str(x).strip())
    try: return int(float(s)) if s not in ('', '-') else 0
    except: return 0

rows = []
import csv
with open(CSV_PATH, encoding="utf-8", newline="") as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for parts in reader:
        pass  # already parsed
        date_str = parts[0].strip()
        org  = parse_num(parts[1])
        non  = parse_num(parts[2])
        try:
            d = datetime.strptime(date_str, '%d/%m/%Y')
        except:
            continue
        if org + non == 0: continue
        rows.append({'date': d, 'organic': org, 'nonorganic': non})

rows.sort(key=lambda r: r['date'])

# ── Aggregate ─────────────────────────────────────────────────────────────
from collections import defaultdict

monthly_org = defaultdict(int)
monthly_non = defaultdict(int)
weekly_org  = defaultdict(int)
weekly_non  = defaultdict(int)

for r in rows:
    mk = r['date'].strftime('%b %Y')
    monthly_org[mk] += r['organic']
    monthly_non[mk] += r['nonorganic']
    # ISO week starting Monday
    wk = r['date'].strftime('%d/%m/%y')
    # group by week number
    wy = r['date'].isocalendar()
    wk2 = f"{wy[0]}-W{wy[1]:02d}"
    weekly_org[wk2]  += r['organic']
    weekly_non[wk2]  += r['nonorganic']

months = list(dict.fromkeys([r['date'].strftime('%b %Y') for r in rows]))
weeks  = sorted(weekly_org.keys())

m_org_vals = [monthly_org[m] for m in months]
m_non_vals = [monthly_non[m] for m in months]
m_tot_vals = [o+n for o,n in zip(m_org_vals, m_non_vals)]
m_org_pct  = [round(o/t*100,1) if t else 0 for o,t in zip(m_org_vals,m_tot_vals)]
m_non_pct  = [round(n/t*100,1) if t else 0 for n,t in zip(m_non_vals,m_tot_vals)]

w_org_vals = [weekly_org[w] for w in weeks]
w_non_vals = [weekly_non[w] for w in weeks]

daily_labels = [r['date'].strftime('%d %b') for r in rows]
daily_org    = [r['organic'] for r in rows]
daily_non    = [r['nonorganic'] for r in rows]
daily_tot    = [r['organic']+r['nonorganic'] for r in rows]
daily_org_pct= [round(o/t*100,1) if t else 0 for o,t in zip(daily_org,daily_tot)]

# ── KPI ───────────────────────────────────────────────────────────────────
total_org = sum(r['organic'] for r in rows)
total_non = sum(r['nonorganic'] for r in rows)
total_all = total_org + total_non
best_day_row = max(rows, key=lambda r: r['organic']+r['nonorganic'])
best_day_val = best_day_row['organic'] + best_day_row['nonorganic']
best_day_str = best_day_row['date'].strftime('%d %b %Y')
org_pct_all  = round(total_org/total_all*100,1) if total_all else 0
non_pct_all  = round(total_non/total_all*100,1) if total_all else 0
last_day = rows[-1]['date'].strftime('%d %b %Y')
updated_at = datetime.now().strftime('%d %b %Y %H:%M')

# Recent 7-day avg
recent = rows[-7:]
avg7 = round(sum(r['organic']+r['nonorganic'] for r in recent)/len(recent)) if recent else 0

# ── HTML ──────────────────────────────────────────────────────────────────
html = f"""<\!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TOSM – Install Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --blue:#2E75B6; --dark:#1F3864; --orange:#ED7D31;
    --green:#70AD47; --bg:#F4F7FB; --card:#fff;
    --text:#1a1a2e; --muted:#6b7280; --border:#e5e7eb;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:'Segoe UI',Arial,sans-serif; background:var(--bg); color:var(--text); }}

  /* NAV */
  nav {{ background:var(--dark); color:#fff; padding:16px 32px;
         display:flex; align-items:center; justify-content:space-between; }}
  nav h1 {{ font-size:1.25rem; font-weight:700; letter-spacing:.5px; }}
  nav span {{ font-size:.8rem; opacity:.7; }}

  /* MAIN */
  .container {{ max-width:1280px; margin:0 auto; padding:28px 24px; }}

  /* KPI CARDS */
  .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:16px; margin-bottom:28px; }}
  .kpi {{ background:var(--card); border-radius:12px; padding:20px 22px;
          box-shadow:0 1px 4px rgba(0,0,0,.07); border-left:4px solid var(--blue); }}
  .kpi.orange {{ border-color:var(--orange); }}
  .kpi.green  {{ border-color:var(--green); }}
  .kpi.dark   {{ border-color:var(--dark); }}
  .kpi .label {{ font-size:.75rem; color:var(--muted); text-transform:uppercase; letter-spacing:.6px; margin-bottom:6px; }}
  .kpi .value {{ font-size:1.8rem; font-weight:700; color:var(--dark); line-height:1; }}
  .kpi .sub   {{ font-size:.78rem; color:var(--muted); margin-top:4px; }}

  /* CHARTS */
  .charts-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:20px; }}
  .chart-full  {{ grid-column:1/-1; }}
  .card {{ background:var(--card); border-radius:12px; padding:22px 24px;
           box-shadow:0 1px 4px rgba(0,0,0,.07); }}
  .card h2 {{ font-size:.95rem; font-weight:600; color:var(--dark); margin-bottom:16px; }}
  .card .canvas-wrap {{ position:relative; height:260px; }}
  .card.tall .canvas-wrap {{ height:300px; }}

  /* TABLE */
  .table-wrap {{ overflow-x:auto; }}
  table {{ width:100%; border-collapse:collapse; font-size:.85rem; }}
  thead tr {{ background:var(--dark); color:#fff; }}
  thead th {{ padding:10px 14px; text-align:center; font-weight:600; font-size:.8rem; letter-spacing:.3px; }}
  tbody tr:nth-child(even) {{ background:#f8fafc; }}
  tbody tr:hover {{ background:#eef4fb; }}
  tbody td {{ padding:8px 14px; text-align:center; border-bottom:1px solid var(--border); }}
  .spike {{ background:#FFF3CD \!important; font-weight:600; }}
  .bar-cell {{ display:flex; align-items:center; gap:6px; justify-content:center; }}
  .bar-bg {{ background:#e5e7eb; border-radius:4px; height:8px; flex:1; max-width:80px; overflow:hidden; }}
  .bar-fill {{ background:var(--blue); height:100%; border-radius:4px; transition:width .3s; }}
  .bar-fill.orange {{ background:var(--orange); }}

  /* FOOTER */
  footer {{ text-align:center; padding:24px; font-size:.78rem; color:var(--muted); }}

  @media(max-width:768px) {{
    .charts-grid {{ grid-template-columns:1fr; }}
    .chart-full {{ grid-column:1; }}
  }}
</style>
</head>
<body>

<nav>
  <h1>🎮 TOSM — Install Dashboard</h1>
  <span>Last updated: {updated_at} &nbsp;|&nbsp; Data up to: {last_day}</span>
</nav>

<div class="container">

  <div class="kpi-grid">
    <div class="kpi">
      <div class="label">Total Installs</div>
      <div class="value">{total_all:,}</div>
      <div class="sub">Since campaign launch</div>
    </div>
    <div class="kpi">
      <div class="label">Organic</div>
      <div class="value">{total_org:,}</div>
      <div class="sub">{org_pct_all}% of total</div>
    </div>
    <div class="kpi orange">
      <div class="label">Non-Organic (Paid)</div>
      <div class="value">{total_non:,}</div>
      <div class="sub">{non_pct_all}% of total</div>
    </div>
    <div class="kpi green">
      <div class="label">Best Single Day</div>
      <div class="value">{best_day_val:,}</div>
      <div class="sub">{best_day_str}</div>
    </div>
    <div class="kpi dark">
      <div class="label">7-Day Avg (Latest)</div>
      <div class="value">{avg7:,}</div>
      <div class="sub">installs / day</div>
    </div>
  </div>

  <div class="charts-grid">
    <div class="card">
      <h2>📊 Monthly Install Mix (Organic vs Non-Organic %)</h2>
      <div class="canvas-wrap"><canvas id="chartMonthMix"></canvas></div>
    </div>
    <div class="card">
      <h2>📦 Monthly Install Volume</h2>
      <div class="canvas-wrap"><canvas id="chartMonthVol"></canvas></div>
    </div>
  </div>

  <div class="charts-grid">
    <div class="card chart-full tall">
      <h2>📅 Weekly Install Trend – Organic vs Non-Organic</h2>
      <div class="canvas-wrap"><canvas id="chartWeekly"></canvas></div>
    </div>
  </div>

  <div class="charts-grid">
    <div class="card chart-full tall">
      <h2>📈 Daily Organic % Trend</h2>
      <div class="canvas-wrap"><canvas id="chartDailyPct"></canvas></div>
    </div>
  </div>

  <div class="card" style="margin-bottom:20px">
    <h2>📋 Monthly Summary Table</h2>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Month</th><th>Organic</th><th>Non-Organic</th><th>Total</th>
          <th>Organic %</th><th>Non-Organic %</th>
        </tr></thead>
        <tbody>
"""
for i, m in enumerate(months):
    o, n, t = m_org_vals[i], m_non_vals[i], m_tot_vals[i]
    op, np_ = m_org_pct[i], m_non_pct[i]
    html += f"""          <tr>
            <td><b>{m}</b></td>
            <td>{o:,}</td><td>{n:,}</td><td><b>{t:,}</b></td>
            <td>
              <div class="bar-cell">
                <div class="bar-bg"><div class="bar-fill" style="width:{op}%"></div></div>
                <span>{op}%</span>
              </div>
            </td>
            <td>
              <div class="bar-cell">
                <div class="bar-bg"><div class="bar-fill orange" style="width:{np_}%"></div></div>
                <span>{np_}%</span>
              </div>
            </td>
          </tr>
"""
# Grand total row
gt_op = round(total_org/total_all*100,1) if total_all else 0
gt_np = round(total_non/total_all*100,1) if total_all else 0
html += f"""          <tr style="background:#EBF3FB;font-weight:700">
            <td>Grand Total</td>
            <td>{total_org:,}</td><td>{total_non:,}</td><td>{total_all:,}</td>
            <td>{gt_op}%</td><td>{gt_np}%</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

</div>
<footer>TOSM Install Dashboard &nbsp;·&nbsp; Auto-generated from AppsFlyer CSV &nbsp;·&nbsp; {updated_at}</footer>

<script>
const BLUE   = '#2E75B6';
const ORANGE = '#ED7D31';
const GREEN  = '#70AD47';

const defOpts = (stacked=false) => ({{
  responsive:true, maintainAspectRatio:false,
  plugins:{{ legend:{{ position:'top', labels:{{ font:{{size:11}}, boxWidth:12 }} }} }},
  scales: stacked ? {{
    x:{{ stacked:true, grid:{{display:false}}, ticks:{{font:{{size:10}}}} }},
    y:{{ stacked:true, grid:{{color:'#f0f0f0'}}, ticks:{{font:{{size:10}}}} }}
  }} : {{
    x:{{ grid:{{display:false}}, ticks:{{font:{{size:10}}}} }},
    y:{{ grid:{{color:'#f0f0f0'}}, ticks:{{font:{{size:10}}}} }}
  }}
}});

// 1. Monthly Mix – 100% Stacked
new Chart(document.getElementById('chartMonthMix'), {{
  type:'bar',
  data:{{
    labels:{json.dumps(months)},
    datasets:[
      {{label:'Organic %', data:{json.dumps(m_org_pct)}, backgroundColor:BLUE+'CC'}},
      {{label:'Non-Organic %', data:{json.dumps(m_non_pct)}, backgroundColor:ORANGE+'CC'}}
    ]
  }},
  options:{{ ...defOpts(true),
    scales:{{
      x:{{ stacked:true, grid:{{display:false}}, ticks:{{font:{{size:10}}}} }},
      y:{{ stacked:true, max:100, grid:{{color:'#f0f0f0'}},
           ticks:{{ font:{{size:10}}, callback: v => v+'%' }} }}
    }}
  }}
}});

// 2. Monthly Volume
new Chart(document.getElementById('chartMonthVol'), {{
  type:'bar',
  data:{{
    labels:{json.dumps(months)},
    datasets:[
      {{label:'Organic', data:{json.dumps(m_org_vals)}, backgroundColor:BLUE+'CC'}},
      {{label:'Non-Organic', data:{json.dumps(m_non_vals)}, backgroundColor:ORANGE+'CC'}}
    ]
  }},
  options:defOpts(true)
}});

// 3. Weekly stacked
new Chart(document.getElementById('chartWeekly'), {{
  type:'bar',
  data:{{
    labels:{json.dumps(weeks)},
    datasets:[
      {{label:'Organic', data:{json.dumps(w_org_vals)}, backgroundColor:BLUE+'CC'}},
      {{label:'Non-Organic', data:{json.dumps(w_non_vals)}, backgroundColor:ORANGE+'CC'}}
    ]
  }},
  options:defOpts(true)
}});

// 4. Daily Organic % Line
new Chart(document.getElementById('chartDailyPct'), {{
  type:'line',
  data:{{
    labels:{json.dumps(daily_labels)},
    datasets:[{{
      label:'Organic %',
      data:{json.dumps(daily_org_pct)},
      borderColor:BLUE, backgroundColor:BLUE+'22',
      borderWidth:2, pointRadius:1.5, fill:true, tension:.3
    }}]
  }},
  options:{{
    responsive:true, maintainAspectRatio:false,
    plugins:{{ legend:{{ position:'top', labels:{{ font:{{size:11}}, boxWidth:12 }} }} }},
    scales:{{
      x:{{ grid:{{display:false}}, ticks:{{
        font:{{size:9}}, maxTicksLimit:20, maxRotation:45
      }} }},
      y:{{ max:100, grid:{{color:'#f0f0f0'}},
           ticks:{{ font:{{size:10}}, callback: v => v+'%' }} }}
    }}
  }}
}});
</script>
</body>
</html>"""

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ Dashboard generated: {HTML_PATH}")
print(f"   Total installs : {total_all:,}")
print(f"   Organic        : {total_org:,} ({org_pct_all}%)")
print(f"   Non-Organic    : {total_non:,} ({non_pct_all}%)")
print(f"   Data up to     : {last_day}")
