"""Round-3 gate math, parser, and the Gemini key guard."""

from __future__ import annotations

import pytest

from hornok.gemini import GeminiVLM, gemini_model_id, select_flash_model
from hornok.harness import GenerationError
from hornok.parse import parse_decision_v3
from hornok.prompts import DRIVING_PROMPT_V3
from hornok.round3 import (
    ADDED_GO,
    ADDED_STOP,
    BA_MIN,
    INHERITED_GO,
    INHERITED_STOP,
    RECALL_MIN,
    evaluate_binary_gate,
)


def _rows(stop_hits: int, go_hits: int, n: int = 20) -> list[dict]:
    rows = []
    for index in range(n):
        rows.append({"binary_label": "STOP", "action": "STOP" if index < stop_hits else "GO"})
        rows.append({"binary_label": "GO", "action": "GO" if index < go_hits else "STOP"})
    return rows


def test_constant_stop_fails_the_gate():
    gate = evaluate_binary_gate(
        [{"binary_label": "STOP", "action": "STOP"}] * 20
        + [{"binary_label": "GO", "action": "STOP"}] * 20,
        20,
        20,
    )
    assert gate["balanced_accuracy"] == pytest.approx(0.5)
    assert gate["recall_go"] == 0
    assert gate["passed"] is False


def test_perfect_stop_and_half_go_fails_recall_floor():
    gate = evaluate_binary_gate(_rows(20, 10), 20, 20)
    assert gate["balanced_accuracy"] == pytest.approx(0.75)
    assert gate["recall_go"] == pytest.approx(0.5)
    assert gate["passed"] is False


def test_balanced_model_passes():
    gate = evaluate_binary_gate(_rows(18, 16), 20, 20)
    assert gate["balanced_accuracy"] >= BA_MIN
    assert gate["recall_stop"] >= RECALL_MIN
    assert gate["recall_go"] >= RECALL_MIN
    assert gate["passed"] is True


def test_unparsed_counts_as_a_miss():
    rows = _rows(20, 20)
    rows[0]["action"] = "UNPARSEABLE"
    rows[1]["action"] = "UNPARSEABLE"
    gate = evaluate_binary_gate(rows, 20, 20)
    assert gate["unparsed"] == 2
    assert gate["recall_stop"] == pytest.approx(19 / 20)
    assert gate["recall_go"] == pytest.approx(19 / 20)


def test_parser_accepts_only_stop_and_go():
    assert parse_decision_v3("STOP") == "STOP"
    assert parse_decision_v3("GO") == "GO"
    assert parse_decision_v3('{"action":"STOP"}') == "STOP"
    assert parse_decision_v3("BRAKE") == "UNPARSEABLE"
    assert parse_decision_v3("CONTINUE") == "UNPARSEABLE"
    assert parse_decision_v3("stop") == "UNPARSEABLE"


def test_prompt_has_no_filled_example_line():
    assert "ACTION:" not in DRIVING_PROMPT_V3
    for line in DRIVING_PROMPT_V3.splitlines():
        assert line.strip() not in {"STOP", "GO"}


def test_dev_scenes_do_not_touch_the_locked_set():
    from hornok.devsplit import dev_specs

    specs = dev_specs()
    ids = {row["id"] for row in specs}
    added = tuple(row["id"] for row in (*ADDED_STOP, *ADDED_GO))
    locked = set(INHERITED_STOP + INHERITED_GO + added)
    assert ids.isdisjoint(locked)
    assert sum(1 for row in specs if row["binary_label"] == "STOP") == 8
    assert sum(1 for row in specs if row["stratum"] == "go_empty") == 4
    assert sum(1 for row in specs if row["stratum"] == "go_shoulder") == 4


def test_scene_lists_are_balanced():
    assert len(INHERITED_STOP) + len(ADDED_STOP) == 20
    assert len(INHERITED_GO) + len(ADDED_GO) == 20
    assert len(set(INHERITED_STOP) & set(INHERITED_GO)) == 0


def test_gemini_is_not_called_without_a_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(GenerationError, match="not set"):
        GeminiVLM()


def test_gemini_model_comes_from_the_env_or_a_live_list(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert gemini_model_id() is None
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.6-flash")
    assert gemini_model_id() == "gemini-3.6-flash"


def test_flash_model_is_chosen_from_the_listed_names():
    chosen = select_flash_model(
        [
            "models/gemini-2.5-flash",
            "models/gemini-3.8-flash-preview",
            "models/gemini-3.8-flash",
            "models/gemini-3.8-flash-tts",
            {"name": "models/gemini-3.1-flash", "supported_actions": ["generateContent"]},
            {"name": "models/gemini-3.9-flash", "supported_actions": ["embedContent"]},
        ]
    )
    assert chosen == "gemini-3.8-flash"


def test_flash_model_refuses_an_empty_list():
    with pytest.raises(GenerationError, match="no Flash model"):
        select_flash_model(["models/gemini-3.1-pro", "models/gemini-embedding-001"])
