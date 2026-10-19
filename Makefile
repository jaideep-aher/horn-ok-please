# Offline checks. `make reproduce` rebuilds summaries from committed predictions
# and exits non-zero if those bytes change. Two analyzers are excluded; the
# Reproduce section of README.md says why.

PYTHON ?= python3
# eval/round3/analyze.py fills `readers` from a set. This seed keeps the
# committed key order. The rates themselves do not depend on it.
REPRO_HASHSEED ?= 6

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
	poster/build/derived_stats.json

reproduce:
	PYTHONHASHSEED=$(REPRO_HASHSEED) $(PYTHON) eval/analyze.py
	PYTHONHASHSEED=$(REPRO_HASHSEED) $(PYTHON) eval/round2/analyze.py
	PYTHONHASHSEED=$(REPRO_HASHSEED) $(PYTHON) eval/round3/analyze.py
	PYTHONHASHSEED=$(REPRO_HASHSEED) $(PYTHON) eval/dev/analyze.py
	PYTHONHASHSEED=$(REPRO_HASHSEED) $(PYTHON) poster/derived_stats.py >/dev/null
	git diff --exit-code -- $(REPRO_SUMMARIES) web site-offline
