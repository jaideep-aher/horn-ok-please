"""Try last-layer attention on Qwen2.5-VL-3B. Record a miss instead of a fake map."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "eval" / "xai" / "results" / "whitebox.json"
MIN_AVAILABLE_BYTES = 8 * 1024**3


def _available() -> int:
    text = Path("/proc/meminfo").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    return 0


def main() -> int:
    available = _available()
    payload = {
        "status": "not_run",
        "reason": (
            f"MemAvailable was {available} bytes; the protocol floor for a second "
            f"Qwen2.5-VL-3B load is {MIN_AVAILABLE_BYTES} bytes. "
            "llama-server does not return attention, and a full-precision "
            "Qwen2.5-VL-3B checkpoint is not in this checkout. No attention map was drawn."
        ),
        "n_images": 0,
        "mem_available": available,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(payload["reason"], flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
