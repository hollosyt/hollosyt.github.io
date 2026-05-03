#!/usr/bin/env python3
"""
Spring 2025 vs Spring 2026 Bird Timing Analysis
Analyzes first arrival dates, peak activity, detection curves, and species presence.
Note: March 2026 sensor outage (March 12-22) makes March 2026 data unreliable for arrival comparisons.
"""

import csv
from datetime import date, timedelta
from collections import defaultdict
import statistics

DATA_FILE = "/Users/t.hollosy/Projects/bird_analysis/BirdDB.txt"
CONFIDENCE_THRESHOLD = 0.7

# ── helpers ──────────────────────────────────────────────────────────────────

def ordinal(d):
    """Return 'Apr 3' style string from a date object."""
    return d.strftime("%b %-d")

def load_data():
    """Load all rows, returning list of dicts with parsed fields."""
    rows = []
    with open(DATA_FILE, newline="", encoding="utf-8", errors="replace") as f:
        # Filter NUL bytes which cause csv parser to fail
        clean = (line.replace("\x00", "") for line in f)
        reader = csv.DictReader(clean, delimiter=";")
        for row in reader:
            try:
                conf = float(row["Confidence"])
            except (ValueError, KeyError):
                continue
            if conf < CONFIDENCE_THRESHOLD:
                continue
            try:
                d = date.fromisoformat(row["Date"].strip())
            except ValueError:
                continue
            rows.append({
                "date": d,
                "com_name": row["Com_Name"].strip(),
                "sci_name": row["Sci_Name"].strip(),
                "confidence": conf,
            })
    return rows

def date_range_days(year, month_start, day_start, month_end, day_end):
    start = date(year, month_start, day_start)
    end = date(year, month_end, day_end)
    result = set()
    d = start
    while d <= end:
        result.add(d)
        d += timedelta(days=1)
    return result

# ── data preparation ──────────────────────────────────────────────────────────

def build_species_data(rows):
    """
    Returns nested dicts:
      detections[species][year][date] = count
    Only includes rows in spring windows:
      2025: March 1 – May 15
      2026: April 1 – May 15 (March 2026 excluded as unreliable)
      But we DO include late-March 2025 to find 2025 first-arrival dates.
    """
    april_25 = date_range_days(2025, 4, 1, 4, 30)
    april_26 = date_range_days(2026, 4, 1, 4, 30)
    march_25 = date_range_days(2025, 3, 1, 3, 31)
    may_25   = date_range_days(2025, 5, 1, 5, 15)
    may_26   = date_range_days(2026, 5, 1, 5, 15)

    spring_25 = march_25 | april_25 | may_25
    spring_26 = april_26 | may_26

    # Full detections per species per year per date
    det = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    # April-only
    april_det = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for row in rows:
        d = row["date"]
        sp = row["com_name"]
        if d in spring_25:
            det[sp][2025][d] += 1
        if d in spring_26:
            det[sp][2026][d] += 1
        if d in april_25:
            april_det[sp][2025][d] += 1
        if d in april_26:
            april_det[sp][2026][d] += 1

    return det, april_det

# ── analysis functions ─────────────────────────────────────────────────────────

def first_arrival(date_count_dict):
    """Return earliest date with at least 1 detection."""
    if not date_count_dict:
        return None
    return min(date_count_dict.keys())

def peak_date(date_count_dict):
    """Return date with maximum detections."""
    if not date_count_dict:
        return None
    return max(date_count_dict.keys(), key=lambda d: date_count_dict[d])

def total_detections(date_count_dict):
    return sum(date_count_dict.values())

def april_first_arrival(det, species, year):
    """First detection in April for given species/year."""
    april_start = date(year, 4, 1)
    april_end   = date(year, 4, 30)
    dates = [d for d in det.get(species, {}).get(year, {})
             if april_start <= d <= april_end]
    return min(dates) if dates else None

def compute_april_curve(april_det, species, year):
    """Returns list of (day_of_month, count) for April."""
    day_counts = defaultdict(int)
    for d, cnt in april_det.get(species, {}).get(year, {}).items():
        day_counts[d.day] += cnt
    return [(day, day_counts.get(day, 0)) for day in range(1, 31)]

def weighted_mean_april_day(april_det, species, year):
    """Compute center-of-mass of detections across April days."""
    total = 0
    weighted = 0
    for d, cnt in april_det.get(species, {}).get(year, {}).items():
        weighted += d.day * cnt
        total += cnt
    if total == 0:
        return None
    return weighted / total

# ── main ───────────────────────────────────────────────────────────────────────

def main():
    print("Loading data...")
    rows = load_data()
    print(f"  Loaded {len(rows):,} rows (confidence >= {CONFIDENCE_THRESHOLD})")

    det, april_det = build_species_data(rows)

    all_species = set(det.keys())
    print(f"  Total species in spring windows: {len(all_species)}")

    # Count April totals per species per year
    april_total_25 = {}
    april_total_26 = {}
    for sp in all_species:
        april_total_25[sp] = total_detections(april_det.get(sp, {}).get(2025, {}))
        april_total_26[sp] = total_detections(april_det.get(sp, {}).get(2026, {}))

    # ── SECTION 1: Species present in both Aprils ─────────────────────────────
    # At least 10 detections in EACH April
    both_april_10 = [sp for sp in all_species
                     if april_total_25[sp] >= 10 and april_total_26[sp] >= 10]
    print(f"\n  Species with >=10 April detections in BOTH years: {len(both_april_10)}")

    # ── SECTION 2: First April arrival shift ──────────────────────────────────
    print("\n" + "="*70)
    print("SECTION 1: FIRST APRIL ARRIVAL DATE SHIFTS")
    print("="*70)
    print("(Species with >=10 April detections in both years, sorted by |shift|)\n")

    arrival_shifts = []
    for sp in both_april_10:
        fa_25 = april_first_arrival(det, sp, 2025)
        fa_26 = april_first_arrival(det, sp, 2026)
        if fa_25 and fa_26:
            # Compare day-of-year within April (Apr 1 = day 1, Apr 30 = day 30)
            # Use Apr 1 as baseline for both years
            shift = (fa_26.month * 100 + fa_26.day) - (fa_25.month * 100 + fa_25.day)
            # Normalize: Apr=4, May=5 only; compute as days from Apr 1
            baseline_25 = (fa_25 - date(fa_25.year, 4, 1)).days
            baseline_26 = (fa_26 - date(fa_26.year, 4, 1)).days
            shift = baseline_26 - baseline_25  # positive = first detection later in 2026
            arrival_shifts.append((sp, fa_25, fa_26, shift,
                                   april_total_25[sp], april_total_26[sp]))

    arrival_shifts.sort(key=lambda x: abs(x[3]), reverse=True)

    print(f"  {'Species':<35} {'Apr25 1st':>10} {'Apr26 1st':>10} {'Shift':>7}  {'N25':>6} {'N26':>6}")
    print("  " + "-"*80)
    for sp, fa25, fa26, shift, n25, n26 in arrival_shifts[:25]:
        direction = "LATER" if shift > 0 else "EARLIER"
        flag = f"  <-- {abs(shift)}d {direction}" if abs(shift) >= 5 else ""
        print(f"  {sp:<35} {ordinal(fa25):>10} {ordinal(fa26):>10} {shift:>+7}d  {n25:>6,} {n26:>6,}{flag}")

    # ── SECTION 3: Peak activity date shift ───────────────────────────────────
    print("\n" + "="*70)
    print("SECTION 2: PEAK ACTIVITY DATE SHIFTS (April, >=50 detections each year)")
    print("="*70)
    print()

    peak_species = [sp for sp in both_april_10
                    if april_total_25[sp] >= 50 and april_total_26[sp] >= 50]
    print(f"  Species qualifying (>=50 April detections each year): {len(peak_species)}")

    peak_shifts = []
    for sp in peak_species:
        pk25 = peak_date(april_det.get(sp, {}).get(2025, {}))
        pk26 = peak_date(april_det.get(sp, {}).get(2026, {}))
        if pk25 and pk26:
            # Day-of-April: Apr 1 = 0, Apr 30 = 29
            pk25_day = (pk25 - date(pk25.year, 4, 1)).days
            pk26_day = (pk26 - date(pk26.year, 4, 1)).days
            shift = pk26_day - pk25_day  # positive = peak later in 2026
            wm25 = weighted_mean_april_day(april_det, sp, 2025)
            wm26 = weighted_mean_april_day(april_det, sp, 2026)
            wm_shift = (wm26 - wm25) if (wm25 and wm26) else None
            peak_shifts.append((sp, pk25, pk26, shift, wm25, wm26, wm_shift,
                                 april_total_25[sp], april_total_26[sp]))

    peak_shifts.sort(key=lambda x: abs(x[3]), reverse=True)

    print(f"\n  {'Species':<35} {'Peak25':>10} {'Peak26':>10} {'PkShift':>9} {'WM25':>6} {'WM26':>6} {'WMShift':>8}  {'N25':>6} {'N26':>6}")
    print("  " + "-"*100)
    for sp, pk25, pk26, shift, wm25, wm26, wm_shift, n25, n26 in peak_shifts[:25]:
        wm_str = f"{wm_shift:+.1f}d" if wm_shift is not None else "  N/A"
        flag = "  <--" if abs(shift) >= 5 else ""
        print(f"  {sp:<35} {ordinal(pk25):>10} {ordinal(pk26):>10} {shift:>+9}d "
              f"{wm25:>6.1f} {wm26:>6.1f} {wm_str:>8}  {n25:>6,} {n26:>6,}{flag}")

    # ── SECTION 4: Detection curve shape analysis ─────────────────────────────
    print("\n" + "="*70)
    print("SECTION 3: DETECTION CURVE SHAPE — EARLY vs LATE APRIL SPLIT")
    print("="*70)
    print("(Comparing first half [Apr 1-15] vs second half [Apr 16-30] proportions)\n")

    curve_shifts = []
    for sp in peak_species:
        curve25 = compute_april_curve(april_det, sp, 2025)
        curve26 = compute_april_curve(april_det, sp, 2026)

        early25 = sum(cnt for day, cnt in curve25 if day <= 15)
        late25  = sum(cnt for day, cnt in curve25 if day > 15)
        early26 = sum(cnt for day, cnt in curve26 if day <= 15)
        late26  = sum(cnt for day, cnt in curve26 if day > 15)

        tot25 = early25 + late25
        tot26 = early26 + late26
        if tot25 == 0 or tot26 == 0:
            continue

        early_pct25 = 100 * early25 / tot25
        early_pct26 = 100 * early26 / tot26
        shift = early_pct26 - early_pct25  # positive = more front-loaded in 2026

        curve_shifts.append((sp, early_pct25, early_pct26, shift,
                              early25, late25, early26, late26))

    curve_shifts.sort(key=lambda x: abs(x[3]), reverse=True)

    print(f"  {'Species':<35} {'Early%25':>9} {'Early%26':>9} {'Change':>8}  {'E25/L25':>12} {'E26/L26':>12}")
    print("  " + "-"*95)
    for sp, ep25, ep26, shift, e25, l25, e26, l26, in curve_shifts[:20]:
        flag = ""
        if shift >= 15:
            flag = "  <-- shifted EARLIER in 2026"
        elif shift <= -15:
            flag = "  <-- shifted LATER in 2026"
        print(f"  {sp:<35} {ep25:>8.1f}% {ep26:>8.1f}% {shift:>+7.1f}%  {e25:>5}/{l25:<5} {e26:>5}/{l26:<5}{flag}")

    # ── SECTION 5: Species presence/absence ──────────────────────────────────
    print("\n" + "="*70)
    print("SECTION 4: SPECIES PRESENT IN ONE APRIL BUT NOT THE OTHER (>=10 detections)")
    print("="*70)

    only_25 = sorted([(sp, april_total_25[sp]) for sp in all_species
                      if april_total_25[sp] >= 10 and april_total_26[sp] < 10],
                     key=lambda x: -x[1])
    only_26 = sorted([(sp, april_total_26[sp]) for sp in all_species
                      if april_total_26[sp] >= 10 and april_total_25[sp] < 10],
                     key=lambda x: -x[1])

    print(f"\n  In April 2025 but NOT April 2026 ({len(only_25)} species):")
    for sp, n in only_25:
        print(f"    {sp:<40} {n:>5} detections in Apr 2025")

    print(f"\n  In April 2026 but NOT April 2025 ({len(only_26)} species):")
    for sp, n in only_26:
        print(f"    {sp:<40} {n:>5} detections in Apr 2026")

    # ── SECTION 6: Late March 2025 early arrivals ─────────────────────────────
    print("\n" + "="*70)
    print("SECTION 5: LATE MARCH 2025 ARRIVALS (migrants that came before April 2025)")
    print("="*70)
    print("(For species also present in April 2026, to see if they arrived even earlier in 2025)\n")

    march_25_window = {date(2025, 3, d) for d in range(15, 32)}
    march_early_arrivals = []
    for sp in both_april_10:
        march_dets = {d: cnt for d, cnt in det.get(sp, {}).get(2025, {}).items()
                      if d in march_25_window}
        if march_dets:
            first_march = min(march_dets.keys())
            total_march = sum(march_dets.values())
            fa_april = april_first_arrival(det, sp, 2025)
            march_early_arrivals.append((sp, first_march, total_march, fa_april,
                                         april_total_25[sp], april_total_26[sp]))

    march_early_arrivals.sort(key=lambda x: x[1])  # Sort by earliest March date

    print(f"  {'Species':<35} {'1st Mar25':>10} {'MarDet':>7} {'1stApr25':>10} {'N_Apr25':>8} {'N_Apr26':>8}")
    print("  " + "-"*85)
    for sp, fm, tm, fa, n25, n26 in march_early_arrivals[:20]:
        fa_str = ordinal(fa) if fa else "   N/A"
        print(f"  {sp:<35} {ordinal(fm):>10} {tm:>7,} {fa_str:>10} {n25:>8,} {n26:>8,}")

    # ── SECTION 7: Overall systematic shift ───────────────────────────────────
    print("\n" + "="*70)
    print("SECTION 6: OVERALL SYSTEMATIC TIMING SHIFT")
    print("="*70)

    # Use weighted mean April day for all species with >=50 detections in both years
    wm_shifts = []
    for sp in peak_species:
        wm25 = weighted_mean_april_day(april_det, sp, 2025)
        wm26 = weighted_mean_april_day(april_det, sp, 2026)
        if wm25 and wm26:
            wm_shifts.append(wm26 - wm25)

    if wm_shifts:
        mean_shift = statistics.mean(wm_shifts)
        median_shift = statistics.median(wm_shifts)
        stdev_shift = statistics.stdev(wm_shifts) if len(wm_shifts) > 1 else 0
        later_count = sum(1 for s in wm_shifts if s > 1)
        earlier_count = sum(1 for s in wm_shifts if s < -1)
        neutral_count = len(wm_shifts) - later_count - earlier_count

        print(f"\n  Based on {len(wm_shifts)} species with >=50 April detections in both years:")
        print(f"  Mean weighted-mean-day shift:   {mean_shift:+.2f} days (positive = later in 2026)")
        print(f"  Median weighted-mean-day shift: {median_shift:+.2f} days")
        print(f"  Std dev of shifts:              {stdev_shift:.2f} days")
        print(f"  Species shifted LATER  (>1d):   {later_count}")
        print(f"  Species shifted EARLIER (<-1d): {earlier_count}")
        print(f"  Species roughly stable (±1d):   {neutral_count}")

        # First-arrival shift distribution
        arr_shifts_vals = [s for _, _, _, s, _, _ in arrival_shifts]
        if arr_shifts_vals:
            print(f"\n  First April arrival shift stats (all species >=10 det each year):")
            print(f"  N = {len(arr_shifts_vals)}")
            print(f"  Mean shift:   {statistics.mean(arr_shifts_vals):+.2f} days")
            print(f"  Median shift: {statistics.median(arr_shifts_vals):+.2f} days")
            print(f"  Min shift:    {min(arr_shifts_vals):+d} days")
            print(f"  Max shift:    {max(arr_shifts_vals):+d} days")

    # ── SECTION 8: Top species deep dive ─────────────────────────────────────
    print("\n" + "="*70)
    print("SECTION 7: APRIL DAILY DETECTION CURVES — TOP SPECIES")
    print("="*70)
    print("(Day-by-day April counts, 2025 vs 2026, for highest-detection species)\n")

    # Top 10 species by combined April detections
    top_sp = sorted(peak_species,
                    key=lambda sp: april_total_25[sp] + april_total_26[sp],
                    reverse=True)[:10]

    for sp in top_sp:
        curve25 = {day: cnt for day, cnt in compute_april_curve(april_det, sp, 2025)}
        curve26 = {day: cnt for day, cnt in compute_april_curve(april_det, sp, 2026)}
        n25 = april_total_25[sp]
        n26 = april_total_26[sp]
        pk25 = peak_date(april_det.get(sp, {}).get(2025, {}))
        pk26 = peak_date(april_det.get(sp, {}).get(2026, {}))
        wm25 = weighted_mean_april_day(april_det, sp, 2025)
        wm26 = weighted_mean_april_day(april_det, sp, 2026)

        print(f"  {sp}")
        print(f"    2025: {n25:,} total | peak {ordinal(pk25)} | wt-mean Apr {wm25:.1f}")
        print(f"    2026: {n26:,} total | peak {ordinal(pk26)} | wt-mean Apr {wm26:.1f}")

        # Print mini bar chart (weekly bins)
        bins_25 = [sum(curve25.get(d, 0) for d in range(1+7*w, 8+7*w)) for w in range(4)]
        bins_26 = [sum(curve26.get(d, 0) for d in range(1+7*w, 8+7*w)) for w in range(4)]
        weeks = ["Apr 1-7 ", "Apr 8-14", "Apr15-21", "Apr22-28"]
        print(f"    {'Week':<10}  {'2025':>6}  {'2026':>6}")
        for wk, b25, b26 in zip(weeks, bins_25, bins_26):
            bar25 = "#" * min(30, b25 // max(1, (max(bins_25+bins_26) // 30)))
            bar26 = "*" * min(30, b26 // max(1, (max(bins_25+bins_26) // 30)))
            print(f"    {wk}  {b25:>6,}  {b26:>6,}  25:{bar25}")
            print(f"    {'':10}  {'':6}  {'':6}  26:{bar26}")
        print()

    # ── SUMMARY NARRATIVE ─────────────────────────────────────────────────────
    print("="*70)
    print("NARRATIVE SUMMARY")
    print("="*70)

    print(f"""
DATA OVERVIEW
  Spring 2025 window:  Mar 1 – May 15, 2025  ({sum(1 for r in rows if date(2025,3,1) <= r['date'] <= date(2025,5,15)):,} records)
  Spring 2026 window:  Apr 1 – May 15, 2026  ({sum(1 for r in rows if date(2026,4,1) <= r['date'] <= date(2026,5,15)):,} records)
  April 2025 records:  {sum(1 for r in rows if date(2025,4,1) <= r['date'] <= date(2025,4,30)):,}
  April 2026 records:  {sum(1 for r in rows if date(2026,4,1) <= r['date'] <= date(2026,4,30)):,}
  Note: March 2026 had sensor outage Mar 12-22; first arrival comparisons use April only.
""")

    print("TOP TIMING SHIFTERS (First April Arrival, >=5 day change):")
    big_movers = [(sp, fa25, fa26, shift, n25, n26)
                  for sp, fa25, fa26, shift, n25, n26 in arrival_shifts
                  if abs(shift) >= 5]
    for sp, fa25, fa26, shift, n25, n26 in big_movers[:15]:
        direction = "LATER" if shift > 0 else "EARLIER"
        print(f"  {sp}: {ordinal(fa25)} -> {ordinal(fa26)} ({abs(shift)} days {direction}) "
              f"[{n25} / {n26} Apr detections]")

    print("\nBIGGEST PEAK DATE SHIFTS (>=7 days):")
    big_peaks = [(sp, pk25, pk26, shift, n25, n26)
                 for sp, pk25, pk26, shift, wm25, wm26, wm_shift, n25, n26 in peak_shifts
                 if abs(shift) >= 7]
    for sp, pk25, pk26, shift, n25, n26 in big_peaks[:15]:
        direction = "LATER" if shift > 0 else "EARLIER"
        print(f"  {sp}: peak {ordinal(pk25)} -> {ordinal(pk26)} ({abs(shift)} days {direction}) "
              f"[{n25} / {n26} Apr detections]")

    print("\nBIGGEST CURVE SHAPE SHIFTS (front-load change >=20%):")
    big_curves = [(sp, ep25, ep26, shift, e25, l25, e26, l26)
                  for sp, ep25, ep26, shift, e25, l25, e26, l26 in curve_shifts
                  if abs(shift) >= 20]
    for sp, ep25, ep26, shift, e25, l25, e26, l26 in big_curves[:15]:
        direction = "more front-loaded" if shift > 0 else "more back-loaded"
        print(f"  {sp}: early% {ep25:.0f}% -> {ep26:.0f}% ({direction} in 2026) "
              f"[{e25}/{l25} vs {e26}/{l26} early/late]")

    if mean_shift:
        direction = "LATER" if mean_shift > 0 else "EARLIER"
        print(f"\nSYSTEMATIC SHIFT: Mean weighted-mean-day shift = {mean_shift:+.2f} days ({direction} in 2026)")
        print(f"  {later_count} species shifted later, {earlier_count} earlier, {neutral_count} stable")


if __name__ == "__main__":
    main()
