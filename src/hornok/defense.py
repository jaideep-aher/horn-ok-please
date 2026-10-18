"""Defenses against instruction-like scene text.

Two deployments are scored:

* ``prompt`` — the image is unchanged and the model receives DEFENSE_PROMPT_V1.
* ``ocr`` — Tesseract (English + Hindi + Marathi) proposes word boxes. Tokens
  other than the regulatory allow-list (STOP, रुको) that look like instructions
  are painted out. The removed strings are appended to the defense prompt.

Regulatory obedience is measured separately so a defense that also hides a real
STOP sign is counted as over-blocking.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

import numpy as np
from PIL import Image, ImageDraw

REGULATORY_RE = re.compile(r"^(?:stop|रुको)$", re.I)
INSTRUCTION_RE = re.compile(
    r"road|clear|brake|ahead|rasta|aage|badho|child|lane|horn|"
    r"रस्ता|मोकळा|पुढे|ब्रेक|थांबा|मुलगा|जा|लावू|नका|मारा",
    re.I,
)
_DEVANAGARI = re.compile(r"[\u0900-\u097F]")


def is_regulatory_token(text: str) -> bool:
    return REGULATORY_RE.match(text.strip()) is not None


def should_mask_token(text: str) -> bool:
    token = text.strip()
    if not token or is_regulatory_token(token):
        return False
    if INSTRUCTION_RE.search(token):
        return True
    if _DEVANAGARI.search(token):
        return True
    return False


def mask_regions(image: Image.Image, boxes: Sequence[dict], pad: int = 4) -> Image.Image:
    """Paint out boxes by copying nearby pixels, so the fill is not a new sign."""
    out = image.convert("RGB").copy()
    arr = np.array(out)
    draw = ImageDraw.Draw(out)
    h, w = arr.shape[:2]
    for box in boxes:
        x0 = max(0, int(box["x"]) - pad)
        y0 = max(0, int(box["y"]) - pad)
        x1 = min(w, int(box["x"]) + int(box["w"]) + pad)
        y1 = min(h, int(box["y"]) + int(box["h"]) + pad)
        if x1 <= x0 or y1 <= y0:
            continue
        ring = _ring_color(arr, x0, y0, x1, y1)
        draw.rectangle((x0, y0, x1, y1), fill=ring)
    return out


def _ring_color(arr: np.ndarray, x0: int, y0: int, x1: int, y1: int) -> tuple[int, int, int]:
    h, w = arr.shape[:2]
    rx0, ry0 = max(0, x0 - 6), max(0, y0 - 6)
    rx1, ry1 = min(w, x1 + 6), min(h, y1 + 6)
    ring = arr[ry0:ry1, rx0:rx1].copy()
    iy0, ix0 = y0 - ry0, x0 - rx0
    iy1, ix1 = iy0 + (y1 - y0), ix0 + (x1 - x0)
    if 0 <= iy0 < iy1 <= ring.shape[0] and 0 <= ix0 < ix1 <= ring.shape[1]:
        ring[iy0:iy1, ix0:ix1] = 0
        mask = np.ones(ring.shape[:2], dtype=bool)
        mask[iy0:iy1, ix0:ix1] = False
        pixels = ring[mask]
    else:
        pixels = ring.reshape(-1, 3)
    if len(pixels) == 0:
        return (128, 128, 128)
    med = np.median(pixels, axis=0)
    return tuple(int(v) for v in med)


# Sparse text: a sign or a tailgate slogan, not a paragraph.
TESSERACT_CONFIG = "--psm 11"


def tesseract_boxes(image: Image.Image, lang: str = "eng+hin+mar") -> list[dict]:
    import pytesseract

    data = pytesseract.image_to_data(
        image, lang=lang, config=TESSERACT_CONFIG, output_type=pytesseract.Output.DICT
    )
    boxes = []
    for i, raw in enumerate(data["text"]):
        text = (raw or "").strip()
        if not text:
            continue
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            conf = -1
        if conf < 40:
            continue
        boxes.append(
            {
                "text": text,
                "conf": conf,
                "x": int(data["left"][i]),
                "y": int(data["top"][i]),
                "w": int(data["width"][i]),
                "h": int(data["height"][i]),
            }
        )
    return boxes


def isolate_instructions(
    image: Image.Image,
    extract: Callable[[Image.Image], list[dict]] | None = None,
) -> tuple[Image.Image, dict]:
    """Mask instruction-like OCR boxes. Regulatory STOP / रुको boxes stay."""
    boxes = (extract or tesseract_boxes)(image)
    masked = [b for b in boxes if should_mask_token(b["text"])]
    kept = [b for b in boxes if is_regulatory_token(b["text"])]
    cleaned = mask_regions(image, masked) if masked else image.convert("RGB")
    report = {
        "boxes": boxes,
        "masked_text": [b["text"] for b in masked],
        "kept_regulatory": [b["text"] for b in kept],
        "transcript": " ".join(b["text"] for b in masked),
    }
    return cleaned, report
