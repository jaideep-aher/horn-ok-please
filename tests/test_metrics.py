from hornok.metrics import holm, is_targeted_flip, mcnemar_exact, text_similarity, wilson_interval


def test_wilson_empty_and_zero():
    assert wilson_interval(0, 0) is None
    low, high = wilson_interval(0, 10)
    assert low == 0
    assert 0.2 < high < 0.35


def test_wilson_full():
    low, high = wilson_interval(10, 10)
    assert high == 1
    assert low > 0.65


def test_mcnemar_no_discordant():
    result = mcnemar_exact([True, False], [True, False])
    assert result["n_discordant"] == 0
    assert result["p"] == 1.0


def test_mcnemar_counts():
    result = mcnemar_exact([True] * 6, [False] * 6)
    assert result["b_only"] == 6
    assert result["c_only"] == 0
    assert result["p"] < 0.05


def test_holm_stepdown():
    adjusted = holm([0.01, 0.04])
    assert adjusted[0] == 0.02
    assert adjusted[1] == 0.04
    capped = holm([0.4, 0.5])
    assert all(p <= 1 for p in capped)


def test_targeted_flip_rules():
    assert is_targeted_flip("BRAKE", "CONTINUE", "CONTINUE")
    assert not is_targeted_flip("CONTINUE", "CONTINUE", "CONTINUE")
    assert not is_targeted_flip("UNPARSEABLE", "CONTINUE", "CONTINUE")
    assert not is_targeted_flip("BRAKE", "SLOW", "CONTINUE")


def test_similarity():
    assert text_similarity("stop", "stop") == 1
    assert text_similarity("stop", "stop!") < 1
    assert text_similarity("", "stop") == 0
