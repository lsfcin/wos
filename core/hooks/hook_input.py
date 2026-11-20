# Shared parser for Claude Code hook stdin JSON — nested (current) and flat (legacy shim) schemas.
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from platform_law import session_state  # noqa: E402


def _ppid_session() -> str:
	shell_pid = os.getppid()
	try:
		result = subprocess.check_output(
			['ps', '-o', 'ppid=', '-p', str(shell_pid)],
			text=True, stderr=subprocess.DEVNULL, encoding='utf-8'
		).strip()
		return result if result.isdigit() else str(shell_pid)
	except Exception:
		return str(shell_pid)


def parse_stdin() -> tuple[dict[str, Any], str, dict[str, Any], str, str]:
	"""Returns (raw, tool_name, tool_input, session_id, cwd).

	Current Claude Code sends {session_id, cwd, tool_name, tool_input:{...}}.
	Legacy/Copilot shim sends flat tool_input fields at top level with
	CLAUDE_TOOL_NAME / CLAUDE_TOOL_INPUT in the environment.
	"""
	raw_env = os.environ.get('CLAUDE_TOOL_INPUT', '')
	try:
		data = json.loads(raw_env) if raw_env else json.load(sys.stdin)
	except Exception:
		data = {}
	if not isinstance(data, dict):
		data = {}

	tool = data.get('tool_name') or os.environ.get('CLAUDE_TOOL_NAME', '')
	tool_input = data.get('tool_input')
	if not isinstance(tool_input, dict):
		tool_input = data  # flat legacy schema: fields live at top level
	session_id = str(data.get('session_id') or '') or _ppid_session()
	cwd = str(data.get('cwd') or os.getcwd())
	return data, tool, tool_input, session_id, cwd


def capability(tool: str, tool_input: dict[str, Any]) -> str:
	"""What this call DOES — 'shell', 'write', 'read' or 'other' — read from the payload.

	The gates used to name tools. On Windows the harness exposes a PowerShell tool beside Bash, and
	`Get-Content` on a source file with a current stub walked past every read gate while `sed`
	through Bash was blocked: the enforcement layer was weaker on one operating system, silently
	(b20260901). A matcher listing tool names is a whitelist that goes stale the next time a harness
	adds one, so the question moved to the payload: a call carrying a command line runs one, a call
	carrying a path plus new content writes it, a call carrying only a path reads it. That stays
	true of a tool nobody here has met yet."""
	if str(tool_input.get('command', '')).strip():
		return 'shell'
	if not any(str(tool_input.get(k, '')).strip()
	           for k in ('file_path', 'notebook_path', 'path')):
		return 'other'
	writes = any(k in tool_input for k in ('content', 'new_string', 'new_source', 'edits'))
	return 'write' if writes else 'read'


def is_subagent(raw: dict[str, Any]) -> bool:
	"""True when this hook fired inside a worker rather than the main thread.

	`agent_id` is present only within a subagent — that is the harness's own documented way to tell
	the two apart, and `agent_type` is NOT (it is set for the main thread too in --agent sessions).

	The rule lives here because two gates need it and a second copy is the drift the law modules
	exist to catch. Why the gates use it: CONTEXT.md carries *routing*, and a worker handed one
	explicit path does not need to know where else it could have gone. Correctness constraints live
	in SPECS.md and `spec-read-gate.py` still fires for everyone. Ruled 2026-08-15 (Lucas); measured
	in core/experiments/subagent-context-chain.md.
	"""
	return bool(raw.get('agent_id'))


def normalise(raw: str) -> str:
	"""One spelling of a path, so a marker written by one hook is legible to another.

	The alternative cost a live gate: the interface gate, while it was still shell, compared three
	spellings of one file with `grep -qxF` — this side's `C:\\Users\\...`, the payload's
	`c:\\Users\\...`, and a `readlink -f` `c:/Users/...`. None matched, so it blocked every source
	read and reading the interface, the thing its own message promised would unlock it, never could.
	Both ends call this now, which is the fix the port made structural.
	"""
	try:
		return str(Path(raw).resolve())
	except OSError:
		return raw


# A SESSION MARKER IS A DIRECTORY, ONE FILE PER ENTRY, and that shape IS the fix for a lost mark.
#
# These were one text file appended to per entry, and a PostToolUse hook is one process per Read, so
# a parallel batch of N reads ran N of them at once. Measured 2026-09-02 on this clone, 16 concurrent
# trackers over 30 rounds: `open(path, 'a')` lost an entry in EVERY round — 22% of writes gone — and
# `os.open(O_APPEND)` + a single `os.write` lost them in 8 rounds of 20. The CRT emulates append as
# seek-to-end-then-write, which is not atomic across processes, so the last writer overwrites what
# landed between its seek and its write. What the agent saw was a gate re-demanding a CONTEXT.md it
# had just read, on the turn it did the right thing.
#
# Creating a DISTINCT file is atomic on both systems: no lock, no retry, and nothing here has to ask
# the boundary what an operating system is. The entry's name is a digest of the path so the same mark
# twice is the same file, which is also what makes marking idempotent and lets every caller drop its
# read-before-write guard.
def store(session_id: str, kind: str) -> Path:
	"""Where one session's marks of one kind live. Public because the wipe deletes these.

	session/precompact-wipe.py spelled `/tmp/claude_ctx_seen_$sid` in shell — a second copy of this
	name, on the wrong temp directory for one of the two systems. The owner of a name owns who can
	ask for it.
	"""
	return session_state(f'claude_{kind}_{session_id}')


# EVERY FAILURE HERE IS PER-ENTRY, and the reason is the defect above one layer up. A `try` around
# the whole comprehension turns ONE unreadable entry into an EMPTY set — the gate re-demanding a
# CONTEXT.md the session already read, which is the exact symptom the directory shape was built to
# end. The store is written by one process while another reads it, so a vanished entry (a concurrent
# precompact wipe) is normal traffic and may cost at most the mark it belongs to.
def _load(session_id: str, kind: str) -> set[str]:
	try:
		entries = list(store(session_id, kind).iterdir())
	except OSError:
		return set()
	found = set()
	for entry in entries:
		try:
			found.add(entry.read_text(encoding='utf-8').strip())
		except OSError:
			continue
	return found


# WRITE THEN RENAME, because creating the file and filling it are two steps and a reader between
# them gets `''`. Distinct-file creation is what made marking atomic; it does not make the CONTENT
# atomic, and _load reads content. `os.replace` is atomic on both systems and overwrites, which is
# what keeps the same mark twice idempotent. The temp name carries the pid so two hooks marking the
# same path at once cannot land on each other's half-written file.
def _mark(session_id: str, kind: str, path: str) -> None:
	folder = store(session_id, kind)
	entry = folder / hashlib.sha1(path.encode('utf-8')).hexdigest()[:16]
	pending = entry.with_suffix(f'.{os.getpid()}')
	try:
		folder.mkdir(parents=True, exist_ok=True)
		pending.write_text(path, encoding='utf-8', newline='\n')
		os.replace(pending, entry)
	except OSError:
		pass  # a PostToolUse exit status is read by nobody; a marker we cannot write is not fatal


def load_seen(session_id: str) -> set[str]:
	return _load(session_id, 'ctx_seen')


def mark_seen(session_id: str, path: str) -> None:
	_mark(session_id, 'ctx_seen', path)


# The interface marker is the same session-scoped list one store over, and it lived privately in
# read/context-tracker.py — which no gate can import, because a hyphen is not an identifier. That is
# the whole reason context-tracker grew a query CLI arm, now deleted with the shell caller that
# needed it. Beside its twin, both readers just call it. The facade pair is the third of the same
# shape, hand-rolled in facade-{gate,tracker}.py until the measurement above showed it had been
# losing marks the whole time too.
def load_iface_seen(session_id: str) -> set[str]:
	return _load(session_id, 'iface_seen')


def mark_iface_seen(session_id: str, path: str) -> None:
	_mark(session_id, 'iface_seen', path)


def load_facades(session_id: str) -> set[str]:
	return _load(session_id, 'facades')


def mark_facade(session_id: str, path: str) -> None:
	_mark(session_id, 'facades', path)


def announced(session_id: str, kind: str, key: str) -> bool:
	"""True when `key` has already been said this session — and records it when it has not.

	Every "say it once" reminder wants this and each used to grep its own text file for a substring,
	which matched a path that merely CONTAINED another. Ask-and-record in one call, because the two
	halves apart are what let a reminder mark itself said on a turn it was never shown.
	"""
	if key in _load(session_id, kind):
		return True
	_mark(session_id, kind, key)
	return False
