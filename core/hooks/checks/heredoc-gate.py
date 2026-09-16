#!/usr/bin/env python3
# PreToolUse: Bash — a shell heredoc that writes a workspace file meets none of the file gates.
#
# `size-gate.py`, `facade-gate.py`, `spec-read-gate.py` and `issues-gate.py` are all
# `PreToolUse: Edit|Write`, so `cat > file << 'EOF'` walks past every one of them. Measured over
# this workspace's transcripts (2026-08-15): 128 such calls, 354,100 chars, and among them
# brain/INBOX.md, HISTORY.md and test_entropy_list.py — written past the 200-line size gate, the
# first-line-comment check and the CONTEXT.md description rule. See core/hooks/SPECS.md.
#
# Two arms, because a payload has two ways to write. The shell's own redirects (`>`, `>>`, `tee`)
# are read off the opener line. A body handed to an interpreter's stdin is read too, but only when
# it BOTH calls a write verb and names a path git tracks — the case on 2026-09-04 where
# `Path('ISSUES.md').write_text(...)` inside a heredoc deleted two bug sections with no gate firing.
#
# Warns, never blocks, and the reason is not politeness: a PreToolUse hook fires AFTER the model has
# emitted the payload. The tokens are already spent, and blocking only makes the turn re-emit them.
# This gate teaches turn N+1. It cannot recover turn N.
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from hook_input import capability, parse_stdin
from platform_law import rel  # noqa: E402

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]

# A heredoc opener: `<< EOF`, `<<'EOF'`, `<<-"EOF"`. Not `<<<`, which is a here-string.
OPENER = re.compile(r'<<-?\s*(?![<])[\'"]?([A-Za-z_][A-Za-z0-9_]*)[\'"]?')
# An output redirect to a path. Excludes `2>`, `>&2` and friends — those go to a stream, not a file.
REDIRECT = re.compile(r'(?<![0-9&>])>>?\s*(?![&>])([^\s;|&<>()]+)')
# `tee out.txt`, `tee -a out.txt`. tee names its target as an argument, with no `>` to spot.
TEE = re.compile(r'\btee\b\s+((?:-\S+\s+)*)([^\s;|&<>()-][^\s;|&<>()]*)')
# An interpreter reading its script from stdin: `python3 - <<'EOF'`, `"$(sh core/run --python)" -`.
STDIN_DASH = re.compile(r'(?:^|[\s"\')])-\s+<<')
# A write performed INSIDE that script. Python and node, the two interpreters reached this way here.
WRITE_VERB = re.compile(r'\b(?:write_text|write_bytes|writeFileSync|appendFileSync|os\.replace'
                        r'|os\.rename|shutil\.(?:copy|copy2|move))\s*\(|\bopen\s*\([^)]*[\'"][wax]')
# A quoted string shaped like a filename. The body is the model's text, so this only proposes.
QUOTED = re.compile(r'[\'"]([^\'"\n]{2,200}\.[A-Za-z0-9]{1,8})[\'"]')


def targets(line: str) -> list:
	"""Every path this OPENER LINE would write, by shell syntax alone — `>`, `>>`, `tee`.

	Empty for `python3 - <<'EOF'`, and the reason is a fact about redirects, not about the process:
	a script reaching an interpreter through stdin can write anything the session can, and this
	function cannot see it. `body_writes` answers that half; keeping them apart is what lets the
	stdin exclusion stay. It is the one this gate cannot get wrong — stdin-to-an-interpreter is 44%
	of all heredoc volume here and is throwaway analysis, and a gate firing on those gets turned off.
	"""
	found = [match.group(1) for match in REDIRECT.finditer(line)]
	found += [match.group(2) for match in TEE.finditer(line)]
	return found


def body_writes(body: str, cwd: str) -> list:
	"""Tracked paths an interpreted body writes. Two conditions, never one.

	A write verb alone fires on every throwaway script that saves a temp file; a tracked path alone
	fires on every script that merely reads one. Both together is the case the file gates would have
	caught had the write gone through the Edit tool. `git ls-files` is asked once, and only after the
	verb has already narrowed the payload.
	"""
	if not WRITE_VERB.search(body):
		return []
	names = sorted({match.group(1) for match in QUOTED.finditer(body)})
	if not names:
		return []
	done = subprocess.run(['git', '-C', cwd or str(WORKSPACE_ROOT), 'ls-files', '--', *names],
	                      capture_output=True, text=True, encoding='utf-8', errors='replace')
	return [line for line in done.stdout.splitlines() if line.strip()]


def in_workspace(target: str, cwd: str) -> Path | None:
	"""The path, if it lands inside the workspace. A write to /tmp is not this gate's business."""
	try:
		path = Path(target).expanduser()
		resolved = (path if path.is_absolute() else Path(cwd or '.') / path).resolve()
		resolved.relative_to(WORKSPACE_ROOT)
	except (ValueError, OSError, RuntimeError):
		return None
	return resolved


def written_paths(command: str, cwd: str) -> list:
	"""Scan a payload for heredoc writes: the opener's redirects, and an interpreted body's writes.

	A body is read ONLY when its opener handed the heredoc to an interpreter's stdin. Every other
	body stays unparsed, which is the property that kept this gate quiet enough to leave switched on.
	"""
	found: list = []
	delimiter, body, interpreted = '', [], False
	for line in command.split('\n'):
		if delimiter:
			if line.strip() != delimiter:
				body.append(line)
				continue
			for name in (body_writes('\n'.join(body), cwd) if interpreted else []):
				path = in_workspace(name, cwd)
				if path and path not in found:
					found.append(path)
			delimiter, body, interpreted = '', [], False
			continue
		opener = OPENER.search(line)
		if not opener:
			continue
		delimiter, interpreted = opener.group(1), bool(STDIN_DASH.search(line))
		for target in targets(line):
			path = in_workspace(target, cwd)
			if path and path not in found:
				found.append(path)
	return found


def main() -> int:
	if not feature_law.is_enabled('heredoc-gate'):
		return 0  # switched off: a disabled gate does not block, and does not pretend it ran
	_raw, tool, tool_input, _session, cwd = parse_stdin()
	if capability(tool, tool_input) != 'shell':
		return 0  # by capability, never by name — a harness may expose a second shell
	paths = written_paths(str(tool_input.get('command', '')), cwd)
	if not paths:
		return 0
	names = ', '.join(rel(p, WORKSPACE_ROOT) for p in paths[:3])
	print(json.dumps({'hookSpecificOutput': {
		'hookEventName': 'PreToolUse',
		'additionalContext': f'⚠ UNGATED WRITE — {names} was written by a heredoc, either redirected '
		                     f'by the shell or written inside an interpreted body, which skips the '
		                     f'size, first-line, CONTEXT.md and ISSUES.md checks. Use the Write tool '
		                     f'for workspace files.',
	}}))
	return 0


if __name__ == '__main__':
	sys.exit(main())
