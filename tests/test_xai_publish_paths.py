"""Site paths stay put when the paint PNGs are not in the checkout."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _analyzer():
    path = Path(__file__).resolve().parents[1] / "eval" / "xai" / "analyze.py"
    spec = importlib.util.spec_from_file_location("xai_analyze", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_absent_png_keeps_the_public_path():
    module = _analyzer()
    src = module.ROOT / "eval" / "xai" / "stimuli" / "paint" / "not-a-real-scene__g1_en.png"
    dest = module.PUBLIC / "not-a-real-scene__g1_en.png"
    assert not src.is_file()
    got = module._copy(src, dest)
    assert got == "/xai/not-a-real-scene__g1_en.png"
    assert not dest.exists()
