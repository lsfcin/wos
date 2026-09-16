#!/usr/bin/env python3
# PreToolUse: Bash — send every line of a multi-line command through rtk, not just the first.
# rtk parses line 1 only, so `cd x\ngit status` reaches the context uncompacted; measured at
# 23.4% of Bash calls (first line is `cd`) plus 1,249 rewritable commands stranded on lines 2+.
# Delegates verbatim to `rtk hook claude` for every shape it cannot split safely.
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law
from hook_input import parse_stdin
from platform_law import session_state  # noqa: E402

# Bound the subprocess fan-out: one rtk call per line, so a huge payload delegates instead.
MAX_LINES = 30
# A line that opens a block, continues onto the next, or feeds a heredoc is not a standalone
# command, and splitting the payload around it would change what the shell runs.
BLOCK_KEYWORD = re.compile(r'^\s*(if|then|else|elif|fi|for|while|until|do|done|case|esac|select|function|\{|\}|\(|\))\b')
CONTINUES = re.compile(r'(\\|\||&&|;)\s*$')


def ask_rtk(command: str) -> str | None:
	"""rtk's raw stdout. Three states the callers all need: None = unrunnable, '' = silent, str = verdict."""
	payload = json.dumps({
		'hook_event_name': 'PreToolUse',
		'tool_name': 'Bash',
		'tool_input': {'command': command},
	})
	# RESOLVED, NEVER THE BARE WORD. `which` honours PATHEXT, so it finds rtk however this machine
	# spells an executable; handing the bare name to subprocess does not — CreateProcess resolves
	# only against .exe, so anything else on PATH is invisible and reads as "rtk declined".
	found = shutil.which('rtk')
	if not found:
		return None
	try:
		done = subprocess.run(
			[found, 'hook', 'claude'], input=payload,
			capture_output=True, text=True, timeout=10, encoding='utf-8'
		)
	except (OSError, subprocess.SubprocessError):
		return None
	return done.stdout if done.stdout.strip() else ''


def rewritten_command(out: str) -> str | None:
	"""The command rtk put in its verdict, or None if the shape is not what we expect."""
	try:
		got = json.loads(out)['hookSpecificOutput']['updatedInput']['command']
	except (ValueError, KeyError, TypeError):
		return None
	return got if isinstance(got, str) else None


def rtk_rewrite(command: str) -> str | None:
	"""How rtk would rewrite one command. None when it declines, errors, or is not installed."""
	got = rewritten_command(ask_rtk(command) or '')
	return got if got is not None and got != command else None


def delegate(command: str) -> str:
	"""Hand the payload to rtk untouched and pass its verdict through. Returns the counter's label."""
	out = ask_rtk(command)
	if out is None:
		return 'no-rtk'
	if not out:
		return 'delegated-noop'
	sys.stdout.write(out)
	return 'delegated-noop' if rewritten_command(out) is None else 'delegated-rewrote'


def record(session_id: str, verdict: str, lines: int) -> None:
	"""One row per Bash call, so adoption is a number instead of a belief. This exact bug read as a
	flat zero for weeks with nothing watching — a lever with no standing metric is a lever nobody
	can tell is broken. Same store convention as hook_input.seen_file(): per session, in /tmp.
	Ephemeral on purpose; the trend belongs in core/experiments/, not in a file that churns git."""
	if not session_id:
		return
	# Overridable so the suite can assert on an isolated dir instead of the shared temp path,
	# and so a harness that owns its own state directory can point this at it.
	name = f'claude_rtk_compact_{session_id}.tsv'
	override = os.environ.get('RTK_COMPACT_DIR')
	target = Path(override) / name if override else session_state(name)
	try:
		with open(target, 'a', encoding='utf-8', newline='\n') as handle:
			handle.write(f'{verdict}\t{lines}\n')
	except OSError:
		pass  # counting must never be able to break the command being counted


def splittable(lines: list[str]) -> bool:
	"""True only when every line stands alone as a simple command. Anything else is rtk's to judge."""
	if len(lines) > MAX_LINES:
		return False
	for line in lines:
		if '<<' in line or BLOCK_KEYWORD.match(line) or CONTINUES.search(line):
			return False
		if line.count("'") % 2 or line.count('"') % 2:
			return False
	return True


def main() -> int:
	_raw, tool, tool_input, session_id, _cwd = parse_stdin()
	if tool and tool != 'Bash':
		return 0
	command = str(tool_input.get('command', ''))
	if not command:
		return 0
	lines = command.split('\n')
	# Its own verdict, never folded into 'no-rtk': switched off and absent are different silences.
	if not feature_law.is_enabled('rtk-compaction'):
		record(session_id, 'off', len(lines))
		return 0
	# Checked once, up front: rtk_rewrite() cannot tell "declined" from "not installed", so
	# without this the split path files a missing binary as `split-noop` — an idle shim and an
	# absent one would read identically, which is the exact ambiguity the counter exists to kill.
	if shutil.which('rtk') is None:
		record(session_id, 'no-rtk', len(lines))
		return 0
	if len(lines) < 2 or not splittable(lines):
		record(session_id, delegate(command), len(lines))
		return 0

	rewritten: list[str] = []
	changed = False
	for line in lines:
		stripped = line.strip()
		if not stripped or stripped.startswith('#'):
			rewritten.append(line)
			continue
		got = rtk_rewrite(stripped)
		if got is None:
			rewritten.append(line)
			continue
		# Keep the original indentation; rtk only ever prefixes the verb.
		rewritten.append(line[:len(line) - len(line.lstrip())] + got)
		changed = True
	if not changed:
		record(session_id, 'split-noop', len(lines))
		return 0

	record(session_id, 'split-rewrote', len(lines))
	updated = dict(tool_input)
	updated['command'] = '\n'.join(rewritten)
	print(json.dumps({'hookSpecificOutput': {
		'hookEventName': 'PreToolUse',
		'permissionDecisionReason': 'RTK auto-rewrite (multi-line)',
		'updatedInput': updated,
	}}))
	return 0


sys.exit(main())
