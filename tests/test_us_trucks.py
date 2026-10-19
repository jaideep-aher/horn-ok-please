"""Phase-2 US dry-van frames are drawings, and the builder regenerates them."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from hornok.round3 import PHRASES
from hornok.scenes import H, W

ROOT = Path(__file__).resolve().parents[1]
US = ROOT / "eval" / "gemini_remote" / "phase2" / "us_trucks"
PHONE = re.compile(r"(?:\+\d{10,}|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b|\b\d{7,}\b)")
HASH = re.compile(r"^[0-9a-f]{64}$")


def _builder():
    path = ROOT / "eval" / "gemini_remote" / "phase2" / "build_us_trucks.py"
    spec = importlib.util.spec_from_file_location("build_us_trucks", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _manifest() -> dict:
    return json.loads((US / "manifest.json").read_text(encoding="utf-8"))


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _quad_mask(quad: list, pad: int = 3) -> Image.Image:
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon([tuple(point) for point in quad], fill=255)
    return mask.filter(ImageFilter.MaxFilter(pad * 2 + 1))


def test_manifest_is_twenty_synthetic_stop_frames():
    manifest = _manifest()
    assert manifest["note"] == "drawn dry-van rear, not a photograph"
    assert manifest["image_size"] == [W, H]
    assert manifest["n_stop"] == manifest["n_clean"] == manifest["n_g1"] == manifest["n_b1"] == 20
    scenes = manifest["scenes"]
    assert len(scenes) == 20
    assert len({row["id"] for row in scenes}) == 20
    assert {row["binary_label"] for row in scenes} == {"STOP"}
    assert {row["source"] for row in scenes} == {"synthetic"}
    assert all(row["drawing"] == manifest["note"] for row in scenes)
    redrawn = [row["id"] for row in scenes if row["redrawn_trailer"]]
    assert redrawn == ["photo_cargo_a", "photo_cargo_b"]
    clean = sorted(path.name for path in (US / "clean").glob("*"))
    attack = sorted(path.name for path in (US / "attack").glob("*"))
    assert clean == sorted(f"{row['id']}.png" for row in scenes)
    assert attack == sorted(
        f"{row['id']}__{phrase}__en.png" for row in scenes for phrase in ("G1", "B1")
    )
    for row in scenes:
        assert [item["phrase"] for item in row["attacks"]] == ["G1", "B1"]
        for attack in row["attacks"]:
            assert attack["script"] == "en"
            assert attack["text"] == PHRASES[attack["phrase"]]["en"]
            assert "__" + attack["phrase"] + "__en.png" in attack["file"]
        for rel in (row["clean_file"], *(item["file"] for item in row["attacks"])):
            image = Image.open(US / rel)
            assert image.format == "PNG"
            assert image.size == (W, H)
            assert image.mode == "RGB"


def test_no_phone_numbers_in_the_locked_text():
    blobs = [
        (ROOT / "eval/gemini_remote/phase2/calls.json").read_text(encoding="utf-8"),
        (ROOT / "eval/gemini_remote/phase2/preregistration.md").read_text(encoding="utf-8"),
        (ROOT / "eval/gemini_remote/RUN.md").read_text(encoding="utf-8"),
    ]
    for blob in blobs:
        assert PHONE.search(blob) is None
    for text in _strings(_manifest()):
        if HASH.fullmatch(text):
            continue
        assert PHONE.search(text) is None
        assert "USDOT" not in text
        assert "license plate" not in text.lower()


def test_plan_points_at_the_drawings_and_keeps_the_call_count():
    calls = json.loads(
        (ROOT / "eval/gemini_remote/phase2/calls.json").read_text(encoding="utf-8")
    )
    block = next(row for row in calls["blocks"] if row["id"] == "us_truck_english_control")
    assert block["stimuli"] == "eval/gemini_remote/phase2/us_trucks"
    assert block["note"] == "drawn dry-van rear, not a photograph"
    assert block["clean"] == 20
    assert block["painted_english_g1"] == 20
    assert block["painted_english_b1"] == 20
    assert block["api_calls"] == 40
    assert calls["api_calls_if_all_run"] == 520
    assert calls["do_not_call"] is True
    plan = (ROOT / "eval/gemini_remote/phase2/preregistration.md").read_text(encoding="utf-8")
    assert "us_trucks" in plan
    assert "redrawn trailers" in plan
    assert "does not start a job" in plan
    assert "not in this commit" not in plan
    assert "40 + 40 + 200 + 240 = **520**" in plan


def test_paint_stays_on_the_door_and_a_rebuild_matches(tmp_path: Path):
    manifest = _manifest()
    for row in manifest["scenes"]:
        clean = np.asarray(Image.open(US / row["clean_file"]).convert("RGB"))
        mask = np.asarray(_quad_mask(row["quad"]))
        for attack in row["attacks"]:
            painted = np.asarray(Image.open(US / attack["file"]).convert("RGB"))
            assert not np.array_equal(clean, painted)
            diff = np.any(clean != painted, axis=2)
            assert not np.any(diff & (mask == 0))
    module = _builder()
    module.build(tmp_path)
    fresh = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert fresh == manifest
    for row in manifest["scenes"]:
        for rel in (row["clean_file"], *(item["file"] for item in row["attacks"])):
            committed = Image.open(US / rel).convert("RGB")
            rebuilt = Image.open(tmp_path / rel).convert("RGB")
            assert committed.tobytes() == rebuilt.tobytes()
