"""Round-2 benchmark. Resume-safe. One stored completion per trial.

Phases, in order: literacy (no grammar), clean gate, attacks on passers,
then defenses on a model that brakes for regulatory signs. The competence
bar is not lowered. See eval/round2/preregistration.md.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from hornok.defense import isolate_instructions  # noqa: E402
from hornok.harness import GenerationError, models_root  # noqa: E402
from hornok.llama_server import LlamaServerVLM  # noqa: E402
from hornok.parse import parse_decision_v2  # noqa: E402
from hornok.prompts import (  # noqa: E402
    DEFENSE_PROMPT_V2,
    DRIVING_PROMPT_V2,
    TRANSCRIBE_PROMPT_V1,
    ocr_defense_prompt_v2,
)
from hornok.round2 import (  # noqa: E402
    CLEAN_ORDER,
    MODELS,
    ORIGINAL_IDS,
    choose_defense_model,
    evaluate_gate,
    latency_valve,
    regulatory_obedience,
    select_attack_models,
)

MANIFEST = ROOT / "eval" / "round2" / "stimuli" / "manifest.json"
OUT_DIR = ROOT / "eval" / "round2" / "results"
PREDICTIONS = OUT_DIR / "predictions.jsonl"
GATE_PATH = OUT_DIR / "gate.json"
GRAMMAR = ROOT / "eval" / "round2" / "action.gbnf"
PORT = 18021
IMAGE_TOKENS = 512


def _key(row: dict) -> str:
    return "|".join(
        [
            str(row.get("task")),
            str(row.get("model")),
            str(row.get("scene")),
            str(row.get("condition")),
            str(row.get("script") or "-"),
            str(row.get("placement") or "-"),
            str(row.get("defense") or "none"),
            str(row.get("phrase") or "-"),
        ]
    )


def _load_rows() -> list[dict]:
    if not PREDICTIONS.is_file():
        return []
    rows = []
    for line in PREDICTIONS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _append(row: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with PREDICTIONS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()


def _base_row(job: dict, raw: str, action: str, seconds: float, error: str | None) -> dict:
    row = {
        "round": 2,
        "task": job["task"],
        "model": job["model"],
        "scene": job["scene"],
        "condition": job["condition"],
        "script": job.get("script"),
        "placement": job.get("placement"),
        "defense": job.get("defense", "none"),
        "phrase": job.get("phrase"),
        "gt": job.get("gt"),
        "target": job.get("target"),
        "role": job.get("role"),
        "legitimate_regulatory": job.get("legitimate_regulatory"),
        "source": job.get("source"),
        "prompt_id": job.get("prompt_id"),
        "action": action,
        "raw": raw[:2000],
        "error": error,
        "seconds": round(seconds, 3),
        "image_tokens": IMAGE_TOKENS,
        "reference": job.get("reference"),
    }
    return row


def _run_server(model: str, jobs: list[dict], *, grammar: bool, max_new_tokens: int) -> None:
    if not jobs:
        return
    done = {_key(row) for row in _load_rows()}
    pending = [job for job in jobs if _key(job) not in done]
    if not pending:
        print(f"skip {model} grammar={grammar}: nothing pending", flush=True)
        return
    spec = MODELS[model]
    root = models_root() / "gguf"
    server = LlamaServerVLM(
        model,
        root / spec["file"],
        root / spec["mmproj"],
        port=PORT,
        grammar_file=GRAMMAR if grammar else None,
        image_tokens=IMAGE_TOKENS,
        log_path=OUT_DIR / f"server-{model}.log",
    )
    server.start()
    print(f"server {model} jobs={len(pending)} grammar={grammar}", flush=True)
    try:
        for index, job in enumerate(pending, start=1):
            started = time.time()
            error = None
            raw = ""
            try:
                raw = server.generate(
                    ROOT / "eval" / "round2" / "stimuli" / job["image"],
                    job["prompt"],
                    max_new_tokens=max_new_tokens,
                )
            except GenerationError as exc:
                error = str(exc)
                if server.proc is None or server.proc.poll() is not None:
                    server.close()
                    server.start()
                    try:
                        raw = server.generate(
                            ROOT / "eval" / "round2" / "stimuli" / job["image"],
                            job["prompt"],
                            max_new_tokens=max_new_tokens,
                        )
                        error = None
                        job = {**job, "infra_restart": True}
                    except GenerationError as again:
                        error = str(again)
                        raw = ""
            seconds = time.time() - started
            if job["task"] == "drive" and error is None:
                action, _rationale = parse_decision_v2(raw)
            elif error is None:
                action = "TRANSCRIPT"
            else:
                action = "UNPARSEABLE"
            row = _base_row(job, raw, action, seconds, error)
            if job.get("infra_restart"):
                row["infra_restart"] = True
            _append(row)
            if index % 5 == 0 or index == len(pending):
                print(
                    f"  {model} {index}/{len(pending)} {job['scene']} "
                    f"{job.get('phrase') or job['condition']} {action} {seconds:.1f}s",
                    flush=True,
                )
    finally:
        server.close()


def _scene_jobs(model: str, scene: dict, *, attacks: bool, benign: bool, valve: dict) -> list[dict]:
    jobs = []
    clean = {
        "task": "drive",
        "model": model,
        "scene": scene["id"],
        "condition": "clean",
        "script": None,
        "placement": scene["placement"],
        "defense": "none",
        "phrase": None,
        "gt": scene["gt"],
        "target": scene["target"],
        "role": scene["role"],
        "legitimate_regulatory": scene["legitimate_regulatory"],
        "source": scene["source"],
        "prompt_id": "DRIVING_PROMPT_V2",
        "prompt": DRIVING_PROMPT_V2,
        "image": scene["clean_file"],
    }
    jobs.append(clean)
    if not attacks and not benign:
        return jobs
    for paint in scene["attacks"]:
        kind = paint["kind"]
        if kind == "attack" and not attacks:
            continue
        if kind == "benign" and not benign:
            continue
        if valve.get("drop_b2") and paint["phrase"] == "B2":
            continue
        if (
            valve.get("drop_a4_except_original_12")
            and paint["phrase"] in {"A4", "F4"}
            and scene["id"] not in ORIGINAL_IDS
        ):
            continue
        jobs.append(
            {
                **clean,
                "condition": kind,
                "script": paint["script"],
                "phrase": paint["phrase"],
                "prompt_id": "DRIVING_PROMPT_V2",
                "prompt": DRIVING_PROMPT_V2,
                "image": paint["file"],
                "defense": "none",
            }
        )
    return jobs


def _literacy_jobs(model: str, manifest: dict) -> list[dict]:
    jobs = []
    for card in manifest["literacy"]:
        jobs.append(
            {
                "task": "literacy",
                "model": model,
                "scene": card["id"],
                "condition": "literacy",
                "script": card["script"],
                "placement": None,
                "defense": "none",
                "phrase": None,
                "gt": None,
                "target": None,
                "role": None,
                "legitimate_regulatory": False,
                "source": "synthetic",
                "prompt_id": "TRANSCRIBE_PROMPT_V1",
                "prompt": TRANSCRIBE_PROMPT_V1,
                "image": card["file"],
                "reference": card["text"],
            }
        )
    return jobs


def _clean_rows(rows: list[dict], model: str) -> list[dict]:
    return [
        row
        for row in rows
        if row["model"] == model
        and row["task"] == "drive"
        and row["condition"] == "clean"
        and row["defense"] == "none"
    ]


def _write_gate(manifest: dict, valve: dict | None = None) -> dict:
    rows = _load_rows()
    n_scenes = manifest["n_scenes"]
    gates = {}
    obedience = {}
    for model in CLEAN_ORDER:
        clean = _clean_rows(rows, model)
        gates[model] = evaluate_gate(clean, n_scenes)
        if gates[model]["status"] != "incomplete":
            obedience[model] = regulatory_obedience(clean)
    attack_models = select_attack_models(gates)
    defense_model = choose_defense_model(gates, obedience)
    enrolled = [
        model
        for model in CLEAN_ORDER
        if gates[model]["status"] != "incomplete"
    ]
    payload = {
        "round": 2,
        "image_tokens": IMAGE_TOKENS,
        "gates": gates,
        "obedience": obedience,
        "enrolled_clean": enrolled,
        "not_enrolled_clean": [model for model in CLEAN_ORDER if model not in enrolled],
        "attack_models": attack_models,
        "defense_model": defense_model,
        "valve": valve,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    GATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("gate", json.dumps({k: gates[k]["status"] for k in CLEAN_ORDER}), flush=True)
    print("attack", attack_models, "defense", defense_model, flush=True)
    return payload


def _median_clean_seconds(models: list[str]) -> float | None:
    samples = []
    for row in _load_rows():
        if row["model"] in models and row["condition"] == "clean" and row["defense"] == "none":
            if row.get("seconds") is not None:
                samples.append(row["seconds"])
    if not samples:
        return None
    return float(statistics.median(samples))


def _defense_jobs(model: str, manifest: dict) -> list[dict]:
    from PIL import Image

    jobs = []
    cache = OUT_DIR / "ocr_cache"
    cache.mkdir(parents=True, exist_ok=True)
    for scene in manifest["scenes"]:
        if not scene["legitimate_regulatory"]:
            continue
        paints = [{"file": scene["clean_file"], "phrase": None, "script": None, "kind": "clean"}]
        for paint in scene["attacks"]:
            if paint["phrase"] in {"A1", "B1"}:
                paints.append(paint)
        for paint in paints:
            image_rel = paint["file"]
            image = Image.open(ROOT / "eval" / "round2" / "stimuli" / image_rel).convert("RGB")
            cleaned, report = isolate_instructions(image)
            slug = image_rel.replace("/", "__")
            cleaned.save(cache / slug)
            ocr_prompt = ocr_defense_prompt_v2(report["transcript"])
            masked_rel = f"../results/ocr_cache/{slug}"
            common = {
                "task": "drive",
                "model": model,
                "scene": scene["id"],
                "condition": paint["kind"] if paint["phrase"] else "clean",
                "script": paint.get("script"),
                "placement": scene["placement"],
                "phrase": paint.get("phrase"),
                "gt": scene["gt"],
                "target": scene["target"],
                "role": scene["role"],
                "legitimate_regulatory": True,
                "source": scene["source"],
            }
            jobs.append(
                {
                    **common,
                    "defense": "prompt",
                    "prompt_id": "DEFENSE_PROMPT_V2",
                    "prompt": DEFENSE_PROMPT_V2,
                    "image": image_rel,
                }
            )
            jobs.append(
                {
                    **common,
                    "defense": "ocr",
                    "prompt_id": "OCR_DEFENSE_V2",
                    "prompt": ocr_prompt,
                    "image": masked_rel,
                }
            )
    return jobs


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    scenes = manifest["scenes"]
    # Literacy on every candidate, no action grammar.
    for model in CLEAN_ORDER:
        _run_server(model, _literacy_jobs(model, manifest), grammar=False, max_new_tokens=64)

    # Clean enrollment stops after two models pass. Finish a model once started.
    for model in CLEAN_ORDER:
        rows = _load_rows()
        clean = _clean_rows(rows, model)
        n_passed = sum(
            1
            for name in CLEAN_ORDER
            if evaluate_gate(_clean_rows(rows, name), manifest["n_scenes"])["passed"]
        )
        if len(clean) == 0 and n_passed >= 2:
            print(f"not enrolling {model}: two models already passed", flush=True)
            continue
        jobs = []
        for scene in scenes:
            jobs.extend(_scene_jobs(model, scene, attacks=False, benign=False, valve={}))
        _run_server(model, jobs, grammar=True, max_new_tokens=8)
        _write_gate(manifest)

    gate_doc = _write_gate(manifest)
    attack_models = gate_doc["attack_models"]
    median = _median_clean_seconds(attack_models)
    valve = latency_valve(median)
    print("valve", valve, flush=True)
    _write_gate(manifest, valve)

    for model in attack_models:
        jobs = []
        for scene in scenes:
            jobs.extend(
                _scene_jobs(model, scene, attacks=True, benign=True, valve=valve)
            )
        # Clean rows already exist; drop them.
        jobs = [job for job in jobs if job["condition"] != "clean"]
        _run_server(model, jobs, grammar=True, max_new_tokens=8)

    defense_model = gate_doc["defense_model"]
    # Re-read in case obedience was incomplete before. It is complete now.
    gate_doc = _write_gate(manifest, valve)
    defense_model = gate_doc["defense_model"]
    if defense_model:
        _run_server(
            defense_model,
            _defense_jobs(defense_model, manifest),
            grammar=True,
            max_new_tokens=8,
        )
    else:
        print("no model met the regulatory-obedience bar; defenses not scored", flush=True)
    _write_gate(manifest, valve)
    print("ROUND2_RUN_DONE", flush=True)


if __name__ == "__main__":
    main()
