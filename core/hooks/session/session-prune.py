#!/usr/bin/env python3
# SessionStart — delete session marker stores older than 2 days. See code/ROADMAP-verify.md W1.
#
# PORTED OUT OF SHELL 2026-09-02. The bash spelled `/tmp` and reached it with `find`, while every
# writer of these stores asks platform_law.session_state — `tempfile.gettempdir()`, which is `%TEMP%`
# on Windows. Whether those are the same directory there depends on Git Bash mounting `/tmp` at
# `%TEMP%`, which platform_law's own docstring asserts and NOTHING in this workspace can check: the
# claim is about a mount on the other clone, and neither machine can test the other. A second
# spelling of a path that another module owns is the defect regardless of which way the coin lands —
# asked of that module now, so the question stops existing.
#
# WHAT WAS ACTUALLY MEASURED, here, on Linux, where the two paths certainly agree: the kind list was
# stale. `ctx_meter` and `agent_ctx` stores from August 27–28 were still in /tmp on 2026-09-02
# because no glob named them, so this hook has been leaking two of its eight kinds regardless of
# operating system. That is the real defect the port carries a fix for, and it is a smaller and
# duller one than the paragraph above.
#
# THE KIND LIST IS HAND-MAINTAINED, and that is a known cost. There is no registry of marker kinds —
# each hook names its own — so a new kind leaks until someone adds it here. The alternative, globbing
# every `claude_*` in the temp directory, would reach files this workspace does not own; a list that
# can go stale is the smaller mistake.
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_law import session_state  # noqa: E402

MAX_AGE_SECONDS = 2 * 24 * 60 * 60
KINDS = ('ctx_seen', 'iface_seen', 'facades', 'cg_nudged', 'nostub', 'branch', 'ctx_meter',
         'agent_ctx')


def stale(now: float, path: Path) -> bool:
	"""Older than two days by mtime, asked without raising on a path that vanished mid-scan.

	A store is written by a live session while this runs, so a race here is normal traffic. Missing
	is not stale: something else already removed it.
	"""
	try:
		return now - path.stat().st_mtime > MAX_AGE_SECONDS
	except OSError:
		return False


def main() -> int:
	"""Never blocks. A SessionStart hook that raises is a traceback where the session belonged."""
	# The parent of a store, never a spelled path: session_state answers where these live, and the
	# argument is discarded. Asking it is what makes this hook find the stores on both systems.
	state_dir = session_state('any').parent
	now = time.time()
	for kind in KINDS:
		for store in state_dir.glob(f'claude_{kind}_*'):
			if not stale(now, store):
				continue
			# Both shapes, because the ported stores are directories and the pre-2026-09-02 ones
			# beside them are still `.txt` files. `rm -rf` in the bash covered both; so does this.
			try:
				if store.is_dir():
					shutil.rmtree(store, ignore_errors=True)
				else:
					store.unlink()
			except OSError:
				continue
	return 0


if __name__ == '__main__':
	sys.exit(main())
