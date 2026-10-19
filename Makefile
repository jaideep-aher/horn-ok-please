# Offline checks. `make reproduce` rebuilds summaries from committed predictions
# and exits non-zero if those bytes change.

PYTHON ?= python3

.PHONY: setup test reproduce

setup:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m ruff check src tests eval poster
	$(PYTHON) -m pytest

REPRO_SUMMARIES := \
	eval/results/summary.json \
	eval/round2/results/summary.json \
	eval/round3/results/summary.json \
	eval/dev/results/summary.json \
	eval/photos/results/summary.json \
	eval/xai/results/summary.json \
	eval/gemini_remote/phase2/results/summary.json \
	poster/build/derived_stats.json

reproduce:
	$(PYTHON) eval/analyze.py
	$(PYTHON) eval/round2/analyze.py
	$(PYTHON) eval/round3/analyze.py
	$(PYTHON) eval/dev/analyze.py
	$(PYTHON) eval/photos/analyze.py
	$(PYTHON) eval/xai/analyze.py
	$(PYTHON) eval/gemini_remote/phase2/analyze_phase2.py
	$(PYTHON) poster/derived_stats.py >/dev/null
	git diff --exit-code -- $(REPRO_SUMMARIES) web site-offline
