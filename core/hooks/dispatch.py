#!/usr/bin/env python3
# PreToolUse, PostToolUse: one process for every gate — read stdin once, ask the moment and the
# capability once, run what they select.
#
# WHAT THIS REPLACED. Each gate in core/hooks/gates.txt was its own `command` in each harness's
# config, so a single tool call spawned nine interpreters that each re-read the same stdin and
# re-asked the same capability question: 0.41 s on a Read that needs two of them (b20260905).
# The nine registrations were also nine hand-copied tables, and three harnesses routed by TOOL
# NAME — the whitelist b20260901 retired. The table is data now, and this file is its one reader.
#
# WHAT IT MAY NOT CHANGE. A gate that blocks exits 2 having written its OWN reason to stderr
# (core/hooks/SPECS.md). This dispatcher never composes, reformats or summarises that reason: it
# lets the gate write straight through and exits 2 itself the moment one does.
import importlib.util
import io
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scoreboard  # noqa: E402
from hook_input import capability, parse_stdin  # noqa: E402

# WOS_GATES_TABLE points this at another table, and exists for the tests alone: a real gate cannot
# be made to crash or to lie about its class on demand, so the isolation and class rules are proven
# against gates written for the purpose. Nothing in the workspace sets it.
def table_path() -> Path:
	return Path(os.environ.get('WOS_GATES_TABLE') or (HERE / 'gates.txt'))


def load_table(table: Path = None) -> dict[tuple[str, str], list[tuple[str, str, str]]]:
	"""(moment, capability) -> [(path, class, feature)], in the order the file declares.

	`table` names another copy of this file, and exists so THIS stays the only parser: trigger_law
	reads the table under a caller-supplied root, and hand-split its own until 2026-09-14 — when
	adding a sixth column broke three separate readers at once. One file, one reader.

	Order is load-bearing and lives in the data, not here: context-gate must clear before
	issues-gate, which reads the target file off disk.

	A FOUR- OR FIVE-COLUMN ROW IS STILL READ — four as `pre`, five with no feature. The tests build
	their own tables and the shims are versioned separately from this file, so a table written
	before either column existed must not silently select nothing — that is the "runs, exits
	cleanly, does nothing" shape gates.txt's own head was written about.
	"""
	rows: dict[tuple[str, str], list[tuple[int, str, str, str]]] = {}
	for line in (table or table_path()).read_text(encoding='utf-8').splitlines():
		line = line.strip()
		if not line or line.startswith('#'):
			continue
		parts = [p.strip() for p in line.split('\t')]
		if len(parts) == 4:
			parts = ['pre', *parts]
		if len(parts) == 5:
			parts = [*parts, '-']
		if len(parts) != 6:
			continue
		moment, cap, order, path, kind, feature = parts
		rows.setdefault((moment, cap), []).append((int(order), path, kind, feature))
	return {key: [(p, k, f) for _, p, k, f in sorted(items)] for key, items in rows.items()}


# EVERY GATE RUNS IN ITS OWN SANDBOX OF PROCESS STATE, because nine processes just became one.
# A gate that inserts on sys.path, sets an env var or leaves sys.argv rewritten used to take that
# damage to its grave; here it would reach the next gate in the chain. Saved and restored around
# each one, so the collapse is invisible from inside a gate — which is the whole reason no gate
# needed editing.
def run_gate(rel: str) -> tuple[int, str, str]:
	"""Run one gate in-process. Returns (exit code, its stdout, its stderr)."""
	path = HERE / rel
	out, err = io.StringIO(), io.StringIO()
	saved_path, saved_argv = list(sys.path), list(sys.argv)
	saved_out, saved_err = sys.stdout, sys.stderr
	sys.stdout, sys.stderr = out, err
	sys.argv = [str(path)]
	# ITS OWN DIRECTORY GOES ON THE PATH FIRST, which running a file as __main__ does for free and
	# exec_module does not: read/context-gate.py opens with `from chain import ...` and every gate
	# in a subdirectory has a sibling like it.
	sys.path.insert(0, str(path.parent))
	code = 0
	try:
		# THE MODULE IS NAMED `__main__`, AND THAT NAME IS A WHOLE GATE. checks/heredoc-gate.py
		# ends `if __name__ == '__main__': sys.exit(main())`; under any other name it imported
		# cleanly, ran nothing, and the dispatcher exited 0 — a silent pass wearing a success's
		# coat, the shape core/SPECS.md § Conventions forbids. The name is set on the SPEC, not on
		# the module afterwards: a loader refuses to execute a module whose name it does not own.
		# Nothing is registered in sys.modules, so the gates do not collide over the one name.
		# Caught 2026-09-05 by diffing a gate's own output against its output through here.
		spec = importlib.util.spec_from_file_location('__main__', path)
		if spec is None or spec.loader is None:
			raise ImportError(f'no loader for {path}')
		spec.loader.exec_module(importlib.util.module_from_spec(spec))
	except SystemExit as exc:
		code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
	except BaseException:  # noqa: BLE001 — see the comment on the caller
		traceback.print_exc()
		code = 1
	finally:
		sys.stdout, sys.stderr = saved_out, saved_err
		sys.path[:] = saved_path
		sys.argv[:] = saved_argv
	return code, out.getvalue(), err.getvalue()


# ONE hookSpecificOutput, NEVER TWO. Claude Code parses a hook's stdout as a single JSON document,
# so two informing gates in one process would emit two and the harness would read one — the same
# "runs, exits cleanly, heard by nobody" failure core/hooks/SPECS.md names as the reason
# additionalContext exists. Plain stdout is folded into the same field rather than dropped: it is
# exit-0 stdout, which that section calls transcript-only and read by nobody, and a gate's text
# arriving at the model is the behaviour the section asks for.
def emit(messages: list[str], event: str = 'PreToolUse') -> None:
	if not messages:
		return
	print(json.dumps({'hookSpecificOutput': {
		'hookEventName': event,
		'additionalContext': '\n'.join(messages),
	}}))


def collect(text: str, messages: list[str]) -> None:
	"""Pull a gate's own additionalContext out of its stdout; keep anything else verbatim."""
	stripped = text.strip()
	if not stripped:
		return
	try:
		payload: Any = json.loads(stripped)
		said = payload['hookSpecificOutput']['additionalContext']
	except (ValueError, KeyError, TypeError):
		messages.append(stripped)
		return
	if isinstance(said, str) and said.strip():
		messages.append(said.strip())


def main() -> int:
	raw, tool, tool_input, _, _ = parse_stdin()
	# THE MOMENT COMES FROM THE PAYLOAD, never from a second registration spelling it. Claude Code
	# and ZCode both send hook_event_name; anything that does not is PreToolUse, which is what this
	# file did before the column existed and what every shim still assumes.
	event = str(raw.get('hook_event_name') or raw.get('hookEventName') or 'PreToolUse')
	moment = 'post' if event == 'PostToolUse' else 'pre'
	cap = capability(tool, tool_input)
	gates = load_table().get((moment, cap), [])
	if not gates:
		return 0  # 'other' selects nothing — a Grep or a TodoWrite pays for no gate at all

	# THE PAYLOAD IS HANDED ON THROUGH THE ENV, which is the flat-schema arm hook_input.parse_stdin
	# already prefers (hook_input.py). stdin is consumed once and cannot be re-read nine times, and
	# this is why not one gate needed a line changed to run here.
	os.environ['CLAUDE_TOOL_INPUT'] = json.dumps(raw)
	if tool:
		os.environ['CLAUDE_TOOL_NAME'] = tool

	messages: list[str] = []
	failed = False
	for rel, kind, feature in gates:
		code, out, err = run_gate(rel)
		# A BLOCK ENDS THE CHAIN AND IS PASSED THROUGH UNTOUCHED. The gate already wrote the reason
		# a model is about to read; anything added here would be a second voice on one rejection.
		if code == 2 and kind == 'blocks':
			# COUNTED HERE BECAUSE THIS IS THE ONLY PLACE THAT SEES AN EXIT CODE. The gate recorded
			# its own `fired` through feature_law; whether that firing ever stopped anything is
			# knowable only from here (/ROADMAP.md § Measurement). A `-` feature counts nothing,
			# which is what keeps the three unswitched gates visible as a gap.
			if feature != '-':
				scoreboard.record(feature, 'blocked')
			sys.stderr.write(err)
			return 2
		if code == 2:
			# `informs` is a promise the table makes on the gate's behalf, and this is where it is
			# kept: an informing gate that tries to block does not get to. Loud, because a gate
			# whose class is wrong is a gate nobody can reason about from the table.
			sys.stderr.write(f'DISPATCH - {rel} is declared `informs` in gates.txt and exited 2.\n')
			sys.stderr.write(err)
			failed = True
			continue
		# A GATE THAT DIES TAKES ONLY ITSELF. Nine processes made that automatic; one process makes
		# it a decision. Never exit 2 on a broken gate — that would block a call it was only meant
		# to observe, the rule core/run states for a half-installed clone.
		if code != 0:
			sys.stderr.write(err)
			failed = True
			continue
		if err.strip():
			sys.stderr.write(err)
		collect(out, messages)

	emit(messages, event)
	return 1 if failed else 0


if __name__ == '__main__':
	sys.exit(main())
