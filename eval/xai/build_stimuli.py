"""Draw the six explanation scenes and the tailgate edits. No model call."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from hornok.attack_paint import ABSORB, INK, WEATHERING  # noqa: E402
from hornok.devsplit import dev_specs  # noqa: E402
from hornok.gen import composite_attack  # noqa: E402
from hornok.round3 import ADDED_GO, ADDED_STOP, INHERITED_GO, INHERITED_STOP  # noqa: E402
from hornok.scenes import render_spec  # noqa: E402
from hornok.xai import (  # noqa: E402
    PAINT_CONDITIONS,
    inpaint_image,
    mean_canvas,
    paint_text,
    paste_mask,
    quad_mask,
    xai_seed,
    xai_specs,
)

OUT = ROOT / "eval" / "xai" / "stimuli"
MANIFEST = OUT / "manifest.json"


def _bbox(quad: list) -> list[float]:
    xs = [point[0] for point in quad]
    ys = [point[1] for point in quad]
    return [min(xs), min(ys), max(xs), max(ys)]


def _intersects(a: list | None, b: list | None) -> bool:
    if not a or not b:
        return False
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def build() -> dict:
    locked = set(INHERITED_STOP + INHERITED_GO + tuple(row["id"] for row in ADDED_STOP + ADDED_GO))
    locked.update(spec["id"] for spec in dev_specs())
    specs = xai_specs()
    overlap = sorted({spec["id"] for spec in specs} & locked)
    if overlap:
        raise SystemExit(f"xai scenes overlap a locked split: {overlap}")
    OUT.mkdir(parents=True, exist_ok=True)
    algorithm = None
    if MANIFEST.is_file():
        algorithm = json.loads(MANIFEST.read_text(encoding="utf-8")).get("inpaint_algorithm")
    scenes = []
    for index, spec in enumerate(specs):
        image, meta = render_spec(spec, seed=9100 + index)
        clean_rel = f"clean/{spec['id']}.png"
        clean_path = OUT / clean_rel
        clean_path.parent.mkdir(parents=True, exist_ok=True)
        if not clean_path.is_file():
            image.save(clean_path)
        else:
            image = image  # geometry comes from the renderer; pixels stay if present
        quad = meta["quads"]["truck_rear"]
        mask = quad_mask(image.size, quad)
        hazard = meta["hazard_bbox"]
        if spec["binary_label"] == "GO":
            hazard = None
        paints = {}
        for condition in PAINT_CONDITIONS:
            text = paint_text(condition)
            if text is None:
                raise SystemExit(condition)
            paint_rel = f"paint/{spec['id']}__{condition}.png"
            inpaint_rel = f"inpaint/{spec['id']}__{condition}.png"
            insert_rel = f"insertion/{spec['id']}__{condition}.png"
            paint_path = OUT / paint_rel
            if paint_path.is_file():
                painted = None
            else:
                painted = composite_attack(
                    image,
                    text,
                    quad,
                    style="painted",
                    weathering=WEATHERING,
                    seed=xai_seed(spec["id"], condition),
                    ink=INK,
                    absorb=ABSORB,
                )
                paint_path.parent.mkdir(parents=True, exist_ok=True)
                painted.save(paint_path)
            inpaint_path = OUT / inpaint_rel
            if not inpaint_path.is_file():
                if painted is None:
                    painted = __import__("PIL").Image.open(paint_path).convert("RGB")
                filled, used = inpaint_image(painted, mask)
                if algorithm not in {None, used}:
                    raise SystemExit(f"inpaint algorithm changed from {algorithm} to {used}")
                algorithm = used
                inpaint_path.parent.mkdir(parents=True, exist_ok=True)
                filled.save(inpaint_path)
            insert_path = OUT / insert_rel
            if not insert_path.is_file():
                if painted is None:
                    painted = __import__("PIL").Image.open(paint_path).convert("RGB")
                canvas = paste_mask(mean_canvas(painted), painted, mask)
                insert_path.parent.mkdir(parents=True, exist_ok=True)
                canvas.save(insert_path)
            paints[condition] = {
                "text": text,
                "file": paint_rel,
                "inpaint": inpaint_rel,
                "insertion": insert_rel,
            }
        scenes.append(
            {
                "id": spec["id"],
                "binary_label": spec["binary_label"],
                "hazard": spec["hazard"],
                "hazard_bbox": hazard,
                "quad": quad,
                "text_on_hazard": _intersects(_bbox(quad), hazard),
                "clean_file": clean_rel,
                "paints": paints,
                "source": "synthetic",
                "license": meta["license"],
            }
        )
    payload = {
        "role": "xai-scenes",
        "protocol": "eval/xai/protocol.md",
        "not_the_test_set": True,
        "inpaint_algorithm": algorithm,
        "scenes": scenes,
    }
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    payload = build()
    print(
        f"scenes {len(payload['scenes'])} algorithm {payload['inpaint_algorithm']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
