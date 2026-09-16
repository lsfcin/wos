# chain.py — the CONTEXT.md chain of a path, and the workspace paths named in a blob of text.
#
# One definition, three callers. It was two copies before (context-gate and bash-context-gate each
# carried a `context_chain`, and they had already drifted on whether to start at the target or its
# parent) — the same duplication the file-law module exists to prevent.
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_law import WORKSPACE_ROOT  # noqa: E402

# Freely readable: the deadlock guard, plus the docs that ARE the context.
EXEMPT_NAMES = {'CONTEXT.md', 'AGENTS.md', 'CLAUDE.md', 'MEMORY.md'}
SKIP_PARTS = {'.git', 'node_modules', 'dist', '.codegraph', '__pycache__', '.vscode', '.hooks'}
TOKEN_RE = re.compile(r'''[^\s'"`;|&<>()=]+''')

# Which stub blocks a read, and which files ARE their own interface. Both asked, never restated:
# stubgen owns the generated set and the wider gated one side by side, file_law owns what a file IS.
# A second copy here is the drift this file was itself created to end.
from file_law import FACADES  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stubgen'))
from stubs import GATE_ON  # noqa: E402


def context_chain(target: Path) -> list[Path]:
	"""CONTEXT.md files from the target's directory up to (excluding) the workspace root."""
	chain: list[Path] = []
	current = target if target.is_dir() else target.parent
	while current != WORKSPACE_ROOT and current != current.parent:
		ctx = current / 'CONTEXT.md'
		if ctx.is_file():
			chain.append(ctx)
		current = current.parent
	return chain


def interface_state(target: Path) -> tuple[str, Path | None]:
	"""The stub beside `target` and which of four states it is in.

	`none` — the type carries no interface convention, or the file IS a facade and already is one.
	`absent` — nothing generated a stub, or `tsc` emitted a zero-byte one for a module that exports
	nothing. An EMPTY stub is absent, not current: blocking a source read and handing the reader a
	blank file in its place is worse than not gating at all.
	`stale` — the source was saved after the stub, so the stub no longer describes it.
	`current` — the only state that gates a read.
	"""
	if target.name in FACADES:
		return 'none', None
	iface_suffix = GATE_ON.get(target.suffix)
	if iface_suffix is None:
		return 'none', None
	iface = target.with_suffix(iface_suffix)
	try:
		if not iface.is_file() or iface.stat().st_size == 0:
			return 'absent', iface
		if target.stat().st_mtime > iface.stat().st_mtime:
			return 'stale', iface
	except OSError:
		return 'absent', iface
	return 'current', iface


def blocking_interface(target: Path) -> Path | None:
	"""The stub that would block a read of `target` — `None` in every other state.

	Not named `interface_for`: stubgen's function of that name answers the GENERATOR's question and
	returns a path whether or not the file exists. Two names, because they are two questions.
	"""
	state, iface = interface_state(target)
	return iface if state == 'current' else None


def prerequisites(target: Path, seen: set[str], iface_seen: set[str], gate_interface: bool) -> list[Path]:
	"""Everything a read of `target` must be preceded by, as ONE list.

	WHY THIS IS ONE LIST AND NOT TWO MESSAGES. `context-gate.py` and `read/pre-read.py` are separate
	PreToolUse hooks on the same Read, both exit 2, and the harness reports only the FIRST — measured
	2026-09-01, both blocking on one payload, one message surfacing. So a gate that names only its own
	prerequisite hands the agent one slice per turn: reading a source file in a fresh subtree cost
	FIVE tool calls, two of them pure retries. Whichever gate wins the race now names the whole set,
	so one parallel batch clears both.

	The stub sits in the target's own directory, so it shares the chain — no second walk.
	`gate_interface` is the caller's answer to "does my tool gate on stubs at all": true for Read,
	false for Edit/Write/Grep, and false whenever `interface-first-reads` is switched off. Asking the
	law here instead would make this module the fourth place that reads the registry.
	"""
	needed = [c for c in context_chain(target) if str(c) not in seen]
	if gate_interface:
		iface = blocking_interface(target)
		# CONTEXT.md first: they are EXEMPT_NAMES, so they are free to read, while the stub itself
		# would trip the chain gate on the retry if the chain were not cleared in the same batch.
		if iface is not None and str(iface) not in iface_seen:
			needed.append(iface)
	return needed


def paths_in(text: str, cwd: str, files_only: bool = False) -> set[Path]:
	"""Every existing workspace path named in a blob of text — a command line, or an agent prompt.

	`files_only` keeps the Bash gate exactly as narrow as it was: a command merely *mentioning* a
	directory has never been gated, and widening that is a separate decision from sharing this code.
	An agent prompt is the opposite case — "work in core/flows/" is precisely the pointer a worker
	should be briefed on — so the collector leaves it off.
	"""
	found: set[Path] = set()
	for token in TOKEN_RE.findall(text):
		# Either separator: a command typed in PowerShell spells the same file with `\`, and a
		# prefilter that knows only `/` makes every such path invisible to the gate. The cheap
		# skip is "no separator at all", not "not a POSIX path".
		if '/' not in token and '\\' not in token:
			continue
		# Prose ends a path with punctuation — "...edit foo/bar.py." — and the trailing period made
		# every sentence-final path invisible. It cost a live check to catch, because the unit test
		# happened to put a space after the path. A path never legitimately ends in these.
		raw = token.strip('\'"`,:;!?()[]{}<>').rstrip('.')
		if raw.startswith('~') or raw.startswith('-'):
			continue
		candidate = Path(raw)
		path = candidate if candidate.is_absolute() else Path(cwd) / raw
		try:
			path = path.resolve()
		except OSError:
			continue
		if not (path.is_file() if files_only else path.exists()):
			continue
		# ASKED OF pathlib, NEVER SPELLED. This was `str(path).startswith(str(WORKSPACE) + '/')`
		# against a hardcoded root, and the `/` was the whole bug: on a clone where the separator
		# is `\` the prefix could never match, so this returned the empty set for every command and
		# BOTH context gates answered 0 to everything. A gate reading green while off, which is the
		# shape this workspace exists to forbid — and it survived because no test ran off /mnt.
		if not path.is_relative_to(WORKSPACE_ROOT):
			continue
		if path.name in EXEMPT_NAMES or SKIP_PARTS.intersection(path.parts):
			continue
		found.add(path)
	return found


def summary_of(ctx: Path) -> str:
	"""A CONTEXT.md's one-line self-description — its `> ` line, which is line 2 by convention.

	The head is what a session pays for; the `>` line is what a *worker* needs. Handing a subagent
	the full head would recreate the cost the exemption exists to avoid.
	"""
	try:
		for line in ctx.read_text(encoding='utf-8', errors='replace').splitlines()[:6]:
			if line.startswith('> '):
				return line[2:].strip()
	except OSError:
		pass
	return ''
