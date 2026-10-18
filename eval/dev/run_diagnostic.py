"""Run the prompt diagnostic. Resume-safe. Does not open round-3 images."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from hornok.devsplit import DEV_MODELS, DEV_PROMPTS  # noqa: E402
from hornok.harness import GenerationError  # noqa: E402
from hornok.llama_server import LlamaServerVLM  # noqa: E402
from hornok.parse import parse_decision_v3, strip_echo  # noqa: E402

MANIFEST = ROOT / "eval" / "dev" / "stimuli" / "manifest.json"
PROTOCOL = ROOT / "eval" / "dev" / "protocol.md"
OUT = ROOT / "eval" / "dev" / "results"
PREDICTIONS = OUT / "predictions.jsonl"
GRAMMAR = ROOT / "eval" / "round3" / "action.gbnf"
PORT = 18022


def _key(row: dict) -> str:
    return "|".join([row["model"], row["scene"], row["prompt_id"]])


def _load() -> list[dict]:
    if not PREDICTIONS.is_file():
        return []
    text = PREDICTIONS.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _append(row: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with PREDICTIONS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()


def main() -> int:
    if not PROTOCOL.is_file():
        print("refusing: eval/dev/protocol.md is missing", flush=True)
        return 2
    if not MANIFEST.is_file():
        print("missing dev stimuli; run eval/dev/build_stimuli.py", flush=True)
        return 2
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if any(not str(scene["id"]).startswith("dev_") for scene in manifest["scenes"]):
        print("refusing: a scene id is outside the dev split", flush=True)
        return 2
    done = {_key(row) for row in _load()}
    for spec in DEV_MODELS:
        pending = []
        for scene in manifest["scenes"]:
            for prompt_id in DEV_PROMPTS:
                row = {
                    "model": spec["id"],
                    "scene": scene["id"],
                    "prompt_id": prompt_id,
                    "binary_label": scene["binary_label"],
                    "stratum": scene["stratum"],
                    "image": str(ROOT / "eval" / "dev" / "stimuli" / scene["clean_file"]),
                }
                if _key(row) not in done:
                    pending.append(row)
        if not pending:
            print(f"skip {spec['id']}: nothing pending", flush=True)
            continue
        server = LlamaServerVLM(
            spec["id"],
            ROOT / spec["weights"],
            ROOT / spec["mmproj"],
            port=PORT,
            grammar_file=GRAMMAR,
            image_tokens=512,
            log_path=OUT / f"{spec['id']}.log",
        )
        server.start()
        try:
            for index, job in enumerate(pending, start=1):
                prompt = DEV_PROMPTS[job["prompt_id"]]
                started = time.time()
                error = None
                raw = ""
                try:
                    raw = server.generate(Path(job["image"]), prompt, max_new_tokens=8)
                except GenerationError as exc:
                    error = str(exc)
                    try:
                        server.close()
                        server.start()
                        raw = server.generate(Path(job["image"]), prompt, max_new_tokens=8)
                        error = None
                    except GenerationError as again:
                        error = str(again)
                if error or not raw:
                    action = "UNPARSEABLE"
                else:
                    action = parse_decision_v3(strip_echo(raw, prompt))
                _append(
                    {
                        "split": "dev",
                        "round": None,
                        "model": job["model"],
                        "scene": job["scene"],
                        "prompt_id": job["prompt_id"],
                        "binary_label": job["binary_label"],
                        "stratum": job["stratum"],
                        "action": action,
                        "raw": (raw or "")[:500],
                        "error": error,
                        "seconds": round(time.time() - started, 3),
                    }
                )
                print(
                    f"  {index}/{len(pending)} {job['prompt_id']} {job['scene']} -> {action}",
                    flush=True,
                )
        finally:
            server.close()
    print("diagnostic complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
