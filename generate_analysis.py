#!/usr/bin/env python3
"""
generate_analysis.py — Bird Detection HTML Generator

Usage:
    python3 generate_analysis.py

Requires:
    pip install pyyaml

Reads:
    BirdDB.txt      — semicolon-delimited acoustic detection data
    narrative.yaml  — all prose, category config, colours

Writes:
    bird_analysis.html  — mobile-responsive single-page dashboard
    wiki_cache.json     — cached Wikipedia photo URLs (auto-managed)
"""

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime

# ── File paths ────────────────────────────────────────────────────────────────
DATA_FILE   = "BirdDB.txt"
NARRATIVE   = "narrative.yaml"
CACHE_FILE  = "wiki_cache.json"
OUTPUT_FILE = "bird_analysis.html"

# Report month (change to regenerate for a different month)
DIGEST_YEAR  = 2026
DIGEST_MONTH = 3

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
YEARS  = [2025, 2026]

# Palette for the digest daily-activity chart (one colour per top-5 species)
DIGEST_COLORS = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]

# ── Species classification ────────────────────────────────────────────────────
# Order matters: first match wins.

INTRODUCED_EXACT = {
    "European Starling", "House Sparrow", "Rock Pigeon",
    "Eurasian Collared-Dove", "Common Myna", "Monk Parakeet",
}
OWL_WORDS       = ["Owl"]
RAPTOR_WORDS    = ["Hawk", "Eagle", "Falcon", "Kestrel", "Merlin",
                   "Harrier", "Kite", "Osprey", "Vulture"]
WP_WORDS        = ["Woodpecker", "Flicker", "Sapsucker"]
HUMMER_WORDS    = ["Hummingbird"]
CORVID_WORDS    = ["Crow", "Raven"]          # Blue Jay → songbirds
DUCK_WORDS      = ["Duck", "Teal", "Mallard", "Pintail", "Wigeon",
                   "Shoveler", "Scaup", "Goldeneye", "Bufflehead",
                   "Canvasback", "Redhead", "Merganser", "Scoter", "Eider"]
GOOSE_WORDS     = ["Goose", "Swan", "Brant"]
SHORE_WORDS     = ["Heron", "Egret", "Bittern", "Crane", "Loon", "Grebe",
                   "Coot", "Rail", "Gallinule", "Moorhen", "Killdeer",
                   "Plover", "Sandpiper", "Dowitcher", "Snipe", "Woodcock",
                   "Yellowlegs", "Dunlin", "Phalarope", "Turnstone",
                   "Tern", "Gull", "Skimmer", "Avocet", "Stilt",
                   "Cormorant", "Pelican", "Ibis", "Spoonbill",
                   "Curlew", "Whimbrel", "Godwit", "Willet", "Knot"]


def classify(name: str) -> str:
    if name in INTRODUCED_EXACT:           return "introduced"
    if any(w in name for w in OWL_WORDS):  return "owls"
    if any(w in name for w in RAPTOR_WORDS): return "birds_of_prey"
    if any(w in name for w in WP_WORDS):   return "woodpeckers"
    if any(w in name for w in HUMMER_WORDS): return "hummingbirds"
    if any(w in name for w in CORVID_WORDS): return "corvids"
    if any(w in name for w in DUCK_WORDS): return "ducks"
    if any(w in name for w in GOOSE_WORDS): return "waterfowl"
    if any(w in name for w in SHORE_WORDS): return "shorebirds"
    return "songbirds"


# ── Load narrative config ─────────────────────────────────────────────────────

def load_narrative():
    try:
        import yaml
    except ImportError:
        print("ERROR: PyYAML not installed.  Run: pip install pyyaml")
        sys.exit(1)
    if not os.path.exists(NARRATIVE):
        print(f"ERROR: {NARRATIVE} not found")
        sys.exit(1)
    with open(NARRATIVE, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Parse BirdDB ──────────────────────────────────────────────────────────────

def parse_data():
    records = []
    print(f"Parsing {DATA_FILE} …", end=" ", flush=True)
    with open(DATA_FILE, newline="", encoding="utf-8", errors="replace") as f:
        # Strip NUL bytes that can appear in BirdNET output files
        reader = csv.DictReader(
            (line.replace("\x00", "") for line in f), delimiter=";"
        )
        for row in reader:
            try:
                dt   = datetime.strptime(row["Date"].strip(), "%Y-%m-%d")
                conf = float(row["Confidence"].strip())
                name = row["Com_Name"].strip()
                if not name:
                    continue
                records.append({
                    "name":  name,
                    "sci":   row.get("Sci_Name", "").strip(),
                    "date":  dt.date(),
                    "year":  dt.year,
                    "month": dt.month,
                    "conf":  conf,
                    "cat":   classify(name),
                })
            except (ValueError, KeyError):
                continue
    print(f"{len(records):,} records loaded.")
    return records


# ── Wikipedia photo cache ─────────────────────────────────────────────────────

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def fetch_wiki(name: str, cache: dict) -> dict:
    """Return {thumb, full} URLs for a species; empty strings if not found."""
    if name in cache:
        return cache[name]
    key = urllib.parse.quote(name.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{key}"
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "BirdAnalysisGenerator/1.0 (academic)"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read())
        thumb = data.get("thumbnail", {}).get("source", "")
        orig  = data.get("originalimage", {}).get("source", "") or thumb
        cache[name] = {"thumb": thumb, "full": orig}
        time.sleep(0.08)
    except Exception:
        cache[name] = {"thumb": "", "full": ""}
    return cache[name]


def fetch_all_photos(records, top_n=15):
    """Fetch Wikipedia photos for the top_n species in each category plus top-20 overall."""
    cache = load_cache()
    by_cat = defaultdict(Counter)
    overall = Counter()
    for r in records:
        by_cat[r["cat"]][r["name"]] += 1
        overall[r["name"]] += 1

    names = set()
    for cnt in by_cat.values():
        names.update(n for n, _ in cnt.most_common(top_n))
    names.update(n for n, _ in overall.most_common(20))

    new_names = [n for n in names if n not in cache]
    if new_names:
        print(f"Fetching {len(new_names)} Wikipedia photos …", end=" ", flush=True)
        for n in new_names:
            fetch_wiki(n, cache)
        save_cache(cache)
        print("done.")
    else:
        print("Wikipedia photo cache up to date.")

    return cache


# ── Compute statistics ────────────────────────────────────────────────────────

def compute_stats(records):
    all_species   = Counter(r["name"] for r in records)
    monthly_overall = [0] * 12
    for r in records:
        monthly_overall[r["month"] - 1] += 1

    cats = defaultdict(list)
    for r in records:
        cats[r["cat"]].append(r)

    cat_stats = {}
    for key, recs in cats.items():
        sp_counts   = Counter(r["name"] for r in recs)
        monthly_yy  = defaultdict(lambda: [0] * 12)
        monthly_div = defaultdict(set)
        conf_sum    = 0.0
        for r in recs:
            m = r["month"] - 1
            monthly_yy[r["year"]][m] += 1
            monthly_div[m].add(r["name"])
            conf_sum += r["conf"]

        monthly_combined = [
            sum(monthly_yy[y][m] for y in YEARS) for m in range(12)
        ]
        diversity = [len(monthly_div[m]) for m in range(12)]

        cat_stats[key] = {
            "total":         len(recs),
            "species_count": len(sp_counts),
            "avg_conf":      conf_sum / len(recs) if recs else 0.0,
            "top_species":   sp_counts.most_common(),
            "monthly":       monthly_combined,
            "diversity":     diversity,
            "heatmap":       {y: monthly_yy[y] for y in YEARS},
            "yr_2025":       sum(monthly_yy[2025]),
            "yr_2026":       sum(monthly_yy[2026]),
        }

    return {
        "total":          len(records),
        "all_species":    all_species,
        "top20":          all_species.most_common(20),
        "monthly_overall": monthly_overall,
        "cat_stats":      cat_stats,
    }


# ── Monthly digest ────────────────────────────────────────────────────────────

def sparkline_svg(data, color, width=80, height=24):
    """Inline SVG mini bar-chart for a species daily activity."""
    if not data or max(data) == 0:
        return f'<svg width="{width}" height="{height}"></svg>'
    max_v = max(data)
    n     = len(data)
    bw    = width / n
    bars  = ""
    for i, v in enumerate(data):
        h = max(1, round(v / max_v * height)) if v else 0
        if h:
            bars += (
                f'<rect x="{i * bw:.1f}" y="{height - h}" '
                f'width="{max(bw - 0.8, 0.5):.1f}" height="{h}" '
                f'fill="{color}" rx="1" opacity=".85"/>'
            )
    return (
        f'<svg width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" '
        f'style="vertical-align:middle;flex-shrink:0">{bars}</svg>'
    )


def _auto_narrative(digest, cat_cfg):
    """Generate a natural-language summary from digest data."""
    total  = digest["total"]
    prev   = digest["prev_total"]
    pct    = digest["pct_change"]
    mn     = digest["month_name"]
    yr     = digest["year"]
    days   = digest["days"]
    top5   = digest["top5"]
    arrivals = digest["new_arrivals"]
    rare     = digest.get("rare_species", [])
    cat_counts = digest.get("cat_counts", {})

    parts = []

    # Trend sentence
    if prev:
        dir_word = "behind" if pct < 0 else "ahead of"
        parts.append(
            f"{mn} {yr} is running {abs(pct):.0f}% {dir_word} the same period "
            f"last year, with {total:,} detections logged in the first "
            f"{max(days) if days else '?'} days."
        )
    else:
        parts.append(
            f"{mn} {yr} has logged {total:,} detections across "
            f"{max(days) if days else '?'} days."
        )

    # Dominant category pair
    if cat_counts and cat_cfg:
        sorted_cats = sorted(cat_counts.items(), key=lambda x: -x[1])
        top_key, top_n = sorted_cats[0]
        top_name = cat_cfg.get(top_key, {}).get("name", top_key)
        top_pct  = top_n / total * 100 if total else 0
        if len(sorted_cats) >= 2:
            sec_key, sec_n = sorted_cats[1]
            sec_name = cat_cfg.get(sec_key, {}).get("name", sec_key)
            parts.append(
                f"{top_name} lead with {top_n:,} detections ({top_pct:.0f}%), "
                f"followed by {sec_name} at {sec_n:,}."
            )
        else:
            parts.append(
                f"{top_name} account for {top_n:,} detections "
                f"({top_pct:.0f}% of the month)."
            )

    # Top species
    if top5:
        sp_name, sp_cnt = top5[0]
        parts.append(
            f"{sp_name} leads all individual species with {sp_cnt:,} detections."
        )

    # Arrivals
    if arrivals:
        n = len(arrivals)
        listed = ", ".join(arrivals[:2])
        suffix = f" and {n - 2} others" if n > 2 else ""
        parts.append(
            f"First-of-year arrivals include {listed}{suffix}."
        )

    # Notable rare
    if rare:
        parts.append(
            f"Notably, {rare[0]['name']} was recorded — "
            f"a rare sighting for this sensor location."
        )

    return " ".join(parts)


def compute_digest(records, year, month, cat_cfg=None):
    cur  = [r for r in records if r["year"] == year and r["month"] == month]
    prev = [r for r in records if r["year"] == year - 1 and r["month"] == month]

    all_counts = Counter(r["name"] for r in records)
    cur_total  = len(cur)
    prev_total = len(prev)
    pct_change = (
        (cur_total - prev_total) / prev_total * 100 if prev_total else 0.0
    )

    month_counts = Counter(r["name"] for r in cur)
    top5 = month_counts.most_common(5)

    seen_before = {
        r["name"] for r in records if r["year"] == year and r["month"] < month
    }
    new_arrivals = [
        n for n, _ in month_counts.most_common()
        if n not in seen_before
    ][:8]

    max_day = max((r["date"].day for r in cur), default=0)
    days    = list(range(1, max_day + 1))

    # ── Category counts & daily-by-category for stacked chart ────────────────
    cat_counts = Counter(r["cat"] for r in cur)

    daily_by_cat = []
    for key in CAT_ORDER:
        n_month = cat_counts.get(key, 0)
        if n_month == 0:
            continue
        cfg   = (cat_cfg or {}).get(key, {})
        color = cfg.get("color", "#8b949e")
        name  = cfg.get("name", key)
        day_c = Counter(r["date"].day for r in cur if r["cat"] == key)
        daily_by_cat.append({
            "key":   key,
            "name":  name,
            "color": color,
            "total": n_month,
            "data":  [day_c.get(d, 0) for d in days],
        })

    # ── Per-species daily breakdown, grouped by category ─────────────────────
    by_cat_species = []
    for key in CAT_ORDER:
        cfg_cat  = (cat_cfg or {}).get(key, {})
        color    = cfg_cat.get("color", "#8b949e")
        sp_pairs = [
            (name, cnt) for name, cnt in month_counts.most_common()
            if classify(name) == key
        ]
        if not sp_pairs:
            continue
        sp_list = []
        for name, cnt in sp_pairs:
            day_c    = Counter(r["date"].day for r in cur if r["name"] == name)
            peak_day = max(day_c, key=day_c.get) if day_c else None
            sp_list.append({
                "name":     name,
                "total":    cnt,
                "data":     [day_c.get(d, 0) for d in days],
                "peak_day": peak_day,
                "peak_val": day_c.get(peak_day, 0) if peak_day else 0,
            })
        by_cat_species.append({
            "key":     key,
            "name":    cfg_cat.get("name", key),
            "icon":    cfg_cat.get("icon", "🐦"),
            "color":   color,
            "total":   sum(c for _, c in sp_pairs),
            "species": sp_list,
        })

    # ── Rare species ─────────────────────────────────────────────────────────
    prev_same_month_species = {r["name"] for r in prev}
    rare = []
    for name, count_month in month_counts.most_common():
        total = all_counts[name]
        if total <= 30:
            reason = (
                "1st ever detection" if total == 1
                else f"only {total} all-time detections"
            )
        elif total <= 75 and name not in prev_same_month_species:
            reason = (
                f"not recorded in {MONTHS[month-1]} {year-1} "
                f"\u00b7 {total} all-time"
            )
        else:
            continue
        rare.append({
            "name":        name,
            "count_month": count_month,
            "total":       total,
            "reason":      reason,
        })
    rare.sort(key=lambda x: x["total"])
    rare = rare[:8]

    digest = {
        "year":           year,
        "month":          month,
        "month_name":     MONTHS[month - 1],
        "total":          cur_total,
        "prev_total":     prev_total,
        "pct_change":     pct_change,
        "top5":           top5,
        "new_arrivals":   new_arrivals,
        "days":           days,
        "cat_counts":     dict(cat_counts),
        "daily_by_cat":   daily_by_cat,
        "by_cat_species": by_cat_species,
        "rare_species":   rare,
    }
    digest["narrative"] = _auto_narrative(digest, cat_cfg)
    return digest


# ── HTML fragment helpers ─────────────────────────────────────────────────────

def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def render_heatmap(heatmap: dict, color: str) -> str:
    all_vals = [v for y in YEARS for v in heatmap.get(y, [0] * 12)]
    max_val  = max(all_vals) if any(all_vals) else 1
    rows = ""
    for yr in YEARS:
        vals  = heatmap.get(yr, [0] * 12)
        cells = ""
        for i, v in enumerate(vals):
            intensity  = 0.05 + (v / max_val * 0.95) if max_val and v else 0.05
            text_color = "#fff" if intensity > 0.6 else "#333"
            bg         = _rgba(color, intensity)
            display    = str(v) if v else ""
            cells += (
                f'<td style="background:{bg};color:{text_color}" '
                f'title="{MONTHS[i]} {yr}: {v}">{display}</td>'
            )
        rows += f"<tr><th>{yr}</th>{cells}</tr>"
    month_headers = "".join(f"<th>{m}</th>" for m in MONTHS)
    return (
        '<div class="heatmap-wrap">'
        '<table class="heatmap">'
        f"<thead><tr><th></th>{month_headers}</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
    )


def render_sp_table(top_species, color: str, photos: dict, group_total: int,
                    max_show: int = 12) -> str:
    if not top_species:
        return "<p>No data.</p>"
    max_c = top_species[0][1]
    rows  = ""
    for i, (name, count) in enumerate(top_species[:max_show], 1):
        pct   = count / group_total * 100 if group_total else 0
        bar_w = int(count / max_c * 100) if max_c else 0
        photo = photos.get(name, {})
        thumb = photo.get("thumb", "")
        full  = photo.get("full", "") or thumb

        if thumb:
            img = (
                f'<img src="{thumb}" data-full="{full}" alt="{name}" '
                f'class="sp-thumb" loading="lazy">'
            )
            thumb_td = f'<td class="sp-thumb-cell">{img}</td>'
        else:
            thumb_td = '<td class="sp-thumb-cell"></td>'

        rows += (
            f"<tr>"
            f'<td class="sp-rank">{i}</td>'
            f"{thumb_td}"
            f'<td class="sp-name">{name}</td>'
            f'<td class="sp-bar-cell"><div class="sp-bar" '
            f'style="width:{bar_w}%;background:{color}"></div></td>'
            f'<td class="sp-count">{count:,}</td>'
            f'<td class="sp-pct">{pct:.1f}%</td>'
            f"</tr>"
        )
    return (
        '<table class="sp-table">'
        "<thead><tr>"
        "<th>#</th><th></th><th>Species</th>"
        '<th class="hide-mobile"></th>'
        "<th>Detections</th><th>% of group</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
    )


def render_category(cat_key: str, cfg: dict, stats: dict, photos: dict) -> str:
    s = stats["cat_stats"].get(cat_key)
    if not s:
        return ""

    color     = cfg["color"]
    narrative = cfg.get("narrative", "").strip()
    section_id = cfg.get("id", cat_key.replace("_", "-"))
    # Compute a subtle colour-tinted gradient that works on the dark background
    hx = color.lstrip("#")
    cr, cg, cb = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
    bg = f"linear-gradient(135deg,rgba({cr},{cg},{cb},0.18) 0%,var(--card) 100%)"

    heatmap_html  = render_heatmap(s["heatmap"], color)
    sp_table_html = render_sp_table(s["top_species"], color, photos,
                                    s["total"])

    chart_m = f"monthly-{cat_key}"
    chart_d = f"diversity-{cat_key}"

    js_monthly  = json.dumps(s["monthly"])
    js_diversity = json.dumps(s["diversity"])

    return f"""
  <section class="cat-section" id="{section_id}">
    <div class="cat-header" style="border-left:6px solid {color};background:{bg}">
      <div class="cat-title-row">
        <span class="cat-icon">{cfg['icon']}</span>
        <h2 class="cat-title" style="color:{color}">{cfg['name']}</h2>
        <div class="cat-meta">
          <span class="meta-pill" style="background:{color}">{s['total']:,} detections</span>
          <span class="meta-pill outline" style="border-color:{color};color:{color}">{s['species_count']} species</span>
          <span class="meta-pill outline" style="border-color:{color};color:{color}">avg conf: {s['avg_conf']:.2f}</span>
        </div>
      </div>
      <div class="yr-badges">
        <span class="yr-badge" style="background:{color}">2025: {s['yr_2025']:,}</span>
        <span class="yr-badge" style="background:{color}">2026: {s['yr_2026']:,}</span>
      </div>
    </div>

    <div class="cat-body">
      <div class="narrative"><p>{narrative}</p></div>

      <div class="charts-grid">
        <div class="chart-card full-width">
          <h3>Detection Heatmap — by Month &amp; Year</h3>
          {heatmap_html}
        </div>
        <div class="chart-card">
          <h3>Monthly Activity (all years combined)</h3>
          <canvas id="{chart_m}" height="200"></canvas>
        </div>
        <div class="chart-card">
          <h3>Species Diversity by Month</h3>
          <canvas id="{chart_d}" height="200"></canvas>
        </div>
      </div>

      <div class="chart-card">
        <h3>Top Species</h3>
        {sp_table_html}
      </div>
    </div>
  </section>
  <script>
  (function(){{
    var md={js_monthly}, dd={js_diversity};
    var mo={json.dumps(MONTHS)}, c='{color}';
    new Chart(document.getElementById('{chart_m}'),{{
      type:'bar',data:{{labels:mo,datasets:[{{label:'Detections',data:md,
        backgroundColor:c+'aa',borderColor:c,borderWidth:1,borderRadius:4}}]}},
      options:{{responsive:true,plugins:{{legend:{{display:false}}}},
        scales:{{y:{{beginAtZero:true,ticks:{{maxTicksLimit:5}}}}}}}}
    }});
    new Chart(document.getElementById('{chart_d}'),{{
      type:'line',data:{{labels:mo,datasets:[{{label:'Species',data:dd,
        borderColor:c,backgroundColor:c+'22',fill:true,tension:0.4,
        pointRadius:4,pointBackgroundColor:c}}]}},
      options:{{responsive:true,plugins:{{legend:{{display:false}}}},
        scales:{{y:{{beginAtZero:true,ticks:{{maxTicksLimit:5}}}}}}}}
    }});
  }})();
  </script>
"""


def render_digest(digest: dict, narrative_cfg: dict, photos: dict) -> str:
    mn    = digest["month_name"]
    yr    = digest["year"]
    total = digest["total"]
    prev  = digest["prev_total"]
    pct   = digest["pct_change"]

    arrow     = "↑" if pct >= 0 else "↓"
    chg_color = "#2ecc71" if pct >= 0 else "#e74c3c"
    vs_label  = f"{arrow} {abs(pct):.0f}% vs {yr - 1}"
    prev_label = f"{prev:,}" if prev else "—"

    # ── Narrative (auto-generated, YAML can override) ─────────────────────────
    narrative_text = digest.get("narrative", "")
    if digest["month"] == DIGEST_MONTH and digest["year"] == DIGEST_YEAR:
        yaml_override = (
            narrative_cfg.get("digest", {})
            .get(f"{MONTHS[DIGEST_MONTH-1].lower()}_{DIGEST_YEAR}", "")
            .strip()
        )
        if yaml_override:
            narrative_text = yaml_override
    narrative_html = (
        f'<p class="digest-narrative">{narrative_text}</p>'
        if narrative_text else ""
    )

    # ── Stacked bar chart — daily activity by category ────────────────────────
    days         = digest["days"]
    daily_by_cat = digest["daily_by_cat"]
    js_labels    = json.dumps([str(d) for d in days])

    datasets = []
    for cat in daily_by_cat:
        datasets.append({
            "label":           cat["name"],
            "data":            cat["data"],
            "backgroundColor": cat["color"] + "cc",
            "borderColor":     cat["color"],
            "borderWidth":     0,
            "stack":           "day",
        })
    js_datasets = json.dumps(datasets)

    legend_items = "".join(
        f'<span class="chart-legend-item">'
        f'<span class="chart-legend-dot" style="background:{c["color"]}"></span>'
        f'{c["name"]}'
        f"</span>"
        for c in daily_by_cat
    )

    chart_block = f"""
    <div class="digest-chart-card">
      <h4>Daily Activity by Group</h4>
      <div class="chart-legend">{legend_items}</div>
      <canvas id="digest-daily-chart" height="160"></canvas>
    </div>
    <script>
    (function(){{
      new Chart(document.getElementById('digest-daily-chart'), {{
        type: 'bar',
        data: {{ labels: {js_labels}, datasets: {js_datasets} }},
        options: {{
          responsive: true,
          interaction: {{ mode: 'index', intersect: false }},
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{
              stacked: true,
              title: {{ display: true, text: 'Day of {mn}', font: {{ size: 11 }} }},
              ticks: {{ maxTicksLimit: 12 }}
            }},
            y: {{ stacked: true, beginAtZero: true, ticks: {{ maxTicksLimit: 5 }} }}
          }}
        }}
      }});
    }})();
    </script>"""

    # ── Species breakdown — collapsible by category ───────────────────────────
    cat_blocks = ""
    for i, cat in enumerate(digest["by_cat_species"]):
        color    = cat["color"]
        sp_rows  = ""
        for sp in cat["species"]:
            name     = sp["name"]
            total_sp = sp["total"]
            peak_day = sp["peak_day"]
            peak_val = sp["peak_val"]
            svg      = sparkline_svg(sp["data"], color)
            peak_txt = f"peak day&nbsp;{peak_day} ({peak_val})" if peak_day else ""
            photo    = photos.get(name, {})
            thumb    = photo.get("thumb", "")
            full     = photo.get("full", "") or thumb
            thumb_html = (
                f'<img src="{thumb}" data-full="{full}" alt="{name}" '
                f'class="sp-thumb sp-thumb-sm" loading="lazy">'
                if thumb else '<div class="sp-thumb-sm-ph"></div>'
            )
            sp_rows += (
                f'<div class="sp-detail-row">'
                f'  {thumb_html}'
                f'  <span class="sp-detail-name">{name}</span>'
                f'  {svg}'
                f'  <span class="sp-detail-right">'
                f'    <span class="sp-detail-count">{total_sp:,}</span>'
                f'    <span class="sp-detail-peak">{peak_txt}</span>'
                f'  </span>'
                f'</div>'
            )
        n_sp   = len(cat["species"])
        # Open the highest-detection category by default
        open_attr = " open" if i == 0 else ""
        cat_blocks += (
            f'<details class="cat-breakdown"{open_attr}>'
            f'  <summary class="cat-breakdown-summary">'
            f'    <span class="cb-icon">{cat["icon"]}</span>'
            f'    <span class="cb-name" style="color:{color}">{cat["name"]}</span>'
            f'    <span class="cb-total" style="background:{color}22;color:{color}">'
            f'      {cat["total"]:,}'
            f'    </span>'
            f'    <span class="cb-species">{n_sp} species</span>'
            f'    <span class="cb-chevron">›</span>'
            f'  </summary>'
            f'  <div class="sp-detail-list">{sp_rows}</div>'
            f'</details>'
        )

    sp_detail_block = (
        '<div class="sp-detail-section">'
        '<h4>Species Breakdown by Group</h4>'
        f'{cat_blocks}'
        "</div>"
    )

    # ── New arrivals chips ────────────────────────────────────────────────────
    arrivals_html = ""
    if digest["new_arrivals"]:
        chips = "".join(
            f'<span class="arrival-chip">{n}</span>'
            for n in digest["new_arrivals"]
        )
        arrivals_html = (
            '<div class="digest-col">'
            "<h4>First of Year</h4>"
            f'<div class="arrivals-list">{chips}</div>'
            "</div>"
        )

    # ── Rare species cards ────────────────────────────────────────────────────
    rare_html = ""
    if digest["rare_species"]:
        cards = ""
        for sp in digest["rare_species"]:
            name   = sp["name"]
            reason = sp["reason"]
            cnt    = sp["count_month"]
            photo  = photos.get(name, {})
            thumb  = photo.get("thumb", "")
            full   = photo.get("full", "") or thumb
            img    = (
                f'<img src="{thumb}" data-full="{full}" alt="{name}" '
                f'class="sp-thumb rare-thumb" loading="lazy">'
                if thumb else '<div class="rare-thumb-placeholder">🐦</div>'
            )
            cards += (
                f'<div class="rare-card">'
                f"  {img}"
                f'  <div class="rare-info">'
                f'    <span class="rare-name">{name}</span>'
                f'    <span class="rare-count">{cnt} detection{"s" if cnt != 1 else ""} this month</span>'
                f'    <span class="rare-badge">{reason}</span>'
                f"  </div>"
                f"</div>"
            )
        rare_html = (
            '<div class="digest-rare">'
            "<h4>🔍 Rare Sightings This Month</h4>"
            f'<div class="rare-grid">{cards}</div>'
            "</div>"
        )

    return f"""
  <div class="digest-card">
    <div class="digest-header">
      <div>
        <h2 class="digest-title">🗓 {mn} {yr} Digest</h2>
        <p class="digest-subtitle">What's active at the sensor right now</p>
      </div>
      <div class="digest-totals">
        <div class="digest-total-block">
          <span class="digest-total-val">{total:,}</span>
          <span class="digest-total-lbl">this month</span>
          <span class="digest-change" style="color:{chg_color}">{vs_label}</span>
        </div>
        <div class="digest-total-block">
          <span class="digest-total-val">{prev_label}</span>
          <span class="digest-total-lbl">{mn} {yr - 1}</span>
        </div>
      </div>
    </div>
    {narrative_html}
    {chart_block}
    {sp_detail_block}
    <div class="digest-grid">
      {arrivals_html}
      {rare_html}
    </div>
  </div>
"""


# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
:root {
  --bg:     #0d1117;
  --card:   #161b22;
  --card2:  #1c2128;
  --text:   #e6edf3;
  --muted:  #8b949e;
  --border: #30363d;
  --radius: 12px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, 'Segoe UI', system-ui, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.6;
}

/* ── NAV ── */
.top-nav {
  position: sticky; top: 0; z-index: 100;
  background: #010409; padding: 0 16px;
  display: flex; align-items: center; gap: 2px;
  overflow-x: auto; white-space: nowrap;
  -webkit-overflow-scrolling: touch; scrollbar-width: none;
  box-shadow: 0 1px 0 var(--border);
}
.top-nav::-webkit-scrollbar { display: none; }
.nav-brand {
  color: #e6edf3; font-weight: 700; font-size: .95rem;
  padding: 0 12px 0 0; border-right: 1px solid var(--border);
  margin-right: 6px; flex-shrink: 0;
  display: flex; align-items: center; height: 48px;
}
.nav-link {
  color: var(--muted); text-decoration: none; font-size: .8rem;
  padding: 0 9px; border-bottom: 3px solid transparent;
  transition: color .2s, border-color .2s; flex-shrink: 0;
  height: 48px; display: flex; align-items: center;
}
.nav-link:hover, .nav-link:active { color: #e6edf3; border-bottom-color: #58a6ff; }

/* ── HERO ── */
.hero {
  background: linear-gradient(135deg,#0d1117 0%,#0d1f33 50%,#0f3460 100%);
  color: #e6edf3; padding: 48px 20px 40px; text-align: center;
  border-bottom: 1px solid var(--border);
}
.hero h1 {
  font-size: clamp(1.5rem, 5vw, 2.6rem);
  font-weight: 800; letter-spacing: -1px; margin-bottom: 8px;
}
.hero .subtitle {
  font-size: clamp(.88rem, 3vw, 1.1rem);
  color: #7da7d4; margin-bottom: 24px;
}
.hero-stats {
  display: flex; flex-wrap: wrap;
  justify-content: center; gap: 12px; margin-top: 20px;
}
.hero-stat {
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 12px; padding: 12px 18px;
  backdrop-filter: blur(8px); min-width: 110px;
}
.hero-stat .val {
  font-size: clamp(1.3rem, 4vw, 2rem);
  font-weight: 800; display: block; color: #79c0ff;
}
.hero-stat .lbl {
  font-size: .72rem; text-transform: uppercase;
  letter-spacing: 1px; color: var(--muted);
}

/* ── MAIN ── */
.main { max-width: 1200px; margin: 0 auto; padding: 24px 16px 40px; }

/* ── DIGEST ── */
.digest-card {
  background: linear-gradient(135deg, #0d1f33 0%, var(--card) 100%);
  border: 1px solid #1d4068; border-radius: var(--radius);
  padding: 22px 20px; margin-bottom: 28px;
}
.digest-header {
  display: flex; justify-content: space-between;
  align-items: flex-start; flex-wrap: wrap; gap: 14px; margin-bottom: 14px;
}
.digest-title {
  font-size: clamp(1rem, 4vw, 1.35rem);
  font-weight: 800; color: #79c0ff;
}
.digest-subtitle { color: var(--muted); font-size: .85rem; margin-top: 3px; }
.digest-totals { display: flex; gap: 20px; flex-wrap: wrap; }
.digest-total-block { text-align: right; }
.digest-total-val {
  font-size: clamp(1.4rem, 5vw, 2rem);
  font-weight: 800; color: #e6edf3; display: block;
}
.digest-total-lbl {
  font-size: .7rem; text-transform: uppercase;
  color: var(--muted); display: block;
}
.digest-change {
  font-size: .82rem; font-weight: 700; display: block; margin-top: 2px;
}
.digest-narrative {
  color: #c9d1d9; font-size: .93rem; line-height: 1.75; margin-bottom: 14px;
  padding: 12px 16px; background: rgba(255,255,255,.04);
  border-radius: 8px; border-left: 3px solid #1d4068;
}
.digest-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 18px;
}
.digest-col h4 {
  font-size: .74rem; text-transform: uppercase;
  letter-spacing: .5px; color: var(--muted); margin-bottom: 8px;
}
.digest-species-list { display: flex; flex-direction: column; gap: 5px; }
.digest-species {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 10px; background: var(--card2);
  border-radius: 8px; border: 1px solid var(--border);
}
.digest-rank { font-size: .72rem; color: var(--muted); width: 16px; flex-shrink: 0; }
.digest-name  { flex: 1; font-size: .88rem; font-weight: 500; color: var(--text); }
.digest-count { font-size: .85rem; font-weight: 700; color: #79c0ff; }
.arrivals-list { display: flex; flex-wrap: wrap; gap: 6px; }
.arrival-chip {
  background: #0d2744; border: 1px solid #1f6feb;
  color: #58a6ff; border-radius: 20px;
  padding: 4px 10px; font-size: .8rem; font-weight: 500;
}

/* ── DIGEST CHART ── */
.digest-chart-card {
  background: var(--card2); border-radius: 10px;
  border: 1px solid var(--border);
  padding: 16px 18px; margin-bottom: 16px;
}
.digest-chart-card h4 {
  font-size: .74rem; text-transform: uppercase;
  letter-spacing: .5px; color: var(--muted); margin-bottom: 8px;
}
.chart-legend {
  display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;
}
.chart-legend-item {
  display: flex; align-items: center; gap: 5px;
  font-size: .78rem; color: var(--text);
}
.chart-legend-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}
.digest-dot {
  width: 8px; height: 8px; border-radius: 50%;
  flex-shrink: 0; display: inline-block;
}

/* ── RARE SPECIES ── */
.digest-rare { margin-top: 18px; }
.digest-rare > h4 {
  font-size: .74rem; text-transform: uppercase;
  letter-spacing: .5px; color: var(--muted); margin-bottom: 10px;
}
.rare-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}
.rare-card {
  display: flex; align-items: center; gap: 12px;
  background: #1a1200; border: 1px solid #3a2d00;
  border-radius: 10px; padding: 10px 12px;
}
.rare-thumb { width: 44px; height: 44px; border-radius: 8px; object-fit: cover; flex-shrink: 0; cursor: pointer; }
.rare-thumb-placeholder {
  width: 44px; height: 44px; border-radius: 8px;
  background: #2a1f00; display: flex; align-items: center;
  justify-content: center; font-size: 1.3rem; flex-shrink: 0;
}
.rare-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.rare-name  { font-size: .88rem; font-weight: 700; color: #fbbf24; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rare-count { font-size: .76rem; color: #d97706; }
.rare-badge {
  font-size: .7rem; font-weight: 600;
  background: #2a1f00; color: #f0b429;
  border: 1px solid #3a2d00;
  border-radius: 4px; padding: 2px 6px;
  display: inline-block; margin-top: 2px;
  white-space: normal; line-height: 1.4;
}

/* ── OVERVIEW ── */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
  gap: 20px; margin-bottom: 28px;
}
.card {
  background: var(--card); border-radius: var(--radius);
  border: 1px solid var(--border); padding: 20px;
}
.card h2 {
  font-size: .85rem; text-transform: uppercase;
  letter-spacing: .5px; color: var(--muted); margin-bottom: 14px;
}

/* ── CATEGORY SECTIONS ── */
.cat-section { margin-bottom: 48px; }
.cat-header {
  border-radius: var(--radius); padding: 18px 20px;
  margin-bottom: 16px; border: 1px solid var(--border);
}
.cat-title-row {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.cat-icon { font-size: 1.6rem; flex-shrink: 0; }
.cat-title {
  font-size: clamp(1.2rem, 4vw, 1.65rem); font-weight: 800;
}
.cat-meta { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
@media (min-width: 600px) { .cat-meta { margin-left: auto; margin-top: 0; } }
.meta-pill {
  border-radius: 20px; padding: 3px 10px;
  font-size: .76rem; font-weight: 600; color: #fff;
}
.meta-pill.outline {
  background: transparent !important;
  border: 1.5px solid; color: inherit;
}
.yr-badges { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.yr-badge {
  border-radius: 6px; padding: 3px 10px;
  font-size: .74rem; font-weight: 600; color: #fff;
}

.cat-body { display: flex; flex-direction: column; gap: 16px; }
.narrative {
  background: var(--card2); border-radius: 10px; padding: 14px 18px;
  font-size: .92rem; color: #c9d1d9; line-height: 1.75;
  border-left: 4px solid var(--border);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}
.chart-card {
  background: var(--card); border-radius: var(--radius);
  border: 1px solid var(--border); padding: 16px;
}
.chart-card.full-width { grid-column: 1 / -1; }
.chart-card h3 {
  font-size: .76rem; text-transform: uppercase;
  letter-spacing: .5px; color: var(--muted); margin-bottom: 10px;
}

/* ── HEATMAP ── */
.heatmap-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.heatmap {
  border-collapse: collapse; font-size: .76rem;
  min-width: 480px; width: 100%;
}
.heatmap th, .heatmap td {
  padding: 6px 4px; text-align: center;
  min-width: 44px; border-radius: 4px;
}
.heatmap thead th { font-weight: 600; color: var(--muted); }
.heatmap tbody th {
  font-weight: 700; text-align: right;
  padding-right: 10px; color: var(--muted); white-space: nowrap;
}

/* ── SPECIES TABLE ── */
.sp-table { width: 100%; border-collapse: collapse; font-size: .85rem; }
.sp-table thead tr { border-bottom: 2px solid var(--border); }
.sp-table th {
  padding: 7px 7px; text-align: left;
  color: var(--muted); font-weight: 600;
  font-size: .74rem; text-transform: uppercase;
}
.sp-table tbody tr { border-bottom: 1px solid var(--border); }
.sp-table tbody tr:hover,
.sp-table tbody tr:active { background: var(--card2); }
.sp-rank  { color: var(--muted); width: 26px; padding: 8px 5px; }
.sp-thumb-cell { width: 50px; padding: 4px 6px; vertical-align: middle; }
.sp-name  { font-weight: 500; padding: 8px 7px; color: var(--text); }
.sp-bar-cell { width: 32%; padding: 8px 7px; }
@media (max-width: 520px) { .sp-bar-cell { display: none; } }
.sp-bar   { height: 8px; border-radius: 4px; min-width: 2px; opacity: .85; }
.sp-count { font-weight: 700; white-space: nowrap; padding: 8px 5px; color: var(--text); }
.sp-pct   { color: var(--muted); font-size: .78rem; padding: 8px 5px; }
@media (max-width: 380px) { .sp-pct { display: none; } }

/* ── THUMBNAIL ── */
.sp-thumb {
  width: 40px; height: 40px; border-radius: 6px;
  object-fit: cover; cursor: pointer; display: block;
  transition: transform .15s, box-shadow .15s;
  border: 1px solid var(--border);
}
.sp-thumb:hover  { transform: scale(1.1); box-shadow: 0 2px 12px rgba(0,0,0,.5); }
.sp-thumb:active { transform: scale(1.04); }

/* ── LIGHTBOX ── */
#lightbox {
  display: none; position: fixed; inset: 0; z-index: 9999;
  background: rgba(0,0,0,.95);
  align-items: center; justify-content: center; flex-direction: column;
  padding: 20px; -webkit-tap-highlight-color: transparent;
}
#lb-close {
  position: absolute; top: 14px; right: 16px;
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.2);
  color: #e6edf3; font-size: 1.2rem;
  width: 44px; height: 44px; border-radius: 50%;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
}
#lb-close:hover { background: rgba(255,255,255,.25); }
#lightbox img {
  max-width: 100%; max-height: 75vh;
  border-radius: 10px; object-fit: contain;
  box-shadow: 0 4px 40px rgba(0,0,0,.8);
}
#lb-name {
  color: #e6edf3; margin-top: 14px; font-size: 1rem;
  font-weight: 600; text-align: center;
}

/* ── SECTION LABEL ── */
.section-label {
  font-size: .66rem; text-transform: uppercase; letter-spacing: 2px;
  color: var(--muted); margin-bottom: 24px; margin-top: 36px;
  display: flex; align-items: center; gap: 12px;
}
.section-label::after { content:''; flex:1; height:1px; background:var(--border); }

/* ── FOOTER ── */
footer {
  text-align: center; padding: 32px 16px;
  color: var(--muted); font-size: .8rem;
  border-top: 1px solid var(--border); margin-top: 24px;
}

/* ── SPECIES DETAIL (digest sparklines) ── */
.sp-detail-section { margin-bottom: 18px; }
.sp-detail-section > h4 {
  font-size: .74rem; text-transform: uppercase;
  letter-spacing: .5px; color: var(--muted); margin-bottom: 8px;
}

/* collapsible category blocks */
.cat-breakdown {
  border: 1px solid var(--border); border-radius: 10px;
  margin-bottom: 6px; overflow: hidden;
}
.cat-breakdown[open] > summary .cb-chevron { transform: rotate(90deg); }
.cat-breakdown-summary {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; cursor: pointer;
  background: var(--card2); list-style: none;
  user-select: none; -webkit-user-select: none;
}
.cat-breakdown-summary::-webkit-details-marker { display: none; }
.cat-breakdown-summary:hover { background: var(--card); }
.cb-icon   { font-size: 1.1rem; flex-shrink: 0; }
.cb-name   { flex: 1; font-size: .88rem; font-weight: 700; }
.cb-total  {
  font-size: .76rem; font-weight: 700;
  border-radius: 20px; padding: 2px 9px; flex-shrink: 0;
}
.cb-species { font-size: .74rem; color: var(--muted); flex-shrink: 0; }
.cb-chevron {
  color: var(--muted); font-size: 1rem; flex-shrink: 0;
  transition: transform .2s; display: inline-block;
}

.sp-detail-list {
  display: flex; flex-direction: column; gap: 2px; padding: 6px 8px;
}
.sp-detail-row {
  display: flex; align-items: center; gap: 10px;
  padding: 5px 8px; background: var(--card2);
  border: 1px solid var(--border); border-radius: 7px;
}
.sp-thumb-sm {
  width: 32px; height: 32px; border-radius: 5px; object-fit: cover;
  flex-shrink: 0; cursor: pointer; border: 1px solid var(--border);
}
.sp-thumb-sm-ph {
  width: 32px; height: 32px; border-radius: 5px; flex-shrink: 0;
  background: var(--card);
}
.sp-detail-name {
  flex: 1; font-size: .84rem; font-weight: 500; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0;
}
.sp-detail-right {
  display: flex; flex-direction: column; align-items: flex-end;
  flex-shrink: 0; gap: 1px;
}
.sp-detail-count { font-size: .8rem; font-weight: 700; color: #79c0ff; }
.sp-detail-peak  { font-size: .67rem; color: var(--muted); white-space: nowrap; }

/* ── MISC ── */
.hide-mobile {}
@media (max-width: 480px) { .hide-mobile { display: none; } }
"""


# ── Main HTML assembly ────────────────────────────────────────────────────────

CAT_ORDER = [
    "birds_of_prey", "owls", "woodpeckers", "ducks", "waterfowl",
    "songbirds", "shorebirds", "hummingbirds", "corvids", "introduced",
]


def render_top20(top20, all_total, photos):
    if not top20:
        return ""
    max_c = top20[0][1]
    rows  = ""
    for i, (name, count) in enumerate(top20, 1):
        pct   = count / all_total * 100 if all_total else 0
        bar_w = int(count / max_c * 100) if max_c else 0
        photo = photos.get(name, {})
        thumb = photo.get("thumb", "")
        full  = photo.get("full", "") or thumb
        if thumb:
            img_html = (
                f'<img src="{thumb}" data-full="{full}" alt="{name}" '
                f'class="sp-thumb" loading="lazy">'
            )
            thumb_td = f'<td class="sp-thumb-cell">{img_html}</td>'
        else:
            thumb_td = '<td class="sp-thumb-cell"></td>'
        rows += (
            f"<tr>"
            f'<td class="sp-rank">{i}</td>'
            f"{thumb_td}"
            f'<td class="sp-name">{name}</td>'
            f'<td class="sp-bar-cell hide-mobile">'
            f'<div class="sp-bar" style="width:{bar_w}%;background:#4a90d9"></div></td>'
            f'<td class="sp-count">{count:,}</td>'
            f'<td class="sp-pct">{pct:.1f}%</td>'
            f"</tr>"
        )
    return (
        '<table class="sp-table">'
        "<thead><tr>"
        "<th>#</th><th></th><th>Species</th>"
        '<th class="hide-mobile"></th>'
        "<th>Detections</th><th></th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
    )


def build_html(stats, narrative_cfg, photos, digest):
    nav_links    = ""
    cat_sections = ""
    cat_labels, cat_data, cat_colors = [], [], []

    for key in CAT_ORDER:
        cfg = narrative_cfg["categories"].get(key)
        if not cfg:
            continue
        href = cfg.get("id", key.replace("_", "-"))
        nav_links    += f'<a href="#{href}" class="nav-link">{cfg["icon"]} {cfg["name"]}</a>\n'
        cat_sections += render_category(key, cfg, stats, photos)
        s = stats["cat_stats"].get(key, {})
        cat_labels.append(cfg["name"])
        cat_data.append(s.get("total", 0))
        cat_colors.append(cfg["color"])

    top20_html   = render_top20(stats["top20"], stats["total"], photos)
    digest_html  = render_digest(digest, narrative_cfg, photos)
    site         = narrative_cfg.get("site", {})
    title        = site.get("title", "Bird Detection Analysis")
    subtitle     = site.get("subtitle", "")
    footer_text  = site.get("footer", "")
    total_det    = stats["total"]
    sp_count     = len(stats["all_species"])
    generated    = date.today().strftime("%Y-%m-%d")

    js_cat_labels  = json.dumps(cat_labels)
    js_cat_data    = json.dumps(cat_data)
    js_cat_colors  = json.dumps(cat_colors)
    js_monthly     = json.dumps(stats["monthly_overall"])
    js_months      = json.dumps(MONTHS)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{title} — Full Record</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>{CSS}</style>
</head>
<body>

<nav class="top-nav">
  <span class="nav-brand">🐦 BirdDB</span>
  <a href="#overview" class="nav-link">Overview</a>
  {nav_links}
</nav>

<header class="hero">
  <h1>{title}</h1>
  <p class="subtitle">{subtitle}</p>
  <div class="hero-stats">
    <div class="hero-stat"><span class="val">{total_det:,}</span><span class="lbl">Total Detections</span></div>
    <div class="hero-stat"><span class="val">{sp_count}</span><span class="lbl">Species Detected</span></div>
    <div class="hero-stat"><span class="val">10</span><span class="lbl">Bird Groups</span></div>
    <div class="hero-stat"><span class="val">2</span><span class="lbl">Years of Data</span></div>
  </div>
</header>

<main class="main" id="overview">

  {digest_html}

  <div class="section-label">Overview</div>

  <div class="overview-grid">
    <div class="card">
      <h2>Detections by Category</h2>
      <canvas id="donut-chart" height="300"></canvas>
    </div>
    <div class="card">
      <h2>Overall Monthly Activity</h2>
      <canvas id="overall-monthly" height="300"></canvas>
    </div>
  </div>

  <div class="card" style="margin-bottom:32px;overflow-x:auto">
    <h2>Top 20 Species — All Time</h2>
    {top20_html}
  </div>

  <div class="section-label">By Bird Group</div>
  {cat_sections}

</main>

<!-- Lightbox overlay -->
<div id="lightbox" role="dialog" aria-modal="true" aria-label="Bird photo">
  <button id="lb-close" aria-label="Close photo">✕</button>
  <img id="lb-img" src="" alt="">
  <p id="lb-name"></p>
</div>

<footer>
  <p>{footer_text} · Generated {generated}</p>
  <p style="margin-top:5px;font-size:.75rem">
    Photos via Wikipedia · Tap any thumbnail to view full size
  </p>
</footer>

<script>
// ── Chart.js dark theme defaults ─────────────────────────────────────────────
Chart.defaults.color = '#8b949e';
Chart.defaults.borderColor = '#30363d';

// ── Overview charts ───────────────────────────────────────────────────────────
new Chart(document.getElementById('donut-chart'), {{
  type: 'doughnut',
  data: {{
    labels: {js_cat_labels},
    datasets: [{{ data: {js_cat_data}, backgroundColor: {js_cat_colors}, borderWidth: 2 }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      legend: {{ position: 'bottom', labels: {{ font: {{ size: 11 }}, padding: 10 }} }}
    }}
  }}
}});

new Chart(document.getElementById('overall-monthly'), {{
  type: 'bar',
  data: {{
    labels: {js_months},
    datasets: [{{
      label: 'Detections', data: {js_monthly},
      backgroundColor: '#4a90d9aa', borderColor: '#4a90d9',
      borderWidth: 1, borderRadius: 4
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ y: {{ beginAtZero: true, ticks: {{ maxTicksLimit: 5 }} }} }}
  }}
}});

// ── Lightbox ──────────────────────────────────────────────────────────────────
(function () {{
  var lb    = document.getElementById('lightbox');
  var lbImg = document.getElementById('lb-img');
  var lbNm  = document.getElementById('lb-name');

  document.addEventListener('click', function (e) {{
    if (e.target.classList.contains('sp-thumb')) {{
      lbImg.src = e.target.dataset.full || e.target.src;
      lbNm.textContent = e.target.alt;
      lb.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    }}
  }});

  function close() {{
    lb.style.display = 'none';
    document.body.style.overflow = '';
    lbImg.src = '';
  }}

  document.getElementById('lb-close').addEventListener('click', close);
  lb.addEventListener('click', function (e) {{ if (e.target === lb) close(); }});
  document.addEventListener('keydown', function (e) {{ if (e.key === 'Escape') close(); }});
}})();
</script>
</body>
</html>
"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    narrative_cfg = load_narrative()
    records       = parse_data()
    photos        = fetch_all_photos(records)
    stats         = compute_stats(records)
    digest        = compute_digest(
        records, DIGEST_YEAR, DIGEST_MONTH,
        cat_cfg=narrative_cfg.get("categories", {})
    )
    html          = build_html(stats, narrative_cfg, photos, digest)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUTPUT_FILE) // 1024
    print(f"Written {OUTPUT_FILE} ({size_kb} KB)")
    print(f"  {stats['total']:,} detections · {len(stats['all_species'])} species")
    print(
        f"  Digest: {MONTHS[DIGEST_MONTH-1]} {DIGEST_YEAR} — "
        f"{digest['total']:,} detections "
        f"({digest['pct_change']:+.0f}% vs {DIGEST_YEAR-1})"
    )


if __name__ == "__main__":
    main()
