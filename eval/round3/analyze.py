"""Summarize round-3 predictions. Numbers come only from the JSONL."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from hornok.metrics import holm, is_targeted_flip, mcnemar_exact  # noqa: E402
from hornok.round3 import (  # noqa: E402
    HOLM_TESTS,
    SCRIPTS,
    TIE_ORDER,
    evaluate_binary_gate,
    flip_rate,
    is_reader,
    load_round2_reader_means,
)

PREDICTIONS = ROOT / "eval" / "round3" / "results" / "predictions.jsonl"
GATE_PATH = ROOT / "eval" / "round3" / "results" / "gate.json"
SUMMARY = ROOT / "eval" / "round3" / "results" / "summary.json"


def _rows() -> list[dict]:
    if not PREDICTIONS.is_file():
        return []
    return [
        json.loads(line)
        for line in PREDICTIONS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _clean(rows: list[dict], model: str) -> dict[str, str]:
    return {
        row["scene"]: row["action"]
        for row in rows
        if row["model"] == model and row["task"] == "gate"
    }


def _attack_action(
    rows: list[dict], model: str, phrase: str, script: str, defense: str
) -> dict[str, str]:
    task = "attack" if defense == "none" else "defense"
    return {
        row["scene"]: row["action"]
        for row in rows
        if row["model"] == model
        and row["task"] == task
        and row.get("phrase") == phrase
        and row.get("script") == script
        and (row.get("defense") or "none") == defense
    }


def _flips(clean: dict[str, str], attacked: dict[str, str], scenes: list[str]) -> list[bool]:
    flags = []
    for scene in scenes:
        if scene not in clean or scene not in attacked:
            return []
        flags.append(is_targeted_flip(clean[scene], attacked[scene], "GO"))
    return flags


def _paired(flags_a: list[bool], flags_b: list[bool]) -> dict | None:
    if not flags_a or len(flags_a) != len(flags_b):
        return None
    return mcnemar_exact(flags_a, flags_b)


def summarize() -> dict:
    rows = _rows()
    gate_rows = [row for row in rows if row["task"] == "gate"]
    models = []
    for model in dict.fromkeys(row["model"] for row in gate_rows):
        mine = [row for row in gate_rows if row["model"] == model]
        if not mine:
            continue
        n_stop = sum(1 for row in mine if row["binary_label"] == "STOP")
        n_go = sum(1 for row in mine if row["binary_label"] == "GO")
        if n_stop == 0 or n_go == 0:
            continue
        block = evaluate_binary_gate(mine, n_stop, n_go)
        block["model"] = model
        block["action_counts"] = dict(Counter(row["action"] for row in mine))
        block["go_hit_scenes"] = sorted(
            row["scene"] for row in mine if row["binary_label"] == "GO" and row["action"] == "GO"
        )
        models.append(block)

    order = {name: index for index, name in enumerate(TIE_ORDER)}
    models.sort(
        key=lambda row: (
            -int(row["passed"]),
            -row["balanced_accuracy"],
            order.get(row["model"], 99),
        )
    )
    passers = [row["model"] for row in models if row["passed"]]
    primary = passers[0] if passers else None

    published = load_round2_reader_means(ROOT / "eval" / "round2" / "results" / "summary.json")
    literacy = []
    for model in dict.fromkeys(row["model"] for row in rows if row["task"] == "literacy"):
        for script in ("en", "deva"):
            cards = [
                row
                for row in rows
                if row["model"] == model
                and row["task"] == "literacy"
                and row.get("script") == script
            ]
            sims = [row["similarity"] for row in cards if row.get("similarity") is not None]
            exact = sum(1 for row in cards if row.get("exact"))
            mean = (sum(sims) / len(sims)) if sims else None
            literacy.append(
                {
                    "model": model,
                    "script": script,
                    "n": len(cards),
                    "mean_similarity": mean,
                    "exact_k": exact,
                }
            )
            if script == "deva" and mean is not None:
                published[model] = mean

    readers = {
        model: is_reader(published.get(model))
        for model in sorted(row["model"] for row in models)
    }

    stop_scenes = sorted({row["scene"] for row in gate_rows if row["binary_label"] == "STOP"})
    go_scenes = sorted({row["scene"] for row in gate_rows if row["binary_label"] == "GO"})

    attacks = []
    benign = []
    for model in passers:
        clean = _clean(rows, model)
        for phrase, bucket in (("G1", attacks), ("B1", benign), ("G2", attacks)):
            for script in SCRIPTS:
                attacked = _attack_action(rows, model, phrase, script, "none")
                if not attacked:
                    continue
                flags = _flips(clean, attacked, stop_scenes)
                rate = flip_rate(flags)
                bucket.append(
                    {
                        "model": model,
                        "phrase": phrase,
                        "script": script,
                        "confirmatory": phrase == "G1",
                        **rate,
                    }
                )

    defenses = []
    overblock = []
    for model in passers:
        clean = _clean(rows, model)
        for defense in ("prompt", "ocr"):
            for script in SCRIPTS:
                attacked = _attack_action(rows, model, "G1", script, defense)
                if not attacked:
                    continue
                flags = _flips(clean, attacked, stop_scenes)
                defenses.append(
                    {
                        "model": model,
                        "defense": defense,
                        "phrase": "G1",
                        "script": script,
                        **flip_rate(flags),
                    }
                )
            # Over-block on clean GO scenes.
            defended = {
                row["scene"]: row["action"]
                for row in rows
                if row["model"] == model
                and row["task"] == "defense"
                and row.get("condition") == "clean"
                and row.get("defense") == defense
            }
            if not defended:
                continue
            eligible = [
                scene for scene in go_scenes if clean.get(scene) == "GO" and scene in defended
            ]
            blocked = [defended[scene] != "GO" for scene in eligible]
            overblock.append({"model": model, "defense": defense, **flip_rate(blocked)})

    tests: list[dict] = []

    def add(name: str, a: list[bool], b: list[bool]) -> None:
        paired = _paired(a, b)
        if paired is None:
            return
        tests.append({"name": name, "a_rate": flip_rate(a), "b_rate": flip_rate(b), **paired})

    if primary:
        clean = _clean(rows, primary)
        by_script = {
            script: _flips(clean, _attack_action(rows, primary, "G1", script, "none"), stop_scenes)
            for script in SCRIPTS
        }
        if all(by_script.values()):
            add("T1_en_vs_mr", by_script["en"], by_script["mr"])
            add("T2_en_vs_hi", by_script["en"], by_script["hi"])
            add("T3_en_vs_hinglish", by_script["en"], by_script["hinglish"])
            add("T4_mr_vs_hi", by_script["mr"], by_script["hi"])
            benign_flags = []
            attack_flags = []
            for script in SCRIPTS:
                b_flags = _flips(
                    clean, _attack_action(rows, primary, "B1", script, "none"), stop_scenes
                )
                if not b_flags:
                    benign_flags = []
                    break
                attack_flags.extend(by_script[script])
                benign_flags.extend(b_flags)
            add("T7_g1_vs_b1", attack_flags, benign_flags)
            for defense, name in (("prompt", "T8_none_vs_prompt"), ("ocr", "T9_none_vs_ocr")):
                undefended = []
                defended = []
                ok = True
                for script in SCRIPTS:
                    d_flags = _flips(
                        clean, _attack_action(rows, primary, "G1", script, defense), stop_scenes
                    )
                    if not d_flags:
                        ok = False
                        break
                    undefended.extend(by_script[script])
                    defended.extend(d_flags)
                if ok:
                    add(name, undefended, defended)

    for family, name, left, right in (
        ("qwen2.5-vl-3b", "T5_qwen_q8_vs_q4", "qwen25vl-3b-q8", "qwen25vl-3b-q4"),
        ("gemma3-4b", "T6_gemma_q8_vs_q4", "gemma3-4b-q8", "gemma3-4b-q4"),
    ):
        del family
        if left not in passers or right not in passers:
            continue
        a_flags = []
        b_flags = []
        ok = True
        for script in SCRIPTS:
            a = _flips(
                _clean(rows, left), _attack_action(rows, left, "G1", script, "none"), stop_scenes
            )
            b = _flips(
                _clean(rows, right), _attack_action(rows, right, "G1", script, "none"), stop_scenes
            )
            if not a or not b:
                ok = False
                break
            a_flags.extend(a)
            b_flags.extend(b)
        if ok:
            add(name, a_flags, b_flags)

    attacked_readers = [model for model in passers if readers.get(model) is True]
    attacked_non = [model for model in passers if readers.get(model) is False]
    if attacked_readers and attacked_non:
        reader = attacked_readers[0]
        nonreader = attacked_non[0]
        a_flags = []
        b_flags = []
        ok = True
        for script in SCRIPTS:
            a = _flips(
                _clean(rows, reader),
                _attack_action(rows, reader, "G1", script, "none"),
                stop_scenes,
            )
            b = _flips(
                _clean(rows, nonreader),
                _attack_action(rows, nonreader, "G1", script, "none"),
                stop_scenes,
            )
            if not a or not b:
                ok = False
                break
            a_flags.extend(a)
            b_flags.extend(b)
        if ok:
            add("T10_reader_vs_nonreader", a_flags, b_flags)

    # Holm on the tests that exist, in the declared family order.
    present = {row["name"]: row for row in tests}
    ordered = [present[name] for name in HOLM_TESTS if name in present]
    if ordered:
        adjusted = holm([float(row["p"]) for row in ordered])
        for row, p_adj in zip(ordered, adjusted, strict=True):
            row["p_holm"] = p_adj
            row["significant_0_05"] = p_adj < 0.05

    checkpoint = {}
    if GATE_PATH.is_file():
        checkpoint = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    smoke_path = ROOT / "eval" / "round3" / "results" / "smoke.jsonl"
    smoke = []
    if smoke_path.is_file():
        smoke = [
            json.loads(line)
            for line in smoke_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    summary = {
        "round": 3,
        "protocol": "eval/round3/preregistration.md",
        "dated": "2026-10-18",
        "n_predictions": len(rows),
        "n_stop": 20,
        "n_go": 20,
        "gate": models,
        "passers": passers,
        "primary": primary,
        "any_passed": bool(passers),
        "readers": readers,
        "literacy": literacy,
        "attacks": [row for row in attacks if row["phrase"] == "G1"],
        "phrase_panel": [row for row in attacks if row["phrase"] == "G2"],
        "benign": benign,
        "defenses": defenses,
        "overblock": overblock,
        "tests": ordered,
        "tests_omitted": [name for name in HOLM_TESTS if name not in present],
        "valve": {
            "run_g2": checkpoint.get("run_g2"),
            "median_clean_seconds": checkpoint.get("median_clean_seconds"),
        },
        "gemini_called": any(str(row["model"]).startswith("gemini:") for row in rows),
        "smoke": smoke,
        "dropped": checkpoint.get("dropped") or [],
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "passers": passers,
                "primary": primary,
                "n": len(rows),
                "tests": [row["name"] for row in ordered],
            },
            indent=2,
        )
    )
    return summary


if __name__ == "__main__":
    summarize()
