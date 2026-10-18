#!/usr/bin/env python3
"""Run the locked round-3 protocol on Gemini. See RUN.md."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        marker = candidate / "eval" / "round3" / "preregistration.md"
        if marker.is_file():
            return candidate
    raise SystemExit("cannot find eval/round3/preregistration.md")


ROOT = _root()
sys.path.insert(0, str(ROOT / "src"))

from hornok.gemini_run import run  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Round-3 Gemini gate, then attacks if it passes.")
    parser.add_argument(
        "--stage",
        default="all",
        choices=("all", "gate", "attack", "lite", "explain", "photos", "smoke"),
        help=(
            "all runs the gate, then attack and Flash-Lite when the gate passes. "
            "explain, photos, and smoke are optional and do not enter the gate."
        ),
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "gemini-out"),
        help="Folder of predictions.jsonl, summary.json, status.json, and models.json",
    )
    args = parser.parse_args()
    return run(ROOT, Path(args.out), args.stage)


if __name__ == "__main__":
    raise SystemExit(main())
