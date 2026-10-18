"""Score the locked real-photo protocol. Resume-safe. Does not open round 3."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from PIL import Image, ImageDraw  # noqa: E402

from hornok.harness import GenerationError  # noqa: E402
from hornok.llama_server import LlamaServerVLM  # noqa: E402
from hornok.metrics import text_similarity  # noqa: E402
from hornok.parse import parse_decision_v3  # noqa: E402
from hornok.photos import GRID_N, PAINTED_MODEL, REPLACEMENTS  # noqa: E402
from hornok.prompts import DRIVING_PROMPT_V3, TRANSCRIBE_PROMPT_V1  # noqa: E402
from hornok.round3 import MODELS  # noqa: E402
from hornok.xai import (  # noqa: E402
    fill_mask,
    fill_rect,
    grid_cells,
    image_mean,
    inpaint_image,
    mean_canvas,
    paste_mask,
)

PHOTO = ROOT / "eval" / "photos"
MANIFEST = PHOTO / "stimuli" / "manifest.json"
OUT = PHOTO / "results"
PREDICTIONS = OUT / "predictions.jsonl"
GRAMMAR = ROOT / "eval" / "round3" / "action.gbnf"
PORT = 18024
MODELS_DIR = ROOT


def _load() -> list[dict]:
    if not PREDICTIONS.is_file():
        return []
    return [json.loads(line) for line in PREDICTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]


def _key(row: dict) -> str:
    return "|".join(
        str(row.get(field))
        for field in ("kind", "model", "scene", "condition", "prompt_id", "cell")
    )


def _append(row: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with PREDICTIONS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()


def _model(model_id: str) -> dict:
    return next(row for row in MODELS if row["id"] == model_id)


def _jobs(manifest: dict) -> list[dict]:
    jobs = []
    driving = [scene for scene in manifest["scenes"] if scene["track"] == "driving"]
    paint = [scene for scene in manifest["scenes"] if scene.get("paint")]
    literacy = [scene for scene in manifest["scenes"] if scene["track"] == "literacy"]
    # Qwen Q8 first: originals, then the paint cohort, then the 6 by 6 grid.
    for scene in driving:
        jobs.append(_direct(PAINTED_MODEL, scene, "original", scene["original"], "direct"))
    for scene in paint:
        jobs.append(_direct(PAINTED_MODEL, scene, "removed", scene["removed"], "direct"))
        for condition in REPLACEMENTS:
            paint_row = scene["paints"][condition]
            jobs.append(_direct(PAINTED_MODEL, scene, condition, paint_row["file"], "direct"))
            jobs.append(_direct(PAINTED_MODEL, scene, condition, paint_row["restored"], "restored"))
            jobs.append(_direct(PAINTED_MODEL, scene, condition, paint_row["insertion"], "insertion"))
        jobs.append(_direct(PAINTED_MODEL, scene, "hazard", scene["hazard"], "direct"))
        jobs.append(_direct(PAINTED_MODEL, scene, "hazard_g1_en", scene["hazard_g1_en"], "direct"))
    for scene in paint:
        for cell in grid_cells(scene["width"], scene["height"], GRID_N):
            jobs.append(_occlusion(scene, f"{cell['r']},{cell['c']}", cell))
        jobs.append(_occlusion(scene, "mask", None))
    for model in MODELS:
        if model["id"] == PAINTED_MODEL:
            continue
        for scene in driving:
            jobs.append(_direct(model["id"], scene, "original", scene["original"], "direct"))
    for scene in literacy:
        jobs.append(_literacy(PAINTED_MODEL, scene, "original", scene["original"]))
        jobs.append(_literacy(PAINTED_MODEL, scene, "mask", scene["original"]))
    for scene in literacy:
        jobs.append(_literacy("gemma3-4b-q8", scene, "original", scene["original"]))
    return jobs


def _direct(model: str, scene: dict, condition: str, rel: str, kind: str) -> dict:
    return {
        "kind": kind,
        "model": model,
        "scene": scene["id"],
        "condition": condition,
        "prompt_id": "D0",
        "cell": None,
        "image": rel,
        "grammar": True,
        "binary_label": "STOP",
        "track": scene["track"],
    }


def _occlusion(scene: dict, name: str, cell: dict | None) -> dict:
    return {
        "kind": "occlusion",
        "model": PAINTED_MODEL,
        "scene": scene["id"],
        "condition": "g1_en",
        "prompt_id": "D0",
        "cell": name,
        "image": scene["paints"]["g1_en"]["file"],
        "_cell": cell,
        "grammar": True,
        "binary_label": "STOP",
        "track": "driving",
    }


def _literacy(model: str, scene: dict, condition: str, rel: str) -> dict:
    return {
        "kind": "literacy",
        "model": model,
        "scene": scene["id"],
        "condition": condition,
        "prompt_id": "L1",
        "cell": None,
        "image": rel,
        "grammar": False,
        "reference": scene.get("reference") or "",
        "track": "literacy",
    }


def _materialize(job: dict, manifest: dict) -> Path:
    source = PHOTO / job["image"]
    if job["kind"] == "literacy" and job["condition"] == "mask":
        return _mask_file(job, manifest)
    if job["kind"] != "occlusion":
        return source
    dest = OUT / "occlusion" / f"{job['scene']}__{job['cell']}.jpg"
    if dest.is_file():
        return dest
    image = Image.open(source).convert("RGB")
    color = image_mean(image)
    if job["cell"] == "mask":
        scene = next(row for row in manifest["scenes"] if row["id"] == job["scene"])
        from hornok.photos import text_mask

        mask = text_mask((scene["width"], scene["height"]), scene["removal_boxes"])
        filled = fill_mask(image, mask, color)
    else:
        filled = fill_rect(image, job["_cell"], color)
    dest.parent.mkdir(parents=True, exist_ok=True)
    filled.save(dest, quality=90)
    return dest


def _mask_file(job: dict, manifest: dict) -> Path:
    dest = OUT / "literacy_mask" / f"{job['scene']}.jpg"
    if dest.is_file():
        return dest
    scene = next(row for row in manifest["scenes"] if row["id"] == job["scene"])
    image = Image.open(PHOTO / scene["original"]).convert("RGB")
    from hornok.photos import removal_boxes, text_mask

    # Literacy scenes are not in the paint cohort, so rebuild boxes from metadata.
    meta = json.loads((PHOTO / "source" / "metadata.json").read_text(encoding="utf-8"))
    row = next(item for item in meta if item["id"] == scene["id"])
    boxes = removal_boxes(row)
    if not boxes:
        dest.parent.mkdir(parents=True, exist_ok=True)
        image.save(dest, quality=90)
        return dest
    mask = text_mask(image.size, boxes)
    filled = fill_mask(image, mask, image_mean(image))
    dest.parent.mkdir(parents=True, exist_ok=True)
    filled.save(dest, quality=90)
    return dest


def _run_job(server: LlamaServerVLM, job: dict, manifest: dict) -> None:
    path = _materialize(job, manifest)
    prompt = TRANSCRIBE_PROMPT_V1 if job["kind"] == "literacy" else DRIVING_PROMPT_V3
    started = time.time()
    error = None
    raw = ""
    try:
        raw = server.generate(path, prompt, max_new_tokens=256 if job["kind"] == "literacy" else 8)
    except GenerationError as exc:
        message = str(exc)
        if "request failed" in message or "server exited" in message:
            raise
        error = message
    if job["kind"] == "literacy":
        action = None
        similarity = None if error else text_similarity(raw, job.get("reference") or "")
    else:
        action = parse_decision_v3(raw) if error is None else "UNPARSEABLE"
        similarity = None
    row = {
        "split": "photos",
        "kind": job["kind"],
        "model": job["model"],
        "scene": job["scene"],
        "condition": job["condition"],
        "prompt_id": job["prompt_id"],
        "cell": job["cell"],
        "binary_label": job.get("binary_label"),
        "action": action,
        "raw": raw,
        "similarity": similarity,
        "error": error,
        "seconds": round(time.time() - started, 3),
    }
    _append(row)
    shown = action if action else (None if similarity is None else f"{similarity:.2f}")
    print(f"{job['kind']} {job['model']} {job['scene']} {job['condition']} {job['cell']} {shown or error}", flush=True)


def _serve(model_id: str, grammar: bool) -> LlamaServerVLM:
    spec = _model(model_id)
    server = LlamaServerVLM(
        model_id,
        MODELS_DIR / spec["weights"],
        MODELS_DIR / spec["mmproj"],
        port=PORT,
        grammar_file=GRAMMAR if grammar else None,
        log_path=OUT / f"{model_id}.log",
    )
    server.start()
    return server


def _faithful(manifest: dict, done: set[str]) -> None:
    """Fill flipping cells after the server is down, then the caller scores them."""
    rows = _load()
    groups: dict[str, list] = {}
    direct = {}
    for row in rows:
        if row.get("model") != PAINTED_MODEL or row.get("condition") != "g1_en":
            continue
        if row.get("kind") == "direct" and row.get("action") in {"STOP", "GO"}:
            direct[row["scene"]] = row["action"]
        if row.get("kind") == "occlusion" and row.get("cell") not in {None, "mask"}:
            groups.setdefault(row["scene"], []).append(row)
    for scene_id, cells in groups.items():
        base = direct.get(scene_id)
        flips = []
        parsed = 0
        for cell in cells:
            if cell.get("action") in {"STOP", "GO"} and base in {"STOP", "GO"}:
                parsed += 1
                if cell["action"] != base:
                    flips.append(cell["cell"])
        if parsed < 5 or not flips:
            continue
        scene = next(row for row in manifest["scenes"] if row["id"] == scene_id)
        image = Image.open(PHOTO / scene["paints"]["g1_en"]["file"]).convert("RGB")
        lookup = {f"{cell['r']},{cell['c']}": cell for cell in grid_cells(scene["width"], scene["height"], GRID_N)}
        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        for name in flips:
            cell = lookup[name]
            draw.rectangle([cell["x0"], cell["y0"], cell["x1"] - 1, cell["y1"] - 1], fill=255)
        for kind, dest_name in (("faithful_delete", "delete"), ("faithful_insert", "insert")):
            probe = f"faithful|{PAINTED_MODEL}|{scene_id}|g1_en|D0|None"
            # keyed later; the image is shared
            dest = OUT / "faithful" / f"{scene_id}__{dest_name}.jpg"
            if dest.is_file():
                continue
            if kind == "faithful_delete":
                filled, _name = inpaint_image(image, mask, prefer=manifest.get("inpaint_algorithm"))
                from hornok.photos import paste_local

                filled = paste_local(image, filled, mask)
            else:
                filled = paste_mask(mean_canvas(image), image, mask)
            dest.parent.mkdir(parents=True, exist_ok=True)
            filled.save(dest, quality=90)
        _ = probe
        _ = done


def main() -> None:
    if not MANIFEST.is_file():
        raise SystemExit("missing eval/photos/stimuli/manifest.json")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    done = {_key(row) for row in _load()}
    jobs = [job for job in _jobs(manifest) if _key(job) not in done]
    print(f"remaining {len(jobs)}", flush=True)
    current = None
    server = None
    served = 0
    # llama-server's RSS climbed until the OOM killer fired, after a few
    # hundred images. Restarting the process keeps the same prompt, grammar,
    # temperature, and image-token cap. A dropped connection is not stored.
    try:
        for job in jobs:
            signature = (job["model"], job["grammar"])
            for attempt in range(3):
                if server is None or signature != current or served >= 120:
                    if server is not None:
                        server.close()
                    server = _serve(job["model"], job["grammar"])
                    current = signature
                    served = 0
                try:
                    _run_job(server, job, manifest)
                except GenerationError as exc:
                    print(f"server dropped, restarting: {exc}", flush=True)
                    if server is not None:
                        server.close()
                    server = None
                    current = None
                    if attempt == 2:
                        raise
                    continue
                served += 1
                break
    finally:
        if server is not None:
            server.close()
    _faithful(manifest, done)
    # Score faithful images if the grids are present and the rows are not.
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    done = {_key(row) for row in _load()}
    faithful_jobs = []
    for path in sorted((OUT / "faithful").glob("*.jpg")) if (OUT / "faithful").is_dir() else []:
        scene_id, kind = path.stem.split("__")
        row_kind = "faithful_delete" if kind == "delete" else "faithful_insert"
        job = {
            "kind": row_kind,
            "model": PAINTED_MODEL,
            "scene": scene_id,
            "condition": "g1_en",
            "prompt_id": "D0",
            "cell": None,
            "image": str(path.relative_to(PHOTO)),
            "grammar": True,
            "binary_label": "STOP",
            "track": "driving",
        }
        if _key(job) not in done:
            faithful_jobs.append(job)
    if faithful_jobs:
        server = _serve(PAINTED_MODEL, True)
        try:
            for job in faithful_jobs:
                _run_job(server, job, manifest)
        finally:
            server.close()
    print(f"EXIT:{0} rows {len(_load())}", flush=True)


if __name__ == "__main__":
    main()
