"""Noto font lookup. The TTFs ship with the package under the SIL OFL 1.1."""

from __future__ import annotations

from pathlib import Path

from PIL import ImageFont

_PACKAGE_FONTS = Path(__file__).resolve().parent / "fonts"
_SYSTEM_FONTS = Path("/usr/share/fonts/truetype/noto")

_FILES = {
    "deva": "NotoSansDevanagari-Bold.ttf",
    "deva-regular": "NotoSansDevanagari-Regular.ttf",
    "latin": "NotoSans-Bold.ttf",
    "latin-regular": "NotoSans-Regular.ttf",
    "nastaliq": "NotoNastaliqUrdu-Bold.ttf",
}


def font_path(kind: str) -> Path:
    name = _FILES[kind]
    bundled = _PACKAGE_FONTS / name
    if bundled.is_file():
        return bundled
    system = _SYSTEM_FONTS / name
    if system.is_file():
        return system
    raise FileNotFoundError(f"missing font {name}; expected {bundled}")


def load_font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(font_path(kind)), size=size)


def font_kind_for_text(text: str) -> str:
    if any("\u0600" <= ch <= "\u06ff" for ch in text):
        return "nastaliq"
    if any("\u0900" <= ch <= "\u097f" for ch in text):
        return "deva"
    return "latin"
