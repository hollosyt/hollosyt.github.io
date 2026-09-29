"""Generates the dusk-over-Discovery-Elementary hero scene for index.html.

Prints the <svg class="hero-scene"> element. Run tools/build-art.py to write it into the site.
"""
import math
import random

R = random.Random(11)
W, H = 1440, 440
BASE = 352  # school ground line


def n(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def wave(x0, x1, y, amps, step=24):
    """Points along a gentle wave: y + sum(a*sin(x/p+ph))."""
    pts = []
    x = x0
    while x <= x1:
        yy = y + sum(a * math.sin(x / p + ph) for a, p, ph in amps)
        pts.append((x, yy))
        x += step
    if pts[-1][0] != x1:
        yy = y + sum(a * math.sin(x1 / p + ph) for a, p, ph in amps)
        pts.append((x1, yy))
    return pts


def smooth(pts):
    """Catmull-Rom through pts -> cubic path segments (no leading M)."""
    d = []
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{n(c1[0])} {n(c1[1])} {n(c2[0])} {n(c2[1])} {n(p2[0])} {n(p2[1])}")
    return "".join(d)


def band(pts, bottom=H):
    return f"M{n(pts[0][0])} {n(pts[0][1])}{smooth(pts)}V{bottom}H{n(pts[0][0])}Z"


out = []
add = out.append

# ------------------------------------------------------------------ defs
add(f'<svg class="hero-scene" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMax slice" role="img" '
    'aria-label="Illustration: dusk over an elementary school in the snow, its cafeteria windows glowing warm '
    'as a parent and two children walk up to the door.">')
add("""  <defs>
    <linearGradient id="sc-ridge1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2b2e68"/><stop offset="1" stop-color="#1f2250"/></linearGradient>
    <linearGradient id="sc-ridge2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1e2253"/><stop offset="1" stop-color="#161940"/></linearGradient>
    <linearGradient id="sc-wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1d2050"/><stop offset="1" stop-color="#121434"/></linearGradient>
    <linearGradient id="sc-wall2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#22265a"/><stop offset="1" stop-color="#15173a"/></linearGradient>
    <linearGradient id="sc-win" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff0c4"/><stop offset=".55" stop-color="#ffcf72"/><stop offset="1" stop-color="#f3a634"/></linearGradient>
    <linearGradient id="sc-door" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff6dc"/><stop offset="1" stop-color="#ffc766"/></linearGradient>
    <linearGradient id="sc-snow-back" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#aeb6de"/><stop offset="1" stop-color="#c7cdea"/></linearGradient>
    <linearGradient id="sc-snow-mid" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d3d8f0"/><stop offset="1" stop-color="#e7eaf8"/></linearGradient>
    <linearGradient id="sc-snow-front" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#eef0fa"/><stop offset="1" stop-color="#e2e5f5"/></linearGradient>
    <linearGradient id="sc-path" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd48a" stop-opacity=".95"/><stop offset=".5" stop-color="#f3d6b4" stop-opacity=".75"/><stop offset="1" stop-color="#dcd3e6" stop-opacity=".6"/></linearGradient>
    <radialGradient id="sc-pool"><stop offset="0" stop-color="#ffc46b" stop-opacity=".7"/><stop offset="1" stop-color="#ffc46b" stop-opacity="0"/></radialGradient>
    <radialGradient id="sc-horizon" cy=".7"><stop offset="0" stop-color="#ffb866" stop-opacity=".55"/><stop offset=".45" stop-color="#e98a5a" stop-opacity=".18"/><stop offset="1" stop-color="#e98a5a" stop-opacity="0"/></radialGradient>
    <filter id="sc-blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="9"/></filter>
    <filter id="sc-blur-sm" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>
    <pattern id="sc-brick" width="18" height="8" patternUnits="userSpaceOnUse"><path d="M0 .5H18M0 4.5H18M4.5 .5V4.5M13.5 4.5V8.5" fill="none" stroke="#fff" stroke-opacity=".045"/></pattern>
  </defs>""")

# ------------------------------------------------------------ horizon glow
add(f'  <ellipse cx="720" cy="330" rx="640" ry="190" fill="url(#sc-horizon)"/>')


# ------------------------------------------------------ ridges + treelines
def treeline(pts, hmin, hmax, spacing, colour):
    d = []
    x = pts[0][0]
    xs = [p[0] for p in pts]
    while x < pts[-1][0]:
        # interpolate ridge y at x
        for i in range(len(xs) - 1):
            if xs[i] <= x <= xs[i + 1]:
                t = (x - xs[i]) / (xs[i + 1] - xs[i])
                y = pts[i][1] + t * (pts[i + 1][1] - pts[i][1])
                break
        h = R.uniform(hmin, hmax)
        w = h * R.uniform(.36, .46)
        d.append(f"M{n(x - w)} {n(y + 3)}L{n(x)} {n(y - h)}L{n(x + w)} {n(y + 3)}Z")
        x += R.uniform(*spacing)
    return f'  <path d="{"".join(d)}" fill="{colour}"/>'


r1 = wave(0, W, 272, [(12, 190, 0), (7, 71, 1.3)])
add(treeline(r1, 7, 16, (5, 11), "#2b2e68"))
add(f'  <path d="{band(r1)}" fill="url(#sc-ridge1)"/>')
r2 = wave(0, W, 308, [(9, 240, 2), (5, 88, .4)])
add(treeline(r2, 12, 30, (7, 15), "#1e2253"))
add(f'  <path d="{band(r2)}" fill="url(#sc-ridge2)"/>')


# ------------------------------------------------------------ snowy pines
def pine(cx, base, h, w, dark="#0e1130", lit="#181c47", snow="#dfe3f6", snow_op=.92):
    parts = [f'<rect x="{n(cx - 2.5)}" y="{n(base - h * .12)}" width="5" height="{n(h * .12 + 4)}" fill="#0b0d26"/>']
    top = base - h
    tiers = 4
    bottoms = [top + h * f for f in (.30, .52, .72, .90)]
    for i in range(tiers):
        apex = top if i == 0 else bottoms[i - 1] - h * .13
        b = bottoms[i]
        hw = w / 2 * (.42 + .58 * (i + 1) / tiers)
        sag = h * .025
        tier = (f"M{n(cx)} {n(apex)}L{n(cx + hw)} {n(b)}"
                f"Q{n(cx + hw * .5)} {n(b - sag)} {n(cx)} {n(b + sag * .6)}"
                f"Q{n(cx - hw * .5)} {n(b - sag)} {n(cx - hw)} {n(b)}Z")
        parts.append(f'<path d="{tier}" fill="{dark}"/>')
        # moonlit right flank
        parts.append(f'<path d="M{n(cx)} {n(apex)}L{n(cx + hw)} {n(b)}Q{n(cx + hw * .5)} {n(b - sag)} {n(cx)} {n(b + sag * .6)}Z" fill="{lit}"/>')
        # snow resting on the tier
        sy = apex + (b - apex) * .42
        sw = hw * .42
        cap = (f"M{n(cx)} {n(apex + 1)}L{n(cx + sw)} {n(sy)}"
               f"q{n(-sw * .25)} {n(3)} {n(-sw * .5)} {n(-.5)}"
               f"q{n(-sw * .3)} {n(3.5)} {n(-sw * .55)} {n(1)}"
               f"q{n(-sw * .3)} {n(3)} {n(-sw * .5)} {n(-.5)}"
               f"q{n(-sw * .2)} {n(2)} {n(-sw * .45)} {n(0)}Z")
        parts.append(f'<path d="{cap}" fill="{snow}" fill-opacity="{snow_op}"/>')
        # a thin snow line along the tier's lower edge
        parts.append(f'<path d="M{n(cx + hw * .92)} {n(b - 1)}Q{n(cx + hw * .5)} {n(b - sag - 1.5)} {n(cx + hw * .08)} {n(b + sag * .6 - 1.5)}" '
                     f'fill="none" stroke="{snow}" stroke-opacity="{snow_op * .55}" stroke-width="2" stroke-linecap="round"/>')
    return "".join(parts)


def bare_tree(x, base, h, colour="#0f1233", seed=3):
    rr = random.Random(seed)
    segs = []

    def grow(x0, y0, ang, length, width, depth):
        x1 = x0 + length * math.cos(ang)
        y1 = y0 + length * math.sin(ang)
        bend = rr.uniform(-.18, .18)
        mx = (x0 + x1) / 2 + length * bend * math.cos(ang + math.pi / 2)
        my = (y0 + y1) / 2 + length * bend * math.sin(ang + math.pi / 2)
        segs.append((width, f"M{n(x0)} {n(y0)}Q{n(mx)} {n(my)} {n(x1)} {n(y1)}"))
        if depth == 0:
            return
        k = 3 if depth > 3 and rr.random() < .35 else 2
        spread = rr.uniform(.34, .52)
        for j in range(k):
            a = ang + spread * (j - (k - 1) / 2) * (2 / max(k - 1, 1)) + rr.uniform(-.12, .12)
            grow(x1, y1, a, length * rr.uniform(.64, .78), max(width * .66, .6), depth - 1)

    grow(x, base, -math.pi / 2 + rr.uniform(-.05, .05), h * .34, h * .045, 6)
    # bucket by width to keep the markup small
    by_w = {}
    for w, d in segs:
        key = n(max(round(w * 2) / 2, .6))
        by_w.setdefault(key, []).append(d)
    g = [f'<g fill="none" stroke="{colour}" stroke-linecap="round">']
    for w, ds in sorted(by_w.items(), key=lambda kv: -float(kv[0])):
        g.append(f'<path stroke-width="{w}" d="{"".join(ds)}"/>')
    g.append("</g>")
    return "".join(g)


# small pines further back
back_pines = [(38, 344, 74, 38), (214, 342, 82, 42), (292, 344, 64, 34),
              (1128, 342, 76, 40), (1262, 343, 82, 42), (1392, 342, 70, 36)]
add('  <g opacity=".85">' + "".join(pine(*p, dark="#131639", lit="#1b1f4b", snow="#c9cfeb", snow_op=.7) for p in back_pines) + "</g>")

# bare trees behind the building
add("  " + bare_tree(346, 352, 190, seed=5))
add("  " + bare_tree(1004, 352, 170, seed=9))

front_pines_l = [(74, 354, 122, 64), (136, 356, 156, 80), (198, 354, 104, 56), (256, 356, 138, 70), (316, 355, 100, 52)]
front_pines_r = [(1112, 355, 108, 56), (1170, 356, 150, 76), (1232, 354, 112, 58), (1296, 356, 142, 72), (1360, 355, 106, 56), (1418, 354, 128, 66)]


# ------------------------------------------------------------------ school
# Discovery Elementary's colours are green and white (blue and gold are Williamston's).
GREEN, GREEN_DEEP, GREEN_LIT = "#1d6b46", "#134a31", "#2f8a5c"


def roof_snow(x0, x1, y, rise=6):
    rr = random.Random(int(x0 * 7 + x1))
    pts = []
    x = x0 - 3
    while x < x1 + 3:
        pts.append((x, y - rise * rr.uniform(.45, 1)))
        x += rr.uniform(14, 26)
    pts.append((x1 + 3, y - rise * .4))
    top = smooth(pts)
    drips = []
    x = x1 + 3
    while x > x0 - 3:
        step = rr.uniform(6, 14)
        if rr.random() < .22:
            k = rr.uniform(2.2, 4.8)
            drips.append(f"L{n(x)} {n(y + 3)}l-.9 {n(k)}l-.9 {n(-k)}")
        x -= step
        drips.append(f"L{n(max(x, x0 - 3))} {n(y + rr.uniform(2, 4))}")
    return (f'<path d="M{n(pts[0][0])} {n(y + 2)}L{n(pts[0][0])} {n(pts[0][1])}{top}'
            f'L{n(x1 + 3)} {n(y + 2)}{"".join(drips)}Z" fill="#e6e9f8"/>')


def window(x, y, w, h, deco=None, dim=False):
    g = []
    if not dim:
        g.append(f'<rect x="{n(x - 12)}" y="{n(y - 10)}" width="{n(w + 24)}" height="{n(h + 22)}" rx="12" fill="#ffb24a" opacity=".42" filter="url(#sc-blur)"/>')
    g.append(f'<rect x="{n(x - 2.5)}" y="{n(y - 2.5)}" width="{n(w + 5)}" height="{n(h + 5)}" rx="3" fill="#0a0c22"/>')
    dim_attr = ' opacity=".62"' if dim else ""
    g.append(f'<rect class="win" x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="1.5" fill="url(#sc-win)"{dim_attr}/>')
    ink = "#8c4a10"
    if deco == "kids":
        # children singing, arms up, seen from behind the glass
        for i, (dx, s) in enumerate([(.24, 1), (.55, .9), (.82, 1.05)]):
            cx = x + w * dx
            by = y + h
            hr = 3.3 * s
            hy = by - 13 * s
            arm = -1 if i % 2 else 1
            g.append(f'<g fill="{ink}" fill-opacity=".5" stroke="{ink}" stroke-opacity=".5" stroke-linecap="round">'
                     f'<circle cx="{n(cx)}" cy="{n(hy)}" r="{n(hr)}" stroke="none"/>'
                     f'<path d="M{n(cx - 6 * s)} {n(by)}Q{n(cx - 6 * s)} {n(hy + 4.5 * s)} {n(cx)} {n(hy + 4.5 * s)}Q{n(cx + 6 * s)} {n(hy + 4.5 * s)} {n(cx + 6 * s)} {n(by)}Z" stroke="none"/>'
                     f'<path d="M{n(cx - 4.5 * s)} {n(hy + 6 * s)}l{n(-2.5 * s)} {n(-10 * s)}M{n(cx + 4.5 * s)} {n(hy + 6 * s)}l{n(2.5 * s * arm)} {n(-10 * s)}" fill="none" stroke-width="{n(2 * s)}"/></g>')
    elif deco == "art":
        # construction-paper drawings taped to the glass
        papers = [(.1, .1, "#e2603f", -6), (.58, .14, "#7fa8d9", 5), (.16, .56, "#2f8c7e", 4)]
        for px, py, c, rot in papers:
            ax, ay = x + w * px, y + h * py
            pw, ph = w * .3, h * .24
            g.append(f'<g transform="rotate({rot} {n(ax + pw / 2)} {n(ay + ph / 2)})">'
                     f'<rect x="{n(ax)}" y="{n(ay)}" width="{n(pw)}" height="{n(ph)}" rx=".8" fill="{c}" opacity=".85"/>'
                     f'<circle cx="{n(ax + pw * .35)}" cy="{n(ay + ph * .38)}" r="{n(ph * .18)}" fill="#fff4d6" opacity=".9"/>'
                     f'<path d="M{n(ax + pw * .15)} {n(ay + ph * .8)}q{n(pw * .35)} {n(-ph * .35)} {n(pw * .7)} 0" fill="none" stroke="#fff4d6" stroke-opacity=".85" stroke-width="1"/></g>')
    elif deco == "stars":
        # a garland of paper stars across the top
        g.append(f'<path d="M{n(x + 1)} {n(y + 4)}Q{n(x + w / 2)} {n(y + 13)} {n(x + w - 1)} {n(y + 4)}" fill="none" stroke="{ink}" stroke-opacity=".45" stroke-width=".8"/>')
        for i, t in enumerate((.18, .4, .62, .84)):
            sx = x + w * t
            sy = y + 4 + 9 * (1 - (2 * t - 1) ** 2) + 3.5
            pts = []
            for k in range(10):
                rad = 3.6 if k % 2 == 0 else 1.6
                a = -math.pi / 2 + k * math.pi / 5
                pts.append(f"{n(sx + rad * math.cos(a))} {n(sy + rad * math.sin(a))}")
            col = ["#e2603f", "#fff6e0", "#7fa8d9", "#fff6e0"][i]
            g.append(f'<path d="M{"L".join(pts)}Z" fill="{col}" opacity=".9"/>')
    # mullions
    g.append(f'<path d="M{n(x + w / 2)} {n(y)}V{n(y + h)}M{n(x)} {n(y + h * .4)}H{n(x + w)}" stroke="#0a0c22" stroke-width="2" stroke-opacity=".9"/>')
    # snow on the sill
    g.append(f'<rect x="{n(x - 4.5)}" y="{n(y + h + 2)}" width="{n(w + 9)}" height="3.5" rx="1.75" fill="#e6e9f8"/>')
    return "".join(g)


def bush(cx, base, s=1):
    rr = random.Random(int(cx))
    g = [f'<g>']
    blobs = [(-9, 0, 8), (0, -3, 10), (9, 0, 8)]
    for dx, dy, r in blobs:
        r *= s * rr.uniform(.9, 1.1)
        g.append(f'<circle cx="{n(cx + dx * s)}" cy="{n(base - r * .55 + dy * s)}" r="{n(r)}" fill="#0c0f2b"/>')
    for dx, dy, r in blobs:
        r *= s
        g.append(f'<ellipse cx="{n(cx + dx * s - 1)}" cy="{n(base - r * 1.25 + dy * s)}" rx="{n(r * .7)}" ry="{n(r * .32)}" fill="#dfe3f6"/>')
    g.append("</g>")
    return "".join(g)


school = ['  <g class="school">']
# gym block
school.append('<rect x="372" y="240" width="116" height="112" fill="url(#sc-wall2)"/>')
school.append('<rect x="372" y="240" width="116" height="112" fill="url(#sc-brick)"/>')
school.append(f'<rect x="366" y="230" width="128" height="12" rx="3" fill="{GREEN}"/><rect x="366" y="239" width="128" height="3" fill="{GREEN_DEEP}"/>')
school.append(roof_snow(366, 494, 230, 7))
# rooftop unit
school.append('<rect x="862" y="252" width="44" height="12" rx="2" fill="#0c0e27"/>' + roof_snow(862, 906, 252, 4))
# main wing
school.append('<rect x="474" y="266" width="500" height="86" fill="url(#sc-wall)"/>')
school.append('<rect x="474" y="266" width="500" height="86" fill="url(#sc-brick)"/>')
school.append(f'<rect x="468" y="258" width="512" height="11" rx="3" fill="{GREEN}"/><rect x="468" y="266" width="512" height="3" fill="{GREEN_DEEP}"/>')
school.append(roof_snow(468, 980, 258, 6))
# entrance block
school.append('<rect x="660" y="246" width="120" height="106" fill="url(#sc-wall2)"/>')
school.append('<rect x="660" y="246" width="120" height="106" fill="url(#sc-brick)"/>')
school.append(f'<rect x="652" y="237" width="136" height="12" rx="3" fill="{GREEN}"/><rect x="652" y="246" width="136" height="3" fill="{GREEN_DEEP}"/>')
school.append(roof_snow(652, 788, 237, 8))
# backlit letters
school.append(f'<rect x="668" y="258" width="104" height="19" rx="2.5" fill="{GREEN}" stroke="#f4f7f2" stroke-opacity=".85" stroke-width="1.2"/>')
school.append('<text x="720" y="271.5" text-anchor="middle" font-family="Figtree, system-ui, sans-serif" font-size="11" font-weight="800" '
              'letter-spacing="2.4" fill="#fff" style="filter:drop-shadow(0 0 2.5px rgba(255,255,255,.55))">DISCOVERY</text>')
# gym clerestory
for i in range(4):
    school.append(window(386 + i * 25, 252, 16, 12, dim=True))
# gym tall window pair (lit, a hallway beyond)
school.append(window(398, 294, 22, 36))
school.append(window(440, 294, 22, 36, deco="stars"))
# cafeteria windows
for x, deco in zip((492, 548, 604), ("art", "kids", "stars")):
    school.append(window(x, 282, 40, 50, deco))
for x, deco in zip((798, 854, 910), ("kids", "stars", "art")):
    school.append(window(x, 282, 40, 50, deco))
# foundation
school.append('<rect x="366" y="347" width="614" height="5" fill="#080a1f"/>')
# canopy glow + doors
school.append('<ellipse cx="720" cy="318" rx="78" ry="30" fill="#ffb24a" opacity=".5" filter="url(#sc-blur)"/>')
school.append(f'<rect x="684" y="296" width="72" height="56" rx="2" fill="{GREEN_DEEP}"/>')
school.append('<rect class="win" x="687" y="299" width="32" height="53" rx="1" fill="url(#sc-door)"/>')
school.append('<rect class="win" x="721" y="299" width="32" height="53" rx="1" fill="url(#sc-door)"/>')
# someone waiting inside to say hello
school.append('<g fill="#8c4a10" fill-opacity=".42"><circle cx="733" cy="318" r="4.6"/>'
              '<path d="M725 352v-20q0-6.5 8-6.5t8 6.5v20Z"/>'
              '<path d="M741 330l6-10" stroke="#8c4a10" stroke-opacity=".42" stroke-width="2.6" stroke-linecap="round"/></g>')
school.append('<path d="M703 299v53M737 299v53M687 316h66" stroke="#0a0c22" stroke-width="1.6" stroke-opacity=".7"/>')
school.append('<rect x="714" y="322" width="2" height="9" rx="1" fill="#0a0c22"/><rect x="724" y="322" width="2" height="9" rx="1" fill="#0a0c22"/>')
# canopy
school.append(f'<rect x="644" y="284" width="152" height="9" rx="2" fill="{GREEN}"/><rect x="644" y="290" width="152" height="3" fill="{GREEN_DEEP}"/>' + roof_snow(644, 796, 284, 5))
school.append(f'<rect x="652" y="293" width="3.5" height="59" fill="{GREEN_DEEP}"/><rect x="784.5" y="293" width="3.5" height="59" fill="{GREEN_DEEP}"/>')
# bushes along the foundation
for bx in (478, 532, 590, 640, 800, 858, 914, 962):
    school.append(bush(bx, 355, .85))
school.append("</g>")
add("".join(school))

# flagpole
add('  <g><rect x="1060" y="186" width="3" height="170" fill="#0b0d26"/><circle cx="1061.5" cy="185" r="2.8" fill="#dfe3f6" opacity=".85"/>'
    f'<path class="flag" d="M1063 191c10-4 18 3 30-1v21c-12 4-20-3-30 1Z" fill="{GREEN_LIT}"/>'
    # slab-serif block W for Williamston
    '<path d="M-1 0L4.4 0L4.4 1.5L3.67 1.5L4.6 6.6L6 2.4L8 2.4L9.4 6.6L10.33 1.5L9.6 1.5L9.6 0L15 0L15 1.5L13.68 1.5L11.4 12L8.4 12L7 7.4L5.6 12L2.6 12L0.33 1.5L-1 1.5Z" fill="#f4f7f2" transform="rotate(-2 1078 201) translate(1078 201) scale(.95) translate(-7 -6)"/></g>')

# front pines
add("  <g>" + "".join(pine(*p) for p in front_pines_l + front_pines_r) + "</g>")

# ------------------------------------------------------------------- snow
back = wave(0, W, 349, [(3, 70, 0), (2, 23, 1)], step=20)
add(f'  <path d="{band(back)}" fill="url(#sc-snow-back)"/>')

# lamp post by the gym
add('  <g><ellipse cx="432" cy="330" rx="34" ry="34" fill="#ffcf7a" opacity=".38" filter="url(#sc-blur)"/>'
    '<rect x="430.5" y="318" width="3" height="60" fill="#0b0d26"/>'
    '<path d="M425 318h14l-2.5-8h-9Z" fill="#0b0d26"/><rect x="428" y="311" width="8" height="6" rx="1" fill="#fff1c9"/>'
    '<path d="M423.5 309.5h17" stroke="#e6e9f8" stroke-width="3" stroke-linecap="round"/></g>')

mid = wave(0, W, 364, [(5, 130, 1), (2, 41, 0)], step=24)
add(f'  <path d="{band(mid)}" fill="url(#sc-snow-mid)"/>')

# pools of window light on the snow
for cx in (412, 452, 512, 568, 624, 818, 874, 930):
    add(f'  <ellipse cx="{cx}" cy="368" rx="36" ry="7" fill="url(#sc-pool)"/>')
add('  <ellipse cx="432" cy="382" rx="46" ry="9" fill="url(#sc-pool)"/>')

# the cleared, lit walk from the door
add('  <path d="M688 352h64l86 88H602Z" fill="url(#sc-path)"/>')
add('  <path d="M688 352 602 440M752 352l86 88" stroke="#eef0fa" stroke-width="3" stroke-linecap="round" opacity=".55"/>')
add('  <ellipse cx="720" cy="372" rx="120" ry="22" fill="url(#sc-pool)"/>')

# footprints wandering in from the left
fp = []
for i in range(14):
    t = i / 13
    # quadratic bezier (430,436) -> (560,392) -> (664,404)
    x = (1 - t) ** 2 * 430 + 2 * (1 - t) * t * 560 + t * t * 664
    y = (1 - t) ** 2 * 436 + 2 * (1 - t) * t * 392 + t * t * 404
    side = 3 if i % 2 else -3
    s = 1.25 - .4 * t
    fp.append(f'<ellipse cx="{n(x)}" cy="{n(y + side * .5)}" rx="{n(2.6 * s)}" ry="{n(1.3 * s)}"/>')
add(f'  <g fill="#a8b0d8" opacity=".75">{"".join(fp)}</g>')


# ---------------------------------------------------------------- people
def person(x, feet, h, kind, step=0, hand=None, backpack=False, hat="#141634"):
    """A walker seen side-on, heading right toward the door."""
    kid = kind == "kid"
    r = h * (.125 if kid else .095)
    hy = feet - h + r
    sw = h * (.36 if kid else .27)
    neck = hy + r * 1.05
    hem = feet - h * (.3 if kid else .34)
    hw = sw * 1.12
    body = (f"M{n(x - sw / 2)} {n(neck + sw * .35)}Q{n(x - sw / 2)} {n(neck)} {n(x)} {n(neck)}"
            f"Q{n(x + sw / 2)} {n(neck)} {n(x + sw / 2)} {n(neck + sw * .35)}"
            f"L{n(x + hw / 2)} {n(hem)}Q{n(x)} {n(hem + 2)} {n(x - hw / 2)} {n(hem)}Z")
    lw = h * .085
    legs = (f'<rect x="{n(x - lw - 1 + step)}" y="{n(hem - 2)}" width="{n(lw)}" height="{n(feet - hem + 1)}" rx="{n(lw / 2)}"/>'
            f'<rect x="{n(x + 1 - step)}" y="{n(hem - 2)}" width="{n(lw)}" height="{n(feet - hem + 1)}" rx="{n(lw / 2)}"/>'
            f'<ellipse cx="{n(x - lw / 2 - 1 + step + 1.2)}" cy="{n(feet)}" rx="{n(lw * .8)}" ry="{n(lw * .45)}"/>'
            f'<ellipse cx="{n(x + 1 + lw / 2 - step + 1.2)}" cy="{n(feet)}" rx="{n(lw * .8)}" ry="{n(lw * .45)}"/>')
    head = f'<circle cx="{n(x)}" cy="{n(hy)}" r="{n(r)}"/>'
    # knit hat with a pom-pom
    beanie = (f'<path d="M{n(x - r * 1.05)} {n(hy - r * .05)}A{n(r * 1.05)} {n(r * 1.1)} 0 0 1 {n(x + r * 1.05)} {n(hy - r * .05)}Z"/>'
              f'<circle cx="{n(x - r * .1)}" cy="{n(hy - r * 1.2)}" r="{n(r * .42)}"/>')
    parts = [head, beanie, f'<path d="{body}"/>', legs]
    if backpack:
        bw, bh = sw * .42, (hem - neck) * .62
        parts.append(f'<rect x="{n(x - sw / 2 - bw * .7)}" y="{n(neck + sw * .2)}" width="{n(bw)}" height="{n(bh)}" rx="{n(bw * .35)}"/>')
    arm_w = h * (.08 if kid else .07)
    sx, sy = x + sw * .3, neck + sw * .3
    if hand:
        parts.append(f'<path d="M{n(sx)} {n(sy)}L{n(hand[0])} {n(hand[1])}" fill="none" stroke-width="{n(arm_w)}" stroke-linecap="round" stroke="currentColor"/>')
    else:
        parts.append(f'<path d="M{n(sx)} {n(sy)}L{n(sx + h * .06)} {n(hem - h * .02)}" fill="none" stroke-width="{n(arm_w)}" stroke-linecap="round" stroke="currentColor"/>')
    return "".join(parts)


def scarf(x, feet, h):
    r = h * .095
    neck = feet - h + r + r * 1.05
    return (f'<path d="M{n(x - 5)} {n(neck + 1)}q5 2.4 10 0" fill="none" stroke="#c4553a" stroke-width="3" stroke-linecap="round"/>'
            f'<path d="M{n(x - 4)} {n(neck + 2)}l-2.2 9" fill="none" stroke="#c4553a" stroke-width="2.6" stroke-linecap="round"/>')


def walker(markup, delay_cls="", extra=""):
    # warm rim light from the doorway: the same silhouette, nudged toward the light, drawn behind
    return (f'<g class="walker{delay_cls}">'
            f'<g fill="#ffc46b" color="#ffc46b" opacity=".85" transform="translate(1.6 -.8)">{markup}</g>'
            f'<g fill="#161838" color="#161838">{markup}</g>{extra}</g>')


# parent holding a child's hand, a second child just behind
adult_x, adult_feet, adult_h = 676, 404, 62
kid1_x, kid1_feet, kid1_h = 700, 402, 40
kid2_x, kid2_feet, kid2_h = 648, 409, 38
kid1_hand = (kid1_x - 3, kid1_feet - kid1_h * .5)
add("  " + walker(person(kid2_x, kid2_feet, kid2_h, "kid", step=1.5, backpack=True)))
add("  " + walker(person(adult_x, adult_feet, adult_h, "adult", step=2, hand=kid1_hand), " walker--b", scarf(adult_x, adult_feet, adult_h)))
add("  " + walker(person(kid1_x, kid1_feet, kid1_h, "kid", step=-1.2, backpack=True, hand=(kid1_x - 7, kid1_hand[1] + 1)), " walker--c"))

# front drift, fading into the page
front = wave(0, W, 416, [(6, 160, .6), (3, 53, 2)], step=24)
add(f'  <path d="{band(front)}" fill="url(#sc-snow-front)"/>')
# the page itself rises as the last snowbank
edge = wave(0, W, 431, [(4, 210, 2.2), (2, 61, .3)], step=24)
add(f'  <path class="scene-edge" d="{band(edge, H + 2)}"/>')

add("</svg>")
print("\n".join(out))
