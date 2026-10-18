"""Download the Wikimedia Commons frames omitted from git.

Reads eval/photos/source/metadata.json and writes
eval/photos/source/images/<id>.jpg. Text boxes in the metadata use the
stored width and height, so each file is scaled to that size. A fresh
Commons download is the same pipeline, not a byte-identical JPEG.

Then rebuild derivatives:

    python eval/photos/build_stimuli.py

LaMa is used when simple-lama-inpainting is installed. Otherwise the
fill is OpenCV Telea. The recorded photo-track algorithm was LaMa.
Plate and face blur needs OpenCV 4.10, because OpenCV 5 has no
CascadeClassifier.

Round 2's letterboxed Commons frames are separate. Their titles are in
eval/round2/photos.json. Download and letterbox them with:

    python eval/round2/build_stimuli.py

Round 3 copies those frames when its stimulus script runs. Do not commit
the unblurred files.
"""

from __future__ import annotations

import json
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "eval" / "photos" / "source"
IMAGES = SOURCE / "images"
UA = "HornOKPlease/1.0 (https://github.com/jaideep-aher/horn-ok-please) Python-urllib"


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def _to_frame(blob: bytes, width: int, height: int) -> Image.Image:
    image = Image.open(BytesIO(blob)).convert("RGB")
    if image.size == (width, height):
        return image
    return image.resize((width, height), Image.Resampling.LANCZOS)


def main() -> None:
    rows = json.loads((SOURCE / "metadata.json").read_text(encoding="utf-8"))
    IMAGES.mkdir(parents=True, exist_ok=True)
    for row in rows:
        scene_id = row["id"]
        dest = IMAGES / f"{scene_id}.jpg"
        width, height = int(row["width"]), int(row["height"])
        if dest.is_file():
            with Image.open(dest) as existing:
                if existing.size == (width, height):
                    print(f"keep {scene_id}", flush=True)
                    continue
        url = row["original_image_url"]
        print(f"get {scene_id} {url}", flush=True)
        frame = _to_frame(_download(url), width, height)
        frame.save(dest, quality=92)
    print(f"wrote {len(rows)} frames under {IMAGES}", flush=True)
    print("next: python eval/photos/build_stimuli.py", flush=True)


if __name__ == "__main__":
    main()
