# b20260901 regression — the gates fire on a capability, not on a tool's name.
#
# On Windows the harness exposes a PowerShell tool beside Bash. `Get-Content` on a source file with
# a current stub was NOT blocked, while `sed` on the same file through Bash was:
# .claude/settings.json matched `Bash` for the command gate and `Read|Edit|Write|Grep|NotebookEdit`
# for the interface gate, and that tool is neither. So the enforcement layer — this workspace's
# whole premise — was weaker on one operating system, silently, in the direction where nothing
# reports it. Same shape as the bare `python3` finding: a gate that reads as installed, never fires.
#
# Ruled 2026-09-04 (Lucas): match every tool and decide in the gate. A call carrying a command line
# runs one; a call carrying a path plus new content writes it; a call carrying only a path reads it.
# The cases below are written with tool names this workspace has never seen on purpose — a gate that
# passes them passes the next harness's tool too, which is the property the old matchers lacked.
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import WORKSPACE_ROOT
from hook_input import capability
from platform_law import interpreter

SETTINGS = WORKSPACE_ROOT / '.claude/settings.json'


def _run(gate: str, tool: str, tool_input: dict) -> subprocess.CompletedProcess:
	payload = json.dumps({'tool_name': tool, 'cwd': str(WORKSPACE_ROOT), 'tool_input': tool_input})
	return subprocess.run([interpreter(), str(WORKSPACE_ROOT / 'core/hooks' / gate)],
	                      input=payload, capture_output=True, text=True, encoding='utf-8')


@pytest.mark.parametrize('tool,tool_input,expected', [
	('PowerShell', {'command': 'Get-Content core/hooks/file_law.py'}, 'shell'),
	('SomeFutureShell', {'command': 'ls'}, 'shell'),
	('Bash', {'command': 'ls'}, 'shell'),
	('ViewFile', {'file_path': '/x/y.py'}, 'read'),
	('Read', {'file_path': '/x/y.py'}, 'read'),
	('Grep', {'path': '/x', 'pattern': 'z'}, 'read'),
	('PatchFile', {'file_path': '/x/y.py', 'new_string': 'a', 'old_string': 'b'}, 'write'),
	('CreateFile', {'file_path': '/x/y.py', 'content': 'a'}, 'write'),
	('Edit', {'file_path': '/x/y.py', 'old_string': 'a', 'new_string': 'b'}, 'write'),
	('WebFetch', {'url': 'https://example.com'}, 'other'),
	('Bash', {'command': '   '}, 'other'),
])
def test_the_capability_is_read_from_the_payload(tool, tool_input, expected):
	"""Names this workspace has never met, answered correctly — that is the whole point."""
	assert capability(tool, tool_input) == expected


def test_a_second_shell_is_gated_like_the_first():
	"""The incident itself: another tool with a command line must meet the command gate."""
	done = _run('read/bash-context-gate.py', 'PowerShell',
	            {'command': 'Get-Content core/hooks/entropy/entropy_size.py'})
	assert done.returncode == 2, done.stdout
	assert 'CONTEXT GATE' in done.stderr


def test_a_read_shaped_call_does_not_reach_the_command_gate():
	"""The mirror half. A gate that fires on everything is a gate that gets switched off."""
	done = _run('read/bash-context-gate.py', 'ViewFile', {'file_path': 'README.md'})
	assert done.returncode == 0 and not done.stderr.strip()


def test_no_access_gate_is_filtered_by_a_tool_name():
	"""A whitelist of names is what went stale, so none may come back for the gates about ACCESS —
	who may read, write or run. `agent-context.py` is exempt and is the only one: it fires on a
	worker being SPAWNED, which is not a capability any file payload carries, and it induces
	rather than blocks, so a harness whose spawn tool it misses loses a briefing, not a gate."""
	hooks = json.loads(SETTINGS.read_text(encoding='utf-8'))['hooks']
	named = [(group.get('matcher', '.*'), hook['command'].rsplit('/', 1)[-1])
	         for event in ('PreToolUse', 'PostToolUse') for group in hooks.get(event, [])
	         for hook in group['hooks'] if group.get('matcher', '.*') != '.*']
	assert [entry for entry in named if entry[1] != 'agent-context.py'] == [], named


if __name__ == '__main__':
	sys.exit(0)
