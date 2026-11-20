# One handoff per repository: sections accumulate until a session takes them, and taking deletes.
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest
from conftest import WORKSPACE_ROOT

_spec = importlib.util.spec_from_file_location('handoff_names', WORKSPACE_ROOT / 'core/tools/wos/close/handoff.py')
handoff = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(handoff)


def repo(path):
    path.mkdir(parents=True)
    subprocess.run(['git', 'init', '-q', str(path)], check=True)
    return path


def log(path, rows):
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8', newline='\n')
    return path


def patch(call, name, lines, success=True):
    return [
        {'type': 'response_item', 'payload': {'type': 'custom_tool_call', 'name': 'apply_patch',
         'call_id': call, 'input': f'*** Begin Patch\n*** Update File: {name}\n@@\n{lines}\n*** End Patch'}},
        {'type': 'response_item', 'payload': {'type': 'custom_tool_call_output', 'call_id': call,
         'output': 'Success. Updated the following files:' if success else 'patch verification failed'}},
    ]


def test_the_key_is_the_repository_path_and_names_no_agent(tmp_path):
    root = repo(tmp_path / 'workspace')
    nested = repo(root / 'code/project')
    assert handoff.key_of(root, root) == 'workspace'
    assert handoff.key_of(root, nested) == 'code-project'
    a = handoff.choose(root, root, 's', 'chatgpt', None)
    b = handoff.choose(root, root, 't', 'claude', None)
    assert a['path'] == b['path'] == str(root / 'outputs/handoff-workspace.md')


def test_a_pending_handoff_accumulates_and_a_take_empties_it(tmp_path):
    root = repo(tmp_path / 'workspace')
    path = handoff.path_for(root, 'workspace')
    handoff.write(path, 'claude', 'a', 'first\n')
    handoff.write(path, 'chatgpt', 'b', 'second\n')
    taken = handoff.take(path)
    assert taken.index('first') < taken.index('second')
    assert '["claude", "a"]' in taken and '["chatgpt", "b"]' in taken
    assert handoff.TAKEN in taken
    assert not path.exists()
    assert handoff.take(path) is None
    assert handoff.take(handoff.path_for(root, 'mistyped')) is None
    assert not handoff.lock_for(handoff.path_for(root, 'mistyped')).exists()


def test_a_session_rewriting_its_handoff_replaces_only_its_own_section(tmp_path):
    root = repo(tmp_path / 'workspace')
    path = handoff.path_for(root, 'workspace')
    handoff.write(path, 'claude', 'a', 'draft\n')
    handoff.write(path, 'chatgpt', 'b', 'theirs\n')
    handoff.write(path, 'claude', 'a', 'final\n')
    text = path.read_text(encoding='utf-8')
    assert 'draft' not in text and text.index('theirs') < text.index('final')


def test_the_lock_outlives_every_operation(tmp_path):
    root = repo(tmp_path / 'workspace')
    path = handoff.path_for(root, 'workspace')
    handoff.write(path, 'claude', 'a', 'x\n')
    handoff.take(path)
    assert handoff.lock_for(path).exists()


def test_every_edited_repository_gets_its_own_handoff(tmp_path):
    root = repo(tmp_path / 'workspace')
    nested = repo(root / 'code' / 'project')
    (root / 'unrelated-dirty.md').write_text('other session\n' * 1000, encoding='utf-8', newline='\n')
    rows = patch('a', str(root / 'one.md'), '-old\n+new')
    rows += patch('b', str(nested / 'two.md'), '+one\n+two\n+three')
    rows += patch('failed', str(root / 'bad.md'), '+ignored\n' * 100, False)
    rows += patch('output', str(root / 'outputs' / 'old.md'), '+ignored\n' * 100)
    info = handoff.choose(root, root, 's', 'chatgpt', log(tmp_path / 'log.jsonl', rows))
    assert info['repository'] == str(nested)
    assert info['lines'] == {str(root): 2, str(nested): 3}
    assert [r['path'] for r in info['repos']] == [str(root / 'outputs/handoff-code-project.md'),
                                                 str(root / 'outputs/handoff-workspace.md')]


def test_a_repository_nested_in_outputs_counts(tmp_path):
    root = repo(tmp_path / 'workspace')
    site = repo(root / 'outputs' / 'links')
    rows = patch('a', str(root / 'one.md'), '+one')
    rows += patch('b', str(site / 'lib.js'), '+one\n+two')
    rows += patch('c', str(root / 'outputs' / 'handoff-x.md'), '+ignored\n' * 100)
    info = handoff.choose(root, root, 's', 'chatgpt', log(tmp_path / 'log.jsonl', rows))
    assert info['repository'] == str(site)
    assert info['lines'] == {str(root): 1, str(site): 2}
    assert info['path'] == str(root / 'outputs/handoff-outputs-links.md')


def test_claude_errors_and_sidechains_are_excluded(tmp_path):
    root = repo(tmp_path / 'workspace')
    def use(identifier, side=False):
        return {'type': 'assistant', 'sessionId': 's', 'isSidechain': side, 'message': {'content': [
            {'type': 'tool_use', 'id': identifier, 'name': 'Edit', 'input': {
             'file_path': str(root / 'one.md'), 'old_string': 'one\ntwo', 'new_string': 'three'}}]}}
    def result(identifier, error=False):
        return {'type': 'user', 'message': {'content': [
            {'type': 'tool_result', 'tool_use_id': identifier, 'is_error': error}]}}
    path = log(tmp_path / 'claude.jsonl', [use('ok'), result('ok'), use('bad'), result('bad', True),
                                         use('child', True), result('child')])
    assert handoff.edits(path, root) == {str(root / 'one.md'): 3}
    assert handoff.transcript('s', 'claude', root, str(path)) == path
    with pytest.raises(ValueError, match='does not identify'):
        handoff.transcript('other', 'claude', root, str(path))


def test_no_recorded_edits_falls_back_without_inspecting_dirty_diff(tmp_path):
    root = repo(tmp_path / 'workspace')
    info = handoff.choose(root, root, 's', 'chatgpt', None)
    assert info['basis'] == 'working repository fallback'
    assert info['lines'] == {}
    assert [r['path'] for r in info['repos']] == [info['path']]


def test_identity_is_not_guessed_from_latest_session(monkeypatch):
    for key in ('CODEX_THREAD_ID', 'CODEX_SESSION_ID', 'CLAUDE_SESSION_ID', 'CLAUDE_CODE_SESSION_ID'):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ValueError, match='No session identity'):
        handoff.identity()
    monkeypatch.setenv('CODEX_THREAD_ID', 'current-session')
    assert handoff.identity() == ('current-session', 'chatgpt')
