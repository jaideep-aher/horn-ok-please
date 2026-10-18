"""Draw the diagnostic scenes. Does not read or write the round-3 stimuli."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from hornok.devsplit import dev_specs
from hornok.scenes import render_spec

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "eval" / "dev" / "stimuli"


def build() -> dict:
    if OUT.exists():
        shutil.rmtree(OUT)
    clean = OUT / "clean"
    clean.mkdir(parents=True)
    scenes = []
    for index, spec in enumerate(dev_specs()):
        image, meta = render_spec(spec, seed=8100 + index)
        name = f"{spec['id']}.png"
        image.save(clean / name, optimize=True)
        scenes.append(
            {
                "id": spec["id"],
                "binary_label": spec["binary_label"],
                "stratum": spec["stratum"],
                "hazard": spec["hazard"],
                "no_truck": bool(spec.get("no_truck")),
                "clean_file": f"clean/{name}",
                "source": "synthetic",
                "license": meta["license"],
            }
        )
    counts = {}
    for row in scenes:
        counts[row["stratum"]] = counts.get(row["stratum"], 0) + 1
    if counts != {"stop": 8, "go_empty": 4, "go_shoulder": 4}:
        raise SystemExit(f"unexpected strata: {counts}")
    manifest = {
        "role": "diagnostic-dev-split",
        "protocol": "eval/dev/protocol.md",
        "not_the_test_set": True,
        "scenes": scenes,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {len(scenes)} dev scenes {counts}")
    return manifest


if __name__ == "__main__":
    build()
