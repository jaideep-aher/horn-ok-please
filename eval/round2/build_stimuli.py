"""Build the round-2 scene manifest and painted images.

Original round-1 clean frames are copied so their pixels stay the round-1
frames. New illustrations are drawn by hornok.scenes. Photographs are
downloaded from Wikimedia Commons, letterboxed to 1280x720, and credited in
the manifest. Attack and benign paints are deterministic.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
import zlib
from collections import Counter
from io import BytesIO
from pathlib import Path

from PIL import Image

from hornok.gen import composite_attack
from hornok.phrases import LITERACY_CARDS
from hornok.round2 import (
    ATTACK_IDS,
    BENIGN_IDS,
    ORIGINAL_IDS,
    SCRIPTS,
    attack_phrase_id,
    phrase_text,
)
from hornok.scenes import (
    RESERVE_SPECS,
    extra_illustration_specs,
    render_literacy_card,
    render_spec,
    scene_specs,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "eval" / "round2" / "stimuli"
PHOTO_SRC = ROOT / "eval" / "round2" / "photo_src"
ROUND1_CLEAN = ROOT / "eval" / "stimuli" / "clean"
UA = "HornOKPlease/0.2 (Duke AIPI research audit; local) Python-urllib"
W, H = 1280, 720
EXPECTED = {"BRAKE": 16, "CONTINUE": 8, "CHANGE_LANE": 9, "SLOW": 9}


def _download(title: str, dest: Path) -> None:
    if dest.is_file() and dest.stat().st_size > 1000:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    name = title.removeprefix("File:")
    url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(name)
    url += "?width=1600"
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=90) as resp:
        data = resp.read()
    dest.write_bytes(data)


def _letterbox(image: Image.Image) -> tuple[Image.Image, dict]:
    image = image.convert("RGB")
    scale = min(W / image.width, H / image.height)
    resized = image.resize(
        (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGB", (W, H), (16, 14, 12))
    pad_x = (W - resized.width) // 2
    pad_y = (H - resized.height) // 2
    canvas.paste(resized, (pad_x, pad_y))
    return canvas, {
        "scale": scale,
        "pad": [pad_x, pad_y],
        "resized": [resized.width, resized.height],
        "source_pixels": [image.width, image.height],
    }


def _paint(base: Image.Image, text: str, quad: list, placement: str, seed: int) -> Image.Image:
    if placement == "road_surface":
        ink = (248, 244, 236)
        absorb = 0.0
    else:
        ink = (32, 18, 14)
        absorb = 0.1
    return composite_attack(
        base,
        text,
        quad,
        style="painted",
        weathering=0.28,
        seed=seed,
        ink=ink,
        absorb=absorb,
    )


def _seed(scene_id: str, phrase: str, script: str) -> int:
    return zlib.crc32(f"{scene_id}:{phrase}:{script}".encode()) % 100000


def _page(title: str) -> str:
    return "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))


def _illustration_record(spec: dict, index: int, clean_dir: Path) -> tuple[Image.Image, dict]:
    image, meta = render_spec(spec, seed=3000 + index)
    existing = ROUND1_CLEAN / f"{spec['id']}.png"
    if spec["id"] in ORIGINAL_IDS and existing.is_file():
        image = Image.open(existing).convert("RGB")
        meta["pixels"] = "copied from round-1 clean frame"
    else:
        meta["pixels"] = "rendered for round 2"
    image.save(clean_dir / f"{spec['id']}.png", optimize=True)
    meta["placement"] = "truck_rear"
    meta["quad"] = meta["quads"]["truck_rear"]
    meta["source"] = "synthetic"
    if spec["id"].startswith("reserve_"):
        meta["source"] = "synthetic_reserve"
    meta["license"] = (
        "Original synthetic illustration created for the Horn OK Please study. "
        "CC-BY-4.0, Jaideep (Jay) Aher."
    )
    meta["artist"] = "Jaideep (Jay) Aher"
    meta["commons_title"] = None
    meta["page"] = None
    return image, meta


def _photo_record(item: dict, clean_dir: Path) -> tuple[Image.Image, dict]:
    filename = item["commons_title"].removeprefix("File:")
    src = PHOTO_SRC / filename
    _download(item["commons_title"], src)
    with Image.open(BytesIO(src.read_bytes())) as raw:
        image, transform = _letterbox(raw)
    image.save(clean_dir / f"{item['id']}.png", optimize=True)
    meta = {
        "id": item["id"],
        "gt": item["gt"],
        "target": item["target"],
        "role": item["role"],
        "legitimate_regulatory": item["legitimate_regulatory"],
        "hazard": item["hazard"],
        "placement": item["placement"],
        "quad": item["quad"],
        "source": "photo",
        "license": item["license"],
        "license_url": item["license_url"],
        "artist": item["artist"],
        "commons_title": item["commons_title"],
        "page": _page(item["commons_title"]),
        "retrieval": "Wikimedia Commons Special:FilePath width=1600, then letterboxed to 1280x720",
        "letterbox": transform,
        "pixels": "photograph",
    }
    return image, meta


def _attacks(image: Image.Image, meta: dict, attack_dir: Path) -> list[dict]:
    rows = []
    scene_id = meta["id"]
    quad = meta["quad"]
    placement = meta["placement"]
    ids = [attack_phrase_id(meta["target"], i) for i in range(1, 5)] + list(BENIGN_IDS)
    for phrase_id in ids:
        for script in SCRIPTS:
            text = phrase_text(phrase_id, script)
            painted = _paint(image, text, quad, placement, _seed(scene_id, phrase_id, script))
            name = f"{scene_id}__{phrase_id}__{script}.png"
            painted.save(attack_dir / name, optimize=True)
            kind = "benign" if phrase_id in BENIGN_IDS else "attack"
            rows.append(
                {
                    "phrase": phrase_id,
                    "script": script,
                    "kind": kind,
                    "file": f"attack/{name}",
                    "text": text,
                    "target": meta["target"] if kind == "attack" else None,
                }
            )
    return rows


def build() -> dict:
    clean_dir = OUT / "clean"
    attack_dir = OUT / "attack"
    lit_dir = OUT / "literacy"
    for folder in (clean_dir, attack_dir, lit_dir):
        folder.mkdir(parents=True, exist_ok=True)

    photo_doc = json.loads((ROOT / "eval" / "round2" / "photos.json").read_text())
    scenes = []
    specs = list(scene_specs()) + extra_illustration_specs()
    for item in photo_doc["items"]:
        if item["kind"] == "reserve":
            specs.append(RESERVE_SPECS[item["id"]]())
    for index, spec in enumerate(specs):
        image, meta = _illustration_record(spec, index, clean_dir)
        meta["clean_file"] = f"clean/{spec['id']}.png"
        meta["attacks"] = _attacks(image, meta, attack_dir)
        meta.pop("quads", None)
        meta.pop("placements", None)
        scenes.append(meta)

    # Photographs replace nothing; they are additional. Reserves were already
    # rendered from specs. Photos are appended from the same list.
    # The loop above rendered reserve via specs, but photos were not in specs.
    rendered_ids = {meta["id"] for meta in scenes}
    for item in photo_doc["items"]:
        if item["kind"] != "photo":
            continue
        if item["id"] in rendered_ids:
            continue
        image, meta = _photo_record(item, clean_dir)
        meta["clean_file"] = f"clean/{item['id']}.png"
        meta["attacks"] = _attacks(image, meta, attack_dir)
        scenes.append(meta)

    cards = []
    for card in LITERACY_CARDS:
        card_image = render_literacy_card(card["text"])
        name = f"{card['id']}.png"
        card_image.save(lit_dir / name, optimize=True)
        cards.append({**card, "file": f"literacy/{name}"})

    counts = Counter(scene["gt"] for scene in scenes)
    if len(scenes) != 42 or dict(counts) != EXPECTED:
        raise SystemExit(f"scene mix {len(scenes)} {dict(counts)} != 42 {EXPECTED}")
    if len({scene["id"] for scene in scenes}) != 42:
        raise SystemExit("duplicate scene ids")

    manifest = {
        "round": 2,
        "image_size": [W, H],
        "style": "painted",
        "weathering": 0.28,
        "n_scenes": 42,
        "gt_counts": dict(counts),
        "attack_phrases": list(ATTACK_IDS),
        "benign_phrases": list(BENIGN_IDS),
        "scripts": list(SCRIPTS),
        "scenes": scenes,
        "literacy": cards,
        "license_note": (
            "Illustrations are original CC-BY-4.0 composites by Jaideep (Jay) Aher. "
            "Photographs are Wikimedia Commons files under the license named on each scene. "
            "Commons files were retrieved at width 1600 and letterboxed. "
            "They are not the camera masters."
        ),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {OUT / 'manifest.json'} scenes={len(scenes)} gt={dict(counts)}")
    return manifest


if __name__ == "__main__":
    build()
