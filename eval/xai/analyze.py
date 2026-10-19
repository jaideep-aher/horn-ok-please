"""Write eval/xai/results/summary.json from stored completions only."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from PIL import Image  # noqa: E402

from hornok.xai import gaze_rows, grid_cells, quad_mask, summarize  # noqa: E402

PREDICTIONS = ROOT / "eval" / "xai" / "results" / "predictions.jsonl"
MANIFEST = ROOT / "eval" / "xai" / "stimuli" / "manifest.json"
DEV = ROOT / "eval" / "dev" / "results" / "predictions.jsonl"
SUMMARY = ROOT / "eval" / "xai" / "results" / "summary.json"
WHITEBOX = ROOT / "eval" / "xai" / "results" / "whitebox.json"
PUBLIC = ROOT / "web" / "public" / "xai"
PUBLIC_DATA = ROOT / "web" / "public" / "data" / "xai.json"


def _rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _inject_directs(dev_rows: list[dict], gaze: list[dict]) -> list[dict]:
    """Copies of stored decisions so the scorer can see them. Not new completions."""
    injected = []
    for row in dev_rows:
        if row.get("prompt_id") != "D0" or row.get("action") not in {"STOP", "GO"}:
            continue
        injected.append(
            {
                "kind": "direct",
                "model": row["model"],
                "scene": row["scene"],
                "condition": "clean",
                "prompt_id": "D0",
                "cell": None,
                "action": row["action"],
                "source": "dev",
            }
        )
    for row in gaze:
        injected.append(
            {
                "kind": "direct",
                "model": row["model"],
                "scene": row["scene"],
                "condition": "clean",
                "prompt_id": row["prompt_id"],
                "cell": None,
                "action": row["action"],
                "source": "dev",
            }
        )
    return injected


def _public_path(dest: Path) -> str:
    return "/" + dest.relative_to(ROOT / "web" / "public").as_posix()


def _copy(src: Path, dest: Path) -> str:
    """Site path for dest. Missing or gitignored PNGs keep that path and are not copied."""
    if src.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    return _public_path(dest)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--publish",
        action="store_true",
        help="copy frames into web/public/xai and write web/public/data/xai.json",
    )
    args = parser.parse_args(argv)
    if not MANIFEST.is_file():
        raise SystemExit("missing eval/xai/stimuli/manifest.json")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    scenes = []
    for scene in manifest["scenes"]:
        mask = None
        if scene.get("quad"):
            sample = ROOT / "eval" / "xai" / "stimuli" / scene["clean_file"]
            if sample.is_file():
                with Image.open(sample) as image:
                    mask = quad_mask(image.size, scene["quad"])
        scenes.append({**scene, "_text_mask": mask})
    dev_rows = _rows(DEV)
    from hornok.devsplit import dev_specs
    from hornok.scenes import render_spec

    meta = {}
    hazards = {}
    for spec in dev_specs():
        _image, rendered = render_spec(spec, seed=0)
        meta[spec["id"]] = rendered["hazard_bbox"]
        hazards[spec["id"]] = spec["hazard"]
    gaze = []
    for row in gaze_rows(dev_rows):
        gaze.append(
            {
                **row,
                "hazard_bbox": meta.get(row["scene"]),
                "hazard": hazards.get(row["scene"], row["scene"]),
            }
        )
    stored = _rows(PREDICTIONS)
    whitebox = {"status": "not_run", "reason": "The white-box attempt has not been recorded."}
    if WHITEBOX.is_file():
        whitebox = json.loads(WHITEBOX.read_text(encoding="utf-8"))
    summary = summarize(
        stored + _inject_directs(dev_rows, gaze),
        scenes=scenes,
        gaze=gaze,
        algorithm=manifest.get("inpaint_algorithm"),
        whitebox=whitebox,
    )
    summary["n_predictions"] = len(stored)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if args.publish:
        _publish_site(summary, manifest)
    print(f"wrote {SUMMARY} rows {summary['n_predictions']}", flush=True)


def _publish_site(summary: dict, manifest: dict) -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    site_scenes = []
    maps = {row["scene"]: row for row in summary["painted_maps"]}
    for scene in manifest["scenes"]:
        stem = scene["id"]
        clean = _copy(ROOT / "eval/xai/stimuli" / scene["clean_file"], PUBLIC / f"{stem}__clean.png")
        paint = scene["paints"]["g1_en"]
        painted = _copy(ROOT / "eval/xai/stimuli" / paint["file"], PUBLIC / f"{stem}__g1_en.png")
        removed = _copy(ROOT / "eval/xai/stimuli" / paint["inpaint"], PUBLIC / f"{stem}__g1_en_inpaint.png")
        decisions = {}
        for condition in ("g1_en", "g1_mr", "benign", "gibberish"):
            pair = next((row for row in summary["pairs"] if row["scene"] == stem and row["condition"] == condition), None)
            if pair:
                decisions[condition] = {
                    "clean": pair["clean"],
                    "painted": pair["painted"],
                    "inpaint": pair["inpaint"],
                    "state": pair["state"],
                }
        site_scenes.append(
            {
                "id": stem,
                "label": scene["binary_label"],
                "hazard": scene["hazard"],
                "text_on_hazard": scene["text_on_hazard"],
                "clean": clean,
                "paint": painted,
                "inpaint": removed,
                "decisions": decisions,
                "map": maps.get(stem),
            }
        )
    gaze_public = []
    for row in summary["gaze"]:
        src = ROOT / "eval" / "dev" / "stimuli" / "clean" / f"{row['scene']}.png"
        image = _copy(src, PUBLIC / f"{row['scene']}.png")
        gaze_public.append(
            {
                "model": row["model"],
                "scene": row["scene"],
                "prompt_id": row["prompt_id"],
                "direct": row["direct"],
                "label": row["label"],
                "mass_hazard": row["mass_hazard"],
                "n_flip_cells": row["n_flip_cells"],
                "n_scored_cells": row["n_scored_cells"],
                "centers_in_hazard": row.get("centers_in_hazard"),
                "cells_meeting_hazard": row.get("cells_meeting_hazard"),
                "image": image,
                "cells": row["cells"],
                "hazard": row.get("hazard"),
            }
        )
    payload = {
        "split": "xai",
        "question": summary["question"],
        "algorithm": summary["inpaint_algorithm"],
        "reading": summary["reading"],
        "conditions": summary["conditions"],
        "says": summary["says"],
        "gaze_counts": summary["gaze_counts"],
        "faithful": summary["faithful"],
        "whitebox": summary["whitebox"],
        "n_predictions": summary["n_predictions"],
        "scenes": site_scenes,
        "gaze": gaze_public,
        "grid": [{"r": cell["r"], "c": cell["c"]} for cell in grid_cells()],
    }
    PUBLIC_DATA.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_DATA.write_text(json.dumps(payload) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
