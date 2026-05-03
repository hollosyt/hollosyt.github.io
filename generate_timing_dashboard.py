#!/usr/bin/env python3
"""
generate_timing_dashboard.py
Spring 2025 vs 2026 timing analysis → timing_dashboard.html
"""

import csv
import json
from datetime import date
from collections import defaultdict
import statistics

DATA_FILE   = "BirdDB.txt"
OUTPUT_FILE = "timing_dashboard.html"
CONF_MIN    = 0.7


# ── load ─────────────────────────────────────────────────────────────────────

def load_data():
    rows = []
    with open(DATA_FILE, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(
            (line.replace("\x00", "") for line in f), delimiter=";"
        )
        for row in reader:
            try:
                conf = float(row["Confidence"])
                if conf < CONF_MIN:
                    continue
                d = date.fromisoformat(row["Date"].strip())
            except (ValueError, KeyError):
                continue
            name = row.get("Com_Name", "").strip()
            if name:
                rows.append({"date": d, "name": name})
    return rows


# ── metrics ───────────────────────────────────────────────────────────────────

def compute_metrics(rows):
    apr = {yr: {date(yr, 4, day) for day in range(1, 31)} for yr in (2025, 2026)}
    det = defaultdict(lambda: {2025: defaultdict(int), 2026: defaultdict(int)})
    for r in rows:
        d, name = r["date"], r["name"]
        for yr in (2025, 2026):
            if d in apr[yr]:
                det[name][yr][d.day] += 1

    out = []
    for name, yd in det.items():
        def tot(yr):   return sum(yd[yr].values())
        def cv(yr):    return [yd[yr].get(day, 0) for day in range(1, 31)]
        def pk(yr):    d = yd[yr]; return max(d, key=d.get) if d else None
        def wm(yr):
            d = yd[yr]; t = sum(d.values())
            return sum(k * v for k, v in d.items()) / t if t else None
        def fd(yr):    d = yd[yr]; return min(d) if d else None

        n25, n26 = tot(2025), tot(2026)
        c25, c26 = cv(2025), cv(2026)
        p25, p26 = pk(2025), pk(2026)
        w25, w26 = wm(2025), wm(2026)
        f25, f26 = fd(2025), fd(2026)
        e25, l25 = sum(c25[:15]), sum(c25[15:])
        e26, l26 = sum(c26[:15]), sum(c26[15:])

        out.append({
            "name":          name,
            "n25":           n25,
            "n26":           n26,
            "curve25":       c25,
            "curve26":       c26,
            "peak25":        p25,
            "peak26":        p26,
            "peak_shift":    (p26 - p25) if (p25 and p26) else None,
            "wm25":          round(w25, 1) if w25 else None,
            "wm26":          round(w26, 1) if w26 else None,
            "wm_shift":      round(w26 - w25, 2) if (w25 and w26) else None,
            "first25":       f25,
            "first26":       f26,
            "arrival_shift": (f26 - f25) if (f25 and f26) else None,
            "early_pct25":   round(100 * e25 / (e25 + l25), 1) if (e25 + l25) else None,
            "early_pct26":   round(100 * e26 / (e26 + l26), 1) if (e26 + l26) else None,
        })
    return out


# ── html ──────────────────────────────────────────────────────────────────────

def render_html(peak_chart, curve_sp, arr_sp, only_25, only_26,
                syst, apr25_tot, apr26_tot, n_both):

    pct      = (apr26_tot - apr25_tot) / apr25_tot * 100 if apr25_tot else 0
    pct_sign = "▲" if pct >= 0 else "▼"
    pct_cls  = "up" if pct >= 0 else "dn"
    smean    = syst["mean"]
    smean_s  = f"{smean:+.1f}d"
    smean_c  = "up" if smean < -0.5 else ("dn" if smean > 0.5 else "neu")
    chart_h  = max(700, len(peak_chart) * 34 + 100)

    # ── curve cards (HTML, one per species) ──────────────────────────────────
    curve_cards = ""
    for i, sp in enumerate(curve_sp):
        wm = sp.get("wm_shift")
        if wm is None or abs(wm) < 0.75:
            badge = '<span class="badge b-neu">≈ stable</span>'
        elif wm < 0:
            badge = f'<span class="badge b-earlier">▲ {abs(wm):.1f}d earlier</span>'
        else:
            badge = f'<span class="badge b-later">▼ {wm:.1f}d later</span>'
        curve_cards += f"""
  <div class="cc">
    <div class="cc-name">{sp["name"]}</div>
    <div class="cc-meta">
      <span class="badge b-25">2025: {sp["n25"]:,}</span>
      <span class="badge b-26">2026: {sp["n26"]:,}</span>
      {badge}
    </div>
    <div class="cc-wrap"><canvas id="cc{i}"></canvas></div>
  </div>"""

    # ── arrival table rows ────────────────────────────────────────────────────
    arr_rows = ""
    for r in arr_sp:
        sh = r.get("arrival_shift") or 0
        wms = r.get("wm_shift")
        wm_s = f"{wms:+.1f}d" if wms is not None else "—"
        if sh < 0:
            pill = f'<span class="pill pill-e">{sh:+d}d earlier</span>'
        elif sh > 0:
            pill = f'<span class="pill pill-l">{sh:+d}d later</span>'
        else:
            pill = '<span class="pill pill-n">same</span>'
        arr_rows += (
            f"<tr><td>{r['name']}</td><td>Apr {r.get('first25', '—')}</td>"
            f"<td>Apr {r.get('first26', '—')}</td><td>{pill}</td>"
            f"<td class='mut'>{wm_s}</td>"
            f"<td class='mut'>{r['n25']:,} / {r['n26']:,}</td></tr>"
        )

    # ── presence rows ─────────────────────────────────────────────────────────
    def pres(items, key):
        return "".join(
            f'<div class="pr"><span>{r["name"]}</span>'
            f'<span class="pr-n">{r[key]:,}</span></div>'
            for r in items
        )

    # ── JSON payloads (strip curve arrays from peak data) ────────────────────
    peak_json = json.dumps(
        [{k: v for k, v in r.items() if k not in ("curve25", "curve26", "early_pct25", "early_pct26")}
         for r in peak_chart],
        separators=(",", ":")
    )
    curve_json = json.dumps(
        [{"name": r["name"], "n25": r["n25"], "n26": r["n26"],
          "wm_shift": r.get("wm_shift"),
          "curve25": r["curve25"], "curve26": r["curve26"]}
         for r in curve_sp],
        separators=(",", ":")
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Spring Timing · Apr 2025 vs 2026</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
:root{{
  --bg:#0d1117;--card:#161b22;--card2:#1c2128;
  --text:#e6edf3;--mut:#8b949e;--bdr:#30363d;--r:12px;
  --c25:#58a6ff;--c26:#3fb950;--later:#f0883e;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,'Segoe UI',system-ui,sans-serif;
     background:var(--bg);color:var(--text);line-height:1.6}}
a{{color:inherit;text-decoration:none}}

/* nav */
.nav{{position:sticky;top:0;z-index:100;background:#010409;
     display:flex;align-items:center;gap:2px;padding:0 16px;
     overflow-x:auto;white-space:nowrap;scrollbar-width:none;
     box-shadow:0 1px 0 var(--bdr)}}
.nav::-webkit-scrollbar{{display:none}}
.nav-brand{{color:var(--text);font-weight:700;font-size:.9rem;
           padding:0 12px 0 0;border-right:1px solid var(--bdr);
           margin-right:6px;flex-shrink:0;height:48px;
           display:flex;align-items:center}}
.nl{{color:var(--mut);font-size:.8rem;padding:0 9px;
     border-bottom:3px solid transparent;
     transition:color .2s,border-color .2s;
     flex-shrink:0;height:48px;display:flex;align-items:center}}
.nl:hover{{color:var(--text);border-bottom-color:var(--c25)}}

/* hero */
.hero{{background:linear-gradient(135deg,#0d1117 0%,#0d1f33 50%,#0f3460 100%);
      padding:52px 20px 44px;text-align:center;border-bottom:1px solid var(--bdr)}}
.hero h1{{font-size:clamp(1.6rem,5vw,2.8rem);font-weight:800;letter-spacing:-1px;margin-bottom:6px}}
.hero .sub{{font-size:clamp(.85rem,3vw,1.05rem);color:#7da7d4;margin-bottom:28px}}
.stats{{display:flex;flex-wrap:wrap;justify-content:center;gap:10px}}
.stat{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
      border-radius:12px;padding:12px 22px;min-width:100px;
      backdrop-filter:blur(8px);text-align:center}}
.stat .v{{font-size:clamp(1.2rem,4vw,1.9rem);font-weight:800;display:block}}
.stat .l{{font-size:.7rem;text-transform:uppercase;letter-spacing:1px;color:var(--mut)}}
.c25 .v{{color:var(--c25)}} .c26 .v{{color:var(--c26)}}
.up .v{{color:#3fb950}}    .dn .v{{color:#f85149}}
.neu .v{{color:var(--mut)}}

/* layout */
.main{{max-width:1200px;margin:0 auto;padding:32px 16px 64px}}
.sec{{margin-bottom:56px}}
.sec-hd{{margin-bottom:18px}}
.sec-title{{font-size:clamp(1.1rem,3vw,1.5rem);font-weight:800;margin-bottom:4px}}
.sec-sub{{font-size:.85rem;color:var(--mut)}}
.card{{background:var(--card);border:1px solid var(--bdr);border-radius:var(--r);padding:20px}}

/* legend */
.legend{{display:flex;gap:16px;align-items:center;margin-bottom:12px}}
.ld{{display:flex;align-items:center;gap:5px;font-size:.8rem;color:var(--mut)}}
.dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}

/* peak chart */
.peak-wrap{{background:var(--card);border:1px solid var(--bdr);
           border-radius:var(--r);padding:22px 20px}}
.peak-inner{{position:relative;height:{chart_h}px}}

/* curve grid */
.cg{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
@media(max-width:900px){{.cg{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:560px){{.cg{{grid-template-columns:1fr}}}}
.cc{{background:var(--card);border:1px solid var(--bdr);
    border-radius:var(--r);padding:14px 16px}}
.cc-name{{font-weight:700;font-size:.92rem;margin-bottom:6px}}
.cc-meta{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px;align-items:center}}
.cc-wrap{{position:relative;height:120px}}

/* badges */
.badge{{display:inline-flex;align-items:center;padding:2px 8px;
       border-radius:20px;font-size:.7rem;font-weight:600;white-space:nowrap}}
.b-25{{background:rgba(88,166,255,.15);color:var(--c25);border:1px solid rgba(88,166,255,.3)}}
.b-26{{background:rgba(63,185,80,.15);color:var(--c26);border:1px solid rgba(63,185,80,.3)}}
.b-later{{background:rgba(240,136,62,.15);color:var(--later);border:1px solid rgba(240,136,62,.3)}}
.b-earlier{{background:rgba(63,185,80,.15);color:#3fb950;border:1px solid rgba(63,185,80,.3)}}
.b-neu{{background:rgba(139,148,158,.12);color:var(--mut);border:1px solid rgba(139,148,158,.25)}}

/* arrival table */
.arr-t{{width:100%;border-collapse:collapse;font-size:.88rem}}
.arr-t th{{padding:8px 12px;text-align:left;color:var(--mut);font-weight:500;
          font-size:.72rem;text-transform:uppercase;letter-spacing:.5px;
          border-bottom:1px solid var(--bdr)}}
.arr-t td{{padding:8px 12px;border-bottom:1px solid rgba(48,54,61,.5)}}
.arr-t tr:last-child td{{border-bottom:none}}
.arr-t tr:hover td{{background:rgba(255,255,255,.025)}}
.mut{{color:var(--mut)}}
.pill{{display:inline-block;padding:1px 9px;border-radius:12px;font-size:.77rem;font-weight:700}}
.pill-e{{background:rgba(63,185,80,.15);color:#3fb950}}
.pill-l{{background:rgba(240,136,62,.15);color:var(--later)}}
.pill-n{{background:rgba(139,148,158,.12);color:var(--mut)}}

/* presence */
.pres-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
@media(max-width:600px){{.pres-grid{{grid-template-columns:1fr}}}}
.pc-title{{font-weight:700;font-size:.92rem;padding-bottom:10px;
          margin-bottom:12px;border-bottom:1px solid var(--bdr);
          display:flex;align-items:center;gap:6px}}
.pc-count{{margin-left:auto;font-weight:400;font-size:.78rem;color:var(--mut)}}
.pr{{display:flex;justify-content:space-between;align-items:center;
    padding:5px 0;border-bottom:1px solid rgba(48,54,61,.35);font-size:.87rem}}
.pr:last-child{{border-bottom:none}}
.pr-n{{font-size:.78rem;color:var(--mut);font-weight:500}}

/* note */
.note{{font-size:.78rem;color:var(--mut);margin-top:14px;padding:10px 14px;
      background:rgba(255,255,255,.03);border-radius:8px;
      border-left:3px solid var(--bdr)}}

/* syst box */
.syst{{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}}
.syst-pill{{background:var(--card2);border:1px solid var(--bdr);
           border-radius:8px;padding:10px 16px;font-size:.85rem}}
.syst-pill b{{color:var(--text)}}
</style>
</head>
<body>

<nav class="nav">
  <div class="nav-brand">🐦 Spring Timing</div>
  <a class="nl" href="#timing">Peak Shifts</a>
  <a class="nl" href="#curves">Daily Curves</a>
  <a class="nl" href="#arrivals">Arrivals</a>
  <a class="nl" href="#presence">Presence</a>
</nav>

<header class="hero">
  <h1>Spring Migration Timing</h1>
  <p class="sub">April 2025 vs April 2026 · Sorg Neighborhood Bird Sensor</p>
  <div class="stats">
    <div class="stat c25">
      <span class="v">{apr25_tot:,}</span>
      <span class="l">Apr 2025 detections</span>
    </div>
    <div class="stat c26">
      <span class="v">{apr26_tot:,}</span>
      <span class="l">Apr 2026 detections</span>
    </div>
    <div class="stat {pct_cls}">
      <span class="v">{pct_sign} {abs(pct):.0f}%</span>
      <span class="l">Year over year</span>
    </div>
    <div class="stat">
      <span class="v" style="color:var(--text)">{n_both}</span>
      <span class="l">Species analyzed</span>
    </div>
    <div class="stat {smean_c}">
      <span class="v">{smean_s}</span>
      <span class="l">Mean timing shift</span>
    </div>
  </div>
</header>

<main class="main">

<!-- ═══ SECTION 1: PEAK TIMING SHIFTS ══════════════════════════════════════ -->
<section class="sec" id="timing">
  <div class="sec-hd">
    <div class="sec-title">Peak Activity Timing Shifts</div>
    <div class="sec-sub">Peak detection day within April for {n_both} species with ≥50 detections each year.
      <span style="color:#3fb950">Green = peaked earlier in 2026</span> ·
      <span style="color:var(--later)">Orange = peaked later in 2026</span>.</div>
  </div>
  <div class="peak-wrap">
    <div class="legend">
      <div class="ld"><div class="dot" style="background:#3fb950"></div>Earlier in 2026</div>
      <div class="ld"><div class="dot" style="background:var(--later)"></div>Later in 2026</div>
    </div>
    <div class="peak-inner"><canvas id="peak-chart"></canvas></div>
  </div>
  <div class="syst">
    <div class="syst-pill">Mean shift <b>{smean:+.2f}d</b></div>
    <div class="syst-pill">Median <b>{syst["median"]:+.2f}d</b></div>
    <div class="syst-pill">Std dev <b>{syst["stdev"]:.2f}d</b></div>
    <div class="syst-pill"><b style="color:#3fb950">{syst["earlier"]}</b> species earlier</div>
    <div class="syst-pill"><b style="color:var(--later)">{syst["later"]}</b> species later</div>
    <div class="syst-pill"><b>{syst["stable"]}</b> stable (±1d)</div>
  </div>
  <p class="note">Peak day = single day with the highest detection count within April.
    Hover bars for details. The weighted mean shift (shown on curve cards) is more robust.
    Sorted earliest → latest peak shift in 2026.</p>
</section>

<!-- ═══ SECTION 2: DAILY CURVES ════════════════════════════════════════════ -->
<section class="sec" id="curves">
  <div class="sec-hd">
    <div class="sec-title">Daily Detection Curves</div>
    <div class="sec-sub">Day-by-day April detections for the {len(curve_sp)} most-recorded species.
      Badge shows weighted mean day shift — the center-of-mass timing change.</div>
  </div>
  <div class="legend">
    <div class="ld"><div class="dot" style="background:var(--c25)"></div>2025</div>
    <div class="ld"><div class="dot" style="background:var(--c26)"></div>2026</div>
  </div>
  <div class="cg">
    {curve_cards}
  </div>
</section>

<!-- ═══ SECTION 3: FIRST ARRIVAL DATES ════════════════════════════════════ -->
<section class="sec" id="arrivals">
  <div class="sec-hd">
    <div class="sec-title">First April Detection Dates</div>
    <div class="sec-sub">Species where the first April detection shifted by ≥3 days.
      March 2026 sensor outage (Mar 12–22) makes pre-April 2026 arrivals unreliable.</div>
  </div>
  <div class="card">
    <table class="arr-t">
      <thead>
        <tr>
          <th>Species</th><th>First · Apr 2025</th><th>First · Apr 2026</th>
          <th>Arrival shift</th><th>Wtd mean shift</th><th>Det. 25 / 26</th>
        </tr>
      </thead>
      <tbody>{arr_rows}</tbody>
    </table>
  </div>
  <p class="note">All comparisons restricted to April 1–30. A positive shift means first detection
    was later in 2026; negative means earlier. Species with fewer than 10 April detections excluded.</p>
</section>

<!-- ═══ SECTION 4: PRESENCE CHANGES ═══════════════════════════════════════ -->
<section class="sec" id="presence">
  <div class="sec-hd">
    <div class="sec-title">Species Presence Changes</div>
    <div class="sec-sub">Species with ≥10 detections in one April but fewer than 10 in the other.</div>
  </div>
  <div class="pres-grid">
    <div class="card">
      <div class="pc-title">
        <span style="color:var(--c25)">●</span> Only in April 2025
        <span class="pc-count">{len(only_25)} species</span>
      </div>
      {pres(only_25, "n25")}
    </div>
    <div class="card">
      <div class="pc-title">
        <span style="color:var(--c26)">●</span> Only in April 2026
        <span class="pc-count">{len(only_26)} species</span>
      </div>
      {pres(only_26, "n26")}
    </div>
  </div>
</section>

</main>

<footer style="text-align:center;padding:24px 16px;font-size:.77rem;color:var(--mut);
               border-top:1px solid var(--bdr)">
  Sorg Neighborhood Bird Sensor · Spring Timing Analysis · April 2025 vs April 2026<br>
  March 2026 sensor outage (Mar 12–22) noted — April comparisons only.
</footer>

<script>
const PEAK_DATA = {peak_json};
const CURVE_SP  = {curve_json};

Chart.defaults.color = '#8b949e';
Chart.defaults.borderColor = '#30363d';
Chart.defaults.font.family = "-apple-system,'Segoe UI',system-ui,sans-serif";

// ── peak shift chart ─────────────────────────────────────────────────────────
(function () {{
  const ctx = document.getElementById('peak-chart').getContext('2d');
  const bg  = PEAK_DATA.map(d => d.peak_shift < 0
    ? 'rgba(63,185,80,0.82)' : 'rgba(240,136,62,0.82)');
  const hov = PEAK_DATA.map(d => d.peak_shift < 0
    ? 'rgba(63,185,80,1)' : 'rgba(240,136,62,1)');

  new Chart(ctx, {{
    type: 'bar',
    data: {{
      labels: PEAK_DATA.map(d => d.name),
      datasets: [{{ data: PEAK_DATA.map(d => d.peak_shift),
        backgroundColor: bg, hoverBackgroundColor: hov,
        borderRadius: 4, borderSkipped: false }}]
    }},
    options: {{
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            title: c => c[0].label,
            label: c => {{
              const d = PEAK_DATA[c.dataIndex];
              const dir = d.peak_shift < 0 ? 'earlier' : 'later';
              const wm  = d.wm_shift != null
                ? ` | wt-mean ${{d.wm_shift > 0 ? '+' : ''}}${{d.wm_shift.toFixed(1)}}d`
                : '';
              return [
                `Peak: Apr ${{d.peak25}} → Apr ${{d.peak26}} (${{Math.abs(d.peak_shift)}} days ${{dir}} in 2026)${{wm}}`,
                `Detections: ${{d.n25.toLocaleString()}} (2025) / ${{d.n26.toLocaleString()}} (2026)`
              ];
            }}
          }}
        }}
      }},
      scales: {{
        x: {{
          grid: {{ color: '#30363d' }},
          ticks: {{ color: '#8b949e', font: {{ size: 11 }} }},
          title: {{ display: true,
            text: '← days earlier in 2026   |   days later in 2026 →',
            color: '#8b949e', font: {{ size: 11 }} }}
        }},
        y: {{
          grid: {{ display: false }},
          ticks: {{ color: '#e6edf3', font: {{ size: 12 }} }}
        }}
      }}
    }}
  }});
}})();

// ── daily curve charts ───────────────────────────────────────────────────────
const APR = Array.from({{length: 30}}, (_, i) => i + 1);

CURVE_SP.forEach((sp, i) => {{
  const el = document.getElementById('cc' + i);
  if (!el) return;
  new Chart(el.getContext('2d'), {{
    type: 'line',
    data: {{
      labels: APR,
      datasets: [
        {{ label: '2025', data: sp.curve25,
           borderColor: '#58a6ff', backgroundColor: 'rgba(88,166,255,0.1)',
           fill: true, tension: 0.4, pointRadius: 0, borderWidth: 1.6 }},
        {{ label: '2026', data: sp.curve26,
           borderColor: '#3fb950', backgroundColor: 'rgba(63,185,80,0.1)',
           fill: true, tension: 0.4, pointRadius: 0, borderWidth: 1.6 }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{
          display: true, position: 'top', align: 'end',
          labels: {{ boxWidth: 8, boxHeight: 8, padding: 6, font: {{ size: 9 }} }}
        }},
        tooltip: {{
          mode: 'index', intersect: false,
          callbacks: {{ title: c => 'Apr ' + c[0].label }}
        }}
      }},
      scales: {{
        x: {{
          grid: {{ color: 'rgba(48,54,61,.5)' }},
          ticks: {{
            color: '#8b949e', font: {{ size: 9 }}, maxTicksLimit: 5,
            callback: (_, i) => 'Apr ' + (i + 1)
          }}
        }},
        y: {{
          grid: {{ color: 'rgba(48,54,61,.5)' }},
          ticks: {{ color: '#8b949e', font: {{ size: 9 }}, maxTicksLimit: 4 }},
          beginAtZero: true
        }}
      }}
    }}
  }});
}});
</script>
</body>
</html>"""


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("Loading data …", flush=True)
    rows = load_data()
    print(f"  {len(rows):,} April records loaded", flush=True)

    print("Computing metrics …", flush=True)
    sp_data = compute_metrics(rows)

    both50  = [r for r in sp_data if r["n25"] >= 50 and r["n26"] >= 50]
    only_25 = sorted([r for r in sp_data if r["n25"] >= 10 and r["n26"] < 10],
                     key=lambda r: -r["n25"])[:12]
    only_26 = sorted([r for r in sp_data if r["n26"] >= 10 and r["n25"] < 10],
                     key=lambda r: -r["n26"])[:12]

    shifts = [r["wm_shift"] for r in both50 if r["wm_shift"] is not None]
    syst = {
        "n":      len(shifts),
        "mean":   round(statistics.mean(shifts),   2) if shifts else 0,
        "median": round(statistics.median(shifts), 2) if shifts else 0,
        "stdev":  round(statistics.stdev(shifts),  2) if len(shifts) > 1 else 0,
        "later":  sum(1 for s in shifts if s >  1),
        "earlier":sum(1 for s in shifts if s < -1),
        "stable": sum(1 for s in shifts if -1 <= s <= 1),
    }

    peak_chart = sorted(
        [r for r in both50 if r["peak_shift"] is not None],
        key=lambda r: r["peak_shift"]
    )
    curve_sp = sorted(both50, key=lambda r: -(r["n25"] + r["n26"]))[:15]
    arr_sp   = sorted(
        [r for r in both50 if r["arrival_shift"] is not None and abs(r["arrival_shift"]) >= 3],
        key=lambda r: r["arrival_shift"]
    )

    apr25_tot = sum(r["n25"] for r in sp_data)
    apr26_tot = sum(r["n26"] for r in sp_data)

    print("Building HTML …", flush=True)
    html = render_html(
        peak_chart, curve_sp, arr_sp, only_25, only_26,
        syst, apr25_tot, apr26_tot, len(both50)
    )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    pct = (apr26_tot - apr25_tot) / apr25_tot * 100 if apr25_tot else 0
    print(f"Written {OUTPUT_FILE}  ({len(html) // 1024} KB)")
    print(f"  Apr 2025: {apr25_tot:,}  →  Apr 2026: {apr26_tot:,}  ({pct:+.0f}%)")
    print(f"  {len(both50)} species · systematic shift {syst['mean']:+.2f}d · "
          f"{syst['earlier']} earlier / {syst['later']} later / {syst['stable']} stable")


if __name__ == "__main__":
    main()
