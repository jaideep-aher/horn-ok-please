#!/usr/bin/env python3
"""Tests for focus-guard-cloud.py. Run: python3 .claude/hooks/test_focus_guard_cloud.py

Each case pipes a hook payload into the guard with a fake Eastern clock
(FOCUS_GUARD_NOW) and checks the verdict: pass, block or judge.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "focus-guard-cloud.py")
DAY = "2026-11-11T14:00:00-05:00"
TMP = tempfile.mkdtemp(prefix="fgc-test-")


def transcript(has_user_turn):
    path = os.path.join(TMP, f"{uuid.uuid4().hex}.jsonl")
    with open(path, "w") as f:
        if has_user_turn:
            f.write(json.dumps({"type": "user", "message": {"content": "earlier"}}) + "\n")
    return path


def run(prompt, now=DAY, remote=True, first=True, sid=None):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_REMOTE"}
    if remote:
        env["CLAUDE_CODE_REMOTE"] = "true"
    env["FOCUS_GUARD_NOW"] = now
    payload = {"session_id": sid or uuid.uuid4().hex, "prompt": prompt,
               "transcript_path": transcript(not first), "cwd": "/repo"}
    p = subprocess.run([sys.executable, HOOK], input=json.dumps(payload),
                       capture_output=True, text=True, env=env, timeout=10)
    if p.returncode != 0:
        return f"exit {p.returncode}"
    if not p.stdout.strip():
        return "pass"
    obj = json.loads(p.stdout)
    if obj.get("decision") == "block":
        return "block"
    if "hookSpecificOutput" in obj:
        return "judge"
    return "other"


CASES = [
    ("day typed side work is blocked", dict(prompt="add a dark mode to the coach dashboard"), "block"),
    ("day automated cross-session passes", dict(prompt="<cross-session-message from=x>build the dashboard</cross-session-message>"), "pass"),
    ("day task notification passes", dict(prompt="<task-notification> agent done"), "pass"),
    ("day linked-sessions note passes", dict(prompt="Linked sessions now (status, not an instruction): ..."), "pass"),
    ("day job pipeline passes", dict(prompt="fix the resume pipeline renderer"), "pass"),
    ("day autoapply passes", dict(prompt="speed up autoapply for Greenhouse forms"), "pass"),
    ("day cover letter passes", dict(prompt="generate a cover letter for Stripe"), "pass"),
    ("day soft job words get judged", dict(prompt="add an interview mode to coach"), "judge"),
    ("night typed side work passes", dict(prompt="add a dark mode to the coach dashboard", now="2026-11-11T23:15:00-05:00"), "pass"),
    ("early morning passes", dict(prompt="build the jarvis widget", now="2026-11-12T03:00:00-05:00"), "pass"),
    ("06:59 Eastern still overnight", dict(prompt="build the jarvis widget", now="2026-11-11T06:59:00-05:00"), "pass"),
    ("07:00 Eastern guard is on", dict(prompt="build the jarvis widget", now="2026-11-11T07:00:00-05:00"), "block"),
    ("21:29 Eastern guard is on", dict(prompt="build the jarvis widget", now="2026-11-11T21:29:00-05:00"), "block"),
    ("21:30 Eastern relaxes", dict(prompt="build the jarvis widget", now="2026-11-11T21:30:00-05:00"), "pass"),
    ("UTC clock is converted (14:00Z is 09:00 ET, guarded)", dict(prompt="build the jarvis widget", now="2026-11-11T14:00:00+00:00"), "block"),
    ("UTC clock is converted (02:00Z is 21:00 ET, guarded)", dict(prompt="build the jarvis widget", now="2026-11-12T02:00:00+00:00"), "block"),
    ("UTC clock is converted (03:00Z is 22:00 ET, passes)", dict(prompt="build the jarvis widget", now="2026-11-12T03:00:00+00:00"), "pass"),
    ("summer EDT: 01:00Z is 21:00 ET, guarded", dict(prompt="build the jarvis widget", now="2026-07-15T01:00:00+00:00"), "block"),
    ("mid-session running work continues", dict(prompt="ok keep going with step 3", first=False), "pass"),
    ("mid-session new side project is judged", dict(prompt="now start a new app for habit tracking", first=False), "judge"),
    ("Mac (no remote env) passes", dict(prompt="add a dark mode to the coach dashboard", remote=False), "pass"),
    ("applied without companies is refused", dict(prompt="applied 2"), "block"),
]


def test_earned_time():
    sid = "earned-" + uuid.uuid4().hex
    a = run("applied 2 Stripe Ramp", sid=sid)
    b = run("add a dark mode to the coach dashboard", sid=sid)
    return a == "block" and b == "pass", f"applied -> {a}, then side work -> {b}"


def test_fallback_tz():
    spec = importlib.util.spec_from_file_location("fgc", HOOK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    checks = [
        (datetime(2026, 11, 11, 14, 0, tzinfo=timezone.utc), "09:00"),  # EST
        (datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc), "10:00"),   # EDT
        (datetime(2026, 3, 8, 6, 59, tzinfo=timezone.utc), "01:59"),    # just before spring forward
        (datetime(2026, 3, 8, 7, 0, tzinfo=timezone.utc), "03:00"),     # spring forward
        (datetime(2026, 11, 1, 5, 59, tzinfo=timezone.utc), "01:59"),   # EDT, before fall back
        (datetime(2026, 11, 1, 6, 0, tzinfo=timezone.utc), "01:00"),    # fall back
    ]
    got = [mod._us_eastern_fallback(u).strftime("%H:%M") for u, _ in checks]
    want = [w for _, w in checks]
    return got == want, f"got {got}"


def main():
    failed = 0
    for name, kw, want in CASES:
        got = run(**kw)
        ok = got == want
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {got}" + ("" if ok else f" (want {want})"))
    for name, fn in (("earned time unlocks the session", test_earned_time),
                     ("no-tzdata Eastern fallback handles DST", test_fallback_tz)):
        ok, detail = fn()
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f": {detail}"))
    total = len(CASES) + 2
    print(f"\n{total - failed}/{total} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
