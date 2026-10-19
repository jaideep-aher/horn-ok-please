"""The Western control drawings match the locked round-3 STOP grid."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def _builder():
    path = ROOT / "eval" / "gemini_remote" / "phase2" / "build_us_trucks.py"
    spec = importlib.util.spec_from_file_location("build_us_trucks", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_us_trucks_match_the_phase2_counts():
    module = _builder()
    manifest = json.loads((module.OUT / "manifest.json").read_text(encoding="utf-8"))
    round3 = json.loads(module.ROUND3.read_text(encoding="utf-8"))
    calls = json.loads(
        (ROOT / "eval" / "gemini_remote" / "phase2" / "calls.json").read_text(encoding="utf-8")
    )
    block = next(row for row in calls["blocks"] if row["id"] == "us_truck_english_control")
    stop = [row for row in round3["scenes"] if row["binary_label"] == "STOP"]

    assert manifest["n_clean"] == manifest["n_g1_en"] == manifest["n_b1_en"] == 20
    assert manifest["scored_api_calls"] == 40
    assert manifest["image_size"] == [1280, 720]
    assert block["api_calls"] == 40
    assert block["clean"] == 20
    assert block["painted_english_g1"] == 20
    assert block["benign_english_b1"] == 20
    assert block["benign_in_api_calls"] is False
    assert block["stimuli"] == "eval/gemini_remote/phase2/us_trucks"
    assert calls["api_calls_if_all_run"] == 520
    assert [row["id"] for row in manifest["scenes"]] == [row["id"] for row in stop]

    total = 0
    for saved, job, locked in zip(manifest["scenes"], module.jobs(), stop, strict=True):
        assert saved["quad"] == job["quad"] == [[int(p[0]), int(p[1])] for p in locked["quad"]]
        assert saved["hazard"] == locked["hazard"]
        assert saved["binary_label"] == "STOP"
        assert saved["source"] == "synthetic"
        assert saved["round3_source"] == locked["source"]
        clean = module.OUT / saved["clean_file"]
        g1 = module.OUT / saved["attacks"][0]["file"]
        b1 = module.OUT / saved["attacks"][1]["file"]
        assert saved["attacks"][0]["text"] == module.G1
        assert saved["attacks"][1]["text"] == module.B1
        assert saved["attacks"][0]["scored"] is True
        assert saved["attacks"][1]["scored"] is False
        for path in (clean, g1, b1):
            image = Image.open(path)
            assert image.size == (1280, 720)
            assert image.mode == "RGB"
            assert path.stat().st_size < 200_000
            total += path.stat().st_size
            image.close()
        assert module.layout_leak(job) == 0
        fresh = module.render_us(job)
        assert fresh.tobytes() == Image.open(clean).convert("RGB").tobytes()
    assert total < 8_000_000


def test_sha256sums_covers_every_png_and_the_manifest():
    module = _builder()
    root = module.OUT
    listed = {}
    for line in (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, rest = line.split(" ", 1)
        assert rest.startswith("*")
        listed[rest[1:]] = digest
    expected = ["manifest.json"]
    expected += [f"attack/{path.name}" for path in sorted((root / "attack").glob("*.png"))]
    expected += [f"clean/{path.name}" for path in sorted((root / "clean").glob("*.png"))]
    assert sorted(listed) == sorted(expected)
    assert len(listed) == 61
    for name, digest in listed.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
