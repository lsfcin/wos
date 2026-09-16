# T0 the heredoc gate: a shell write to a workspace file must not walk past the file gates.
#
# The write gates and the other file checks are `PreToolUse: Edit|Write`, so `cat > f << 'EOF'` met
# none of them — 128 such calls in this workspace's transcripts, among them brain/INBOX.md and
# HISTORY.md, both written past the size gate and the first-line-comment check.
#
# The silence cases matter more than the firing ones. Stdin-to-an-interpreter is 44% of heredoc
# volume here and is throwaway analysis; a gate that fires on all of those is a gate that gets
# switched off, and it would fire on every cost-measurement script in core/tools/wos/session/.
# Such a body CAN write — that half is b20260904, and its spec sits beside this file.
import json
import subprocess

import pytest

from conftest import WORKSPACE_ROOT
from platform_law import interpreter, posix

GATE = WORKSPACE_ROOT / 'core/hooks/checks/heredoc-gate.py'
# The cases below need this clone's root spelled INSIDE a shell command, which is the boundary's
# `posix` case exactly. They were an absolute path on one machine, so on any other clone the gate
# correctly found no workspace file and the test read as a gate that had stopped firing.
WS = posix(WORKSPACE_ROOT)


def run(command: str, tool: str = 'Bash', tool_input: dict | None = None) -> str:
	"""The context the gate would inject, or '' when it stays silent."""
	payload = json.dumps({'tool_name': tool, 'cwd': str(WORKSPACE_ROOT),
	                      'tool_input': {'command': command} if tool_input is None else tool_input})
	done = subprocess.run([interpreter(), str(GATE)], input=payload,
	                      capture_output=True, text=True, encoding='utf-8')
	assert done.returncode == 0, f'the gate must never block: {done.stderr}'
	if not done.stdout.strip():
		return ''
	return json.loads(done.stdout)['hookSpecificOutput']['additionalContext']


@pytest.mark.parametrize('command', [
	f"cat > {WS}/brain/INBOX.md << 'EOF'\nx\nEOF",
	f"cat >> {WS}/HISTORY.md <<'EOF'\nx\nEOF",
	f"tee {WS}/notes.md <<'EOF'\nx\nEOF",
	f"tee -a {WS}/notes.md <<'EOF'\nx\nEOF",
	"cat > notes.md <<'EOF'\nx\nEOF",
])
def test_a_heredoc_that_writes_a_workspace_file_is_named(command):
	"""Both spellings and both append forms, absolute and relative to cwd."""
	assert 'UNGATED WRITE' in run(command)


@pytest.mark.parametrize('command', [
	"python3 - <<'EOF'\nprint(1)\nEOF",
	"python3 - 2>/dev/null <<'EOF'\nprint(1)\nEOF",
	"bash <<'EOF'\nls\nEOF",
	"cat <<'EOF'\njust printing\nEOF",
	f"grep x <<< '{WS}/a.md'",
	'echo hi',
	f'cat {WS}/README.md',
])
def test_analysis_and_ordinary_shell_stay_silent(command):
	"""Nothing here writes a workspace file, and a false fire is what kills a warn-only gate."""
	assert run(command) == ''


def test_a_write_outside_the_workspace_is_not_this_gate_s_business():
	"""Scratch files are the reason /tmp exists; gating them would be noise with no rule behind it."""
	assert run("cat > /tmp/scratch.md <<'EOF'\nx\nEOF") == ''


def test_a_redirect_inside_the_heredoc_body_is_text_not_shell():
	"""The body is data. Parsing it would fire on any script that merely mentions a path."""
	assert run(f"python3 - <<'EOF'\nopen('> {WS}/z.md', 'w')\nEOF") == ''


def test_the_message_names_one_action():
	"""AGENTS.md: agent-facing text names one flow. Two suggestions is a decision to improvise on."""
	message = run(f"cat > {WS}/x.md <<'EOF'\nx\nEOF")
	assert 'Write tool' in message
	assert message.count('Use ') == 1


def test_a_call_that_runs_no_command_is_not_touched():
	"""Registered on every tool since 2026-09-04, so what it declines is a payload shape rather
	than a name: a write carries a path and content, and Edit and Write have their own gates.

	The name is deliberately not the filter. `Write` carrying a `command` used to be the case
	here, and it is a payload no harness sends — while `PowerShell` carrying one is exactly what
	the old name matcher let through (b20260901-a-second-shell-tool-walks-past-every-read-gate)."""
	assert run('', tool='Write', tool_input={'file_path': f'{WS}/x.md', 'content': 'x'}) == ''
