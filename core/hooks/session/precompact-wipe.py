#!/usr/bin/env python3
# PreCompact — wipe this session's CONTEXT.md and interface markers so both chains are re-read after
# compaction (injected context may be summarized away). See code/ROADMAP-verify.md W1.
# Switched off: the seen-markers survive compaction, so the chain is not re-read.
#
# PORTED OUT OF SHELL 2026-09-02, same move as session-prune.py beside it. The bash spelled
# `/tmp/claude_ctx_seen_$sid` — the store's name copied by hand out of hook_input.py — and paid three
# subprocesses to get there: `run --python`, a `python -c` to pull one field out of the payload, and
# a `run hooks/feature_law.py` to ask the switch. All three are imports here.
#
# THE COPIED NAME IS THE POINT, not the `/tmp` in it. hook_input.py builds `claude_<kind>_<sid>`
# under platform_law.session_state; this file rebuilt the same string from two literals. Nothing
# checked they agreed, and the one place they could disagree — a temp directory that is `%TEMP%` on
# one clone — is the one place no test here can look. Ask the owner and the question is gone.
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from hook_input import parse_stdin, store  # noqa: E402

# Both stores. The interface marker was never wiped here, so a compaction re-asked for the
# CONTEXT.md chain while leaving the stub gate unlocked — half a wipe, on the one event that exists
# to reset both.
KINDS = ('ctx_seen', 'iface_seen')


def main() -> int:
	"""Never blocks. A PreCompact hook that raises loses the compaction, not just the wipe."""
	if not feature_law.is_enabled('precompact-wipe'):
		return 0
	# No empty-id guard, and the bash had one. parse_stdin falls back to the parent pid when the
	# payload carries no session_id, and that is the SAME id every writer of these stores used, so
	# skipping would leave exactly the marks the wipe exists to clear.
	_, _, _, session_id, _ = parse_stdin()
	for kind in KINDS:
		shutil.rmtree(store(session_id, kind), ignore_errors=True)
	return 0


if __name__ == '__main__':
	sys.exit(main())
