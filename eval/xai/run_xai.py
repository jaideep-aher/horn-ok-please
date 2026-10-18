"""Score the locked explanation protocol. Resume-safe. Does not open round 3."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from PIL import Image  # noqa: E402

from hornok.devsplit import DEV_MODELS, DEV_PROMPTS, dev_specs  # noqa: E402
from hornok.harness import GenerationError  # noqa: E402
from hornok.llama_server import LlamaServerVLM  # noqa: E402
from hornok.parse import parse_decision_v3  # noqa: E402
from hornok.prompts import DRIVING_PROMPT_V3  # noqa: E402
from hornok.scenes import render_spec  # noqa: E402
from hornok.xai import (  # noqa: E402
    GAZE_MODELS,
    PAINTED_MODEL,
    REASON_PROMPT_V1,
    fill_rect,
    gaze_rows,
    grid_cells,
    image_mean,
    inpaint_image,
    mean_canvas,
    paste_mask,
)

PROTOCOL = ROOT / "eval" / "xai" / "protocol.md"
MANIFEST = ROOT / "eval" / "xai" / "stimuli" / "manifest.json"
DEV_PREDICTIONS = ROOT / "eval" / "dev" / "results" / "predictions.jsonl"
OUT = ROOT / "eval" / "xai" / "results"
PREDICTIONS = OUT / "predictions.jsonl"
GRAMMAR = ROOT / "eval" / "round3" / "action.gbnf"
PORT = 18023
STIM = ROOT / "eval" / "xai" / "stimuli"


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


def _dev_meta() -> dict[str, dict]:
    meta = {}
    for spec in dev_specs():
        _image, rendered = render_spec(spec, seed=0)
        meta[spec["id"]] = {
            "hazard_bbox": rendered["hazard_bbox"],
            "hazard": spec["hazard"],
        }
    return meta


def _gaze() -> list[dict]:
    rows = [json.loads(line) for line in DEV_PREDICTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    meta = _dev_meta()
    chosen = []
    for row in gaze_rows(rows):
        info = meta[row["scene"]]
        chosen.append({**row, "hazard_bbox": info["hazard_bbox"], "hazard": info["hazard"]})
    return chosen


def _jobs(manifest: dict, gaze: list[dict]) -> list[dict]:
    jobs = []
    for scene in manifest["scenes"]:
        files = {"clean": scene["clean_file"]}
        for condition, paint in scene["paints"].items():
            files[condition] = paint["file"]
            jobs.append(_direct(scene, condition, paint["inpaint"], "inpaint"))
            jobs.append(_direct(scene, condition, paint["insertion"], "insertion"))
            jobs.append(_reason(scene["id"], condition, paint["file"]))
        for condition, rel in files.items():
            jobs.append(_direct(scene, condition, rel, "direct"))
        jobs.append(_reason(scene["id"], "clean", scene["clean_file"]))
        paint = scene["paints"]["g1_en"]
        for cell in grid_cells():
            jobs.append(_occlusion(PAINTED_MODEL, scene["id"], "g1_en", "D0", cell, paint["file"], "xai"))
    for row in gaze:
        image = f"eval/dev/stimuli/clean/{row['scene']}.png"
        for cell in grid_cells():
            jobs.append(
                _occlusion(row["model"], row["scene"], "clean", row["prompt_id"], cell, image, "dev")
            )
    dev_ids = [spec["id"] for spec in dev_specs()]
    for model in GAZE_MODELS:
        for scene_id in dev_ids:
            jobs.append(
                {
                    "kind": "reason",
                    "model": model,
                    "scene": scene_id,
                    "condition": "clean",
                    "prompt_id": "R1",
                    "cell": None,
                    "source": "dev",
                    "image": f"eval/dev/stimuli/clean/{scene_id}.png",
                    "grammar": False,
                }
            )
    return jobs


def _direct(scene: dict, condition: str, rel: str, kind: str) -> dict:
    return {
        "kind": kind,
        "model": PAINTED_MODEL,
        "scene": scene["id"],
        "condition": condition,
        "prompt_id": "D0",
        "cell": None,
        "binary_label": scene["binary_label"],
        "image": f"eval/xai/stimuli/{rel}",
        "grammar": True,
        "source": "xai",
    }


def _reason(scene_id: str, condition: str, rel: str) -> dict:
    return {
        "kind": "reason",
        "model": PAINTED_MODEL,
        "scene": scene_id,
        "condition": condition,
        "prompt_id": "R1",
        "cell": None,
        "image": f"eval/xai/stimuli/{rel}",
        "grammar": False,
        "source": "xai",
    }


def _occlusion(model: str, scene: str, condition: str, prompt_id: str, cell: dict, rel: str, source: str) -> dict:
    return {
        "kind": "occlusion",
        "model": model,
        "scene": scene,
        "condition": condition,
        "prompt_id": prompt_id,
        "cell": f"{cell['r']},{cell['c']}",
        "image": rel if rel.startswith("eval/") else f"eval/xai/stimuli/{rel}",
        "grammar": True,
        "source": source,
        "_cell": cell,
    }


def _server(model_id: str, grammar: bool) -> LlamaServerVLM:
    spec = next(row for row in DEV_MODELS if row["id"] == model_id)
    return LlamaServerVLM(
        model_id,
        ROOT / spec["weights"],
        ROOT / spec["mmproj"],
        port=PORT,
        grammar_file=GRAMMAR if grammar else None,
        image_tokens=512,
        log_path=OUT / f"{model_id}.log",
    )


def _run_job(server: LlamaServerVLM, job: dict) -> None:
    image_path = _materialize(job)
    started = time.time()
    raw = ""
    error = None
    try:
        prompt = REASON_PROMPT_V1 if job["kind"] == "reason" else _prompt(job)
        raw = server.generate(image_path, prompt, 96 if job["kind"] == "reason" else 8)
    except GenerationError as exc:
        error = str(exc)
    action = None
    if job["kind"] == "reason":
        action = None
    elif error is None:
        action = parse_decision_v3(raw)
    row = {
        "split": "xai",
        "kind": job["kind"],
        "model": job["model"],
        "scene": job["scene"],
        "condition": job["condition"],
        "prompt_id": job["prompt_id"],
        "cell": job["cell"],
        "source": job.get("source"),
        "binary_label": job.get("binary_label"),
        "action": action,
        "raw": raw,
        "error": error,
        "seconds": round(time.time() - started, 3),
    }
    _append(row)
    print(
        f"{job['kind']} {job['model']} {job['scene']} {job['condition']} {job['cell']} {action or error}",
        flush=True,
    )


def _prompt(job: dict) -> str:
    if job.get("source") == "dev" and job["kind"] != "reason":
        return DEV_PROMPTS[job["prompt_id"]]
    return DRIVING_PROMPT_V3


def _materialize(job: dict) -> Path:
    source = ROOT / job["image"]
    if job["kind"] != "occlusion":
        return source
    cell = job["_cell"]
    dest = OUT / "occlusion" / f"{job['model']}__{job['scene']}__{job['condition']}__{job['prompt_id']}__{job['cell']}.png"
    if dest.is_file():
        return dest
    image = Image.open(source).convert("RGB")
    color = image_mean(image)
    filled = fill_rect(image, cell, color)
    dest.parent.mkdir(parents=True, exist_ok=True)
    filled.save(dest)
    return dest


def _faithful_jobs(manifest: dict, gaze: list[dict], done: set[str]) -> list[dict]:
    """Inpaint the flipping cells. Skipped when the map has no flip."""
    rows = _load()
    by_group: dict[tuple, list] = {}
    for row in rows:
        if row.get("kind") != "occlusion" or row.get("error"):
            continue
        key = (row["model"], row["scene"], row["condition"], row["prompt_id"])
        by_group.setdefault(key, []).append(row)
    direct = {}
    for row in rows:
        if row.get("kind") == "direct" and row.get("action") in {"STOP", "GO"}:
            direct[(row["model"], row["scene"], row["condition"], row["prompt_id"])] = row["action"]
    for row in gaze:
        direct[(row["model"], row["scene"], "clean", row["prompt_id"])] = row["action"]
    jobs = []
    for key, cells in by_group.items():
        model, scene, condition, prompt_id = key
        prompt_key = "D0" if str(scene).startswith("xai_") else prompt_id
        base_action = direct.get((model, scene, condition, prompt_key))
        flips = []
        parsed = 0
        for cell in cells:
            if cell.get("action") in {"STOP", "GO"} and base_action in {"STOP", "GO"}:
                parsed += 1
                if cell["action"] != base_action:
                    flips.append(cell["cell"])
        if parsed < 5 or not flips:
            continue
        for kind in ("faithful_delete", "faithful_insert"):
            probe = {
                "kind": kind,
                "model": model,
                "scene": scene,
                "condition": condition,
                "prompt_id": prompt_id,
                "cell": None,
            }
            if _key(probe) in done:
                continue
            jobs.append(
                {
                    **probe,
                    "flips": flips,
                    "grammar": True,
                    "source": "xai" if str(scene).startswith("xai_") else "dev",
                }
            )
    return jobs


def _faithful_image(job: dict, manifest: dict) -> Path:
    kind = job["kind"]
    dest = OUT / "faithful" / f"{job['model']}__{job['scene']}__{job['condition']}__{job['prompt_id']}__{kind}.png"
    if dest.is_file():
        return dest
    if str(job["scene"]).startswith("xai_"):
        scene = next(row for row in manifest["scenes"] if row["id"] == job["scene"])
        rel = scene["paints"][job["condition"]]["file"] if job["condition"] != "clean" else scene["clean_file"]
        source = STIM / rel
    else:
        source = ROOT / "eval" / "dev" / "stimuli" / "clean" / f"{job['scene']}.png"
    image = Image.open(source).convert("RGB")
    mask = Image.new("L", image.size, 0)
    from PIL import ImageDraw

    draw = ImageDraw.Draw(mask)
    lookup = {f"{cell['r']},{cell['c']}": cell for cell in grid_cells(image.size[0], image.size[1])}
    for name in job["flips"]:
        cell = lookup[name]
        draw.rectangle([cell["x0"], cell["y0"], cell["x1"] - 1, cell["y1"] - 1], fill=255)
    if kind == "faithful_delete":
        filled, _algorithm = inpaint_image(image, mask, prefer=manifest.get("inpaint_algorithm"))
    else:
        filled = paste_mask(mean_canvas(image), image, mask)
    dest.parent.mkdir(parents=True, exist_ok=True)
    filled.save(dest)
    return dest


def main() -> int:
    if not PROTOCOL.is_file():
        print("refusing: eval/xai/protocol.md is missing", flush=True)
        return 2
    if not MANIFEST.is_file():
        print("missing xai stimuli; run eval/xai/build_stimuli.py", flush=True)
        return 2
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    gaze = _gaze()
    (OUT / "gaze_cohort.json").write_text(json.dumps(gaze, indent=2) + "\n", encoding="utf-8")
    print(f"gaze cohort {len(gaze)}", flush=True)
    pending_all = _jobs(manifest, gaze)
    done = {_key(row) for row in _load()}
    order = [PAINTED_MODEL, "gemma3-4b-q8"]
    for grammar in (True, False):
        for model in order:
            batch = [
                job
                for job in pending_all
                if job["model"] == model and job["grammar"] is grammar and _key(job) not in done
            ]
            if not batch:
                continue
            server = _server(model, grammar)
            try:
                server.start()
                for job in batch:
                    _run_job(server, job)
                    done.add(_key(job))
            finally:
                server.close()
    faithful = _faithful_jobs(manifest, gaze, done)
    by_model: dict[str, list] = {}
    for job in faithful:
        by_model.setdefault(job["model"], []).append(job)
    for model, batch in by_model.items():
        server = _server(model, True)
        try:
            server.start()
            for job in batch:
                image = _faithful_image(job, manifest)
                job["image"] = str(image.relative_to(ROOT))
                job["_cell"] = {"r": 0, "c": 0, "x0": 0, "y0": 0, "x1": 1, "y1": 1}
                # _materialize only special-cases occlusion. Point the job at the png.
                job["kind_run"] = job["kind"]
                _run_prepared(server, job, image)
                done.add(_key(job))
        finally:
            server.close()
    print(f"stored {len(_load())}", flush=True)
    return 0


def _run_prepared(server: LlamaServerVLM, job: dict, image: Path) -> None:
    started = time.time()
    raw = ""
    error = None
    try:
        raw = server.generate(image, _prompt(job), 8)
    except GenerationError as exc:
        error = str(exc)
    action = parse_decision_v3(raw) if error is None else None
    _append(
        {
            "split": "xai",
            "kind": job["kind"],
            "model": job["model"],
            "scene": job["scene"],
            "condition": job["condition"],
            "prompt_id": job["prompt_id"],
            "cell": None,
            "source": job.get("source"),
            "action": action,
            "raw": raw,
            "error": error,
            "seconds": round(time.time() - started, 3),
        }
    )
    print(f"{job['kind']} {job['model']} {job['scene']} {job['condition']} {action or error}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
