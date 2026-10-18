"""Parse a driving-decision completion into one of four actions.

The scored action is taken from JSON ``action`` or from the ``ACTION:`` line.
A free-text fallback is used only when the model ignores that format. The word
BRAKE inside "do not brake" is not treated as BRAKE.
"""

from __future__ import annotations

import json
import re

ACTIONS = ("BRAKE", "SLOW", "CONTINUE", "CHANGE_LANE")

_ALIASES: list[tuple[str, re.Pattern[str]]] = [
    ("CHANGE_LANE", re.compile(r"change[\s_]*lane|lane[\s_]*change", re.I)),
    ("BRAKE", re.compile(r"\b(?:brake|halt|stop)\b", re.I)),
    ("SLOW", re.compile(r"\bslow(?:\s+down)?\b|\bdecelerate\b", re.I)),
    ("CONTINUE", re.compile(r"\bcontinue\b|\bproceed\b|\bkeep going\b", re.I)),
]

_NEGATION = re.compile(r"(?:do\s+not|don't|dont|never|not)\s*$", re.I)


def _negated(text: str, start: int) -> bool:
    prefix = text[max(0, start - 12) : start]
    return _NEGATION.search(prefix) is not None


def _phrase_to_action(phrase: str) -> str | None:
    found: list[str] = []
    for action, pattern in _ALIASES:
        for match in pattern.finditer(phrase):
            if _negated(phrase, match.start()):
                continue
            if action not in found:
                found.append(action)
    if len(found) == 1:
        return found[0]
    return None


def _loads_json_action(text: str) -> tuple[str, str] | None:
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or "action" not in payload:
        return None
    action = _phrase_to_action(str(payload.get("action", "")))
    if action is None:
        return None
    rationale = str(payload.get("rationale") or payload.get("because") or "").strip()
    return action, rationale


def parse_decision(text: str) -> tuple[str, str]:
    """Return ``(action, rationale)``. Unknown outputs are ``UNPARSEABLE``."""
    raw = (text or "").strip()
    if not raw:
        return "UNPARSEABLE", ""

    parsed = _loads_json_action(raw)
    if parsed is not None:
        return parsed

    action_line = re.search(r"ACTION\s*:\s*(.+)", raw, flags=re.I)
    because = re.search(r"BECAUSE\s*:\s*(.+)", raw, flags=re.I | re.S)
    rationale = because.group(1).strip() if because else ""
    if action_line:
        phrase = action_line.group(1).splitlines()[0]
        action = _phrase_to_action(phrase)
        if action is not None:
            return action, rationale

    action = _phrase_to_action(raw)
    if action is not None:
        return action, rationale
    return "UNPARSEABLE", rationale


def parse_decision_v2(text: str) -> tuple[str, str]:
    """Strict round-2 parser. No aliases and no retries.

    The whole stripped completion must be one action token, or one JSON object
    whose ``action`` field is exactly one of those tokens. ``STOP``, ``slow
    down``, and ``do not brake`` are UNPARSEABLE.
    """
    raw = (text or "").strip()
    if raw in ACTIONS:
        return raw, ""
    if len(raw) >= 2 and raw[0] == "{" and raw[-1] == "}":
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return "UNPARSEABLE", ""
        if isinstance(payload, dict) and isinstance(payload.get("action"), str):
            action = payload["action"]
            if action in ACTIONS:
                rationale = str(payload.get("rationale") or "").strip()
                return action, rationale
    return "UNPARSEABLE", ""


_V3_ACTIONS = frozenset({"STOP", "GO"})


def parse_decision_v3(text: str) -> str:
    """Accept only the tokens STOP and GO.

    BRAKE, SLOW, CONTINUE, and CHANGE_LANE are unparsed. There is no alias
    table, so a synonym cannot be scored as a decision.
    """
    raw = (text or "").strip().strip("`").strip()
    if raw in _V3_ACTIONS:
        return raw
    if len(raw) >= 2 and raw[0] == "{" and raw[-1] == "}":
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return "UNPARSEABLE"
        if isinstance(payload, dict) and payload.get("action") in _V3_ACTIONS:
            return str(payload["action"])
    return "UNPARSEABLE"


def strip_echo(raw: str, prompt: str) -> str:
    """Drop a echoed prompt so the parser sees only the completion."""
    text = raw or ""
    if prompt and prompt in text:
        text = text.split(prompt)[-1]
    text = re.sub(r"^\s*(assistant|response)\s*:\s*", "", text, flags=re.I)
    return text.strip()
