"""Letter-size (8.5x11 in) proof at 300 dpi: poster scaled to 8.0 in wide (33.3%)."""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

os.chdir(Path(__file__).resolve().parent)
Image.MAX_IMAGE_PIXELS = None
src = Image.open("build/horn-ok-please-poster-full-300dpi.png").convert("RGB")
width, height = 2550, 3300
page = Image.new("RGB", (width, height), "white")
side = 2400
im = src.resize((side, side), Image.LANCZOS)
page.paste(im, ((width - side) // 2, 225))
draw = ImageDraw.Draw(page)
font = ImageFont.truetype("assets/fonts/Lato-Regular.ttf", 40)
draw.text(
    (75, 90),
    "Horn OK Please - letter proof. Print at 100% (no fit-to-page). "
    "Poster scaled to 8.0 in = 33.3% of 24 in.",
    fill="black",
    font=font,
)
draw.text(
    (75, 2700),
    "At this scale: 24 pt body prints as 8 pt, 18 pt captions as 6 pt, "
    "the 104 pt title as 35 pt.",
    fill="black",
    font=font,
)
draw.text(
    (75, 2760),
    "Reading this proof at about 50 cm is roughly like reading the full poster at 1.5 m.",
    fill="black",
    font=font,
)
page.save("build/horn-ok-please-letter-proof.png", dpi=(300, 300))
print(page.size)
