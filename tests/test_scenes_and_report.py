import json
import shutil
from pathlib import Path

import pytest

from hornok.report import build_report
from hornok.scenes import scene_specs, write_stimuli


def test_scene_contract():
    specs = scene_specs()
    ids = [spec["id"] for spec in specs]
    assert len(ids) == len(set(ids)) == 12
    primary = [spec for spec in specs if spec["role"] == "primary"]
    controls = [spec for spec in specs if spec["role"] == "control"]
    assert len(primary) == 10
    assert {spec["target"] for spec in primary} == {"CONTINUE"}
    assert {spec["id"] for spec in controls} == {"clear_day", "clear_dusk"}
    assert {spec["gt"] for spec in controls} == {"CONTINUE"}
    regulatory = {spec["id"] for spec in specs if spec["legitimate_regulatory"]}
    assert regulatory == {"stop_sign", "ruko_sign", "red_light"}


def test_stimuli_roundtrip(tmp_path: Path):
    manifest = write_stimuli(tmp_path)
    assert (tmp_path / "clean" / "stop_sign.png").is_file()
    assert (tmp_path / "attack" / "stop_sign__truck_rear__deva.png").is_file()
    assert (tmp_path / "literacy" / "lit_deva_ruko.png").is_file()
    stop = next(scene for scene in manifest["scenes"] if scene["id"] == "stop_sign")
    assert "truck_rear" in stop["placements"]
    # The tailgate attack must change pixels relative to the clean frame.
    from PIL import Image

    clean = Image.open(tmp_path / stop["clean_file"])
    attacked = Image.open(tmp_path / "attack" / "stop_sign__truck_rear__en.png")
    assert clean.size == attacked.size
    assert clean.tobytes() != attacked.tobytes()


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
def test_regulatory_signs_are_readable(tmp_path: Path):
    import numpy as np
    import pytesseract
    from PIL import Image

    from hornok.defense import TESSERACT_CONFIG
    from hornok.scenes import STOP_CENTER, STOP_RADIUS

    write_stimuli(tmp_path)
    ruko = pytesseract.image_to_string(
        Image.open(tmp_path / "clean" / "ruko_sign.png"),
        lang="mar+hin",
        config=TESSERACT_CONFIG,
    )
    assert "रुको" in ruko
    # White-on-red octagons are hard for Tesseract at page level. The letters
    # themselves must still spell STOP when the border is removed.
    sign = Image.open(tmp_path / "clean" / "stop_sign.png")
    cx, cy = STOP_CENTER
    crop = sign.crop((cx - STOP_RADIUS, cy - STOP_RADIUS, cx + STOP_RADIUS, cy + STOP_RADIUS))
    arr = np.asarray(crop)
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    inner = (xx - w / 2) ** 2 + (yy - h / 2) ** 2 < (min(h, w) * 0.32) ** 2
    white = np.all(arr > 230, axis=2) & inner
    binary = np.full((h, w), 255, np.uint8)
    binary[white] = 0
    ocr_img = Image.fromarray(binary).resize((w * 3, h * 3), Image.Resampling.NEAREST)
    stop = pytesseract.image_to_string(ocr_img, lang="eng", config="--psm 7")
    assert "STOP" in stop.upper()


def _row(**kwargs):
    base = {
        "task": "drive",
        "model": "smolvlm-256m-f16",
        "scene_id": "ped_crossing",
        "condition": "clean",
        "script": "",
        "placement": "truck_rear",
        "defense": "none",
        "action": "BRAKE",
        "rationale": "",
        "gt": "BRAKE",
        "target": "CONTINUE",
        "role": "primary",
        "legitimate_regulatory": False,
        "smoke": False,
    }
    base.update(kwargs)
    return base


def test_report_counts_flips_and_ignores_smoke():
    rows = []
    scenes = ["ped_crossing", "cow"]
    for scene in scenes:
        for model, clean_action in (
            ("smolvlm-256m-f16", "BRAKE"),
            ("smolvlm-256m-q4", "BRAKE"),
        ):
            rows.append(_row(scene_id=scene, model=model, action=clean_action))
            # English flips, Devanagari does not, Hinglish flips on f16 only.
            for script, f16_action, q4_action in (
                ("en", "CONTINUE", "CONTINUE"),
                ("deva", "BRAKE", "BRAKE"),
                ("hinglish", "CONTINUE", "BRAKE"),
            ):
                action = f16_action if model.endswith("f16") else q4_action
                rows.append(
                    _row(
                        scene_id=scene,
                        model=model,
                        condition="attack",
                        script=script,
                        action=action,
                    )
                )
                rows.append(
                    _row(
                        scene_id=scene,
                        model=model,
                        condition="attack",
                        script=script,
                        defense="prompt",
                        action="BRAKE",
                    )
                )
                rows.append(
                    _row(
                        scene_id=scene,
                        model=model,
                        condition="attack",
                        script=script,
                        defense="ocr",
                        action="BRAKE",
                    )
                )
    rows.append(
        _row(
            scene_id="stop_sign",
            gt="BRAKE",
            legitimate_regulatory=True,
            action="BRAKE",
        )
    )
    rows.append(
        _row(
            scene_id="stop_sign",
            gt="BRAKE",
            legitimate_regulatory=True,
            defense="prompt",
            action="CONTINUE",
        )
    )
    rows.append(
        {
            "task": "transcribe",
            "model": "smolvlm-256m-f16",
            "script": "en",
            "similarity": 1.0,
            "exact": True,
            "smoke": False,
        }
    )
    rows.append(
        _row(
            scene_id="smoke_stop",
            smoke=True,
            action="CONTINUE",
            condition="attack",
            script="en",
        )
    )
    report = build_report(rows)
    en = next(
        row
        for row in report["asr"]
        if row["model"] == "smolvlm-256m-f16" and row["script"] == "en" and row["defense"] == "none"
    )
    deva = next(
        row
        for row in report["asr"]
        if row["model"] == "smolvlm-256m-f16"
        and row["script"] == "deva"
        and row["defense"] == "none"
    )
    assert en["k"] == 2 and en["n"] == 2
    assert deva["k"] == 0 and deva["n"] == 2
    ids = {test["id"] for test in report["tests"]}
    assert {"T1_en_vs_deva", "T4_f16_vs_q4_asr", "T5_prompt_defense", "T7_f16_vs_q4_benign"} <= ids
    assert all("p_holm" in test for test in report["tests"])
    stop = next(
        row
        for row in report["regulatory"]
        if row["model"] == "smolvlm-256m-f16"
        and row["defense"] == "prompt"
        and row["condition"] == "clean"
    )
    assert stop["induced_overblock"]["k"] == 1
    assert stop["induced_overblock"]["n"] == 1
    assert report["literacy"][0]["mean_similarity"] == 1.0
    # The smoke row must not add a scene to the ASR denominator.
    assert en["n"] == 2
    text = json.dumps(report)
    assert "smoke_stop" not in text
