"""Per-element font sizes measured in the PDF. Element boxes come from the DOM (data-el, pt);
every text span in the PDF (PyMuPDF; cross-checked per character with pdfplumber if present) is
assigned to the smallest element box containing its centre. Output: build/fontmap.txt
"""

import collections
import html
import os
import re
import subprocess
from pathlib import Path

import pymupdf

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
P = "build/horn-ok-please-poster.pdf"
dom = subprocess.run(
    [
        os.environ.get("CHROME", "google-chrome"),
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--window-size=2304,2304",
        "--virtual-time-budget=5000",
        "--dump-dom",
        (HERE / "poster.html").as_uri(),
    ],
    capture_output=True,
    text=True,
).stdout
pre = html.unescape(re.search(r'<pre id="measure"[^>]*>(.*?)</pre>', dom, re.S).group(1))
els = []
for line in pre.splitlines():
    if line.startswith("EL\t"):
        _, name, bb = line.split("\t")
        els.append((name, tuple(map(float, bb.split(",")))))
pg = pymupdf.open(P)[0]
agg = collections.defaultdict(lambda: [999, 0, 0, collections.Counter()])
unassigned = []
for block in pg.get_text("rawdict")["blocks"]:
    for line in block.get("lines", []):
        for span in line["spans"]:
            for char in span["chars"]:
                if not char["c"].strip():
                    continue
                x0, y0, x1, y1 = char["bbox"]
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                hit = [
                    (abs((box[2] - box[0]) * (box[3] - box[1])), name)
                    for name, box in els
                    if box[0] - 1 <= cx <= box[2] + 1 and box[1] - 1 <= cy <= box[3] + 1
                ]
                name = min(hit)[1] if hit else "(no tagged element)"
                stats = agg[name]
                size = round(span["size"], 2)
                stats[0] = min(stats[0], size)
                stats[1] = max(stats[1], size)
                stats[2] += 1
                stats[3][size] += 1
                if not hit:
                    unassigned.append(char["c"])
order = [name for name, _ in els]
seen = []
for name in order + ["(no tagged element)"]:
    if name in agg and name not in seen:
        seen.append(name)
lines = [
    "| Element | Min pt | Max pt | Chars | Sizes (pt: chars) |",
    "|---|---|---|---|---|",
]
for name in seen:
    stats = agg[name]
    size_bits = ", ".join(f"{key:g}: {value}" for key, value in sorted(stats[3].items()))
    lines.append(f"| {name} | {stats[0]:g} | {stats[1]:g} | {stats[2]} | {size_bits} |")
out = "\n".join(lines)
if unassigned:
    out += "\n\nUntagged characters: " + repr("".join(unassigned)[:200])
if pdfplumber is not None:
    with pdfplumber.open(P) as pdf:
        sizes = collections.Counter(
            round(char["size"], 2) for char in pdf.pages[0].chars if char["text"].strip()
        )
    listed = ", ".join(f"{key:g}: {value}" for key, value in sorted(sizes.items()))
    out += "\n\npdfplumber per-character sizes (pt: chars): " + listed
else:
    out += "\n\n(pdfplumber not installed)"
open("build/fontmap.txt", "w").write(out + "\n")
print(out)
