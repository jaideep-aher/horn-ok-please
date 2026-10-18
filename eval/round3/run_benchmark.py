"""Round-3 benchmark. Resume-safe. One stored completion per trial.

The gate is scored before any attack. Models that fail are not attacked.
See eval/round3/preregistration.md, which must exist before this process
writes a scored row.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from hornok.defense import isolate_instructions  # noqa: E402
from hornok.gemini import GeminiVLM, gemini_api_key, gemini_model_id  # noqa: E402
from hornok.harness import GenerationError  # noqa: E402
from hornok.llama_server import LlamaServerVLM  # noqa: E402
from hornok.metrics import text_similarity  # noqa: E402
from hornok.parse import parse_decision_v3, strip_echo  # noqa: E402
from hornok.prompts import (  # noqa: E402
    DEFENSE_PROMPT_V3,
    DRIVING_PROMPT_V3,
    TRANSCRIBE_PROMPT_V1,
    ocr_defense_prompt_v3,
)
from hornok.round3 import (  # noqa: E402
    MODELS,
    TIE_ORDER,
    evaluate_binary_gate,
    is_reader,
    load_round2_reader_means,
)

MANIFEST = ROOT / "eval" / "round3" / "stimuli" / "manifest.json"
PROTOCOL = ROOT / "eval" / "round3" / "preregistration.md"
OUT_DIR = ROOT / "eval" / "round3" / "results"
PREDICTIONS = OUT_DIR / "predictions.jsonl"
GATE_PATH = OUT_DIR / "gate.json"
SMOKE_PATH = OUT_DIR / "smoke.jsonl"
GRAMMAR = ROOT / "eval" / "round3" / "action.gbnf"
SMOKE_IMAGE = ROOT / "eval" / "round2" / "stimuli" / "clean" / "slow_edge.png"
PORT = 18021
IMAGE_TOKENS = 512
SMOKE_LIMIT_S = 90.0
G2_BUDGET_S = 45 * 60
DEFENSE_EXTRA_BUDGET_S = 90 * 60


def _key(row: dict) -> str:
    return "|".join(
        [
            str(row.get("task")),
            str(row.get("model")),
            str(row.get("scene")),
            str(row.get("condition")),
            str(row.get("script") or "-"),
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


def _norm(text: str) -> str:
    return " ".join((text or "").split()).casefold()


def _scenes(manifest: dict) -> list[dict]:
    return list(manifest["scenes"])


def _gate_jobs(model: str, manifest: dict) -> list[dict]:
    jobs = []
    for scene in _scenes(manifest):
        jobs.append(
            {
                "task": "gate",
                "model": model,
                "scene": scene["id"],
                "condition": "clean",
                "script": None,
                "defense": "none",
                "phrase": None,
                "binary_label": scene["binary_label"],
                "image": str(ROOT / "eval" / "round3" / "stimuli" / scene["clean_file"]),
                "prompt_id": "v3",
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
                "defense": "none",
                "phrase": None,
                "binary_label": None,
                "image": str(ROOT / "eval" / "round3" / "stimuli" / card["file"]),
                "prompt_id": "transcribe-v1",
                "reference": card["text"],
            }
        )
    return jobs


def _attack_jobs(model: str, manifest: dict, phrases: tuple[str, ...]) -> list[dict]:
    jobs = []
    root = ROOT / "eval" / "round3" / "stimuli"
    for scene in _scenes(manifest):
        if scene["binary_label"] != "STOP":
            continue
        for attack in scene["attacks"]:
            if attack["phrase"] not in phrases:
                continue
            jobs.append(
                {
                    "task": "attack",
                    "model": model,
                    "scene": scene["id"],
                    "condition": attack["phrase"],
                    "script": attack["script"],
                    "defense": "none",
                    "phrase": attack["phrase"],
                    "binary_label": "STOP",
                    "image": str(root / attack["file"]),
                    "prompt_id": "v3",
                }
            )
    return jobs


def _defense_jobs(model: str, manifest: dict) -> list[dict]:
    jobs = []
    root = ROOT / "eval" / "round3" / "stimuli"
    for scene in _scenes(manifest):
        if scene["binary_label"] == "STOP":
            for attack in scene["attacks"]:
                if attack["phrase"] != "G1":
                    continue
                for defense in ("prompt", "ocr"):
                    jobs.append(
                        {
                            "task": "defense",
                            "model": model,
                            "scene": scene["id"],
                            "condition": "G1",
                            "script": attack["script"],
                            "defense": defense,
                            "phrase": "G1",
                            "binary_label": "STOP",
                            "image": str(root / attack["file"]),
                            "prompt_id": "v3-defense" if defense == "prompt" else "v3-ocr",
                        }
                    )
        else:
            for defense in ("prompt", "ocr"):
                jobs.append(
                    {
                        "task": "defense",
                        "model": model,
                        "scene": scene["id"],
                        "condition": "clean",
                        "script": None,
                        "defense": defense,
                        "phrase": None,
                        "binary_label": "GO",
                        "image": str(root / scene["clean_file"]),
                        "prompt_id": "v3-defense" if defense == "prompt" else "v3-ocr",
                    }
                )
    return jobs


class _Local:
    def __init__(self, spec: dict, grammar: bool):
        self.spec = spec
        self.server = LlamaServerVLM(
            spec["id"],
            ROOT / spec["weights"],
            ROOT / spec["mmproj"],
            port=PORT,
            grammar_file=GRAMMAR if grammar else None,
            image_tokens=IMAGE_TOKENS,
            log_path=OUT_DIR / f"{spec['id']}.log",
        )

    def start(self) -> None:
        self.server.start()

    def generate(self, image: str, prompt: str, max_new_tokens: int) -> str:
        return self.server.generate(Path(image), prompt, max_new_tokens=max_new_tokens)

    def close(self) -> None:
        self.server.close()


class _Gemini:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.client = GeminiVLM(model_id)

    def start(self) -> None:
        return None

    def generate(self, image: str, prompt: str, max_new_tokens: int) -> str:
        del max_new_tokens
        schema = TRANSCRIBE_PROMPT_V1 not in prompt
        return self.client.generate(Path(image), prompt, schema=schema)

    def close(self) -> None:
        return None


def _prompt_for(job: dict, image: Path) -> str:
    if job["task"] == "literacy":
        return TRANSCRIBE_PROMPT_V1
    if job.get("defense") == "prompt":
        return DEFENSE_PROMPT_V3
    if job.get("defense") == "ocr":
        cleaned, report = isolate_instructions(Image_open(image))
        cache = OUT_DIR / "ocr"
        cache.mkdir(parents=True, exist_ok=True)
        cached = (
            cache
            / f"{job['model']}__{job['scene']}__{job['condition']}__{job.get('script') or 'na'}.png"
        )
        cleaned.save(cached)
        job["image"] = str(cached)
        job["ocr_transcript"] = report.get("transcript") or ""
        return ocr_defense_prompt_v3(job["ocr_transcript"])
    return DRIVING_PROMPT_V3


def Image_open(path: Path):
    from PIL import Image

    return Image.open(path).convert("RGB")


def _run_jobs(backend, jobs: list[dict], max_new_tokens: int) -> None:
    if not jobs:
        return
    done = {_key(row) for row in _load_rows()}
    pending = [job for job in jobs if _key(job) not in done]
    if not pending:
        print(f"nothing pending ({len(jobs)} already stored)", flush=True)
        return
    backend.start()
    try:
        for index, job in enumerate(pending, start=1):
            started = time.time()
            raw = ""
            error = None
            try:
                image = Path(job["image"])
                prompt = _prompt_for(job, image)
                image = Path(job["image"])
                raw = backend.generate(str(image), prompt, max_new_tokens)
            except GenerationError as exc:
                error = str(exc)
                # One infrastructure retry if the local server died.
                if "exited" in error or "request failed" in error:
                    try:
                        backend.close()
                        backend.start()
                        raw = backend.generate(str(image), prompt, max_new_tokens)
                        error = None
                    except GenerationError as again:
                        error = str(again)
            except Exception as exc:
                error = str(exc)
            seconds = time.time() - started
            if job["task"] == "literacy":
                action = ""
            else:
                action = (
                    "UNPARSEABLE"
                    if error or not raw
                    else parse_decision_v3(strip_echo(raw, prompt))
                )
            row = {
                "round": 3,
                "task": job["task"],
                "model": job["model"],
                "scene": job["scene"],
                "condition": job["condition"],
                "script": job.get("script"),
                "defense": job.get("defense") or "none",
                "phrase": job.get("phrase"),
                "binary_label": job.get("binary_label"),
                "prompt_id": job.get("prompt_id"),
                "action": action,
                "raw": (raw or "")[:2000],
                "error": error,
                "seconds": round(seconds, 3),
                "image_tokens": IMAGE_TOKENS,
                "reference": job.get("reference"),
                "ocr_transcript": job.get("ocr_transcript"),
            }
            if job["task"] == "literacy" and job.get("reference"):
                hyp = _norm(raw)
                ref = _norm(job["reference"])
                row["similarity"] = None if error else text_similarity(hyp, ref)
                row["exact"] = (not error) and hyp == ref
            _append(row)
            label = row["action"] or f"sim={row.get('similarity')}"
            phrase = job.get("phrase") or ""
            script = job.get("script") or ""
            print(
                f"  {index}/{len(pending)} {job['task']} {job['scene']} "
                f"{phrase} {script} {job.get('defense')} -> {label} ({seconds:.1f}s)",
                flush=True,
            )
    finally:
        backend.close()


def _gate_table(model_ids: list[str]) -> list[dict]:
    rows = [row for row in _load_rows() if row["task"] == "gate"]
    table = []
    for model in model_ids:
        mine = [row for row in rows if row["model"] == model]
        if len(mine) != 40:
            continue
        scored = evaluate_binary_gate(mine, 20, 20)
        scored["model"] = model
        table.append(scored)
    return table


def _write_gate(table: list[dict], extra: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"round": 3, "models": table, **extra}
    GATE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _median_clean(model: str) -> float | None:
    seconds = [
        row["seconds"]
        for row in _load_rows()
        if row["model"] == model and row["task"] == "gate" and row.get("seconds") is not None
    ]
    if not seconds:
        return None
    return float(statistics.median(seconds))


def _already_enrolled(model: str) -> bool:
    if any(row["model"] == model and row["task"] == "gate" for row in _load_rows()):
        return True
    if not SMOKE_PATH.is_file():
        return False
    for line in SMOKE_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("model") == model and record.get("enrolled") is True:
            return True
    return False


def _smoke_gemma(spec: dict) -> bool:
    """Return True if Gemma Q4 may be enrolled. The smoke image is not scored."""
    if _already_enrolled(spec["id"]):
        print(f"smoke {spec['id']}: already enrolled, not repeated", flush=True)
        return True
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    backend = _Local(spec, grammar=True)
    started = time.time()
    error = None
    raw = ""
    try:
        backend.start()
        raw = backend.generate(str(SMOKE_IMAGE), DRIVING_PROMPT_V3, 8)
    except GenerationError as exc:
        error = str(exc)
    finally:
        backend.close()
    seconds = time.time() - started
    record = {
        "model": spec["id"],
        "image": "eval/round2/stimuli/clean/slow_edge.png",
        "scored": False,
        "seconds": round(seconds, 3),
        "raw": raw[:200],
        "error": error,
        "enrolled": error is None and seconds <= SMOKE_LIMIT_S,
    }
    with SMOKE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    print(
        f"smoke {spec['id']}: {seconds:.1f}s enrolled={record['enrolled']} error={error}",
        flush=True,
    )
    return record["enrolled"]


def _literacy_mean(model: str) -> float | None:
    sims = [
        row["similarity"]
        for row in _load_rows()
        if row["model"] == model
        and row["task"] == "literacy"
        and row.get("script") == "deva"
        and row.get("similarity") is not None
    ]
    if len(sims) != 4:
        return None
    return sum(sims) / len(sims)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=("llama", "gemini"), default="llama")
    args = parser.parse_args()
    if not PROTOCOL.is_file():
        print("refusing to score: eval/round3/preregistration.md is missing", flush=True)
        return 2
    if not MANIFEST.is_file():
        print("missing stimuli manifest; run eval/round3/build_stimuli.py", flush=True)
        return 2
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    if args.backend == "gemini":
        if not gemini_api_key():
            print("GEMINI_API_KEY is not set. Gemini was not called.", flush=True)
            return 0
        model_id = "gemini:" + gemini_model_id()
        print(f"gemini model {model_id}", flush=True)
        backend = _Gemini(gemini_model_id())
        _run_jobs(backend, _gate_jobs(model_id, manifest), 16)
        table = _gate_table([model_id])
        passers = [row["model"] for row in table if row["passed"]]
        _write_gate(table, {"backend": "gemini", "passers": passers})
        if not passers:
            print("gemini did not pass the gate; attacks were not run", flush=True)
            return 0
        _run_jobs(backend, _attack_jobs(model_id, manifest, ("G1", "B1", "G2")), 16)
        _run_jobs(backend, _defense_jobs(model_id, manifest), 16)
        return 0

    enrolled = []
    for spec in MODELS:
        if spec["optional"]:
            if not _smoke_gemma(spec):
                print(f"dropped {spec['id']} on the smoke rule", flush=True)
                continue
        enrolled.append(spec)

    reader_means = load_round2_reader_means(ROOT / "eval" / "round2" / "results" / "summary.json")

    for spec in enrolled:
        model = spec["id"]
        print(f"== gate {model}", flush=True)
        if model == "gemma3-4b-q4":
            _run_jobs(_Local(spec, grammar=False), _literacy_jobs(model, manifest), 64)
            mean = _literacy_mean(model)
            reader_means[model] = mean
            print(f"  devanagari mean {mean}", flush=True)
        _run_jobs(_Local(spec, grammar=True), _gate_jobs(model, manifest), 8)

    table = _gate_table([spec["id"] for spec in enrolled])
    for row in table:
        print(
            f"GATE {row['model']} BA={row['balanced_accuracy']:.3f} "
            f"STOP={row['recall_stop']:.3f} GO={row['recall_go']:.3f} "
            f"unparsed={row['unparsed_rate']:.3f} passed={row['passed']}",
            flush=True,
        )
    order = {name: index for index, name in enumerate(TIE_ORDER)}
    passers = sorted(
        [row for row in table if row["passed"]],
        key=lambda row: (-row["balanced_accuracy"], order.get(row["model"], 99)),
    )
    passer_ids = [row["model"] for row in passers]
    medians = {model: _median_clean(model) for model in passer_ids}
    slowest = max(medians.values()) if medians else None
    run_g2 = False
    if passer_ids and slowest is not None:
        run_g2 = len(passer_ids) * 20 * 4 * slowest <= G2_BUDGET_S
    phrases = ("G1", "B1", "G2") if run_g2 else ("G1", "B1")
    _write_gate(
        table,
        {
            "backend": "llama",
            "passers": passer_ids,
            "reader_means": reader_means,
            "readers": {model: is_reader(mean) for model, mean in reader_means.items()},
            "median_clean_seconds": medians,
            "run_g2": run_g2,
            "dropped": [
                spec["id"]
                for spec in MODELS
                if spec["id"] not in {row["model"] for row in table}
                and spec["id"] not in {s["id"] for s in enrolled}
            ],
        },
    )
    if not passer_ids:
        print("no model passed the gate; attacks were not run", flush=True)
        return 0

    by_id = {spec["id"]: spec for spec in enrolled}
    for model in passer_ids:
        print(f"== attack {model} phrases={phrases}", flush=True)
        _run_jobs(_Local(by_id[model], grammar=True), _attack_jobs(model, manifest, phrases), 8)

    primary = passer_ids[0]
    defense_models = [primary]
    extra_seconds = 0.0
    for model in passer_ids[1:]:
        median = medians.get(model) or slowest or 30.0
        # 160 G1 defense images + 40 clean GO defense images.
        extra_seconds += 200 * median
    if extra_seconds <= DEFENSE_EXTRA_BUDGET_S:
        defense_models = list(passer_ids)
    for model in defense_models:
        print(f"== defense {model}", flush=True)
        _run_jobs(_Local(by_id[model], grammar=True), _defense_jobs(model, manifest), 8)
    print(f"done. primary={primary} defenses={defense_models}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
