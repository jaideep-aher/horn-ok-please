"""Explanation scores stay null when the denominator is empty."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from hornok.devsplit import dev_specs
from hornok.gemini_run import run_explain
from hornok.round3 import ADDED_GO, ADDED_STOP, INHERITED_GO, INHERITED_STOP
from hornok.scenes import render_spec
from hornok.xai import (
    GIBBERISH,
    PAINTED_MODEL,
    QUESTION,
    REASON_PROMPT_V1,
    count_cells_meeting_bbox,
    count_centers_in_bbox,
    gaze_rows,
    grid_cells,
    inpaint_image,
    mentions_painted,
    occlusion_mass,
    paint_text,
    parse_reason,
    quad_mask,
    summarize,
    xai_specs,
)

ROOT = Path(__file__).resolve().parents[1]


def test_grid_covers_the_frame_once():
    seen = [[0] * 1280 for _ in range(720)]
    for cell in grid_cells():
        assert cell["x1"] > cell["x0"]
        assert cell["y1"] > cell["y0"]
        for y in range(cell["y0"], cell["y1"]):
            for x in range(cell["x0"], cell["x1"]):
                seen[y][x] += 1
    assert all(value == 1 for row in seen for value in row)


def test_xai_scenes_are_new():
    locked = set(INHERITED_STOP + INHERITED_GO)
    locked.update(row["id"] for row in ADDED_STOP + ADDED_GO)
    locked.update(spec["id"] for spec in dev_specs())
    ids = [spec["id"] for spec in xai_specs()]
    assert len(ids) == 6
    assert len(ids) == len(set(ids))
    assert not (set(ids) & locked)
    assert paint_text("gibberish") == GIBBERISH
    assert "HORN" not in GIBBERISH
    assert "रोड" not in GIBBERISH


def test_block_text_sits_on_the_hazard_and_the_person_does_not():
    block = next(spec for spec in xai_specs() if spec["id"] == "xai_block")
    person = next(spec for spec in xai_specs() if spec["id"] == "xai_person")
    _block_image, block_meta = render_spec(block, seed=9100)
    _person_image, person_meta = render_spec(person, seed=9101)
    block_mask = quad_mask((1280, 720), block_meta["quads"]["truck_rear"])
    person_mask = quad_mask((1280, 720), person_meta["quads"]["truck_rear"])
    cells = grid_cells()
    assert any(_center_on(cell, block_mask) and _in_box(cell, block_meta["hazard_bbox"]) for cell in cells)
    assert person_meta["hazard_bbox"] is not None
    assert not any(_center_on(cell, person_mask) and _in_box(cell, person_meta["hazard_bbox"]) for cell in cells)


def _center_on(cell, mask) -> bool:
    from hornok.xai import mask_center

    return mask_center(cell, mask)


def _in_box(cell, box) -> bool:
    from hornok.xai import center_in_bbox

    return center_in_bbox(cell, box)


def test_reason_parser_uses_only_the_last_line():
    action, rationale = parse_reason("The painted line says stop.\nGO")
    assert action == "GO"
    assert "painted" in rationale
    assert parse_reason("I would STOP here because of the person.")[0] == "UNPARSEABLE"
    assert parse_reason("A person is in the lane.\nstop.")[0] == "STOP"
    assert REASON_PROMPT_V1.strip().endswith("you should continue.")


def test_mention_cues():
    phrase = paint_text("g1_en") or ""
    assert mentions_painted("The tailgate says ROAD CLEAR.", phrase)
    assert mentions_painted("The line reads पुढे जा.", phrase)
    assert not mentions_painted("A person is standing in the lane.", phrase)


def test_gaze_cohort_is_fixed_by_the_committed_file():
    rows = [
        json.loads(line)
        for line in (ROOT / "eval/dev/results/predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    chosen = gaze_rows(rows)
    keys = {(row["model"], row["prompt_id"], row["scene"]) for row in chosen}
    assert ("gemma3-4b-q8", "D3", "dev_person") in keys
    assert ("gemma3-4b-q8", "D3", "dev_cow") in keys
    assert ("qwen25vl-3b-q8", "D0", "dev_person") in keys
    assert ("qwen25vl-3b-q8", "D3", "dev_person") in keys
    assert ("qwen25vl-3b-q8", "D1", "dev_person_dusk") in keys
    assert all(row["prompt_id"] != "D4" for row in chosen)


def test_rates_stay_null_without_a_causal_pair():
    scenes = [{"id": "xai_empty", "binary_label": "GO", "text_on_hazard": False, "hazard_bbox": None}]
    rows = [
        _direct("xai_empty", "clean", "GO"),
        _direct("xai_empty", "g1_en", "GO"),
    ]
    summary = summarize(rows, scenes=scenes, gaze=[], algorithm="telea")
    assert summary["conditions"]["g1_en"]["causal"]["k"] == 0
    assert summary["conditions"]["g1_en"]["causal"]["n"] == 1
    assert summary["conditions"]["g1_en"]["restored"]["rate"] is None
    assert summary["says"]["hidden_influence"]["rate"] is None
    assert "not defined" in summary["reading"] or "did not change" in summary["reading"]


def test_restoration_and_hidden_influence_use_only_causal_pairs():
    scenes = [{"id": "xai_person", "binary_label": "STOP", "text_on_hazard": False, "hazard_bbox": [1, 1, 2, 2]}]
    rows = [
        _direct("xai_person", "clean", "STOP"),
        _direct("xai_person", "g1_en", "GO"),
        _kind("inpaint", "xai_person", "g1_en", "D0", "STOP"),
        _kind("insertion", "xai_person", "g1_en", "D0", "GO"),
        {
            "kind": "reason",
            "model": PAINTED_MODEL,
            "scene": "xai_person",
            "condition": "g1_en",
            "prompt_id": "R1",
            "cell": None,
            "source": "xai",
            "raw": "A person is in the lane.\nGO",
        },
    ]
    summary = summarize(rows, scenes=scenes, gaze=[], algorithm="telea")
    assert summary["conditions"]["g1_en"]["causal"] == {"k": 1, "n": 1, "rate": 1.0}
    assert summary["conditions"]["g1_en"]["restored"]["k"] == 1
    assert summary["conditions"]["g1_en"]["insertion"]["k"] == 1
    assert summary["says"]["hidden_influence"] == {"k": 1, "n": 1, "rate": 1.0}


def test_occlusion_mass_names_the_failure():
    cells = []
    for cell in grid_cells():
        saliency = 1 if cell["r"] == 0 else 0
        cells.append({**cell, "saliency": saliency})
    missed = occlusion_mass(cells, lambda cell: cell["r"] == 2)
    assert missed["label"] == "hazard_missed"
    assert missed["mass"] == 0
    inert = occlusion_mass([{**cell, "saliency": 0} for cell in grid_cells()], lambda _cell: False)
    assert inert["label"] == "occlusion_inert"
    assert inert["mass"] is None


def test_inpaint_removes_a_marked_square_and_keeps_the_corner():
    image = Image.new("RGB", (64, 64), (40, 80, 120))
    draw = ImageDraw.Draw(image)
    draw.rectangle([20, 20, 40, 40], fill=(220, 20, 20))
    mask = Image.new("L", (64, 64), 0)
    ImageDraw.Draw(mask).rectangle([20, 20, 40, 40], fill=255)
    filled, name = inpaint_image(image, mask, prefer="telea")
    assert name == "telea"
    assert filled.getpixel((0, 0)) == (40, 80, 120)
    assert filled.getpixel((30, 30)) != (220, 20, 20)


def test_protocol_names_the_question_and_the_papers():
    text = (ROOT / "eval" / "xai" / "protocol.md").read_text(encoding="utf-8")
    assert QUESTION in text
    for arxiv in ("2510.21689", "2510.03317", "2608.20670", "2604.09923"):
        assert arxiv in text
    assert "does not rescore" in text


def _occlusion(scene: str, prompt: str, flips: set[tuple[int, int]]) -> list[dict]:
    rows = []
    for cell in grid_cells():
        rows.append(
            {
                "kind": "occlusion",
                "model": PAINTED_MODEL,
                "scene": scene,
                "condition": "clean",
                "prompt_id": prompt,
                "cell": f"{cell['r']},{cell['c']}",
                "action": "STOP" if (cell["r"], cell["c"]) in flips else "GO",
            }
        )
    return rows


def test_an_empty_center_intersection_keeps_the_miss_label():
    gaze = [
        {
            "model": PAINTED_MODEL,
            "scene": "dev_person",
            "prompt_id": "D0",
            "action": "GO",
            "hazard": "person",
            "hazard_bbox": [372, 474, 472, 675],
        }
    ]
    summary = summarize(_occlusion("dev_person", "D0", {(2, 0), (2, 1)}), scenes=[], gaze=gaze, algorithm="telea")
    row = summary["gaze"][0]
    assert row["label"] == "hazard_missed"
    assert row["centers_in_hazard"] == 0
    assert row["cells_meeting_hazard"] == 4
    assert row["mass_hazard"] == 0
    assert "Hazard mass cannot be positive" in summary["reading"]
    assert "empty intersection" in summary["reading"]


def test_a_box_with_one_center_still_names_a_miss_when_the_flip_is_elsewhere():
    gaze = [
        {
            "model": PAINTED_MODEL,
            "scene": "dev_cow",
            "prompt_id": "D3",
            "action": "GO",
            "hazard": "cow",
            "hazard_bbox": [450, 520, 660, 660],
        }
    ]
    summary = summarize(_occlusion("dev_cow", "D3", {(0, 1)}), scenes=[], gaze=gaze, algorithm="telea")
    row = summary["gaze"][0]
    assert count_centers_in_bbox(row["hazard_bbox"]) == 1
    assert row["label"] == "hazard_missed"
    assert row["mass_hazard"] == 0
    assert "were not that center" in summary["reading"]
    assert count_cells_meeting_bbox([566, 614, 674, 650]) >= 1
    assert count_centers_in_bbox([566, 614, 674, 650]) == 0


def test_explain_refuses_without_stimuli(tmp_path: Path):
    root = tmp_path / "root"
    (root / "eval" / "xai").mkdir(parents=True)
    code = run_explain(root, tmp_path / "out", backend=None, model_id="gemini:gemini-2.5-flash")
    assert code == 2


def _direct(scene: str, condition: str, action: str) -> dict:
    return _kind("direct", scene, condition, "D0", action)


def _kind(kind: str, scene: str, condition: str, prompt: str, action: str) -> dict:
    return {
        "kind": kind,
        "model": PAINTED_MODEL,
        "scene": scene,
        "condition": condition,
        "prompt_id": prompt,
        "cell": None,
        "action": action,
        "source": "xai",
    }
