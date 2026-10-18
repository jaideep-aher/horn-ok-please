"""Run the pre-registered grid.

Reads eval/run_config.json if it exists, otherwise the full grid in
eval/preregistration.md. Appends to eval/results/predictions.jsonl and skips
trial ids that are already present, so a stopped run can continue. One attempt
per trial. Failures are stored as UNPARSEABLE rows with an error string.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from hornok.defense import isolate_instructions  # noqa: E402
from hornok.harness import build_backend  # noqa: E402
from hornok.metrics import text_similarity  # noqa: E402
from hornok.parse import parse_decision  # noqa: E402
from hornok.prompts import (  # noqa: E402
    DEFENSE_PROMPT_V1,
    DRIVING_PROMPT_V1,
    TRANSCRIBE_PROMPT_V1,
    ocr_defense_prompt,
)
from hornok.scenes import write_stimuli  # noqa: E402

PROMPTS = {"DRIVING_PROMPT_V1": DRIVING_PROMPT_V1, "DEFENSE_PROMPT_V1": DEFENSE_PROMPT_V1}

DEFAULT_CONFIG = {
    "prompt_id": "DRIVING_PROMPT_V1",
    "defense_prompt_id": "DEFENSE_PROMPT_V1",
    "models": [
        "smolvlm-256m-hf",
        "smolvlm-256m-f16",
        "smolvlm-256m-q4",
        "smolvlm-500m-hf",
    ],
    "defense_models": ["smolvlm-256m-f16", "smolvlm-256m-q4"],
    "placements": ["truck_rear"],
    "clean_defense_all_scenes": True,
    "note": "Default full grid from the preregistration. Replace this file to narrow.",
}


def normalize_text(text: str) -> str:
    collapsed = unicodedata.normalize("NFC", text or "")
    collapsed = " ".join(collapsed.replace("।", " ").split())
    return collapsed.casefold()


def trial_key(row: dict) -> str:
    return "|".join(
        [
            row.get("task", "drive"),
            row["model"],
            row["scene_id"],
            row.get("condition") or "",
            row.get("script") or "",
            row.get("placement") or "",
            row.get("defense") or "none",
        ]
    )


def load_config(path: Path) -> dict:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return dict(DEFAULT_CONFIG)


def ensure_stimuli(path: Path) -> dict:
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        return write_stimuli(path)
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def file_tag(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest[:16]


def build_jobs(manifest: dict, config: dict) -> list[dict]:
    placements = set(config["placements"])
    defense_models = set(config["defense_models"])
    jobs: list[dict] = []
    for model in config["models"]:
        for scene in manifest["scenes"]:
            for placement in placements:
                if placement not in scene["placements"]:
                    continue
                jobs.append(
                    {
                        "task": "drive",
                        "model": model,
                        "scene_id": scene["id"],
                        "condition": "clean",
                        "script": "",
                        "placement": placement,
                        "defense": "none",
                        "image": scene["clean_file"],
                        "gt": scene["gt"],
                        "target": scene["target"],
                        "role": scene["role"],
                        "legitimate_regulatory": scene["legitimate_regulatory"],
                    }
                )
                do_clean_defense = model in defense_models and (
                    config.get("clean_defense_all_scenes", True) or scene["legitimate_regulatory"]
                )
                if do_clean_defense:
                    for defense in ("prompt", "ocr"):
                        jobs.append(
                            {
                                **jobs[-1],
                                "defense": defense,
                            }
                        )
                for attack in scene["attacks"]:
                    if attack["placement"] != placement:
                        continue
                    base = {
                        "task": "drive",
                        "model": model,
                        "scene_id": scene["id"],
                        "condition": "attack",
                        "script": attack["script"],
                        "placement": placement,
                        "defense": "none",
                        "image": attack["file"],
                        "gt": scene["gt"],
                        "target": scene["target"],
                        "role": scene["role"],
                        "legitimate_regulatory": scene["legitimate_regulatory"],
                        "attack_text": attack["text"],
                    }
                    jobs.append(base)
                    if model in defense_models:
                        for defense in ("prompt", "ocr"):
                            jobs.append({**base, "defense": defense})
        for card in manifest["literacy"]:
            jobs.append(
                {
                    "task": "transcribe",
                    "model": model,
                    "scene_id": card["id"],
                    "condition": "transcribe",
                    "script": card["script"],
                    "placement": "",
                    "defense": "none",
                    "image": card["file"],
                    "reference": card["text"],
                }
            )
    return jobs


def _prompt_for(job: dict, config: dict, transcript: str) -> str:
    if job["task"] == "transcribe":
        return TRANSCRIBE_PROMPT_V1
    if job["defense"] == "none":
        return PROMPTS[config["prompt_id"]]
    if job["defense"] == "prompt":
        return PROMPTS[config["defense_prompt_id"]]
    return ocr_defense_prompt(transcript)


def _ocr_image(src: Path, cache: Path) -> tuple[Path, str]:
    """Return the masked image and the removed transcript. Cache by file hash."""
    tag = file_tag(src)
    out = cache / f"{tag}.png"
    sidecar = cache / f"{tag}.json"
    if out.is_file() and sidecar.is_file():
        report = json.loads(sidecar.read_text(encoding="utf-8"))
        return out, report.get("transcript", "")
    from PIL import Image

    cleaned, report = isolate_instructions(Image.open(src))
    cache.mkdir(parents=True, exist_ok=True)
    cleaned.save(out)
    sidecar.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    return out, report.get("transcript", "")


def run(config_path: Path, stimuli: Path, out_path: Path) -> None:
    config = load_config(config_path)
    manifest = ensure_stimuli(stimuli)
    jobs = build_jobs(manifest, config)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    if out_path.is_file():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(trial_key(json.loads(line)))
    meta = {
        "config": config,
        "n_jobs": len(jobs),
        "n_already_done": len(done),
        "stimuli": str(stimuli),
    }
    meta_path = out_path.parent / "run_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"{len(jobs)} jobs, {len(done)} already done", flush=True)

    by_model: dict[str, list[dict]] = {}
    for job in jobs:
        by_model.setdefault(job["model"], []).append(job)

    ocr_cache = out_path.parent / "ocr_cache"
    with out_path.open("a", encoding="utf-8") as handle:
        for model_name, model_jobs in by_model.items():
            pending = [job for job in model_jobs if trial_key(job) not in done]
            if not pending:
                print(f"skip {model_name}, complete", flush=True)
                continue
            print(f"loading {model_name} ({len(pending)} trials)", flush=True)
            backend = build_backend(model_name)
            try:
                for index, job in enumerate(pending, start=1):
                    image_path = stimuli / job["image"]
                    transcript = ""
                    if job["defense"] == "ocr":
                        image_path, transcript = _ocr_image(image_path, ocr_cache)
                    prompt = _prompt_for(job, config, transcript)
                    started = time.perf_counter()
                    error = ""
                    try:
                        raw = backend.generate(image_path, prompt)
                    except Exception as exc:  # stored, not swallowed silently
                        raw = ""
                        error = f"{type(exc).__name__}: {exc}"
                    seconds = round(time.perf_counter() - started, 3)
                    row = {
                        **job,
                        "prompt_id": config["prompt_id"],
                        "raw": raw[:2000],
                        "seconds": seconds,
                        "error": error,
                        "image_sha256_16": file_tag(image_path) if image_path.is_file() else "",
                        "smoke": False,
                    }
                    if job["task"] == "transcribe":
                        hyp = normalize_text(raw)
                        ref = normalize_text(job.get("reference") or "")
                        row["hypothesis"] = hyp
                        row["reference_norm"] = ref
                        row["similarity"] = text_similarity(hyp, ref)
                        row["exact"] = hyp == ref
                        row["action"] = ""
                    else:
                        action, rationale = parse_decision(raw)
                        row["action"] = action
                        row["rationale"] = rationale
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    handle.flush()
                    label = row.get("action") or f"sim={row.get('similarity')}"
                    print(
                        f"  [{index}/{len(pending)}] {trial_key(job)} -> {label} ({seconds}s)",
                        flush=True,
                    )
            finally:
                backend.close()


def main() -> None:
    config_path = ROOT / "eval" / "run_config.json"
    stimuli = ROOT / "eval" / "stimuli"
    out_path = ROOT / "eval" / "results" / "predictions.jsonl"
    run(config_path, stimuli, out_path)


if __name__ == "__main__":
    main()
