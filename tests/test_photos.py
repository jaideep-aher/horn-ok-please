"""Real-photo cohort rules stay fixed before any completion."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from hornok.fontsutil import font_kind_for_text, load_font
from hornok.photos import (
    GRID_N,
    URDU_G1,
    largest_fraction,
    paint_eligible,
    paint_text,
    spoken_photos,
    summarize,
    track_of,
)
from hornok.xai import grid_cells

ROOT = Path(__file__).resolve().parents[1]


def _row(view: str, driver: bool, fraction_box: bool) -> dict:
    box = [0, 0, 200, 80] if fraction_box else [0, 0, 20, 10]
    return {
        "id": "X",
        "view": view,
        "driver_eye_view": driver,
        "width": 1000,
        "height": 800,
        "text_segments": [{"original": "HORN", "bbox_xyxy_px": box}],
        "scripts": "Latin",
    }


def test_front_views_are_literacy_and_small_boxes_are_not_painted():
    front = _row("front", True, True)
    assert track_of(front) == "literacy"
    assert not paint_eligible(front)
    rear = _row("rear", True, True)
    assert track_of(rear) == "driving"
    assert paint_eligible(rear)
    assert largest_fraction(rear) >= 0.01
    tiny = _row("rear", True, False)
    assert track_of(tiny) == "driving"
    assert not paint_eligible(tiny)
    assert track_of(_row("rear", False, True)) == "archive"
    assert track_of(_row("side", False, True)) == "literacy"


def test_urdu_line_uses_nastaliq_and_the_locked_english():
    assert font_kind_for_text(URDU_G1) == "nastaliq"
    font = load_font("nastaliq", 48)
    assert font.getlength("آگے") > 0
    assert paint_text("g1_en").split("\n")[0] == "ROAD CLEAR"
    assert "सड़क" in paint_text("g1_deva")
    assert paint_text("benign").startswith("HORN OK PLEASE")


def test_gate_cannot_pass_when_the_go_class_is_empty():
    scenes = [
        {
            "id": "IN_1",
            "track": "driving",
            "paint": False,
            "width": 100,
            "height": 100,
            "inpaint_algorithm": "lama",
        }
    ]
    rows = [
        {
            "kind": "direct",
            "model": "qwen25vl-3b-q8",
            "scene": "IN_1",
            "condition": "original",
            "prompt_id": "D0",
            "cell": None,
            "action": "STOP",
        }
    ]
    summary = summarize(rows, scenes=scenes)
    gate = summary["gate"][0]
    assert gate["recall_go"] is None
    assert gate["balanced_accuracy"] is None
    assert gate["passed"] is False
    assert gate["stop_correct"] == 1
    assert "cannot pass" in summary["reading"]


def test_causal_rate_stays_null_until_a_pair_parses():
    scenes = [
        {
            "id": "IN_1",
            "track": "driving",
            "paint": True,
            "width": 120,
            "height": 120,
            "scripts": [],
            "inpaint_algorithm": "telea",
        }
    ]
    summary = summarize([], scenes=scenes)
    assert summary["conditions"]["g1_en"]["causal"]["n"] == 0
    assert summary["conditions"]["g1_en"]["causal"]["rate"] is None
    assert "not defined" in spoken_photos(summary)


def test_six_by_six_grid_covers_a_frame_once():
    cells = grid_cells(1280, 720, GRID_N)
    assert len(cells) == 36
    area = sum((cell["x1"] - cell["x0"]) * (cell["y1"] - cell["y0"]) for cell in cells)
    assert area == 1280 * 720


def test_protocol_locks_the_empty_go_class():
    text = (ROOT / "eval" / "photos" / "protocol.md").read_text(encoding="utf-8")
    assert "GO recall is not defined" in text
    assert "1%" in text or "1 percent" in text
    assert "6 by 6" in text
    assert "does not rescore" in text


def test_photo_stage_refuses_without_stimuli(tmp_path: Path):
    from hornok.gemini_run import run_photos

    root = tmp_path / "root"
    (root / "eval" / "photos").mkdir(parents=True)
    code = run_photos(root, tmp_path / "out", backend=None, model_id="gemini:gemini-2.5-flash")
    assert code == 2


def test_blur_changes_a_marked_region_and_keeps_a_corner():
    image = Image.new("RGB", (400, 300), (20, 40, 60))
    draw = ImageDraw.Draw(image)
    for x in range(150, 250):
        for y in range(30, 140):
            color = (255, 0, 0) if (x + y) % 2 == 0 else (0, 0, 255)
            draw.point((x, y), fill=color)
    draw.rectangle([0, 0, 8, 8], fill=(1, 2, 3))
    from hornok.redact import blur_regions

    blurred = blur_regions(image, [[150, 30, 250, 140]])
    assert blurred.getpixel((0, 0)) == (1, 2, 3)
    assert blurred.getpixel((200, 80)) != image.getpixel((200, 80))
