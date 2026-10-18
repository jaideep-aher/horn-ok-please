"""Write eval/photos/results/summary.json from stored completions only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


from hornok.photos import spoken_photos, summarize, text_mask  # noqa: E402

MANIFEST = ROOT / "eval" / "photos" / "stimuli" / "manifest.json"
PREDICTIONS = ROOT / "eval" / "photos" / "results" / "predictions.jsonl"
SUMMARY = ROOT / "eval" / "photos" / "results" / "summary.json"
PUBLIC = ROOT / "web" / "public" / "data" / "photos.json"


def main() -> None:
    if not MANIFEST.is_file():
        raise SystemExit("missing photo manifest")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    scenes = []
    for scene in manifest["scenes"]:
        mask = None
        if scene.get("paint") and scene.get("removal_boxes"):
            mask = text_mask((scene["width"], scene["height"]), scene["removal_boxes"])
        scenes.append({**scene, "_text_mask": mask, "inpaint_algorithm": manifest.get("inpaint_algorithm")})
    rows = []
    if PREDICTIONS.is_file():
        rows = [json.loads(line) for line in PREDICTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = summarize(rows, scenes=scenes)
    summary["inpaint_algorithm"] = manifest.get("inpaint_algorithm")
    summary["reading"] = spoken_photos(summary)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    # Masks are images and must not land in the JSON.
    summary["maps"] = [{key: value for key, value in row.items()} for row in summary["maps"]]
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    _site(summary, manifest)
    print(f"wrote {SUMMARY} rows {summary['n_predictions']}", flush=True)


def _site(summary: dict, manifest: dict) -> None:
    gallery = []
    by_pair = {}
    for row in summary.get("pairs") or []:
        by_pair[(row["scene"], row["condition"])] = row
    hazards = {row["scene"]: row for row in (summary.get("hazard") or {}).get("rows") or []}
    decisions_path = ROOT / "eval" / "photos" / "results" / "predictions.jsonl"
    direct = {}
    if decisions_path.is_file():
        for line in decisions_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("model") == summary["painted_model"] and row.get("kind") == "direct" and not row.get("error"):
                direct[(row["scene"], row["condition"])] = row.get("action")
    maps = {row["scene"]: row for row in summary.get("maps") or []}
    for scene in manifest["scenes"]:
        if not scene.get("paint"):
            continue
        stem = scene["id"]
        gallery.append(
            {
                "id": stem,
                "country": scene["country"],
                "author": scene["author"],
                "license": scene["license"],
                "source_url": scene["source_url"],
                "hazard_kind": scene.get("hazard_kind"),
                "original": f"/photos/{stem}__original.jpg",
                "removed": f"/photos/{stem}__removed.jpg",
                "paint": f"/photos/{stem}__g1_en.jpg",
                "hazard": f"/photos/{stem}__hazard.jpg",
                "hazard_paint": f"/photos/{stem}__hazard_g1_en.jpg",
                "actions": {
                    "original": direct.get((stem, "original")),
                    "removed": direct.get((stem, "removed")),
                    "g1_en": direct.get((stem, "g1_en")),
                    "g1_deva": direct.get((stem, "g1_deva")),
                    "g1_ur": direct.get((stem, "g1_ur")),
                    "benign": direct.get((stem, "benign")),
                    "hazard": direct.get((stem, "hazard")),
                    "hazard_g1_en": direct.get((stem, "hazard_g1_en")),
                },
                "pair": by_pair.get((stem, "g1_en")),
                "hazard_row": hazards.get(stem),
                "map": maps.get(stem),
            }
        )
    payload = {
        "split": "photos",
        "algorithm": summary.get("inpaint_algorithm"),
        "reading": summary.get("reading"),
        "n_predictions": summary.get("n_predictions"),
        "n_driving": summary.get("n_driving"),
        "n_paint": summary.get("n_paint"),
        "n_literacy": summary.get("n_literacy"),
        "gate": summary.get("gate"),
        "conditions": summary.get("conditions"),
        "hazard": {
            "missed_hazard": (summary.get("hazard") or {}).get("missed_hazard"),
            "text_overrode": (summary.get("hazard") or {}).get("text_overrode"),
        },
        "tests": summary.get("tests"),
        "literacy": summary.get("literacy"),
        "scenes": gallery,
    }
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC.write_text(json.dumps(payload) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
