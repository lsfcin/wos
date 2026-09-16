# b20260901-the-codegraph-nudge-only-fires-when-a-stub-is-stale regression — a suggestion about the
# PROJECT fires for the project, not for the one file whose stub happens to be out of date.
#
# The nudge sat at the foot of the shell gate, reachable on exactly ONE path: a source whose stub was
# stale. Every other state returned before it — a facade, a type with no interface convention, an
# absent or empty stub, a stub already read, and a current stub, which blocks before line 89. Its own
# comment said "one-time per project per session", which describes neither.
#
# It was unreachable for a SECOND reason nobody had found, measured here on 2026-09-02: the guard was
# `[[ "$file" == "$WORKSPACE_ROOT"/code/* ]]`, and `$WORKSPACE_ROOT` came from a `cd` — `/c/Users/...`
# in MSYS — while the payload carries `C:\Users\...`. The glob could not match on this clone, so even
# the stale path printed nothing. That is inside the file whose own comment block records the same
# failure being fixed on 2026-08-30: a branch that cannot fire is indistinguishable from one with no
# reason to, twice over, in the same twenty lines.
#
# It is NOT emitted on the blocking branch. The harness shows stderr on exit 2, so a nudge printed to
# stdout there would mark itself said on a turn nobody saw it — the same defect one layer down.
import json
import shutil
import subprocess
import uuid

import pytest

from conftest import WORKSPACE_ROOT

GATE = 'hooks/read/pre-read.py'
MARKER = 'codegraph indexed'

# SERIAL, and this file is the second case b20260902 recorded. Every case here creates a real
# directory under code/ and removes it, so a worker walking that tree beside them hits a path that
# vanished mid-walk: test_present_tense_state_is_not_a_corpse died on `code/_nudgeprobe5b974581`
# exactly that way. The marker was missing until 2026-09-05 because nothing checked the law —
# core/tools/test/conftest.py's tree guard is what checks it now.
pytestmark = pytest.mark.serial


@pytest.fixture
def indexed_project():
	"""A throwaway codegraph-indexed project under code/, because that is where the guard looks.

	Built on disk rather than mocked: the defect WAS the guard's reading of a real path, and a fake
	one would have passed against the shell it replaced.
	"""
	project = WORKSPACE_ROOT / f'code/_nudgeprobe{uuid.uuid4().hex[:8]}'
	(project / '.codegraph').mkdir(parents=True)
	(project / 'mod.py').write_text('def g():\n    return 2\n', encoding='utf-8', newline='\n')
	yield project
	shutil.rmtree(project, ignore_errors=True)


def _read(path, session: str) -> subprocess.CompletedProcess:
	payload = json.dumps({'session_id': session, 'tool_name': 'Read',
	                      'tool_input': {'file_path': str(path)}})
	return subprocess.run(['sh', str(WORKSPACE_ROOT / 'core/run'), GATE], input=payload,
	                      capture_output=True, text=True, check=False,
	                      encoding='utf-8', errors='replace')


def _stub(project, mtime: str) -> None:
	stub = project / 'mod.pyi'
	stub.write_text('def g() -> int: ...\n', encoding='utf-8', newline='\n')
	if mtime == 'stale':
		import os
		os.utime(stub, (0, 0))


@pytest.mark.parametrize('state', ['absent', 'stale'])
def test_the_nudge_fires_on_every_state_that_lets_the_read_through(indexed_project, state) -> None:
	if state == 'stale':
		_stub(indexed_project, 'stale')
	result = _read(indexed_project / 'mod.py', f'test-{uuid.uuid4()}')

	assert result.returncode == 0
	assert MARKER in result.stdout, (
		f'the project is indexed and the read was allowed in state {state!r}, and the suggestion '
		f'was not made:\n{result.stdout!r}')


def test_the_nudge_names_the_project_root_not_the_file(indexed_project) -> None:
	result = _read(indexed_project / 'mod.py', f'test-{uuid.uuid4()}')
	assert str(indexed_project) in result.stdout
	assert 'mod.py' not in result.stdout.split(MARKER, 1)[1]


def test_it_is_said_once_per_project_per_session(indexed_project) -> None:
	"""Its own comment's promise, and the half that was true before the fix."""
	session = f'test-{uuid.uuid4()}'
	first = _read(indexed_project / 'mod.py', session)
	(indexed_project / 'other.py').write_text('def h():\n    return 3\n',
	                                          encoding='utf-8', newline='\n')
	second = _read(indexed_project / 'other.py', session)

	assert MARKER in first.stdout
	assert MARKER not in second.stdout, 'a per-project nudge repeated for a second file'


def test_a_blocked_read_does_not_spend_the_nudge(indexed_project) -> None:
	"""Exit 2 shows stderr, so a stdout nudge there is marked said and never seen. The next read
	that actually goes through is the one that must carry it."""
	_stub(indexed_project, 'current')
	session = f'test-{uuid.uuid4()}'
	blocked = _read(indexed_project / 'mod.py', session)
	assert blocked.returncode == 2
	assert MARKER not in blocked.stdout

	(indexed_project / 'plain.py').write_text('def k():\n    return 4\n',
	                                          encoding='utf-8', newline='\n')
	assert MARKER in _read(indexed_project / 'plain.py', session).stdout


def test_an_unindexed_project_is_silent(indexed_project) -> None:
	shutil.rmtree(indexed_project / '.codegraph')
	assert MARKER not in _read(indexed_project / 'mod.py', f'test-{uuid.uuid4()}').stdout
