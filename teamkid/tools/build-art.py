"""Regenerates the illustrated school and writes it into the site.

    python3 tools/build-art.py

- index.html: replaces the inline <svg class="hero-scene"> with a fresh one
- assets/school-at-dusk.svg: the round vignette used in the About / Volunteer / Give headers
"""
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
svg = subprocess.run([sys.executable, str(ROOT / "tools/scene.py")],
                     capture_output=True, text=True, check=True).stdout.strip()

# 1. hero scene, inline in index.html
index = ROOT / "index.html"
html, k = re.subn(r'<svg class="hero-scene".*?</svg>', lambda m: svg, index.read_text(), count=1, flags=re.S)
assert k == 1, "hero-scene svg not found in index.html"
index.write_text(html)

# 2. square crop around the entrance, with its own sky, as a standalone file
X, Y, S = 545, 90, 350
v = re.sub(r'<svg class="hero-scene"[^>]*>', f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{X} {Y} {S} {S}">', svg, count=1)
v = re.sub(r'\s*<path class="scene-edge"[^>]*/>', "", v)  # that edge takes the page colour; not wanted here
rr = random.Random(4)
stars = "".join(
    f'<circle cx="{X + rr.uniform(8, S - 8):.1f}" cy="{Y + rr.uniform(6, 150):.1f}" r="{rr.uniform(.5, 1.3):.1f}" fill="#fff" opacity="{rr.uniform(.35, .9):.2f}"/>'
    for _ in range(26))
sky = ('<defs><linearGradient id="vg-sky" x1="0" y1="0" x2="0" y2="1">'
       '<stop offset="0" stop-color="#0c0d24"/><stop offset=".45" stop-color="#1b1d4a"/><stop offset=".72" stop-color="#34306a"/>'
       '<stop offset=".88" stop-color="#6a4a72"/><stop offset="1" stop-color="#8a5560"/></linearGradient>'
       '<radialGradient id="vg-moon"><stop offset=".3" stop-color="#fff3d4" stop-opacity=".5"/><stop offset="1" stop-color="#fff3d4" stop-opacity="0"/></radialGradient>'
       f'<mask id="vg-mm"><rect x="{X}" y="{Y}" width="{S}" height="{S}" fill="#fff"/><circle cx="843" cy="140" r="13" fill="#000"/></mask></defs>'
       f'<rect x="{X}" y="{Y}" width="{S}" height="{S}" fill="url(#vg-sky)"/>{stars}'
       '<circle cx="834" cy="146" r="34" fill="url(#vg-moon)"/><circle cx="834" cy="146" r="14" fill="#fff6e0" mask="url(#vg-mm)"/>')
v = v.replace("  </defs>", "  </defs>\n" + sky, 1)
(ROOT / "assets/school-at-dusk.svg").write_text(v + "\n")
print("wrote index.html hero scene and assets/school-at-dusk.svg")
