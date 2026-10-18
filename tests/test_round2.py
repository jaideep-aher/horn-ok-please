"""Round-2 parser, gate, and phrase locks. Round 1 behavior stays put."""

from hornok.parse import parse_decision, parse_decision_v2
from hornok.prompts import DRIVING_PROMPT_V2
from hornok.round2 import (
    BENIGN_IDS,
    PHRASES,
    SCRIPTS,
    evaluate_gate,
    latency_valve,
    select_attack_models,
)
from hornok.scenes import extra_illustration_specs, scene_specs


def test_v2_accepts_only_exact_actions_or_json():
    assert parse_decision_v2("BRAKE") == ("BRAKE", "")
    assert parse_decision_v2("  SLOW\n") == ("SLOW", "")
    assert parse_decision_v2('{"action":"CONTINUE"}')[0] == "CONTINUE"
    assert parse_decision_v2('{"action":"CHANGE_LANE","rationale":"open"}') == (
        "CHANGE_LANE",
        "open",
    )


def test_v2_rejects_aliases_and_surrounding_prose():
    for text in ("stop", "STOP.", "BRAKE.", "slow down", "do not brake", "continue please"):
        assert parse_decision_v2(text)[0] == "UNPARSEABLE"
    wrapped = 'The action is {"action": "BRAKE"}'
    assert parse_decision_v2(wrapped)[0] == "UNPARSEABLE"
    assert parse_decision("Stop.")[0] == "BRAKE"


def test_prompt_v2_has_no_filled_action_line():
    assert "ACTION:" not in DRIVING_PROMPT_V2
    assert "BECAUSE:" not in DRIVING_PROMPT_V2
    for action in ("BRAKE", "SLOW", "CONTINUE", "CHANGE_LANE"):
        assert action in DRIVING_PROMPT_V2


def test_gate_requires_both_bars():
    def rows(actions, gts):
        return [{"action": action, "gt": gt} for action, gt in zip(actions, gts, strict=True)]

    ten = ["BRAKE"] * 10
    # 6/10 agree, none unparsed.
    passed = evaluate_gate(rows(["BRAKE"] * 6 + ["CONTINUE"] * 4, ten), 10)
    assert passed["passed"] is True
    assert passed["status"] == "passed"
    # 60% agree but 40% unparsed.
    mixed = evaluate_gate(rows(["BRAKE"] * 6 + ["UNPARSEABLE"] * 4, ten), 10)
    assert mixed["passed"] is False
    assert mixed["unparsed_rate"] == 0.4
    # One unparsed in ten is exactly the cap, with 9/10 agreement.
    edge = evaluate_gate(rows(["BRAKE"] * 9 + ["UNPARSEABLE"], ten), 10)
    assert edge["passed"] is True
    short = evaluate_gate(rows(["BRAKE"] * 9, ["BRAKE"] * 9), 10)
    assert short["status"] == "incomplete"
    assert short["passed"] is False


def test_attack_model_cap_and_edge_partner():
    def gate(agreement, passed=True):
        status = "passed" if passed else "gated_out"
        return {"passed": passed, "agreement": agreement, "status": status}

    both = {
        "qwen25vl-3b-q8": gate(0.7),
        "qwen25vl-3b-q4": gate(0.9),
        "gemma3-4b-q8": gate(0.95),
    }
    # Both Qwen quants passed, so they are the attack pair even though Gemma
    # agreed more often. Q4 is listed first because its agreement is higher.
    assert select_attack_models(both) == ["qwen25vl-3b-q4", "qwen25vl-3b-q8"]
    only_gemma = {"gemma3-4b-q8": gate(0.8), "internvl25-1b-q8": gate(0.7)}
    assert select_attack_models(only_gemma) == ["gemma3-4b-q8", "internvl25-1b-q8"]
    assert select_attack_models({}) == []


def test_latency_valve_uses_seconds_only():
    assert latency_valve(13.0) == {
        "median_clean_seconds": 13.0,
        "drop_b2": False,
        "drop_a4_except_original_12": False,
    }
    assert latency_valve(21.0)["drop_b2"] is True
    assert latency_valve(21.0)["drop_a4_except_original_12"] is False
    assert latency_valve(30.0)["drop_a4_except_original_12"] is True


def test_benign_strings_are_not_driving_orders():
    latin_banned = ("BRAKE", "STOP", "SLOW", "LANE", "CONTINUE", "GO")
    deva_banned = ("थांबा", "रुको", "ब्रेक", "मोकळ", "पुढे")
    for phrase_id in BENIGN_IDS:
        for script in SCRIPTS:
            text = PHRASES[phrase_id][script].upper()
            if script == "deva":
                for stem in deva_banned:
                    assert stem not in PHRASES[phrase_id][script]
            else:
                for word in latin_banned:
                    assert word not in text.split()


def test_round1_scene_list_is_unchanged_and_extras_do_not_collide():
    original = [spec["id"] for spec in scene_specs()]
    assert len(original) == 12
    extra = [spec["id"] for spec in extra_illustration_specs()]
    assert len(extra) == 18
    assert set(original).isdisjoint(extra)
