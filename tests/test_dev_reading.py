"""The diagnostic write-up may only say what a fixture's counts support."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _publisher():
    path = Path(__file__).resolve().parents[1] / "poster" / "publish_round3.py"
    spec = importlib.util.spec_from_file_location("publish_round3", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _block(prompt_id: str, model: str, stop: int, go: int, empty: int, shoulder: int) -> dict:
    return {
        "prompt_id": prompt_id,
        "model": model,
        "n_stop": 8,
        "n_go": 8,
        "stop_correct": stop,
        "go_correct": go,
        "unparsed": 0,
        "recall_stop": stop / 8,
        "recall_go": go / 8,
        "balanced_accuracy": (stop / 8 + go / 8) / 2,
        "passed": False,
        "go_empty": {"k": empty, "n": 4, "rate": empty / 4},
        "go_shoulder": {"k": shoulder, "n": 4, "rate": shoulder / 4},
    }


def test_empty_go_and_shoulder_stop_is_not_called_a_blanket_stop():
    module = _publisher()
    dev = {
        "n_predictions": 32,
        "promoted_prompt": None,
        "blocks": [
            _block("D1", "qwen25vl-3b-q8", 4, 4, 4, 0),
            _block("D4", "qwen25vl-3b-q8", 8, 0, 0, 0),
        ],
    }
    text = module.diagnostic_reading(dev)
    assert "does not fit this file" in text
    assert "Round 4 was not opened" in text
    assert "D4 on Qwen2.5-VL 3B Q8_0" in text
    assert "under 60%" in text
    assert "shoulder" in text


def test_all_stop_is_the_overcaution_finding():
    module = _publisher()
    dev = {
        "n_predictions": 16,
        "promoted_prompt": None,
        "blocks": [_block("D1", "gemma3-4b-q8", 8, 0, 0, 0)],
    }
    text = module.diagnostic_reading(dev)
    assert "default to STOP from a still frame" in text
    assert "does not fit this file" not in text


def test_markdown_prints_the_stored_fractions():
    module = _publisher()
    dev = {
        "n_predictions": 16,
        "promoted_prompt": None,
        "blocks": [_block("D3", "qwen25vl-3b-q8", 5, 3, 3, 0)],
    }
    text = module.diagnostic_markdown(dev)
    assert "STOP 5/8" in text
    assert "GO 3/8" in text
    assert "empty-lane GO 3/4" in text
    assert "shoulder-truck GO 0/4" in text
    assert "16" in text
