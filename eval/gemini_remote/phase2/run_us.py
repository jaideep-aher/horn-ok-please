#!/usr/bin/env python3
"""Phase-2 block 2: US-truck English control.

20 clean + 20 G1 (en) = 40 scored calls. B1 controls are not scored.
The drawing directory is not in this repo. Pass it with --us-stim or
PHASE2_US_STIM. --out / PHASE2_OUT selects the results directory.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import run_phase2 as phase2

from hornok.gemini import gemini_api_key
from hornok.gemini_run import StopRun, model_key, run_jobs, write_json

COMBINED_CAP = 530


def _env_path(name: str) -> Path | None:
    raw = os.environ.get(name, "").strip()
    return Path(raw).expanduser() if raw else None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the locked US-truck control.")
    parser.add_argument(
        "--out",
        type=Path,
        default=_env_path("PHASE2_OUT") or phase2.OUT,
        help="Directory for the US JSONL, counts, and status.",
    )
    parser.add_argument(
        "--us-stim",
        type=Path,
        default=_env_path("PHASE2_US_STIM"),
        help="Directory of the US dry-van drawings (manifest.json plus images).",
    )
    return parser.parse_args(argv)


class USVLM(phase2.Phase2VLM):
    def total(self, field):
        own = sum(value.get(field, 0) for value in self.counts.values())
        if field == "attempts":
            main_counts = phase2.OUT / "call_counts.json"
            if main_counts.is_file():
                main = json.loads(main_counts.read_text(encoding="utf-8"))
                main_attempts = sum(value.get(field, 0) for value in main.values())
                if own + main_attempts >= COMBINED_CAP:
                    return 10**9
        return own


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.us_stim is None:
        print("no US stimuli: pass --us-stim or PHASE2_US_STIM")
        return 2
    phase2.OUT = args.out
    phase2.COUNTS = phase2.OUT / "us_call_counts.json"
    manifest = json.loads((args.us_stim / "manifest.json").read_text(encoding="utf-8"))
    model = model_key(phase2.MODEL)
    jobs = []
    for scene in manifest["scenes"]:
        jobs.append(
            {
                "task": "us_clean",
                "model": model,
                "scene": scene["id"],
                "condition": "us_clean",
                "script": None,
                "defense": "none",
                "phrase": None,
                "binary_label": scene["binary_label"],
                "image": str(args.us_stim / scene["clean_file"]),
                "prompt_id": "v3",
            }
        )
        for attack in scene["attacks"]:
            if attack.get("scored") and attack["phrase"] == "G1":
                jobs.append(
                    {
                        "task": "us_attack",
                        "model": model,
                        "scene": scene["id"],
                        "condition": "us_G1",
                        "script": attack["script"],
                        "defense": "none",
                        "phrase": "G1",
                        "binary_label": "STOP",
                        "image": str(args.us_stim / attack["file"]),
                        "prompt_id": "v3",
                    }
                )
    print("planned", len(jobs), flush=True)
    key = gemini_api_key()
    if not key:
        print("no key")
        return 2
    backend = USVLM(model_id=phase2.MODEL, api_key=key)
    backend.block, backend.seed = "b2_us_truck_control", None
    state, message = "completed", "US block finished"
    try:
        for start in range(0, len(jobs), 10):
            run_jobs(
                backend,
                jobs[start : start + 10],
                phase2.OUT / "b2_us_truck_control.jsonl",
                phase2.OUT,
                args.us_stim,
            )
            phase2.check_errors(backend)
    except StopRun as exc:
        state, message = exc.state, exc.message
    write_json(
        phase2.OUT / "us_status.json",
        {"state": state, "message": message, "counts": backend.counts},
    )
    print("STATE", state, message, "\nUS_DONE", flush=True)
    return 0 if state == "completed" else 3


if __name__ == "__main__":
    raise SystemExit(main())
