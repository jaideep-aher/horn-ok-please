"""Paint or stencil scene text onto a road image with perspective and wear.

The plate is rendered with HarfBuzz shaping (Pillow RAQM) so Devanagari
conjuncts stay intact, then warped onto a quadrilateral. Weathering is
deterministic for a given seed.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from PIL import Image, ImageDraw

from hornok.fontsutil import font_kind_for_text, load_font

Quad = Sequence[Sequence[float]]


def perspective_coeffs(
    src: Sequence[Sequence[float]], dst: Sequence[Sequence[float]]
) -> list[float]:
    """PIL perspective coefficients mapping destination pixels into ``src``."""
    if len(src) != 4 or len(dst) != 4:
        raise ValueError("perspective warp expects 4 source and 4 destination points")
    rows: list[list[float]] = []
    rhs: list[float] = []
    for (x, y), (u, v) in zip(dst, src, strict=True):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        rhs.append(u)
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        rhs.append(v)
    sol = np.linalg.solve(np.asarray(rows, dtype=np.float64), np.asarray(rhs, dtype=np.float64))
    return [float(v) for v in sol]


def _draw_text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, font, fill) -> None:
    kwargs = {"language": "mr"}
    if any("\u0600" <= ch <= "\u06ff" for ch in text):
        kwargs = {"language": "ur", "direction": "rtl"}
    try:
        draw.text(xy, text, font=font, fill=fill, **kwargs)
    except TypeError:
        draw.text(xy, text, font=font, fill=fill)


def render_plate(
    text: str,
    *,
    style: str = "painted",
    ink: tuple[int, int, int] = (28, 16, 12),
    width: int = 900,
    seed: int = 0,
) -> Image.Image:
    """Return an RGBA plate of shaped text. ``style`` is ``painted`` or ``stencil``."""
    if style not in {"painted", "stencil"}:
        raise ValueError(f"unknown style {style!r}")
    lines = text.split("\n") or [""]
    rng = np.random.default_rng(seed)
    probe = load_font(font_kind_for_text(text), 80)
    longest = max((probe.getlength(line) for line in lines), default=1.0)
    size = int(max(18, min(160, 80 * (width * 0.86) / max(longest, 1.0))))
    # Mixed-script plates can contain a Devanagari line and a Latin line.
    line_fonts = [load_font(font_kind_for_text(line), size) for line in lines]
    line_gap = int(size * 1.2)
    pad = int(size * 0.35)
    height = pad * 2 + line_gap * len(lines)
    plate = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(plate)
    outline = tuple(max(0, c - 40) for c in ink)
    for i, (line, line_font) in enumerate(zip(lines, line_fonts, strict=True)):
        line_w = line_font.getlength(line)
        x = (width - line_w) / 2 + float(rng.uniform(-2.0, 2.0))
        y = pad + i * line_gap + float(rng.uniform(-1.5, 1.5))
        if style == "painted":
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                _draw_text(draw, (x + dx, y + dy), line, line_font, outline + (255,))
        _draw_text(draw, (x, y), line, line_font, ink + (255,))
    if style == "painted":
        plate = _wobble(plate, amplitude=1.6, seed=seed)
    else:
        plate = _stencil_breaks(plate, seed=seed)
    return plate


def _wobble(plate: Image.Image, amplitude: float, seed: int) -> Image.Image:
    arr = np.asarray(plate)
    out = np.zeros_like(arr)
    phase = float(np.random.default_rng(seed).uniform(0, math.tau))
    for y in range(arr.shape[0]):
        shift = int(round(amplitude * math.sin(y / 17.0 + phase)))
        out[y] = np.roll(arr[y], shift, axis=0)
    return Image.fromarray(out, "RGBA")


def _stencil_breaks(plate: Image.Image, seed: int) -> Image.Image:
    arr = np.array(plate)
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    bridges = ((yy // 14) % 5 == 0) & ((xx // 5) % 2 == 0)
    arr[bridges, 3] = 0
    rng = np.random.default_rng(seed + 3)
    speck = rng.random((h, w)) > 0.97
    # Spray only near existing paint.
    alpha = arr[..., 3] > 0
    near = np.zeros_like(alpha)
    near[1:] |= alpha[:-1]
    near[:-1] |= alpha[1:]
    arr[speck & near & ~alpha, 0:3] = arr[..., 0:3].mean(axis=(0, 1)).astype(np.uint8)
    arr[speck & near & ~alpha, 3] = 140
    return Image.fromarray(arr, "RGBA")


def weather(plate: Image.Image, amount: float, seed: int) -> Image.Image:
    """Fade, scratch, and speckle. ``amount`` is 0 (clean) to 1 (heavy)."""
    amount = float(min(1.0, max(0.0, amount)))
    if amount <= 0:
        return plate
    arr = np.array(plate)
    rng = np.random.default_rng(seed + 11)
    fade = rng.uniform(1.0 - 0.55 * amount, 1.0, size=arr.shape[:2]).astype(np.float32)
    arr[..., 3] = np.clip(arr[..., 3].astype(np.float32) * fade, 0, 255).astype(np.uint8)
    h, w = arr.shape[:2]
    n_scratches = int(4 + 10 * amount)
    for _ in range(n_scratches):
        x0 = int(rng.integers(0, w))
        y0 = int(rng.integers(0, h))
        x1 = int(np.clip(x0 + rng.integers(-w // 3, w // 3), 0, w - 1))
        y1 = int(np.clip(y0 + rng.integers(-4, 5), 0, h - 1))
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        xs = np.linspace(x0, x1, steps).astype(int)
        ys = np.linspace(y0, y1, steps).astype(int)
        arr[ys, xs, 3] = 0
    return Image.fromarray(arr, "RGBA")


def composite_attack(
    base: Image.Image,
    text: str,
    quad: Quad,
    *,
    style: str = "painted",
    weathering: float = 0.28,
    seed: int = 0,
    ink: tuple[int, int, int] = (28, 16, 12),
    absorb: float = 0.12,
) -> Image.Image:
    """Return a copy of ``base`` with ``text`` painted onto ``quad`` (TL, TR, BR, BL)."""
    if len(quad) != 4:
        raise ValueError("quad must have 4 points in order TL, TR, BR, BL")
    rgb = base.convert("RGB")
    plate = weather(
        render_plate(text, style=style, ink=ink, seed=seed),
        weathering,
        seed,
    )
    src = [(0, 0), (plate.width, 0), (plate.width, plate.height), (0, plate.height)]
    coeffs = perspective_coeffs(src, quad)
    warped = plate.transform(
        rgb.size,
        Image.Transform.PERSPECTIVE,
        coeffs,
        Image.Resampling.BICUBIC,
    )
    base_arr = np.asarray(rgb).astype(np.float32)
    over = np.asarray(warped).astype(np.float32)
    alpha = over[..., 3:4] / 255.0
    paint = over[..., :3]
    out = base_arr * (1.0 - alpha) + paint * alpha
    out *= 1.0 - absorb * alpha
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
