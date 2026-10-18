"""Write eval/results/summary.json from predictions.jsonl."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hornok.report import build_report  # noqa: E402


def main() -> None:
    src = ROOT / "eval" / "results" / "predictions.jsonl"
    text = src.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in text if line.strip()]
    report = build_report(records)
    out = ROOT / "eval" / "results" / "summary.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out} from {report['n_drive_records']} drive rows")


if __name__ == "__main__":
    main()
