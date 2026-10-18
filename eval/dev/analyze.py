"""Summarize the dev diagnostic. Promotion follows eval/dev/protocol.md."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from hornok.devread import diagnostic_reading  # noqa: E402
from hornok.devsplit import CANDIDATE_PROMPTS, DEV_PROMPTS  # noqa: E402
from hornok.round3 import evaluate_binary_gate  # noqa: E402

PREDICTIONS = ROOT / "eval" / "dev" / "results" / "predictions.jsonl"
SUMMARY = ROOT / "eval" / "dev" / "results" / "summary.json"


def _rows() -> list[dict]:
    if not PREDICTIONS.is_file():
        return []
    text = PREDICTIONS.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _stratum(rows: list[dict], stratum: str, want: str) -> dict:
    mine = [row for row in rows if row["stratum"] == stratum]
    hits = sum(1 for row in mine if row["action"] == want)
    n = len(mine)
    return {"k": hits, "n": n, "rate": None if n == 0 else hits / n}


def summarize() -> dict:
    rows = _rows()
    blocks = []
    models = list(dict.fromkeys(row["model"] for row in rows))
    for prompt_id in DEV_PROMPTS:
        for model in models:
            mine = [row for row in rows if row["model"] == model and row["prompt_id"] == prompt_id]
            n_stop = sum(1 for row in mine if row["binary_label"] == "STOP")
            n_go = sum(1 for row in mine if row["binary_label"] == "GO")
            if n_stop == 0 or n_go == 0:
                continue
            gate = evaluate_binary_gate(mine, n_stop, n_go)
            gate["model"] = model
            gate["prompt_id"] = prompt_id
            gate["eligible"] = prompt_id in CANDIDATE_PROMPTS and gate["passed"]
            gate["go_empty"] = _stratum(mine, "go_empty", "GO")
            gate["go_shoulder"] = _stratum(mine, "go_shoulder", "GO")
            gate["stop_stratum"] = _stratum(mine, "stop", "STOP")
            gate["misses"] = [
                {"scene": row["scene"], "label": row["binary_label"], "action": row["action"]}
                for row in mine
                if row["action"] != row["binary_label"]
            ]
            blocks.append(gate)
    eligible = [row for row in blocks if row["eligible"]]
    means: dict[str, list[float]] = {}
    for row in blocks:
        if row["prompt_id"] not in CANDIDATE_PROMPTS:
            continue
        means.setdefault(row["prompt_id"], []).append(row["balanced_accuracy"])
    promoted = None
    if eligible:
        ids = sorted({row["prompt_id"] for row in eligible})

        def sort_key(prompt_id: str) -> tuple:
            values = means.get(prompt_id) or [0.0]
            mean = sum(values) / len(values)
            return (-mean, CANDIDATE_PROMPTS.index(prompt_id))

        promoted = sorted(ids, key=sort_key)[0]
    summary = {
        "split": "dev",
        "protocol": "eval/dev/protocol.md",
        "dated": "2026-10-18",
        "n_predictions": len(rows),
        "blocks": blocks,
        "promoted_prompt": promoted,
        "round4": promoted is not None,
    }
    summary["reading"] = diagnostic_reading(summary)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for row in blocks:
        print(
            f"{row['prompt_id']} {row['model']} BA={row['balanced_accuracy']:.3f} "
            f"STOP={row['recall_stop']:.3f} GO={row['recall_go']:.3f} "
            f"empty={row['go_empty']['k']}/{row['go_empty']['n']} "
            f"shoulder={row['go_shoulder']['k']}/{row['go_shoulder']['n']} "
            f"passed={row['passed']}"
        )
    print("promoted", promoted)
    return summary


if __name__ == "__main__":
    summarize()
