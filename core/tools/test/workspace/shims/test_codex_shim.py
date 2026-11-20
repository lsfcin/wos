# Codex integration: patches reach every write gate and successful shell reads unlock interfaces.
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys

import pytest
from conftest import WORKSPACE_ROOT

POLICY = WORKSPACE_ROOT / 'core/hooks/codex/policy.py'


def module(name):
    path = POLICY.parent / f'{name}.py'
    spec = importlib.util.spec_from_file_location(f'codex_{name}', path)
    result = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(result)
    return result


def run_hook(payload, tmp_path, table):
    hook = tmp_path / 'core/hooks/codex/policy.py'
    if not hook.exists():
        shutil.copytree(WORKSPACE_ROOT / 'core/hooks', tmp_path / 'core/hooks')
        for name in ('features.txt', 'profile.txt'):
            shutil.copyfile(WORKSPACE_ROOT / 'core' / name, tmp_path / 'core' / name)
    env = dict(os.environ, WOS_GATES_TABLE=str(table))
    env.pop('CLAUDE_TOOL_INPUT', None)
    env.pop('CLAUDE_TOOL_NAME', None)
    payload.setdefault('session_id', f'codex-test-{tmp_path.name}')
    payload.setdefault('cwd', str(tmp_path))
    return subprocess.run([sys.executable, str(hook)], input=json.dumps(payload),
                          capture_output=True, text=True, env=env, encoding='utf-8')


def seen(workspace, sid):
    code = ('import sys,json; sys.path.insert(0,sys.argv[1]); '
            'from hook_input import load_seen; print(json.dumps(list(load_seen(sys.argv[2]))))')
    done = subprocess.run([sys.executable, '-c', code, str(workspace / 'core/hooks'), sid],
                          capture_output=True, text=True, check=True, encoding='utf-8')
    return json.loads(done.stdout)


def test_patch_checks_every_file_and_reconstructs_content(tmp_path):
    (tmp_path / 'old.py').write_text('# old\nx = 1\n', encoding='utf-8', newline='\n')
    patch = ('*** Begin Patch\n*** Update File: old.py\n@@\n # old\n-x = 1\n+x = 2\n'
             '*** Add File: new.py\n+# new\n+y = 3\n*** End Patch\n')
    changes = module('patch').changes(patch, str(tmp_path))
    assert [(Path(p['file_path']).name, p['content']) for p in changes] == [
        ('old.py', '# old\nx = 2\n'), ('new.py', '# new\ny = 3\n')]
    assert (tmp_path / 'old.py').read_text(encoding='utf-8') == '# old\nx = 1\n'
    assert not (tmp_path / 'new.py').exists()


def test_patch_delete_move_eof_and_sequential_hunks(tmp_path):
    (tmp_path / 'a.py').write_text('# a\nx = 1\ny = 2\n', encoding='utf-8', newline='\n')
    (tmp_path / 'd.py').write_text('# delete\n', encoding='utf-8', newline='\n')
    patch = ('*** Begin Patch\n*** Update File: a.py\n*** Move to: moved.py\n'
             '@@\n-x = 1\n+x = 3\n@@\n-y = 2\n+y = 4\n*** End of File\n'
             '*** Delete File: d.py\n*** End Patch\n')
    changes = module('patch').changes(patch, str(tmp_path))
    assert [Path(x['file_path']).name for x in changes] == ['a.py', 'moved.py', 'd.py']
    assert changes[1]['content'] == '# a\nx = 3\ny = 4\n'
    assert changes[0]['operation'] == changes[2]['operation'] == 'delete'


def test_bad_patch_is_refused_without_mutation(tmp_path):
    (tmp_path / 'a.py').write_text('# a\nx = 1\n', encoding='utf-8', newline='\n')
    with pytest.raises(ValueError):
        module('patch').changes('*** Begin Patch\n*** Update File: a.py\n@@\n-missing\n+x\n*** End Patch', str(tmp_path))
    assert (tmp_path / 'a.py').read_text(encoding='utf-8') == '# a\nx = 1\n'


def test_real_first_line_gate_blocks_patch_even_on_second_file(tmp_path):
    table = tmp_path / 'gates.txt'
    table.write_text('pre\twrite\t10\tchecks/first-line-gate.py\tblocks\tfirst-line-comment\n', encoding='utf-8', newline='\n')
    patch = ('*** Begin Patch\n*** Add File: good.py\n+# good\n'
             '*** Add File: bad.py\n+print(1)\n*** End Patch')
    result = run_hook({'tool_name': 'apply_patch', 'tool_input': {'command': patch}}, tmp_path, table)
    assert result.returncode == 2, result.stderr
    assert 'FIRST LINE' in result.stderr or 'FIRST-LINE' in result.stderr
    assert 'bad.py' in result.stderr
    assert not (tmp_path / 'good.py').exists()


def test_shell_read_is_recorded_only_after_success(tmp_path):
    context = tmp_path / 'CONTEXT.md'
    context.write_text('# Context\n> test\n', encoding='utf-8', newline='\n')
    table = tmp_path / 'gates.txt'
    table.write_text('post\tread\t10\tread/context-tracker.py\tinforms\tsubtree-read-tracking\n', encoding='utf-8', newline='\n')
    payload = {'hook_event_name': 'PostToolUse', 'tool_name': 'Bash',
               'tool_input': {'command': f'cat {context}'}, 'tool_response': {'exit_code': 1}}
    failed = run_hook(payload, tmp_path, table)
    assert failed.returncode == 0, failed.stderr
    sid = f'codex-test-{tmp_path.name}'
    assert str(context) not in seen(tmp_path, sid)
    payload['tool_response'] = {'exit_code': 0}
    passed = run_hook(payload, tmp_path, table)
    assert passed.returncode == 0, passed.stderr
    assert str(context) in seen(tmp_path, sid)
    # The tracker must dedupe, not accumulate copies of the same read.
    run_hook(payload, tmp_path, table)
    assert list(seen(tmp_path, sid)).count(str(context)) == 1


def test_shell_context_read_does_not_deadlock_and_then_unlocks(tmp_path):
    folder = tmp_path / 'module'
    folder.mkdir()
    context = folder / 'CONTEXT.md'
    context.write_text('# Context\n> test\n', encoding='utf-8', newline='\n')
    target = folder / 'notes.md'
    target.write_text('# Notes\n', encoding='utf-8', newline='\n')
    table = tmp_path / 'gates.txt'
    table.write_text('pre\tread\t10\tread/context-gate.py\tblocks\tcontext-chain\n'
                     'post\tread\t10\tread/context-tracker.py\tinforms\tsubtree-read-tracking\n', encoding='utf-8', newline='\n')
    payload = {'tool_name': 'Bash', 'tool_input': {'command': f'cat {target}'}}
    blocked = run_hook(payload, tmp_path, table)
    assert blocked.returncode == 2 and 'CONTEXT.md' in blocked.stderr
    payload['tool_input']['command'] = f'cat {context}'
    assert run_hook(payload, tmp_path, table).returncode == 0
    payload.update(hook_event_name='PostToolUse', tool_response={'exit_code': 0})
    assert run_hook(payload, tmp_path, table).returncode == 0
    payload.update(hook_event_name='PreToolUse', tool_input={'command': f'cat {target}'})
    assert run_hook(payload, tmp_path, table).returncode == 0


def test_search_redirect_and_running_commands_are_not_fabricated_reads(tmp_path):
    target = tmp_path / 'CONTEXT.md'
    target.write_text('# Context\n> test\n', encoding='utf-8', newline='\n')
    policy = module('policy')
    for command in (f'rg test {target}', f'cat > {target}', f'python -c "{target}"'):
        assert policy.shell_reads(command, str(tmp_path)) == []
    assert not policy.succeeded({'tool_response': {'session_id': 1, 'exit_code': None}})
    assert policy.succeeded({'tool_response': 'Process exited with code 0\nOutput: text'})


def test_unrelated_tool_is_silent(tmp_path):
    table = tmp_path / 'gates.txt'
    table.write_text('', encoding='utf-8', newline='\n')
    result = run_hook({'tool_name': 'update_plan', 'tool_input': {}}, tmp_path, table)
    assert result.returncode == 0 and not result.stdout and not result.stderr

def test_real_size_gate_sees_complete_patch_result(tmp_path):
    source = tmp_path / 'large.py'
    source.write_text('# Large\n' + 'x = 1\n' * 245, encoding='utf-8', newline='\n')
    table = tmp_path / 'gates.txt'
    table.write_text('pre\twrite\t10\tchecks/size-gate.py\tblocks\tfile-size-caps\n', encoding='utf-8', newline='\n')
    patch = ('*** Begin Patch\n*** Update File: large.py\n@@\n # Large\n'
             + '+y = 2\n' * 20 + '*** End Patch')
    done = run_hook({'tool_name': 'apply_patch', 'tool_input': {'command': patch}}, tmp_path, table)
    assert done.returncode == 2, done.stderr
    assert source.read_text(encoding='utf-8').count('y = 2') == 0


def test_rtk_success_unlocks_context_with_relative_workdir(tmp_path):
    folder = tmp_path / 'module'
    folder.mkdir()
    context = folder / 'CONTEXT.md'
    context.write_text('# Context\n> Test\n', encoding='utf-8', newline='\n')
    table = tmp_path / 'gates.txt'
    table.write_text('post\tread\t10\tread/context-tracker.py\tinforms\tsubtree-read-tracking\n', encoding='utf-8', newline='\n')
    done = run_hook({'hook_event_name': 'PostToolUse', 'tool_name': 'exec_command',
                     'tool_input': {'cmd': 'rtk read CONTEXT.md', 'workdir': 'module'},
                     'tool_response': {'exit_code': 0}}, tmp_path, table)
    assert done.returncode == 0, done.stderr
    assert str(context) in seen(tmp_path, f'codex-test-{tmp_path.name}')


def test_a_failed_patch_does_not_run_the_post_edit_pipeline(tmp_path):
    table = tmp_path / 'gates.txt'
    table.write_text('', encoding='utf-8', newline='\n')
    done = run_hook({'hook_event_name': 'PostToolUse', 'tool_name': 'apply_patch',
                     'tool_input': {'command': 'invalid patch'},
                     'tool_response': {'isError': True}}, tmp_path, table)
    assert done.returncode == 0 and not done.stderr and not done.stdout


def test_ambiguous_shell_results_do_not_record_reads(tmp_path):
    context = tmp_path / 'CONTEXT.md'
    context.write_text('# Context\n> Test\n', encoding='utf-8', newline='\n')
    policy = module('policy')
    for command in (f'cat {context}; true', f'cat {context} || true',
                    f'cat {context} | head', f'cat {context} &'):
        assert policy.shell_reads(command, str(tmp_path)) == []
    assert policy.shell_reads(f'cat {context} && cat {context}', str(tmp_path))


@pytest.mark.parametrize('command', ['cat CONTEXT.md', 'rtk read CONTEXT.md', 'rtk proxy cat CONTEXT.md'])
def test_native_stdout_only_read_unlocks_context(tmp_path, command):
    context = tmp_path / 'CONTEXT.md'
    text = '# Context\n> Native stdout without exit metadata\n'
    context.write_text(text, encoding='utf-8', newline='\n')
    table = tmp_path / 'gates.txt'
    table.write_text('post\tread\t10\tread/context-tracker.py\tinforms\tsubtree-read-tracking\n', encoding='utf-8', newline='\n')
    payload = {'hook_event_name': 'PostToolUse', 'tool_name': 'Bash',
               'tool_input': {'command': command}, 'tool_response': text}
    result = run_hook(payload, tmp_path, table)
    assert result.returncode == 0, result.stderr
    assert str(context) in seen(tmp_path, payload['session_id'])


def test_native_stdout_requires_complete_unambiguous_read(tmp_path):
    text = '# Context\n> Test\n'
    (tmp_path / 'CONTEXT.md').write_text(text, encoding='utf-8', newline='\n')
    policy = module('policy')
    payload = {'cwd': str(tmp_path), 'tool_input': {'command': 'cat CONTEXT.md'}}
    for response in (text[:10], 'Error: failed', '', {'exit_code': 1, 'exitCode': 0},
                     {'exit_code': 0, 'isError': True}):
        assert not policy.succeeded({**payload, 'tool_response': response})
    for command in ('head CONTEXT.md', 'cat -n CONTEXT.md', 'cat CONTEXT.md missing.md',
                    'cat CONTEXT.md || true', 'printf Context'):
        assert not policy.succeeded({**payload, 'tool_input': {'command': command}, 'tool_response': text})


def test_generator_progress_does_not_enter_model_context(tmp_path, monkeypatch, capsys):
    import io
    policy = module('policy')
    target = tmp_path / 'notes.md'
    target.write_text('# Notes\n', encoding='utf-8', newline='\n')
    payload = {'session_id': 'quiet', 'cwd': str(tmp_path), 'hook_event_name': 'PostToolUse',
               'tool_name': 'Write', 'tool_input': {'file_path': str(target), 'content': '# Notes\n'}}
    monkeypatch.setattr(policy.sys, 'stdin', io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(policy.dispatch, 'run_gate', lambda _: (0, '', ''))
    monkeypatch.setattr(policy.subprocess, 'run', lambda *a, **k:
                        subprocess.CompletedProcess([], 0, 'Interface regenerated\n', ''))
    assert policy.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output == {'systemMessage': 'Interface regenerated'}
