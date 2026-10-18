"""Blur faces and plates on copies that the site and the poster show.

The detector is OpenCV 4.10 Haar cascades (frontal face, profile face, Russian
plate) plus a contour heuristic for plates the cascade misses. OpenCV 5 has
no CascadeClassifier. A miss is possible. The model-facing stimuli are not blurred.
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


def _expand(box: list[int], width: int, height: int, pad: float) -> list[int]:
    x, y, w, h = box
    dx, dy = int(w * pad), int(h * pad)
    return [
        max(0, x - dx),
        max(0, y - dy),
        min(width, x + w + dx),
        min(height, y + h + dy),
    ]


def detect_regions(image: Image.Image, avoid: list[list[float]] | None = None) -> list[list[int]]:
    """Pixel boxes to blur. Plate boxes that mostly cover a text box are dropped."""
    import cv2

    rgb = np.asarray(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    height, width = gray.shape
    cascades = _cascades()
    boxes: list[list[int]] = []
    for name in ("face", "profile"):
        cascade = cascades.get(name)
        if cascade is None:
            continue
        found = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(24, 24))
        for x, y, w, h in found:
            boxes.append(_expand([int(x), int(y), int(w), int(h)], width, height, 0.35))
    plate = cascades.get("plate")
    if plate is not None:
        found = plate.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 16))
        for x, y, w, h in found:
            boxes.append(_expand([int(x), int(y), int(w), int(h)], width, height, 0.15))
    boxes.extend(_contour_plates(gray, avoid or []))
    return _dedupe(boxes)


def _contour_plates(gray: np.ndarray, avoid: list[list[float]]) -> list[list[int]]:
    import cv2

    height, width = gray.shape
    y0 = int(height * 0.55)
    crop = gray[y0:, :]
    edges = cv2.Canny(cv2.bilateralFilter(crop, 7, 40, 40), 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    frame = float(width * height)
    found = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h < 10 or w < 24:
            continue
        ratio = w / float(h)
        if ratio < 2.0 or ratio > 6.5:
            continue
        area = w * h
        if area < frame * 0.0015 or area > frame * 0.03:
            continue
        box = [int(x), int(y0 + y), int(x + w), int(y0 + y + h)]
        if _overlaps_text(box, avoid):
            continue
        found.append(box)
    return found


def _overlaps_text(box: list[int], avoid: list[list[float]]) -> bool:
    area = max(1, (box[2] - box[0]) * (box[3] - box[1]))
    for other in avoid:
        x0 = max(box[0], other[0])
        y0 = max(box[1], other[1])
        x1 = min(box[2], other[2])
        y1 = min(box[3], other[3])
        if x1 > x0 and y1 > y0 and (x1 - x0) * (y1 - y0) / area > 0.5:
            return True
    return False


def _dedupe(boxes: list[list[int]]) -> list[list[int]]:
    kept: list[list[int]] = []
    for box in boxes:
        if any(_iou(box, prior) > 0.5 for prior in kept):
            continue
        kept.append(box)
    return kept


def _iou(a: list[int], b: list[int]) -> float:
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


def blur_regions(image: Image.Image, boxes: list[list[int]]) -> Image.Image:
    out = image.convert("RGB").copy()
    for box in boxes:
        crop = out.crop(box)
        short = max(1, min(crop.size))
        # Two pixels on the short side. A plate character cannot survive that.
        cells = max(1, short // 2)
        small = crop.resize(
            (max(1, crop.width // cells), max(1, crop.height // cells)),
            Image.Resampling.BOX,
        )
        pixel = small.resize(crop.size, Image.Resampling.NEAREST)
        out.paste(pixel, box)
    return out


def blurred_copy(
    image: Image.Image,
    avoid: list[list[float]] | None = None,
) -> tuple[Image.Image, list[list[int]]]:
    boxes = detect_regions(image, avoid)
    return blur_regions(image, boxes), boxes
