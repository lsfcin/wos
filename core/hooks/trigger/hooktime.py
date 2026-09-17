# What the enforcement layer COSTS when it fires, in seconds, read from the registrations rather
# than from a hardcoded list. Usage: core/run hooks/trigger/hooktime.py [--reps N] [--config PATH].
# No network, no model.
#
# BESIDE trigger_law.py ON PURPOSE, and not in core/tools/ with the other instruments (ruled
# 2026-09-05, Lucas). This directory's question is "read it from the registrations, never from
# where the file sits": trigger_law.py answers WHEN a feature fires, this answers WHAT IT COSTS
# when it does, and both parse the same harness config to do it. It also takes `--config`, because
# a number measured on one harness says nothing about the other four.
#
# Exists because the numbers that steered the last two fixes — 0.41 s per gated Read, 0.054 s for
# the dispatcher — live only as prose in core/hooks/gates.txt, core/hooks/dispatch.py and a commit
# message. The script that produced them died in a scratchpad, so nothing could re-run them, and a
# measured number nobody can check is the shape this workspace forbids twice over. This is the
# bench, in the tree, so the next session inherits the method and not just the digits.
#
# THE PAYLOAD IS THE QUESTION. Hooks select on capability(), never on tool name, so the bench feeds
# one canonical payload per capability and reports what each registered hook charges for it. A row
# reading ~0 for a capability the hook cannot serve is the hook exiting early — which is the saving
# the dispatcher was built for, and the thing to watch when a matcher is narrowed.
import json
import re
import statistics
import subprocess
import sys
import time
import uuid
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_law import WORKSPACE_ROOT as ROOT  # noqa: E402 — path is set above, house pattern

# `${CLAUDE_PROJECT_DIR}`, `${ZCODE_PROJECT_DIR}`, and whatever the next harness calls its root.
ROOT_VAR = re.compile(r'\$\{[A-Z_]*PROJECT_DIR\}')

# One payload per capability, shaped so capability() answers what the key says. The session id is a
# throwaway per run: several hooks write per-session state, and a bench must not seed the real one.
PAYLOADS = {
	'read': ('Read', {'file_path': str(ROOT / 'AGENTS.md')}),
	'write': ('Edit', {'file_path': str(ROOT / 'AGENTS.md'),
	                   'old_string': 'x', 'new_string': 'y'}),
	'shell': ('Bash', {'command': 'true'}),
	'other': ('Grep', {'pattern': 'nothing'}),
}


def commands(config: Path, event: str) -> list:
	"""Every hook command registered for one event, in the order the harness runs them.

	TWO CONFIG SHAPES, because two harnesses spell the same registration differently: Claude Code
	puts the events directly under `hooks`, ZCode nests them under `hooks.events` beside an
	`enabled` flag. Reading only the first shape made this bench report ZERO hooks for ZCode —
	silently, as a clean run — which is the reading of a harness's config that b20260901 is about.
	"""
	data = json.loads(config.read_text(encoding='utf-8'))
	events = data.get('hooks') or {}
	if isinstance(events.get('events'), dict):
		events = events['events']
	found = []
	for entry in events.get(event, []):
		matcher = entry.get('matcher', '.*')
		for hook in entry.get('hooks', []):
			if command := hook.get('command'):
				# EVERY HARNESS NAMES THE ROOT ITSELF — ${CLAUDE_PROJECT_DIR}, ${ZCODE_PROJECT_DIR},
				# and whatever the next one calls it. Substituting only the Claude spelling left
				# every ZCode command unresolvable, and an unresolvable command returns in 0.001 s:
				# the bench reported the broken harness as the fast one.
				found.append((matcher, ROOT_VAR.sub(str(ROOT), command)))
	return found


def timed(command: str, payload: str, reps: int) -> float:
	"""Median wall time of one hook over `reps` runs, or -1.0 if it never ran.

	Median, not mean: a first run pays the filesystem cache and would otherwise set the number.
	A HOOK THAT CANNOT START IS NOT A FAST HOOK — an unresolvable command comes back in about a
	millisecond, so without this the bench scores a broken registration as the best row on the
	page. Exit 2 is a gate blocking, which is the gate working; anything the shell itself refuses
	(126, 127) is the spawn failing.
	"""
	samples = []
	for _ in range(reps):
		start = time.perf_counter()
		done = subprocess.run(command, shell=True, input=payload, text=True, encoding='utf-8',
		                      capture_output=True, cwd=ROOT)
		samples.append(time.perf_counter() - start)
		if done.returncode in (126, 127):
			return -1.0
	return statistics.median(samples)


def floor(reps: int) -> None:
	"""What a hook costs before any of our code runs — the number every row below sits on top of."""
	python = subprocess.run(['sh', str(ROOT / 'core' / 'run'), '--python'], capture_output=True,
	                        text=True, encoding='utf-8').stdout.strip()
	rows = [('sh core/run --python', f'sh {ROOT / "core" / "run"} --python'),
	        ('the interpreter alone', f'{python} -c pass')]
	print('floor — paid before a gate asks anything')
	for label, command in rows:
		print(f'  {label:<34} {timed(command, "", reps):6.3f} s')


def main() -> int:
	args = sys.argv[1:]
	reps = int(args[args.index('--reps') + 1]) if '--reps' in args else 3
	config = (Path(args[args.index('--config') + 1]).resolve() if '--config' in args
	          else ROOT / '.claude' / 'settings.json')
	if not config.is_file():
		sys.exit(f'no such config: {config}')

	name = config.relative_to(ROOT) if config.is_relative_to(ROOT) else config
	print(f'{name} · median of {reps} · {ROOT}\n')
	floor(reps)

	for event in ('PreToolUse', 'PostToolUse'):
		registered = commands(config, event)
		if not registered:
			continue
		print(f'\n{event} — {len(registered)} hook(s), each row the cost of ONE tool call')
		print(f"  {'hook':<44} " + ' '.join(f'{name:>8}' for name in PAYLOADS))
		totals = dict.fromkeys(PAYLOADS, 0.0)
		for matcher, command in registered:
			label = command.replace(str(ROOT), '').lstrip('/ ')[:44]
			cells = []
			for capability, (tool, tool_input) in PAYLOADS.items():
				# THE MATCHER IS PART OF THE PRICE. A hook the harness skips costs nothing, so a
				# bench that runs it anyway reports a bill nobody pays — and would have scored
				# narrowing a matcher, the cheapest fix there is, as no improvement at all.
				if not re.search(matcher, tool):
					cells.append(f'{"—":>8}')
					continue
				payload = json.dumps({'session_id': f'hooktime-{uuid.uuid4().hex[:8]}',
				                      'cwd': str(ROOT), 'tool_name': tool,
				                      'tool_input': tool_input})
				seconds = timed(command, payload, reps)
				if seconds < 0:
					cells.append(f'{"FAILED":>8}')
					continue
				totals[capability] += seconds
				cells.append(f'{seconds:8.3f}')
			print(f'  {label:<44} ' + ' '.join(cells) + f'   [{matcher}]')
		print(f"  {'TOTAL':<44} " + ' '.join(f'{totals[c]:8.3f}' for c in PAYLOADS))
	return 0


if __name__ == '__main__':
	sys.exit(main())
