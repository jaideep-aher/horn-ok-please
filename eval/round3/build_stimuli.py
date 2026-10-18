"""Build the round-3 STOP/GO images.

Inherited frames are copied from round 2 so the pixels match the label that
was locked there. New frames are drawn from the specs named in the amendment.
Attack paint is applied only to STOP scenes, on the truck tailgate.
"""

from __future__ import annotations

import json
import shutil
import zlib
from pathlib import Path

from PIL import Image

from hornok.gen import composite_attack
from hornok.phrases import LITERACY_CARDS
from hornok.round3 import (
    ADDED_GO,
    ADDED_STOP,
    INHERITED_GO,
    INHERITED_STOP,
    PHRASES,
    SCRIPTS,
    added_specs,
)
from hornok.scenes import render_literacy_card, render_spec

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "eval" / "round3" / "stimuli"
ROUND2 = ROOT / "eval" / "round2" / "stimuli"


def _seed(scene_id: str, phrase: str, script: str) -> int:
    return zlib.crc32(f"r3:{scene_id}:{phrase}:{script}".encode()) % 100000


def _paint(base: Image.Image, text: str, quad: list, seed: int) -> Image.Image:
    return composite_attack(
        base,
        text,
        quad,
        style="painted",
        weathering=0.28,
        seed=seed,
        ink=(32, 18, 14),
        absorb=0.1,
    )


def _inherited() -> list[dict]:
    manifest = json.loads((ROUND2 / "manifest.json").read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in manifest["scenes"]}
    records = []
    for scene_id in INHERITED_STOP + INHERITED_GO:
        src = by_id[scene_id]
        label = "STOP" if scene_id in INHERITED_STOP else "GO"
        records.append(
            {
                "id": scene_id,
                "binary_label": label,
                "hazard": src["hazard"],
                "source": src.get("source"),
                "license": src.get("license"),
                "license_url": src.get("license_url"),
                "artist": src.get("artist"),
                "commons_title": src.get("commons_title"),
                "page": src.get("page"),
                "quad": src["quad"],
                "placement": "truck_rear",
                "round2_gt": src["gt"],
                "inherited": True,
                "clean_src": str(ROUND2 / src["clean_file"]),
            }
        )
    return records


def _added() -> list[dict]:
    records = []
    for index, spec in enumerate(added_specs()):
        image, meta = render_spec(spec, seed=4100 + index)
        records.append(
            {
                "id": spec["id"],
                "binary_label": spec["binary_label"],
                "hazard": spec["hazard"],
                "source": "synthetic",
                "license": meta["license"],
                "quad": meta["quads"]["truck_rear"],
                "placement": "truck_rear",
                "round2_gt": None,
                "inherited": False,
                "image": image,
            }
        )
    return records


def build() -> dict:
    if OUT.exists():
        shutil.rmtree(OUT)
    clean_dir = OUT / "clean"
    attack_dir = OUT / "attack"
    lit_dir = OUT / "literacy"
    clean_dir.mkdir(parents=True)
    attack_dir.mkdir(parents=True)
    lit_dir.mkdir(parents=True)

    scenes = []
    for record in _inherited() + _added():
        clean_name = f"{record['id']}.png"
        dest = clean_dir / clean_name
        if record["inherited"]:
            shutil.copyfile(record["clean_src"], dest)
        else:
            record["image"].save(dest, optimize=True)
        attacks = []
        if record["binary_label"] == "STOP":
            base = Image.open(dest).convert("RGB")
            for phrase_id, phrase in PHRASES.items():
                for script in SCRIPTS:
                    text = phrase[script]
                    painted = _paint(
                        base, text, record["quad"], _seed(record["id"], phrase_id, script)
                    )
                    name = f"{record['id']}__{phrase_id}__{script}.png"
                    painted.save(attack_dir / name, optimize=True)
                    attacks.append(
                        {
                            "phrase": phrase_id,
                            "kind": phrase["kind"],
                            "script": script,
                            "file": f"attack/{name}",
                            "text": text,
                        }
                    )
        scenes.append(
            {
                "id": record["id"],
                "binary_label": record["binary_label"],
                "hazard": record["hazard"],
                "source": record["source"],
                "license": record["license"],
                "license_url": record.get("license_url"),
                "artist": record.get("artist"),
                "commons_title": record.get("commons_title"),
                "page": record.get("page"),
                "quad": record["quad"],
                "placement": "truck_rear",
                "round2_gt": record["round2_gt"],
                "inherited": record["inherited"],
                "clean_file": f"clean/{clean_name}",
                "attacks": attacks,
            }
        )

    cards = []
    for card in LITERACY_CARDS:
        image = render_literacy_card(card["text"])
        name = f"{card['id']}.png"
        image.save(lit_dir / name, optimize=True)
        cards.append({**card, "file": f"literacy/{name}"})

    stop = sum(1 for row in scenes if row["binary_label"] == "STOP")
    go = sum(1 for row in scenes if row["binary_label"] == "GO")
    if stop != 20 or go != 20:
        raise SystemExit(f"expected 20/20, got STOP={stop} GO={go}")
    if len(ADDED_STOP) != 4 or len(ADDED_GO) != 12:
        raise SystemExit("added scene counts drifted from the amendment")

    manifest = {
        "round": 3,
        "protocol": "eval/round3/preregistration.md",
        "image_size": [1280, 720],
        "n_stop": stop,
        "n_go": go,
        "placement": "truck_rear",
        "scenes": scenes,
        "literacy": cards,
        "phrases": PHRASES,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {stop} STOP, {go} GO, {sum(len(s['attacks']) for s in scenes)} paints")
    return manifest


if __name__ == "__main__":
    build()
