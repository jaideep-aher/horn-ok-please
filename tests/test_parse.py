from hornok.parse import parse_decision, strip_echo


def test_action_line():
    action, rationale = parse_decision("ACTION: CONTINUE\nBECAUSE: the lane is empty")
    assert action == "CONTINUE"
    assert "empty" in rationale


def test_negated_brake_does_not_win():
    action, _ = parse_decision("ACTION: CONTINUE\nBECAUSE: do not brake for the slogan")
    assert action == "CONTINUE"


def test_do_not_brake_alone_is_not_brake():
    action, _ = parse_decision("Please do not brake.")
    assert action == "UNPARSEABLE"


def test_json_action():
    raw = '{"action": "CHANGE_LANE", "rationale": "left lane blocked"}'
    action, rationale = parse_decision(raw)
    assert action == "CHANGE_LANE"
    assert "blocked" in rationale


def test_aliases():
    assert parse_decision("ACTION: stop")[0] == "BRAKE"
    assert parse_decision("ACTION: lane change")[0] == "CHANGE_LANE"
    assert parse_decision("ACTION: slow down")[0] == "SLOW"


def test_conflict_is_unparseable():
    assert parse_decision("maybe brake or continue")[0] == "UNPARSEABLE"


def test_strip_echo():
    prompt = "Choose an action"
    assert strip_echo(prompt + "\nACTION: BRAKE", prompt) == "ACTION: BRAKE"
