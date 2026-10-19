"""Redact faces and plates on copies that the site and the poster show.

The detector is OpenCV 4.10 Haar cascades (frontal face, profile face, Russian
plate) plus a bright-background text-line finder for plates the cascade misses.
OpenCV 5 has no CascadeClassifier. A miss is possible. Detected regions are
painted as a solid mean color, expanded past the box, so a character cannot
remain inside the box. The model-facing stimuli are not redacted.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

CASCADE_DIR = Path(__file__).resolve().parents[2] / "eval" / "photos" / "cascades"


def _cascades():
    import cv2

    files = {
        "face": CASCADE_DIR / "haarcascade_frontalface_default.xml",
        "profile": CASCADE_DIR / "haarcascade_profileface.xml",
        "plate": CASCADE_DIR / "haarcascade_russian_plate_number.xml",
    }
    loaded = {}
    for name, path in files.items():
        if path.is_file():
            cascade = cv2.CascadeClassifier(str(path))
            if not cascade.empty():
                loaded[name] = cascade
    return loaded


def _expand(box: list[int], width: int, height: int, pad: float, minimum: int) -> list[int]:
    x, y, w, h = box
    dx = max(minimum, int(w * pad))
    dy = max(minimum, int(h * pad))
    return [
        max(0, x - dx),
        max(0, y - dy),
        min(width, x + w + dx),
        min(height, y + h + dy),
    ]


def detect_regions(image: Image.Image, avoid: list[list[float]] | None = None) -> list[list[int]]:
    """Pixel boxes to paint over. ``avoid`` is kept for callers; plates are not dropped for it."""
    del avoid
    found = detect_labeled(image)
    return [row["box"] for row in found]


def detect_labeled(image: Image.Image) -> list[dict]:
    """Boxes tagged ``face`` or ``plate``. Plate entries are what the review list counts."""
    import cv2

    rgb = np.asarray(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    height, width = gray.shape
    cascades = _cascades()
    labeled: list[dict] = []
    for name in ("face", "profile"):
        cascade = cascades.get(name)
        if cascade is None:
            continue
        found = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(20, 20))
        for x, y, w, h in found:
            labeled.append(
                {
                    "kind": "face",
                    "box": _expand([int(x), int(y), int(w), int(h)], width, height, 0.45, 12),
                }
            )
    plate = cascades.get("plate")
    if plate is not None:
        found = plate.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(36, 12))
        for x, y, w, h in found:
            if h > height * 0.12 or w > width * 0.55:
                continue
            if w / float(h) < 1.6 or w / float(h) > 7.5:
                continue
            labeled.append(
                {
                    "kind": "plate",
                    "box": _expand([int(x), int(y), int(w), int(h)], width, height, 0.35, 14),
                }
            )
    for box in _text_line_plates(gray):
        labeled.append({"kind": "plate", "box": _expand(box, width, height, 0.28, 18)})
    return _dedupe_labeled(labeled)


def _text_line_plates(gray: np.ndarray) -> list[list[int]]:
    """Horizontal dark glyphs sitting on a bright patch. Rear plates, not tailgate poetry."""
    import cv2

    height, width = gray.shape
    blackhat = cv2.morphologyEx(
        gray, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5))
    )
    bright = cv2.dilate((gray > 140).astype(np.uint8), np.ones((11, 25), np.uint8))
    ink = ((blackhat > 28) & bright.astype(bool)).astype(np.uint8) * 255
    ink[: int(height * 0.45)] = 0
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 7))
    closed = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    frame = float(width * height)
    found: list[list[int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h < 10 or w < 40:
            continue
        ratio = w / float(h)
        if ratio < 1.5 or ratio > 9.0:
            continue
        area = w * h
        if area < frame * 0.0004 or area > frame * 0.04:
            continue
        if h > height * 0.09 or w > width * 0.5:
            continue
        found.append([int(x), int(y), int(w), int(h)])
    return found


def _dedupe_labeled(rows: list[dict]) -> list[dict]:
    kept: list[dict] = []
    for row in rows:
        if any(_iou(row["box"], prior["box"]) > 0.45 for prior in kept):
            continue
        kept.append(row)
    return kept


def _iou(a: list[int], b: list[int]) -> float:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


def blur_regions(image: Image.Image, boxes: list[list[int]]) -> Image.Image:
    """Paint each box a single mean color."""
    out = image.convert("RGB").copy()
    for box in boxes:
        x0, y0, x1, y1 = (int(v) for v in box)
        if x1 <= x0 or y1 <= y0:
            continue
        crop = np.asarray(out.crop((x0, y0, x1, y1)))
        if crop.size == 0:
            continue
        flat = crop.reshape(-1, 3)
        mean = tuple(int(channel) for channel in flat.sum(axis=0) // flat.shape[0])
        out.paste(mean, (x0, y0, x1, y1))
    return out


def blurred_copy(
    image: Image.Image,
    avoid: list[list[float]] | None = None,
) -> tuple[Image.Image, list[list[int]]]:
    boxes = detect_regions(image, avoid)
    return blur_regions(image, boxes), boxes
