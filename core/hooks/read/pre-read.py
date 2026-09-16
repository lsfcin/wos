#!/usr/bin/env python3
# PreToolUse: Read — block a source read while its interface stub is current.
# Current stub: hard block (exit 2), the stub must be read first. Stale: warn and allow.
#
# Ported out of shell 2026-09-02, the last bash on the hot read path. It spent FIVE subprocesses
# per Read — `run --python`, two `python -c` JSON parses, and on the blocking branch a query each to
# context-tracker, feature_law and context-gate — to answer one mtime comparison between two files.
# Every one of them is an import here. Being shell is also what kept the stub map out of Python until
# stubs.GATE_ON: the four states this gate ranks lived in a `case` no Python caller could ask, so the
# CONTEXT.md gate could not know a stub was about to block the same Read.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from chain import EXEMPT_NAMES, interface_state, prerequisites  # noqa: E402
from file_law import is_code_file  # noqa: E402
from hook_input import announced, capability, load_iface_seen, load_seen, parse_stdin  # noqa: E402
from platform_law import WORKSPACE_ROOT  # noqa: E402


def codegraph_root(target: Path) -> Path | None:
	"""The nearest ancestor holding a `.codegraph` index, or None.

	WORKSPACE_ROOT, not a spelled path. Until 2026-08-30 the shell condition matched one machine's
	absolute code/ directory, which no other clone has — and it was STILL broken here on 2026-09-02,
	because that root came from a `cd` (`/c/Users/...` in MSYS) while the payload carries
	`C:\\Users\\...`, so the glob could not match on a Windows clone either. Asked of pathlib now.

	`is_code_file` rather than a suffix list of its own: it is the one definition of what code is,
	and it already answers no for a generated stub, which is the only exclusion the shell `case`
	really encoded.
	"""
	if not target.is_relative_to(WORKSPACE_ROOT / 'code') or not is_code_file(target):
		return None
	for directory in target.parents:
		if (directory / '.codegraph').is_dir():
			return directory
		if directory == WORKSPACE_ROOT:
			break
	return None


def nudge(session_id: str, target: Path, state: str, iface: Path | None) -> None:
	"""What a read that is going THROUGH still has to say. Never reached on the blocking branch.

	The codegraph suggestion used to sit at the foot of the shell script, reachable on exactly one
	path — a source whose stub was stale — because every other state returned before it. Its own
	comment says "one-time per project per session", which describes a hook that fires for the
	PROJECT, so it fires on every read this gate allows. It is not emitted on the blocking branch:
	the harness shows stderr there and a nudge that marked itself said on a turn nobody saw it is
	the same defect one layer down.
	"""
	if state == 'absent' and not announced(session_id, 'nostub', str(target)):
		# NAMED BUT ABSENT was silent until 2026-08-31, and it is the worst of the states: a current
		# stub blocks, a stale one warns, and a missing one switches the gate OFF for that file while
		# the hook still reads as passing. 200 files sat in it across the nested repos. Allow the
		# read — blocking a reader because a GENERATOR never ran punishes the wrong side — but never
		# in silence. An EMPTY stub counts as absent: tsc emits a zero-byte .d.ts for a module that
		# exports nothing, and blocking the source to hand back a blank file is worse than no gate.
		print(f'ℹ️  NO INTERFACE — {target}\n'
		      '   Nothing generated a stub, so the interface-first gate is OFF for this file.\n'
		      f'   Generate: core/run hooks/stubgen/stubs.py {target}')
	elif state == 'stale':
		print(f'⚠️  INTERFACE STALE: {iface}\n'
		      '   Source was modified after interface was generated.\n'
		      '   Reading source directly — save the file to regenerate the interface.')

	root = codegraph_root(target)
	if root is not None and not announced(session_id, 'cg_nudged', str(root)):
		print('💡 codegraph indexed — explore before reading source:\n'
		      f'   codegraph explore "<question>" {root}\n'
		      f'   codegraph query "<symbol>" {root}')


def main() -> int:
	# THE LAW IS ASKED AT THE TOP NOW, and the reason it was not is a cost this port deleted. In
	# shell the question meant `sh run hooks/feature_law.py --enabled …` — a whole subprocess on a
	# hook that fires on every Read — so it was pushed down onto the rare branch about to block. In
	# Python it is an import and two small file reads. A switch consulted only where a gate happens
	# to block is also a switch nothing can observe: test_the_wired_gates_actually_consult_the_law
	# drives each wired hook with a payload and this arm was the one it could not see.
	if not feature_law.is_enabled('interface-first-reads'):
		return 0
	_, tool, tool_input, session_id, _ = parse_stdin()
	# A read, by capability — the `file_path` check below is what keeps a directory-wide search out.
	if capability(tool, tool_input) != 'read':
		return 0
	raw = str(tool_input.get('file_path', ''))
	if not raw:
		return 0
	try:
		target = Path(raw).resolve()
	except OSError:
		return 0

	# A facade IS its own interface, and a type carrying no interface convention has nothing to say.
	# Both are `none`, and silence is correct for both.
	state, iface = interface_state(target)
	if state != 'current' or str(iface) in load_iface_seen(session_id):
		nudge(session_id, target, state, iface)
		return 0

	# NAME THE WHOLE SET, NOT THIS GATE'S SLICE. context-gate.py fires on the same Read, also exits 2,
	# and the harness reports only whichever lands first — measured 2026-09-01, both blocking on one
	# payload and one message surfacing. A message naming only the stub sends the agent back for the
	# CONTEXT.md chain on the NEXT turn: five tool calls to read one file, two of them pure retries.
	needed = prerequisites(target, load_seen(session_id), load_iface_seen(session_id), True)
	print(f'⛔ READ INTERFACE FIRST — {target}\n'
	      '   Read these first, in ONE parallel batch, then retry:', file=sys.stderr)
	for path in needed:
		note = '' if path.name in EXEMPT_NAMES else \
			'   <- interface; all public signatures without implementation noise'
		print(f'   {path}{note}', file=sys.stderr)
	print('   (Reading the interface unlocks the source for this session.)', file=sys.stderr)
	return 2


sys.exit(main())
