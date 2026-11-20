# T0 the handoff gate: a handoff is opened by taking it, so Read, Write and a shell reader are each sent to `--take`.
import json
import subprocess
import uuid

import pytest

from conftest import WORKSPACE_ROOT
from platform_law import interpreter

GATE = WORKSPACE_ROOT / 'core/hooks/read/handoff-gate.py'


def _run(tool: str, tool_input: dict) -> subprocess.CompletedProcess:
    payload = {'tool_name': tool, 'tool_input': tool_input, 'session_id': f't-{uuid.uuid4()}',
               'cwd': str(WORKSPACE_ROOT)}
    return subprocess.run([interpreter(), str(GATE)], input=json.dumps(payload),
                          capture_output=True, text=True, check=False, encoding='utf-8')


@pytest.fixture
def pending():
    path = WORKSPACE_ROOT / 'outputs' / f'handoff-zz-gate-test-{uuid.uuid4().hex[:8]}.md'
    path.parent.mkdir(exist_ok=True)
    path.write_text('# pending\n', encoding='utf-8', newline='\n')
    yield path
    path.unlink(missing_ok=True)


def test_read_and_write_are_sent_to_take(pending):
    for tool, data in (('Read', {'file_path': str(pending)}),
                       ('Write', {'file_path': str(pending), 'content': '# x\n'})):
        done = _run(tool, data)
        assert done.returncode == 2, tool
        assert '--take' in done.stderr


def test_a_shell_reader_is_sent_to_take(pending):
    done = _run('Bash', {'command': f'cat {pending.relative_to(WORKSPACE_ROOT)}'})
    assert done.returncode == 2 and '--take' in done.stderr


def test_the_tool_itself_and_unrelated_commands_pass(pending):
    key = pending.stem.removeprefix('handoff-')
    for command in (f'core/run tools/wos/handoff --take {key}', 'ls outputs/handoff-*', 'git status'):
        assert _run('Bash', {'command': command}).returncode == 0, command


def test_a_file_that_only_looks_like_a_handoff_passes(tmp_path):
    other = tmp_path / 'handoff-notes.md'
    assert _run('Read', {'file_path': str(other)}).returncode == 0
