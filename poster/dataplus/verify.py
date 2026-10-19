"""Print-readiness checks for the poster PDF."""

import collections
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pymupdf

os.chdir(Path(__file__).resolve().parent)
P = sys.argv[1] if len(sys.argv) > 1 else "build/horn-ok-please-poster.pdf"
doc = pymupdf.open(P)
pg = doc[0]
print("pages", len(doc), "rect", pg.rect, "inches", pg.rect.width / 72, pg.rect.height / 72)
sizes = collections.Counter()
small = []
spans = []
for block in pg.get_text("dict")["blocks"]:
    for line in block.get("lines", []):
        for span in line["spans"]:
            text = span["text"].strip()
            if not text:
                continue
            size = round(span["size"], 1)
            sizes[size] += len(text)
            spans.append((size, text, span["bbox"], span["font"]))
            if size < 18:
                small.append((size, text))
print("font sizes (pt: chars):", sorted(sizes.items()))
print("min size", min(sizes), "max size", max(sizes))
print("spans under 18pt:", small[:20] or "none")
for key in ["Horn OK Please", "Why it matters", "What I built", "What I found", "Limits and next"]:
    print(key, sorted({size for size, text, _, _ in spans if text == key}))
# body text share in 24-28 pt
tot = sum(sizes.values())
body = sum(value for key, value in sizes.items() if 24 <= key <= 28)
under = sum(value for key, value in sizes.items() if 18 <= key < 24)
print(f"chars at 24-28pt: {body}/{tot} = {body / tot:.0%}; chars 18-<24pt: {under}")
# margin: any text/image/drawing bbox inside outer 36pt?
margin = 36
bad = []
for _size, text, bb, _font in spans:
    if bb[0] < margin or bb[1] < margin or bb[2] > 1728 - margin or bb[3] > 1728 - margin:
        bad.append(("text", text, bb))
for image in pg.get_image_info():
    bb = image["bbox"]
    if bb[0] < margin or bb[1] < margin or bb[2] > 1728 - margin or bb[3] > 1728 - margin:
        bad.append(("image", bb))
for drawing in pg.get_drawings():
    bb = drawing["rect"]
    if (
        bb.x0 < margin - 0.01
        or bb.y0 < margin - 0.01
        or bb.x1 > 1728 - margin + 0.01
        or bb.y1 > 1728 - margin + 0.01
    ):
        bad.append(("vector", tuple(round(value, 1) for value in bb)))
print("objects intruding into 0.5in margin:", bad[:10] or "none", len(bad))
# raster check of margin (ink = non-white pixel)
pix = pg.get_pixmap(dpi=72)
samples = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)[:, :, :3]
ink = (samples < 250).any(axis=2)
band = ink.copy()
band[margin:-margin, margin:-margin] = False
print("inked pixels in margin band at 72dpi:", int(band.sum()))
# QR decode from a 300dpi render of the PDF
pix = pg.get_pixmap(dpi=300)
samples = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)[:, :, :3]
qrinfo = [
    image
    for image in pg.get_image_info()
    if abs((image["bbox"][2] - image["bbox"][0]) - (image["bbox"][3] - image["bbox"][1])) < 1
]
bb = min(qrinfo, key=lambda image: image["bbox"][2] - image["bbox"][0])["bbox"]
scale = 300 / 72
pad = 40
crop = np.ascontiguousarray(
    samples[
        int(bb[1] * scale) - pad : int(bb[3] * scale) + pad,
        int(bb[0] * scale) - pad : int(bb[2] * scale) + pad,
    ]
)
val, _pts, _ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY))
print("QR placed size in:", round((bb[2] - bb[0]) / 72, 2), "decoded:", repr(val))
