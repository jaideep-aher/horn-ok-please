"""Time one forward pass per model on images that are not in the scored twelve.

Writes eval/smoke/timing.json. Does not write predictions.jsonl.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hornok.harness import build_backend  # noqa: E402
from hornok.parse import parse_decision  # noqa: E402
from hornok.prompts import DRIVING_PROMPT_V1  # noqa: E402
from hornok.scenes import render_spec  # noqa: E402

SMOKE_SPEC = {
    "id": "smoke_stop",
    "gt": "BRAKE",
    "target": "CONTINUE",
    "role": "smoke",
    "legitimate_regulatory": True,
    "hazard": "Smoke image. Not part of the scored scene list.",
    "distance": "far",
    "elements": ["stop"],
    "dusk": True,
    "truck_dx": -80,
}


def main() -> None:
    out_dir = ROOT / "eval" / "smoke"
    out_dir.mkdir(parents=True, exist_ok=True)
    image, _ = render_spec(SMOKE_SPEC, seed=7)
    image_path = out_dir / "smoke_stop.png"
    image.save(image_path)
    models = sys.argv[1:] or ["smolvlm-256m-hf"]
    rows = []
    if (out_dir / "timing.json").is_file():
        rows = json.loads((out_dir / "timing.json").read_text(encoding="utf-8"))
    have = {row["model"] for row in rows}
    for name in models:
        if name in have:
            print(f"already timed {name}", flush=True)
            continue
        print(f"timing {name}", flush=True)
        started = time.perf_counter()
        backend = build_backend(name)
        try:
            raw = backend.generate(image_path, DRIVING_PROMPT_V1, max_new_tokens=64)
            error = ""
        except Exception as exc:
            raw = ""
            error = f"{type(exc).__name__}: {exc}"
        finally:
            backend.close()
        seconds = round(time.perf_counter() - started, 3)
        action, rationale = parse_decision(raw)
        row = {
            "model": name,
            "seconds": seconds,
            "action": action,
            "rationale": rationale[:300],
            "raw": raw[:800],
            "error": error,
            "image": "eval/smoke/smoke_stop.png",
            "scored": False,
        }
        rows.append(row)
        (out_dir / "timing.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(json.dumps({k: row[k] for k in ("model", "seconds", "action", "error")}), flush=True)


if __name__ == "__main__":
    main()
