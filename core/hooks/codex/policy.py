# Codex lifecycle adapter: translate tool payloads and reuse the canonical WOS dispatcher.
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent), str(HERE.parent / 'read')]
import dispatch
import hook_input
from chain import EXEMPT_NAMES
from patch import changes


def shell_commands(command: str) -> list[list[str]]:
    """Observe explicit cat/head/tail/sed reads, never searches, redirects or interpreter bodies."""
    if '&' in command.replace('&&', ''):
        return []
    if any(token in command for token in ('>', '<', '$(', '`', ';', '|')):
        return []
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|')
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return []
    segments, segment = [], []
    for token in tokens + [';']:
        if token in (';', '&&', '||', '|'):
            segments.append(segment)
            segment = []
        else:
            segment.append(token)
    return segments


def read_command(parts: list[str]) -> list[str]:
    if parts[:2] == ['rtk', 'read']:
        parts = ['cat', *parts[2:]]
    elif parts[:2] == ['rtk', 'proxy']:
        parts = parts[2:]
    if not parts or Path(parts[0]).name not in ('cat', 'head', 'tail', 'sed'):
        return []
    if Path(parts[0]).name == 'sed' and any(p.startswith('-i') for p in parts[1:]):
        return []
    return parts


def shell_reads(command: str, cwd: str) -> list[dict]:
    result = []
    for parts in shell_commands(command):
        parts = read_command(parts)
        if not parts:
            continue
        for token in parts[1:]:
            path = (Path(cwd) / token).resolve()
            if token.startswith('-') or not path.is_file():
                continue
            item = {'file_path': str(path)}
            if item not in result:
                result.append(item)
    return result


def succeeded(raw: dict) -> bool:
    """Accept an exit status, or prove a stdout-only native cat returned the whole file."""
    response = raw.get('tool_response')
    if isinstance(response, dict):
        if response.get('isError') or response.get('error'):
            return False
        return response.get('exit_code', response.get('exitCode')) == 0
    if not isinstance(response, str):
        return False
    status = re.search(r'^Process exited with code (\d+)(?:\s|$)', response, re.MULTILINE)
    if status:
        return status.group(1) == '0'
    data = raw.get('tool_input') or {}
    commands = shell_commands(str(data.get('command') or data.get('cmd') or ''))
    expected = []
    try:
        for parts in commands:
            parts = read_command(parts)
            if not parts or Path(parts[0]).name != 'cat' or len(parts) < 2:
                return False
            for token in parts[1:]:
                if token.startswith('-'):
                    return False
                expected.append((Path(raw.get('cwd') or os.getcwd()) / token).read_text(encoding='utf-8'))
    except (OSError, UnicodeError):
        return False
    return bool(expected) and response == ''.join(expected)


def invoke(raw: dict, rel: str, messages: list[str]) -> int:
    os.environ['CLAUDE_TOOL_INPUT'] = json.dumps(raw)
    os.environ['CLAUDE_TOOL_NAME'] = str(raw.get('tool_name', ''))
    code, out, err = dispatch.run_gate(rel)
    sys.stderr.write(err)
    if code == 0:
        dispatch.collect(out, messages)
    return code


def translated(raw: dict, tool: str, data: dict) -> dict:
    return {**raw, 'tool_name': tool, 'tool_input': data}


def main() -> int:
    raw = json.load(sys.stdin)
    if not isinstance(raw, dict) or not raw.get('session_id'):
        print('WOS: Codex hook requires a session-stable session_id', file=sys.stderr)
        return 1
    event = raw.get('hook_event_name', 'PreToolUse')
    cwd = str(raw.get('cwd') or os.getcwd())
    tool = str(raw.get('tool_name', ''))
    data = raw.get('tool_input') or {}
    messages, notices, failed = [], [], False
    lifecycle = {
        'SessionStart': ['session/session-prune.py', 'session/mirror-heal.py', 'session/reminders.py'],
        'PreCompact': ['session/precompact-wipe.py'],
        'SubagentStart': ['read/agent-context.py'],
        'UserPromptSubmit': ['session/context-meter.py', 'session/downloads.py'],
    }
    if event in lifecycle:
        for rel in lifecycle[event]:
            failed |= invoke(raw, rel, messages) != 0
        dispatch.emit(messages, event)
        return int(failed)
    if event not in ('PreToolUse', 'PostToolUse') or not isinstance(data, dict):
        return 0
    post = event == 'PostToolUse'
    cwd = str((Path(cwd) / (data.get('workdir') or '.')).resolve())
    raw['cwd'] = cwd
    response = raw.get('tool_response')
    if post and isinstance(response, dict) and (response.get('isError') or response.get('error')
                                               or response.get('exit_code') not in (None, 0)):
        return 0
    command = str(data.get('command') or data.get('cmd') or '')
    if post and command and tool != 'apply_patch' and not succeeded(raw):
        return 0
    if tool == 'apply_patch' or command.lstrip().startswith('*** Begin Patch'):
        try:
            items = [(tool, item) for item in changes(command, cwd, after=post)]
        except (ValueError, OSError) as error:
            print(f'WOS PATCH: {error}', file=sys.stderr)
            return 1 if post else 2
    elif command:
        reads = shell_reads(command, cwd)
        items = [('Read', item) for item in reads]
        # Context documents are freely readable. Shell context enforcement must not deadlock them.
        context_only = reads and all(Path(item['file_path']).name in EXEMPT_NAMES for item in reads)
        context_only = context_only and all(read_command(parts) for parts in shell_commands(command))
        if not context_only:
            items.append(('Bash', {**data, 'command': command}))
    else:
        data = dict(data)
        path = data.get('file_path') or data.get('path')
        if path:
            data['file_path'] = str((Path(cwd) / path).resolve())
        items = [(tool, data)]
    if not post and tool in ('Agent', 'spawn_agent'):
        briefing = translated(raw, 'Agent', {**data, 'prompt': data.get('prompt') or data.get('message', '')})
        failed |= invoke(briefing, 'read/agent-context.py', messages) != 0
    for name, item in items:
        payload = translated(raw, name, item)
        code = invoke(payload, 'dispatch.py', messages)
        if code == 2:
            return 2
        failed |= code != 0
        if post and hook_input.capability(name, item) == 'write' and Path(item.get('file_path', '')).is_file():
            done = subprocess.run(['bash', str(HERE.parent / 'post-edit.sh')],
                                  input=json.dumps(payload), capture_output=True, text=True, encoding='utf-8')
            sys.stderr.write(done.stderr)
            # Generator progress is for Lucas; only explicit agent guidance enters context.
            try:
                json.loads(done.stdout)
            except ValueError:
                if done.stdout.strip():
                    notices.append(done.stdout.strip())
            else:
                dispatch.collect(done.stdout, messages)
            failed |= done.returncode != 0
    if not post and command and not command.lstrip().startswith('*** Begin Patch'):
        payload = translated(raw, 'Bash', {**data, 'command': command})
        os.environ['CLAUDE_TOOL_INPUT'] = json.dumps(payload)
        code, out, err = dispatch.run_gate('compact/bash-compact-rewrite.py')
        sys.stderr.write(err)
        if out.strip():
            rewrite = json.loads(out).get('hookSpecificOutput', {}).get('updatedInput')
            if rewrite:
                result = {'hookEventName': event, 'permissionDecision': 'allow',
                          'updatedInput': {**data, 'command': rewrite['command']}}
                if messages:
                    result['additionalContext'] = '\n'.join(dict.fromkeys(messages))
                print(json.dumps({'hookSpecificOutput': result}))
                return int(failed or code != 0)
    result = {}
    if messages:
        result['hookSpecificOutput'] = {'hookEventName': event,
                                        'additionalContext': '\n'.join(dict.fromkeys(messages))}
    if notices:
        result['systemMessage'] = '\n'.join(dict.fromkeys(notices))
    if result:
        print(json.dumps(result))
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
