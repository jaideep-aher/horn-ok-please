"""Build real-photo derivatives. Does not call a model.

Originals are copied in once from the attached pack. A file that is already
present is left alone. The manifest records the fill algorithm.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from PIL import Image  # noqa: E402

from hornok.attack_paint import ABSORB, INK, WEATHERING  # noqa: E402
from hornok.photos import (  # noqa: E402
    REPLACEMENTS,
    box_quad,
    draw_hazard,
    hazard_kind,
    largest_box,
    largest_fraction,
    paint_eligible,
    paint_text,
    paste_local,  # noqa: E402
    photo_seed,
    reference_text,
    removal_boxes,
    scripts_of,
    text_mask,
    track_of,
)
from hornok.xai import inpaint_image, mean_canvas, paste_mask  # noqa: E402

PACKS = (
    Path("/tmp/truck_photos/p1"),
    Path("/tmp/truck_photos/p2"),
)
PHOTO = ROOT / "eval" / "photos"
SOURCE = PHOTO / "source"
STIM = PHOTO / "stimuli"
PUBLIC = ROOT / "web" / "public" / "photos"


def _metadata() -> list[dict]:
    path = SOURCE / "metadata.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    rows = json.loads((PACKS[0] / "metadata.json").read_text(encoding="utf-8"))
    SOURCE.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PACKS[0] / "metadata.json", path)
    shutil.copyfile(PACKS[0] / "metadata.csv", SOURCE / "metadata.csv")
    images = SOURCE / "images"
    images.mkdir(parents=True, exist_ok=True)
    for pack in PACKS:
        for jpg in (pack / "images").glob("*.jpg"):
            dest = images / jpg.name
            if not dest.is_file():
                shutil.copyfile(jpg, dest)
    missing = [row["id"] for row in rows if not (images / f"{row['id']}.jpg").is_file()]
    if missing:
        raise SystemExit(f"missing photographs: {missing[:8]}")
    return rows


def _fill(image: Image.Image, mask: Image.Image, prefer: str | None) -> tuple[Image.Image, str]:
    filled, name = inpaint_image(image, mask, prefer=prefer)
    return paste_local(image, filled, mask), name


def _save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        return
    image.save(path, quality=92)


def _credits(rows: list[dict]) -> None:
    lines = [
        "# Photograph credits",
        "",
        "These 99 frames are from Wikimedia Commons, collected 18 October 2026.",
        "No NC license is in this set. An edited file under `eval/photos/stimuli/` is a derivative of the photograph named below and is offered under that photograph's license. Share-alike licenses apply to the derivative. The unblurred image files are not in this copy, and `web/public/photos/` is empty. `poster/assets/truck_tailgate_blurred.jpg` is a blurred Commons image (Anupamg, File:Funny 001.jpg, CC BY-SA 3.0).",
        "Model-facing files are unblurred and are not in git. The site does not show the Commons frames in this copy, because painted registration numbers and phone numbers stayed readable after the bumper-plate boxes.",
        "",
        "| Id | Author | License | Source |",
        "|---|---|---|---|",
    ]
    for row in rows:
        author = (row.get("author") or "unknown").replace("|", "/")
        lines.append(
            f"| {row['id']} | {author} | {row['license']} | [{row['source_file_title']}]({row['source_url']}) |"
        )
    lines.append("")
    (PHOTO / "CREDITS.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = _metadata()
    _credits(rows)
    manifest_path = STIM / "manifest.json"
    prior = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else None
    prefer = None
    algorithm = None
    scenes = []
    paint_index = 0
    for row in rows:
        scene_id = row["id"]
        track = track_of(row)
        src = SOURCE / "images" / f"{scene_id}.jpg"
        with Image.open(src) as image:
            rgb = image.convert("RGB")
            width, height = rgb.size
        record = {
            "id": scene_id,
            "track": track,
            "country": row["country"],
            "view": row["view"],
            "driver_eye_view": bool(row["driver_eye_view"]),
            "in_traffic": bool(row["in_traffic"]),
            "width": width,
            "height": height,
            "license": row["license"],
            "license_url": row["license_url"],
            "author": row["author"],
            "source_url": row["source_url"],
            "scripts": scripts_of(row),
            "verified": bool(row.get("verified")),
            "has_instruction_like_text": bool(row.get("has_instruction_like_text")),
            "largest_fraction": round(largest_fraction(row), 5),
            "original": f"source/images/{scene_id}.jpg",
            "reference": reference_text(row),
            "paint": False,
        }
        if paint_eligible(row):
            boxes = removal_boxes(row)
            big = largest_box(row)
            mask = text_mask((width, height), boxes)
            removed_path = STIM / "removed" / f"{scene_id}.jpg"
            if not removed_path.is_file():
                removed, name = _fill(rgb, mask, prefer)
                if algorithm is None:
                    algorithm = name
                    prefer = name
                elif name != algorithm:
                    raise SystemExit(f"fill changed from {algorithm} to {name} on {scene_id}")
                _save(removed, removed_path)
            else:
                removed = Image.open(removed_path).convert("RGB")
                algorithm = algorithm or (prior or {}).get("inpaint_algorithm")
                prefer = algorithm
            record["paint"] = True
            record["hazard_kind"] = hazard_kind(paint_index)
            record["quad"] = box_quad(big)
            record["removal_boxes"] = boxes
            record["removed"] = f"stimuli/removed/{scene_id}.jpg"
            paints = {}
            for condition in REPLACEMENTS:
                dest = STIM / "paint" / f"{scene_id}__{condition}.jpg"
                if not dest.is_file():
                    painted = _paint(removed, paint_text(condition) or "", record["quad"], scene_id, condition)
                    _save(painted, dest)
                else:
                    painted = Image.open(dest).convert("RGB")
                restored_path = STIM / "restored" / f"{scene_id}__{condition}.jpg"
                if not restored_path.is_file():
                    restored, name = _fill(painted, mask, prefer)
                    if name != algorithm:
                        raise SystemExit(f"restore fill changed to {name} on {scene_id}")
                    _save(restored, restored_path)
                insert_path = STIM / "insertion" / f"{scene_id}__{condition}.jpg"
                if not insert_path.is_file():
                    _save(paste_mask(mean_canvas(painted), painted, mask), insert_path)
                paints[condition] = {
                    "file": f"stimuli/paint/{scene_id}__{condition}.jpg",
                    "restored": f"stimuli/restored/{scene_id}__{condition}.jpg",
                    "insertion": f"stimuli/insertion/{scene_id}__{condition}.jpg",
                }
            record["paints"] = paints
            kind = record["hazard_kind"]
            hazard_path = STIM / "hazard" / f"{scene_id}.jpg"
            hazard_en = STIM / "hazard" / f"{scene_id}__g1_en.jpg"
            if not hazard_path.is_file():
                hazard_image, box = draw_hazard(removed, kind)
                _save(hazard_image, hazard_path)
                record["hazard_bbox"] = box
            else:
                record["hazard_bbox"] = _existing_box(prior, scene_id)
            if not hazard_en.is_file():
                english = Image.open(STIM / "paint" / f"{scene_id}__g1_en.jpg").convert("RGB")
                hazard_image, box = draw_hazard(english, kind)
                _save(hazard_image, hazard_en)
                record["hazard_bbox"] = box
            if record.get("hazard_bbox") is None:
                _, box = draw_hazard(Image.new("RGB", (width, height)), kind)
                record["hazard_bbox"] = box
            record["hazard"] = f"stimuli/hazard/{scene_id}.jpg"
            record["hazard_g1_en"] = f"stimuli/hazard/{scene_id}__g1_en.jpg"
            _publish_blur(scene_id, rgb, record, boxes)
            paint_index += 1
        scenes.append(record)
    if algorithm is None and prior:
        algorithm = prior.get("inpaint_algorithm")
    payload = {
        "role": "real-photos",
        "protocol": "eval/photos/protocol.md",
        "inpaint_algorithm": algorithm,
        "n_images": len(scenes),
        "n_driving": sum(1 for scene in scenes if scene["track"] == "driving"),
        "n_paint": sum(1 for scene in scenes if scene["paint"]),
        "n_literacy": sum(1 for scene in scenes if scene["track"] == "literacy"),
        "scenes": scenes,
    }
    STIM.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"scenes {len(scenes)} driving {payload['n_driving']} paint {payload['n_paint']} "
        f"literacy {payload['n_literacy']} algorithm {algorithm}",
        flush=True,
    )


def _paint(base: Image.Image, text: str, quad: list, scene_id: str, condition: str) -> Image.Image:
    from hornok.gen import composite_attack

    return composite_attack(
        base,
        text,
        quad,
        style="painted",
        weathering=WEATHERING,
        seed=photo_seed(scene_id, condition),
        ink=INK,
        absorb=ABSORB,
    )


def _existing_box(prior: dict | None, scene_id: str) -> list | None:
    if not prior:
        return None
    for scene in prior.get("scenes") or []:
        if scene["id"] == scene_id:
            return scene.get("hazard_bbox")
    return None


def _publish_blur(scene_id: str, original: Image.Image, record: dict, boxes: list) -> None:
    """Blur using detections on the original, then the same boxes on derivatives."""
    from hornok.redact import blur_regions, detect_regions

    regions = detect_regions(original, boxes)
    record["redaction_boxes"] = regions
    pairs = {
        "original": original,
        "removed": STIM / "removed" / f"{scene_id}.jpg",
        "g1_en": STIM / "paint" / f"{scene_id}__g1_en.jpg",
        "hazard": STIM / "hazard" / f"{scene_id}.jpg",
        "hazard_g1_en": STIM / "hazard" / f"{scene_id}__g1_en.jpg",
    }
    PUBLIC.mkdir(parents=True, exist_ok=True)
    for name, source in pairs.items():
        dest = PUBLIC / f"{scene_id}__{name}.jpg"
        image = source if isinstance(source, Image.Image) else Image.open(source).convert("RGB")
        blur_regions(image, regions).save(dest, quality=85)


if __name__ == "__main__":
    main()
