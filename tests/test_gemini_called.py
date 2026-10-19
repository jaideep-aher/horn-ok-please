"""Round-3 gemini_called comes from the committed Gemini bundle, not a hand edit."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "eval" / "round3" / "results" / "summary.json"
WEB = ROOT / "web" / "public" / "data" / "round3.json"
GEMINI = ROOT / "eval" / "gemini_remote" / "results" / "summary.json"


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_analyzer_keeps_open_weight_counts_and_marks_the_gemini_run(tmp_path, monkeypatch):
    module = _load(ROOT / "eval" / "round3" / "analyze.py")
    monkeypatch.setattr(module, "SUMMARY", tmp_path / "summary.json")
    fresh = module.summarize()
    committed = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert fresh == committed
    assert fresh["n_predictions"] == 168
    assert fresh["gemini_called"] is True
    assert fresh["gemini_run"]["model_id"] == "gemini-3.8-flash"
    assert fresh["gemini_run"]["results_file"] == "eval/gemini_remote/results/summary.json"
    source = json.loads(GEMINI.read_text(encoding="utf-8"))
    assert fresh["gemini_run"]["model_id"] == source["resolved_models"]["flash"]
    dated = [source.get(key) for key in ("run_date", "dated", "date")]
    if not any(isinstance(value, str) and value.strip() for value in dated):
        assert "run_date" not in fresh["gemini_run"]
    assert all(not str(row["model"]).startswith("gemini:") for row in fresh["gate"])
    assert fresh["passers"] == []


def test_web_round3_matches_the_summary_bytes():
    assert WEB.read_bytes() == SUMMARY.read_bytes()


def test_poster_text_quotes_the_committed_gemini_run():
    module = _load(ROOT / "poster" / "publish_round3.py")
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    round2_path = ROOT / "eval" / "round2" / "results" / "summary.json"
    pilot_path = ROOT / "eval" / "results" / "summary.json"
    round2 = json.loads(round2_path.read_text(encoding="utf-8"))
    pilot = json.loads(pilot_path.read_text(encoding="utf-8"))
    gemini = json.loads(GEMINI.read_text(encoding="utf-8"))
    rendered = "\n".join(
        [
            module.results_markdown(summary, round2, pilot),
            module.pitch_markdown(summary, round2),
            module.poster_html(summary, round2),
        ]
    )
    assert "Gemini was not called" not in rendered
    assert "There is no API key in this run" not in rendered
    assert "GEMINI_API_KEY was unset" not in rendered
    assert gemini["resolved_models"]["flash"] in rendered
    assert "eval/gemini_remote/results/summary.json" in rendered
    assert str(gemini["n_predictions"]) in rendered
