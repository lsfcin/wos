#!/usr/bin/env python3
# SessionStart — delete session marker stores older than 2 days. See code/ROADMAP-verify.md W1.
#
# THIS HOOK IS NOW LOAD-BEARING, not hygiene. The stores moved out of the temp directory into the
# repository on 2026-09-22, because a session outlives a reboot and a temp directory does not. The
# operating system used to empty them; nothing does now but this. If it stops running, the stores
# accumulate under core/state/ forever — which is the cost that buys a marker surviving the night.
#
# A SECOND SPELLING OF A PATH ANOTHER MODULE OWNS is the defect this was ported to remove, and it
# outranks any question about which directory is which: the store's name is asked of hook_input, and
# where state lives is asked of platform_law. Neither is restated here.
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
KINDS = ('ctx_seen', 'iface_seen', 'facades', 'cg_reminded', 'nostub', 'branch', 'ctx_meter',
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
