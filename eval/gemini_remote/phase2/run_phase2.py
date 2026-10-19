#!/usr/bin/env python3
"""Phase-2 Gemini runner (blocks 1, 3, 4 of the locked preregistration).

Uses the repo's own client, prompts, OCR defense, and run loop. Block 2 is
run_us.py. Model pinned to gemini-3.8-flash, thinking pinned to the stored
mode ("off"), no temperature. seed is sent only in block 1 (seed 2) and
block 4 (seeds 3, 4, 5).

Paths default to this checkout. Override with --repo, --out, --stim-root,
or PHASE2_REPO, PHASE2_OUT, PHASE2_STIM_ROOT. --stim-root is a checkout that
contains eval/round3/stimuli, the same layout as the stored run.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from hornok.gemini import GeminiVLM, gemini_api_key
from hornok.gemini_run import (
    StopRun,
    attack_jobs,
    load_manifest,
    load_rows,
    model_key,
    run_jobs,
    write_json,
)

MODEL = "gemini-3.8-flash"
HARD_CAP = 520  # every HTTP generate attempt, retries included
ERR_FRAC = 0.10
HERE = Path(__file__).resolve().parent


def _env_path(name: str) -> Path | None:
    raw = os.environ.get(name, "").strip()
    return Path(raw).expanduser() if raw else None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    repo = _env_path("PHASE2_REPO") or HERE.parents[2]
    parser = argparse.ArgumentParser(description="Run locked phase-2 blocks 1, 3, and 4.")
    parser.add_argument("--repo", type=Path, default=repo, help="Repository root.")
    parser.add_argument(
        "--out",
        type=Path,
        default=_env_path("PHASE2_OUT") or (HERE / "results"),
        help="Where JSONL, counts, and status are written.",
    )
    parser.add_argument(
        "--stim-root",
        type=Path,
        default=_env_path("PHASE2_STIM_ROOT") or repo,
        help="Checkout whose eval/round3/stimuli images are scored.",
    )
    return parser.parse_args(argv)


REPO = _env_path("PHASE2_REPO") or HERE.parents[2]
STIM_ROOT = _env_path("PHASE2_STIM_ROOT") or REPO
OUT = _env_path("PHASE2_OUT") or (HERE / "results")
COUNTS = OUT / "call_counts.json"


class Phase2VLM(GeminiVLM):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._thinking_mode = "off"  # stored rows used thinking_budget=0
        self.seed = None
        self.block = None
        self.counts = json.loads(COUNTS.read_text(encoding="utf-8")) if COUNTS.is_file() else {}
        inner = self._client.models.generate_content

        def counted(*call_args, **call_kwargs):
            if self.total("attempts") >= HARD_CAP:
                raise StopRun("call_cap", f"hard cap of {HARD_CAP} API attempts reached")
            self._bump("attempts")
            try:
                return inner(*call_args, **call_kwargs)
            except Exception as exc:
                self._bump("failed_attempts")
                message = str(exc).lower()
                seed_rejected = "seed" in message and (
                    "invalid" in message
                    or "unknown" in message
                    or "not supported" in message
                    or "400" in message
                )
                if seed_rejected:
                    raise StopRun("seed_rejected", f"API rejected seed: {exc}") from exc
                raise

        self._client.models.generate_content = counted

    def total(self, field):
        return sum(value.get(field, 0) for value in self.counts.values())

    def _bump(self, field):
        bucket = self.counts.setdefault(self.block, {})
        bucket[field] = bucket.get(field, 0) + 1
        COUNTS.write_text(json.dumps(self.counts, indent=2), encoding="utf-8")

    def _config(self, *, schema, max_output_tokens, mode):
        cfg = super()._config(schema=schema, max_output_tokens=max_output_tokens, mode=mode)
        if self.seed is not None:
            cfg.seed = int(self.seed)
        return cfg

    def generate(self, image_path, prompt, **kwargs):
        try:
            return super().generate(image_path, prompt, **kwargs)
        except Exception as exc:
            cause = exc
            while cause is not None:
                if isinstance(cause, StopRun):
                    raise cause
                cause = cause.__cause__
            raise


def g2_defense_jobs(model, manifest, stimuli):
    jobs = []
    for scene in manifest["scenes"]:
        if scene["binary_label"] == "STOP":
            for attack in scene["attacks"]:
                if attack["phrase"] != "G2":
                    continue
                for defense in ("prompt", "ocr"):
                    prompt_id = "v3-defense" if defense == "prompt" else "v3-ocr"
                    jobs.append(
                        {
                            "task": "defense",
                            "model": model,
                            "scene": scene["id"],
                            "condition": "G2",
                            "script": attack["script"],
                            "defense": defense,
                            "phrase": "G2",
                            "binary_label": "STOP",
                            "image": str(stimuli / attack["file"]),
                            "prompt_id": prompt_id,
                            "_scene": scene,
                            "_attack": attack,
                        }
                    )
        else:
            for defense in ("prompt", "ocr"):
                prompt_id = "v3-defense" if defense == "prompt" else "v3-ocr"
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
                        "image": str(stimuli / scene["clean_file"]),
                        "prompt_id": prompt_id,
                    }
                )
    return jobs


def check_errors(backend):
    del backend
    rows = []
    for path in OUT.glob("*.jsonl"):
        rows += load_rows(path)
    n_rows = len(rows)
    n_errors = sum(1 for row in rows if row.get("error"))
    if n_rows >= 20 and n_errors / n_rows > ERR_FRAC:
        raise StopRun("error_rate", f"{n_errors}/{n_rows} rows errored (>10%)")


def main(argv: list[str] | None = None) -> int:
    global REPO, STIM_ROOT, OUT, COUNTS
    args = parse_args(argv)
    REPO = args.repo
    STIM_ROOT = args.stim_root
    OUT = args.out
    COUNTS = OUT / "call_counts.json"
    key = gemini_api_key()
    if not key:
        print("no key")
        return 2
    manifest = load_manifest(STIM_ROOT)
    stimuli = STIM_ROOT / "eval" / "round3" / "stimuli"
    model = model_key(MODEL)
    backend = Phase2VLM(model_id=MODEL, api_key=key)
    plan = []
    g2_jobs = attack_jobs(model, manifest, stimuli, ("G2",))
    g2 = [job for job in g2_jobs if job["script"] in ("mr", "hi")]
    plan.append(("b1_g2_replication_seed2", 2, g2, "b1_g2_replication_seed2.jsonl"))
    defense_jobs = g2_defense_jobs(model, manifest, stimuli)
    plan.append(("b3_defenses_on_g2", None, defense_jobs, "b3_defenses_on_g2.jsonl"))
    for seed in (3, 4, 5):
        plan.append(
            (
                f"b4_g1_repeat_seed{seed}",
                seed,
                attack_jobs(model, manifest, stimuli, ("G1",)),
                f"b4_g1_repeat_seed{seed}.jsonl",
            )
        )
    print("planned calls:", {item[0]: len(item[2]) for item in plan}, flush=True)
    state, message = "completed", "all planned blocks finished"
    try:
        for block, seed, jobs, filename in plan:
            backend.block, backend.seed = block, seed
            print(f"== {block} seed={seed} n={len(jobs)}", flush=True)
            for start in range(0, len(jobs), 10):
                run_jobs(backend, jobs[start : start + 10], OUT / filename, OUT, stimuli)
                check_errors(backend)
    except StopRun as exc:
        state, message = exc.state, exc.message
    write_json(
        OUT / "status.json",
        {
            "state": state,
            "message": message,
            "counts": backend.counts,
            "total_attempts": backend.total("attempts"),
        },
    )
    print("STATE", state, message, flush=True)
    print("PHASE2_DONE", flush=True)
    return 0 if state == "completed" else 3


if __name__ == "__main__":
    raise SystemExit(main())
