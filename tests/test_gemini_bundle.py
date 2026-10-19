"""The Gemini bundle runner must not call the network."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from hornok.attack_paint import paint_attack
from hornok.gemini import QuotaError, select_flash_lite_model, select_flash_model
from hornok.gemini_run import run

ROOT = Path(__file__).resolve().parents[1]


class Scripted:
    def __init__(self, model_id: str, go_ids: set[str], quota_after: int | None = None):
        self.model_id = model_id
        self.go_ids = go_ids
        self.quota_after = quota_after
        self.calls: list[str] = []

    def generate(self, image: str, prompt: str, *, schema: bool = True) -> str:
        del prompt
        self.calls.append(image)
        if self.quota_after is not None and len(self.calls) > self.quota_after:
            raise QuotaError("Gemini quota stopped the run: You exceeded your current quota")
        if not schema:
            return "रोड क्लिअर"
        action = "GO" if Path(image).stem in self.go_ids else "STOP"
        return json.dumps({"action": action})


def _go_ids() -> set[str]:
    manifest = json.loads((ROOT / "eval/round3/stimuli/manifest.json").read_text(encoding="utf-8"))
    return {row["id"] for row in manifest["scenes"] if row["binary_label"] == "GO"}


def _models() -> dict:
    return {
        "listed": ["models/gemini-2.5-flash", "models/gemini-2.5-flash-lite"],
        "selector_flash": "gemini-2.5-flash",
        "flash": "gemini-2.5-flash",
        "flash_override": False,
        "flash_lite": "gemini-2.5-flash-lite",
        "lite_override": False,
    }


def test_primary_flash_skips_a_higher_version_lite():
    chosen = select_flash_model(
        ["models/gemini-2.0-flash", "models/gemini-3.0-flash-lite", "models/gemini-2.5-flash-lite"]
    )
    assert chosen == "gemini-2.0-flash"
    assert (
        select_flash_lite_model(
            ["models/gemini-2.5-flash-lite-preview", "models/gemini-2.5-flash-lite"]
        )
        == "gemini-2.5-flash-lite"
    )
    assert select_flash_lite_model(["models/gemini-2.5-flash"]) is None


def test_missing_key_does_not_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    code = run(ROOT, tmp_path / "out", "all")
    assert code == 0
    status = json.loads((tmp_path / "out" / "status.json").read_text(encoding="utf-8"))
    assert status["state"] == "not_called"
    assert not (tmp_path / "out" / "predictions.jsonl").exists()


def test_failed_gate_does_not_start_attacks(tmp_path: Path):
    backend = Scripted("gemini-2.5-flash", go_ids=set())

    def factory(model_id: str):
        assert model_id == "gemini-2.5-flash"
        return backend

    code = run(ROOT, tmp_path / "out", "all", models=_models(), backend_factory=factory)
    assert code == 0
    assert len(backend.calls) == 40
    status = json.loads((tmp_path / "out" / "status.json").read_text(encoding="utf-8"))
    assert status["state"] == "gate_failed"
    summary = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert summary["passers"] == []
    assert summary["any_passed"] is False
    models = json.loads((tmp_path / "out" / "models.json").read_text(encoding="utf-8"))
    assert models["flash"] == "gemini-2.5-flash"
    text = (tmp_path / "out" / "predictions.jsonl").read_text(encoding="utf-8")
    rows = [json.loads(line) for line in text.splitlines()]
    assert {row["resolved_model_id"] for row in rows} == {"gemini-2.5-flash"}
    assert {row["task"] for row in rows} == {"gate"}


def test_passing_gate_starts_the_attack_then_stops_on_quota(tmp_path: Path):
    backend = Scripted("gemini-2.5-flash", go_ids=_go_ids(), quota_after=40)

    def factory(model_id: str):
        return backend

    code = run(ROOT, tmp_path / "out", "all", models=_models(), backend_factory=factory)
    assert code == 3
    status = json.loads((tmp_path / "out" / "status.json").read_text(encoding="utf-8"))
    assert status["state"] == "stopped_on_quota"
    text = (tmp_path / "out" / "predictions.jsonl").read_text(encoding="utf-8")
    rows = [json.loads(line) for line in text.splitlines()]
    assert len(rows) == 40
    assert all(row["task"] == "gate" for row in rows)
    summary = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert summary["passers"] == ["gemini:gemini-2.5-flash"]
    assert len(backend.calls) == 41


def test_attack_stage_refuses_without_a_pass(tmp_path: Path):
    backend = Scripted("gemini-2.5-flash", go_ids=set())

    def factory(model_id: str):
        return backend

    out = tmp_path / "out"
    assert run(ROOT, out, "gate", models=_models(), backend_factory=factory) == 0
    calls = len(backend.calls)
    code = run(ROOT, out, "attack", models=_models(), backend_factory=factory)
    assert code == 2
    assert len(backend.calls) == calls


def test_quota_error_is_not_retried(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from hornok.gemini import GeminiVLM

    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    image = tmp_path / "blank.png"
    Image.new("RGB", (8, 8), "white").save(image)
    vlm = GeminiVLM(model_id="gemini-test")
    calls = {"n": 0}

    class _Models:
        def generate_content(self, **kwargs):
            del kwargs
            calls["n"] += 1
            raise RuntimeError("429 You exceeded your current quota")

    vlm._client = type("Client", (), {"models": _Models()})()
    with pytest.raises(QuotaError):
        vlm.generate(image, "prompt")
    assert calls["n"] == 1


def test_short_cap_is_raised_and_schema_is_response_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from hornok.gemini import GeminiVLM, effective_output_tokens

    assert effective_output_tokens(64) == 1024
    assert effective_output_tokens(2048) == 2048
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    image = tmp_path / "blank.png"
    Image.new("RGB", (8, 8), "white").save(image)
    vlm = GeminiVLM(model_id="gemini-3.8-flash")
    seen: list[tuple] = []

    class _Response:
        text = "Here"
        parsed = {"action": "STOP"}
        candidates = []
        usage_metadata = None

    class _Models:
        def generate_content(self, **kwargs):
            config = kwargs["config"]
            thinking = config.thinking_config
            budget = None if thinking is None else thinking.thinking_budget
            level = None if thinking is None else thinking.thinking_level
            seen.append((budget, None if level is None else str(level)))
            assert config.max_output_tokens == 1024
            assert config.response_mime_type == "application/json"
            assert config.response_schema is not None
            assert config.response_json_schema is None
            if budget == 0:
                raise RuntimeError("thinking_budget is not supported for this model")
            return _Response()

    vlm._client = type("Client", (), {"models": _Models()})()
    assert vlm.generate(image, "prompt", max_output_tokens=64) == '{"action":"STOP"}'
    assert seen[0] == (0, None)
    assert seen[1][0] is None
    assert "MINIMAL" in seen[1][1]
    assert vlm.last_meta["thinking"] == "minimal"
    assert vlm.last_meta["max_output_tokens"] == 1024


def test_smoke_prints_three_raw_replies_and_skips_the_gate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    class Talker:
        def __init__(self, model_id: str):
            self.model_id = model_id
            self.last_meta = {
                "thinking": "off",
                "max_output_tokens": 1024,
                "finish_reason": "STOP",
                "thoughts_token_count": 0,
            }

        def generate(self, image: str, prompt: str, *, schema: bool = True) -> str:
            del image, prompt, schema
            return json.dumps({"action": "GO"})

    def factory(model_id: str):
        return Talker(model_id)

    out = tmp_path / "out"
    assert run(ROOT, out, "smoke", models=_models(), backend_factory=factory) == 0
    printed = capsys.readouterr().out
    assert printed.count("raw=") == 3
    assert "parsed=GO" in printed
    assert "thinking=off" in printed
    assert not (out / "predictions.jsonl").exists()
    status = json.loads((out / "status.json").read_text(encoding="utf-8"))
    assert status["state"] == "smoke_printed"


def test_cli_accepts_explain_photos_and_smoke():
    import subprocess
    import sys

    script = ROOT / "eval" / "gemini_remote" / "run_gemini.py"
    proc = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert proc.returncode == 0
    for name in ("explain", "photos", "smoke"):
        assert name in proc.stdout


def _locked_attack_cases() -> list[tuple[dict, dict]]:
    """Every paint on ped_crossing, plus the first paint of each other drawn STOP scene."""
    manifest = json.loads((ROOT / "eval/round3/stimuli/manifest.json").read_text(encoding="utf-8"))
    cases = []
    for scene in manifest["scenes"]:
        if scene["source"] != "synthetic" or not scene["attacks"]:
            continue
        attacks = scene["attacks"] if scene["id"] == "ped_crossing" else scene["attacks"][:1]
        cases.extend((scene, attack) for attack in attacks)
    return cases


@pytest.mark.parametrize(
    "scene,attack",
    _locked_attack_cases(),
    ids=lambda value: value.get("file", value.get("id")) if isinstance(value, dict) else None,
)
def test_locked_attack_matches_the_painter(scene: dict, attack: dict):
    """The scored PNGs ship as WebP previews; the painter must rebuild their exact pixels."""
    import hashlib

    stimuli = ROOT / "eval/round3/stimuli"
    pixels = json.loads((stimuli / "PIXELS.sha256.json").read_text(encoding="utf-8"))
    base = Image.open(stimuli / scene["clean_file"]).convert("RGB")
    painted = paint_attack(
        base, attack["text"], scene["quad"], scene["id"], attack["phrase"], attack["script"]
    )
    assert painted.size == base.size
    assert hashlib.sha256(painted.tobytes()).hexdigest() == pixels[attack["file"]]
