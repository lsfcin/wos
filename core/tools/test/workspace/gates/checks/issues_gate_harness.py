# Shared harness for the issues-gate tests: a throwaway repo with an ISSUES.md, and the gate
# run over an Edit payload the way the hook protocol delivers it. One copy, two consumers —
# the duplication gate refused the second inline duplicate.
import json
import subprocess
import sys

from conftest import WORKSPACE_ROOT

GATE = WORKSPACE_ROOT / 'core/hooks/checks/issues-gate.py'


def repo_with(tmp_path, body):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    issues = tmp_path / 'ISSUES.md'
    issues.write_text(f'# Workspace issues\n\n{body}', encoding='utf-8', newline='\n')
    return issues


def edit_issue(tmp_path, issues, old, new):
    payload = {'session_id': 'test-issues-gate', 'cwd': str(WORKSPACE_ROOT), 'tool_name': 'Edit',
               'tool_input': {'file_path': str(issues), 'old_string': old, 'new_string': new}}
    return subprocess.run([sys.executable, str(GATE)], input=json.dumps(payload),
                          capture_output=True, text=True, timeout=180, encoding='utf-8')


def spec_file(tmp_path, name):
    testdir = tmp_path / 'test'
    testdir.mkdir(exist_ok=True)
    (testdir / name).write_text('def test_it():\n    assert True\n', encoding='utf-8', newline='\n')
