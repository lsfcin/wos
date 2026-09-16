# b20260901-a-read-gate-races-the-tracker-that-clears-it regression — a parallel batch of reads
# loses none of its marks.
#
# The gate's own message says to read the whole CONTEXT.md chain in ONE parallel batch. Doing exactly
# that could still be refused, naming a file the batch had just read: on 2026-09-01 a four-file batch
# cleared three, and core/tools/test/CONTEXT.md — read successfully in it — was demanded again on the
# retry. It cost the round trip the message exists to save, on the turn the agent did the right thing.
#
# TWO HYPOTHESES, ONE ESTABLISHED. The finding named both and could not choose: a lost append, or the
# gate simply running before the last PostToolUse tracker finished. Measured 2026-09-02 on this clone,
# 16 concurrent trackers over 30 rounds: `open(path, 'a')` lost a mark in EVERY round, ~22% of writes,
# and `os.open(O_APPEND)` + one `os.write` lost them in 8 rounds of 20 — the CRT emulates append as
# seek-then-write, which is not atomic between processes. A marker is a directory of one file per
# entry now, and that is what this spec holds: not the implementation, the property.
#
# CONCURRENT PROCESSES, NOT THREADS. Threads share a file object and an interpreter lock, so a
# threaded version of this passes against the very code that shipped the bug.
import json
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor

from conftest import WORKSPACE_ROOT
from hook_input import load_facades, load_iface_seen, load_seen
from platform_law import interpreter

TRACKER = WORKSPACE_ROOT / 'core/hooks/read/context-tracker.py'
FACADE_TRACKER = WORKSPACE_ROOT / 'core/hooks/facade/facade-tracker.py'
BATCH = 16


def _fire(tracker, session: str, path: str) -> None:
	payload = json.dumps({'session_id': session, 'cwd': str(WORKSPACE_ROOT),
	                      'tool_name': 'Read', 'tool_input': {'file_path': path}})
	subprocess.run([interpreter(), str(tracker)], input=payload, capture_output=True,
	               text=True, check=False, encoding='utf-8')


def _batch(tracker, session: str, paths: list) -> None:
	with ThreadPoolExecutor(max_workers=len(paths)) as pool:
		list(pool.map(lambda p: _fire(tracker, session, p), paths))


def test_a_parallel_batch_of_context_reads_loses_no_mark() -> None:
	session = f'test-{uuid.uuid4()}'
	_batch(TRACKER, session, [str(WORKSPACE_ROOT / f'check{i}/CONTEXT.md') for i in range(BATCH)])
	assert len(load_seen(session)) == BATCH, (
		f'{BATCH} concurrent trackers left {len(load_seen(session))} marks. The gate will re-demand '
		"a CONTEXT.md that was read — see this file's header for what a lost mark costs")


def test_a_parallel_batch_of_interface_reads_loses_no_mark() -> None:
	"""The stub marker is the same store one over, and it unlocks a source read the same way."""
	session = f'test-{uuid.uuid4()}'
	_batch(TRACKER, session, [str(WORKSPACE_ROOT / f'check{i}/subject.pyi') for i in range(BATCH)])
	assert len(load_iface_seen(session)) == BATCH


def test_a_parallel_batch_of_facade_reads_loses_no_mark() -> None:
	"""The third store of the same shape. It was hand-rolled in facade-{gate,tracker}.py and had been
	losing marks for exactly as long, silently, because nothing had ever pointed a batch at it."""
	session = f'test-{uuid.uuid4()}'
	_batch(FACADE_TRACKER, session,
	       [str(WORKSPACE_ROOT / f'code/check{i}/__init__.py') for i in range(BATCH)])
	assert len(load_facades(session)) == BATCH


def test_marking_the_same_path_twice_is_one_mark() -> None:
	"""Idempotence is what let every caller drop its read-before-write guard — the read half of the
	read-modify-write that made the window wide enough to lose a mark in the first place."""
	session = f'test-{uuid.uuid4()}'
	target = str(WORKSPACE_ROOT / 'check/CONTEXT.md')
	_batch(TRACKER, session, [target] * 4)
	assert load_seen(session) == {target}
