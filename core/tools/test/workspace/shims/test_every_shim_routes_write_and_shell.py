# Every harness shim hands BOTH a write and a shell command to core/hooks/dispatch.py — the one
# place the branch lock is enforced (core/hooks/git/SPECS.md). b20261110 was a shim that forwarded
# paths only; a lock is only as strong as the harness that skips it.
#
# Each case runs the real shim against a gate table holding one gate that refuses everything:
# a shim that routes the call is blocked, one that drops it lets it through.
import json
import os
import re
import subprocess
import sys

import pytest
from conftest import WORKSPACE_ROOT

REFUSER = ('import sys\nprint("REFUSER refused", file=sys.stderr)\n'
         'print(\'{"decision": "deny", "reason": "REFUSER"}\')\nsys.exit(2)\n')
OPENCODE = ('const m = await import(process.argv[1]); const h = await m.WorkspacePolicy({client: {}});'
            'try { await h["tool.execute.before"](JSON.parse(process.argv[2]), JSON.parse(process.argv[3]));'
            ' } catch (e) { console.error(e.message); process.exit(2) }')


@pytest.fixture
def table(tmp_path):
    (tmp_path / 'refuser.py').write_text(REFUSER, encoding='utf-8', newline='\n')
    rows = ''.join(f'pre\t{cap}\t1\t{tmp_path / "refuser.py"}\tblocks\t-\n' for cap in ('write', 'shell'))
    (tmp_path / 'gates.txt').write_text(rows, encoding='utf-8', newline='\n')
    return tmp_path / 'gates.txt'


def _run(argv, payload, table, stdin=True):
    env = {k: v for k, v in os.environ.items() if k not in ('CLAUDE_TOOL_INPUT', 'CLAUDE_TOOL_NAME')}
    env.update(WOS_GATES_TABLE=str(table), CLAUDE_PROJECT_DIR=str(WORKSPACE_ROOT),
               ZCODE_PROJECT_DIR=str(WORKSPACE_ROOT))
    return subprocess.run(argv, input=json.dumps(payload) if stdin else None, capture_output=True,
                          text=True, cwd=str(WORKSPACE_ROOT), env=env, encoding='utf-8')


def _config_command(path):
    """The PreToolUse command the harness's own config registers, variables expanded."""
    hooks = json.loads((WORKSPACE_ROOT / path).read_text(encoding='utf-8'))['hooks']
    hooks = hooks.get('events', hooks)['PreToolUse']
    command = hooks[0]['hooks'][0]['command']
    return re.sub(r'\$\{\w+\}', str(WORKSPACE_ROOT), command).split()


def configured(path):
    def call(table, kind, target):
        tool, data = ('Write', {'file_path': target, 'content': '# x\n'}) if kind == 'write' \
            else ('Bash', {'command': target})
        return _run(_config_command(path), {
            'session_id': 's', 'hook_event_name': 'PreToolUse', 'tool_name': tool, 'tool_input': data}, table)
    return call


def codex(table, kind, target):
    command = f'*** Begin Patch\n*** Add File: {target}\n+# x\n*** End Patch' if kind == 'write' else target
    tool = 'apply_patch' if kind == 'write' else 'Bash'
    return _run([sys.executable, str(WORKSPACE_ROOT / 'core/hooks/codex/policy.py')], {
        'session_id': 's', 'cwd': str(WORKSPACE_ROOT), 'hook_event_name': 'PreToolUse',
        'tool_name': tool, 'tool_input': {'command': command}}, table)


def copilot(table, kind, target):
    data = {'filePath': target, 'content': '# x\n'} if kind == 'write' else {'command': target}
    return _run([sys.executable, str(WORKSPACE_ROOT / 'core/hooks/copilot/copilot-pre-tool.py')], {
        'cwd': str(WORKSPACE_ROOT), 'tool_name': 'edit' if kind == 'write' else 'bash',
        'tool_input': data}, table)


def antigravity(table, kind, target):
    call = {'name': 'write_to_file', 'args': {'TargetFile': target, 'CodeContent': '# x\n'}} \
        if kind == 'write' else {'name': 'run_command', 'args': {'CommandLine': target}}
    return _run([sys.executable, str(WORKSPACE_ROOT / 'core/hooks/antigravity/antigravity_policy.py'),
                 'PreToolUse'], {'conversationId': 's', 'toolCall': call}, table)


def opencode(table, kind, target):
    tool, args = ('write', {'filePath': target, 'content': '# x\n'}) if kind == 'write' \
        else ('bash', {'command': target})
    plugin = (WORKSPACE_ROOT / '.opencode/plugins/workspace-policy.js').as_uri()
    return _run(['node', '--input-type=module', '-e', OPENCODE, plugin, json.dumps({'tool': tool}),
                 json.dumps({'args': args})], {}, table, stdin=False)


SHIMS = {'claude': configured('.claude/settings.json'), 'zcode': configured('.zcode/config.json'),
         'codex': codex, 'copilot': copilot, 'antigravity': antigravity, 'opencode': opencode}


@pytest.mark.parametrize('kind, target', [('write', str(WORKSPACE_ROOT / 'outputs/refuser.md')),
                                          ('shell', 'git status')])
@pytest.mark.parametrize('shim', sorted(SHIMS))
def test_the_shim_hands_the_call_to_the_dispatcher(table, shim, kind, target):
    done = SHIMS[shim](table, kind, target)
    assert done.returncode == 2 or '"deny"' in done.stdout or 'REFUSER' in done.stdout + done.stderr, \
        f'{shim} let a {kind} through: {done.returncode} {done.stdout} {done.stderr}'
