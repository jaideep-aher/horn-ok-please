import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("publish", ROOT / "poster" / "publish.py")
publish = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(publish)


def test_web_prompt_matches_locked_prompt():
    from hornok.prompts import DEFENSE_APPENDIX_V1, DRIVING_PROMPT_V1

    text = (ROOT / "web" / "src" / "lib" / "prompts.ts").read_text(encoding="utf-8")
    assert DRIVING_PROMPT_V1 in text
    assert DEFENSE_APPENDIX_V1 in text


def test_pending_poster_has_no_invented_rate():
    html = publish.poster_html({"pending": True, "reason": "not yet"})
    assert "Results pending" in html
    assert "30.0%" not in html
    assert "QR placeholder" in html


def test_poster_prints_only_stored_counts():
    summary = {
        "pending": False,
        "primary_model": "smolvlm-256m-f16",
        "edge_model": "smolvlm-256m-q4",
        "placement": "truck_rear",
        "n_records": 4,
        "n_drive_records": 4,
        "asr": [
            {
                "model": "smolvlm-256m-f16",
                "script": "en",
                "placement": "truck_rear",
                "defense": "none",
                "subset": "primary",
                "k": 2,
                "n": 10,
                "rate": 0.2,
                "ci_low": 0.057,
                "ci_high": 0.510,
            }
        ],
        "benign_accuracy": [],
        "tests": [],
        "literacy": [],
        "regulatory": [],
        "parse_failures": [],
    }
    html = publish.poster_html(summary)
    assert "2/10" in html
    assert "20.0%" in html
    markdown = publish.results_markdown(summary)
    assert "2/10 (20.0%, Wilson 95% CI 5.7–51.0%)" in markdown
    pitch = publish.pitch_markdown(summary)
    assert "2/10" in pitch
    assert "GPT-4o" in pitch
