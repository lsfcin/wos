# T0: a blocking read gate names every prerequisite of the read, not the one it happens to own.
#
# Two PreToolUse hooks fire on the same Read -- read/context-gate.py for the CONTEXT.md chain and
# read/pre-read.py for the interface stub -- both exit 2, and the harness reports only whichever
# lands first. Measured 2026-09-01: one payload, both gates blocking, one message surfacing. So a
# gate naming its own slice sent the agent back for the rest on the NEXT turn, and reading one
# source file in a fresh subtree cost FIVE tool calls, two of them pure retries. In the six-hour
# session sampled that day, 33 of 295 tool calls were gate rejections.
#
# The guarantee is agreement, not any one message: whichever gate wins the race, the agent gets the
# same complete list and one parallel batch clears both.
import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from conftest import WORKSPACE_ROOT
from platform_law import interpreter

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/read'))
from chain import blocking_interface, context_chain, interface_state  # noqa: E402

CONTEXT_GATE = WORKSPACE_ROOT / 'core/hooks/read/context-gate.py'
PRE_READ = WORKSPACE_ROOT / 'core/hooks/read/pre-read.py'


def _subject() -> Path:
	"""A real source file with a current stub AND a CONTEXT.md chain — both gates must want it.

	Chosen from the tree rather than spelled, because the state under test is a *relationship*
	between three files on disk, and a name pinned here would rot the first time one of them moved.
	"""
	for source in sorted((WORKSPACE_ROOT / 'core/hooks').rglob('*.py')):
		if blocking_interface(source) is not None and len(context_chain(source)) >= 2:
			return source
	pytest.skip('no source file in core/hooks/ currently carries both a stub and a chain')


def _run(gate: Path, target: Path, session: str, tool: str = 'Read') -> subprocess.CompletedProcess:
	"""Through `core/run`, because that is how every harness spawns a gate.

	Not `[interpreter(), gate]`: `run` is what exports PYTHONIOENCODING=utf-8, and without it a gate
	printing ⛔ dies inside its own message on a console codepage that has no such character. A spec
	that spawns a gate a way nobody spawns it measures a program nobody runs.
	"""
	# The payload carries the SHAPE the named tool really sends, because that shape is what the
	# gates read now — a call with a path and new content writes, one with only a path reads
	# (b20260901-a-second-shell-tool-walks-past-every-read-gate). A bare file_path under the name
	# `Edit` is a payload no harness produces, and asserting on one measures nobody's program.
	tool_input = {'file_path': str(target)}
	if tool != 'Read':
		tool_input |= {'old_string': 'a', 'new_string': 'b'}
	payload = json.dumps({'session_id': session, 'cwd': str(WORKSPACE_ROOT),
	                      'tool_name': tool, 'tool_input': tool_input})
	argv = ['sh', str(WORKSPACE_ROOT / 'core/run'), f'hooks/read/{gate.name}']
	return subprocess.run(argv, input=payload, capture_output=True, text=True,
	                      check=False, encoding='utf-8', errors='replace')


def _named(result: subprocess.CompletedProcess, candidates: list[Path]) -> set[str]:
	return {p.name for p in candidates if p.name in result.stderr}


def test_both_read_gates_name_the_same_complete_set() -> None:
	subject = _subject()
	session = f'test-{uuid.uuid4()}'
	expected = context_chain(subject) + [blocking_interface(subject)]

	from_chain_gate = _run(CONTEXT_GATE, subject, session)
	from_stub_gate = _run(PRE_READ, subject, session)

	assert from_chain_gate.returncode == 2 and from_stub_gate.returncode == 2, (
		'both gates must block an unprepared read, or this spec is measuring nothing')
	assert _named(from_chain_gate, expected) == {p.name for p in expected}, (
		f'the chain gate named a subset:\n{from_chain_gate.stderr}')
	assert _named(from_stub_gate, expected) == {p.name for p in expected}, (
		f'the stub gate named a subset:\n{from_stub_gate.stderr}')


def test_a_satisfied_read_costs_no_further_round_trip() -> None:
	"""Reading everything the first message named must be enough — one batch, then through."""
	subject = _subject()
	session = f'test-{uuid.uuid4()}'
	tracker = WORKSPACE_ROOT / 'core/hooks/read/context-tracker.py'
	for prerequisite in context_chain(subject) + [blocking_interface(subject)]:
		_run(tracker, prerequisite, session)

	assert _run(CONTEXT_GATE, subject, session).returncode == 0
	assert _run(PRE_READ, subject, session).returncode == 0


def test_a_stub_is_demanded_of_a_read_and_of_nothing_else() -> None:
	"""read/pre-read.py matches Read alone, so an Edit that demanded a stub would invent a rule."""
	subject = _subject()
	result = _run(CONTEXT_GATE, subject, f'test-{uuid.uuid4()}', tool='Edit')

	assert result.returncode == 2, 'the chain is still owed on an Edit'
	assert blocking_interface(subject).name not in result.stderr, (
		f'no gate enforces a stub before an Edit:\n{result.stderr}')


@pytest.mark.parametrize('state,expected_rc,marker', [
	('current', 2, 'READ INTERFACE FIRST'),
	('stale', 0, 'INTERFACE STALE'),
	('absent', 0, 'NO INTERFACE'),
	('none', 0, ''),
])
def test_the_state_a_gate_acts_on_is_the_state_the_chain_reports(state, expected_rc, marker,
                                                                 tmp_path) -> None:
	"""`chain.interface_state` is what lets the chain gate speak for the stub gate's prerequisite.

	Both gates read it now, which is what the port bought — the four states used to live twice, once
	here and once as a shell `case` no Python caller could ask, and two readings of one law drift the
	way STUB_FOR and GATE_ON once did. This pins the definition to the behaviour on every state, so a
	future divergence fails here rather than in a message an agent cannot satisfy.
	"""
	source = tmp_path / ('__init__.py' if state == 'none' else 'subject.py')
	source.write_text('def f():\n    return 1\n', encoding='utf-8', newline='\n')
	stub = tmp_path / 'subject.pyi'
	if state == 'current':
		stub.write_text('def f() -> int: ...\n', encoding='utf-8', newline='\n')
	elif state == 'stale':
		stub.write_text('def f() -> int: ...\n', encoding='utf-8', newline='\n')
		import os
		os.utime(stub, (0, 0))

	assert interface_state(source)[0] == state
	result = _run(PRE_READ, source, f'test-{uuid.uuid4()}')
	assert result.returncode == expected_rc
	if marker:
		assert marker in (result.stdout + result.stderr)
