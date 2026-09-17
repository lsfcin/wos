# Makefile — verification contract (see code/VERIFY.md). verify-fast is free; live smoke is manual.
#
# The interpreter is asked for, never named: ../../core/run --python prints this clone's venv
# python, whichever layout the machine uses. It was an absolute POSIX path until aiwbot was
# versioned inside the workspace (2026-09-12).
PY := $(shell ../../core/run --python)

verify-fast:
	$(PY) -m pytest -q tests

verify-full:
	$(PY) -m pytest -q tests

test: verify-fast

smoke:
	$(PY) proto.py

.PHONY: verify-fast verify-full test smoke
