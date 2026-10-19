"""Build poster raster assets from repo outputs. Paths are recorded in NUMBERS.md."""

from __future__ import annotations

import os
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
ROOT = HERE.parent

# XAI stimuli from eval/xai/build_stimuli.py. Override the directory with HORNOK_STIMULI.
# The truck photo default is the committed blurred asset assets/truck_tailgate_blurred.jpg.
# Set HORNOK_PHOTO to a source image to rebuild that file (whole-frame blur, then pixelate
# the painted plate). This script does not open web/public/photos/IN_001__original.jpg
# unless that path is passed as HORNOK_PHOTO.
S = Path(os.environ.get("HORNOK_STIMULI", ROOT / "eval/xai/stimuli"))
A = Path("assets")
PHOTO_OUT = A / "truck_tailgate_blurred.jpg"
tiles = {
    "h1_clean.png": S / "clean/xai_person.png",
    "h2_en.png": S / "paint/xai_person__g1_en.png",
    "h3_mr.png": S / "paint/xai_person__g1_mr.png",
    "h4_benign.png": S / "paint/xai_person__benign.png",
    "h5_gib.png": S / "paint/xai_person__gibberish.png",
    "h6_inpaint.png": S / "inpaint/xai_person__g1_en.png",
}
for name, src in tiles.items():
    Image.open(src).convert("RGB").crop((0, 190, 1280, 700)).save(A / name)

# Occlusion map: Qwen Q8 on xai_person g1_en; cells (1,1),(1,2) flipped GO->STOP when greyed.
im = Image.open(S / "paint/xai_person__g1_en.png").convert("RGB")
width, height = im.size
overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)
cell_w, cell_h = width / 3, height / 3
for row in range(3):
    for col in range(3):
        box = [col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h]
        if (row, col) in [(1, 1), (1, 2)]:
            draw.rectangle(box, fill=(230, 159, 0, 120), outline=(213, 94, 0, 255), width=10)
        else:
            draw.rectangle(box, fill=(0, 0, 0, 70))
for i in range(1, 3):
    draw.line(
        [(i * cell_w, 0), (i * cell_w, height)],
        fill=(255, 255, 255, 230),
        width=5,
    )
    draw.line(
        [(0, i * cell_h), (width, i * cell_h)],
        fill=(255, 255, 255, 230),
        width=5,
    )
Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB").save(
    A / "occlusion_person_en.png"
)


def rebuild_blurred_photo(src: Path, dest: Path) -> None:
    """Whole-frame blur, then pixelate the painted plate. Used only for HORNOK_PHOTO."""
    photo = Image.open(src).convert("RGB")
    photo = photo.filter(ImageFilter.GaussianBlur(5))
    plate = (820, 395, 1035, 540)
    region = photo.crop(plate)
    region = region.resize((6, 4)).resize(region.size, Image.Resampling.NEAREST)
    photo.paste(region, plate)
    photo.save(dest, quality=92)


photo_override = os.environ.get("HORNOK_PHOTO")
if photo_override:
    rebuild_blurred_photo(Path(photo_override), PHOTO_OUT)
elif not PHOTO_OUT.is_file():
    raise SystemExit(
        f"missing {PHOTO_OUT}; set HORNOK_PHOTO to a source image to rebuild the blurred tailgate"
    )

qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=24, border=2)
qr.add_data("https://jaideep-aher.github.io/horn-ok-please")
qr.make(fit=True)
qr.make_image(fill_color="black", back_color="white").convert("RGB").save(A / "qr.png")
print("ok", Image.open(A / "qr.png").size)
