"""Paint the locked round-3 tailgate images when the PNG is not already on disk.

The seed, ink, and weathering match ``eval/round3/build_stimuli.py``. A file
that is already present is left alone, so a pre-rendered attack is not redrawn.
"""

from __future__ import annotations

import json
import zlib
from pathlib import Path

from PIL import Image

from hornok.gen import composite_attack

INK = (32, 18, 14)
ABSORB = 0.1
WEATHERING = 0.28


def attack_seed(scene_id: str, phrase: str, script: str) -> int:
    return zlib.crc32(f"r3:{scene_id}:{phrase}:{script}".encode()) % 100000


def paint_attack(base: Image.Image, text: str, quad: list, scene_id: str, phrase: str, script: str):
    return composite_attack(
        base,
        text,
        quad,
        style="painted",
        weathering=WEATHERING,
        seed=attack_seed(scene_id, phrase, script),
        ink=INK,
        absorb=ABSORB,
    )


def ensure_scene_attacks(stimuli: Path, scene: dict) -> int:
    """Write missing attack PNGs for one scene. Returns how many were written."""
    if scene.get("binary_label") != "STOP":
        return 0
    written = 0
    base: Image.Image | None = None
    for attack in scene.get("attacks") or []:
        dest = stimuli / attack["file"]
        if dest.is_file():
            continue
        if base is None:
            base = Image.open(stimuli / scene["clean_file"]).convert("RGB")
        painted = paint_attack(
            base,
            attack["text"],
            scene["quad"],
            scene["id"],
            attack["phrase"],
            attack["script"],
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        painted.save(dest)
        written += 1
    return written


def ensure_attack_images(stimuli: Path, manifest: dict | None = None) -> int:
    if manifest is None:
        manifest = json.loads((stimuli / "manifest.json").read_text(encoding="utf-8"))
    written = 0
    for scene in manifest["scenes"]:
        written += ensure_scene_attacks(stimuli, scene)
    return written
