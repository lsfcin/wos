# T0 the bash context gate reads the COMMAND, never the text the command carries.
# Zero-token, runs in verify-fast.
#
# Reported by Lucas (INBOX 2026-08-17) and hit twice more while fixing it: a
# `git commit -F - <<'EOF'` whose MESSAGE names a path was read as a command touching that
# subtree, so the gate demanded a CONTEXT.md before letting the commit through. A commit message
# is prose about work already done; the files it describes are staged, not read.
#
# The gate's reason for existing is unaffected and the second case here is what proves it: a
# redirection target is named OUTSIDE the heredoc body, so `cat > notes.md <<EOF` still gates on
# notes.md. Stripping bodies closes a false positive without reopening the cat/grep bypass.
import json
import subprocess

from conftest import WORKSPACE_ROOT
from platform_law import interpreter

GATE = WORKSPACE_ROOT / 'core/hooks/read/bash-context-gate.py'
# A subtree whose CONTEXT.md a fresh session has certainly not read, named inside a message.
DEEP_PATH = 'core/hooks/entropy/dashboard/entropy_report.py'


def _run(command: str, session: str) -> subprocess.CompletedProcess:
    payload = json.dumps({
        'tool_name': 'Bash',
        'tool_input': {'command': command},
        'session_id': session,
        'cwd': str(WORKSPACE_ROOT),
    })
    return subprocess.run([interpreter(), str(GATE)], input=payload,
                          capture_output=True, text=True, check=False, encoding='utf-8')


def test_a_path_named_only_in_a_heredoc_body_does_not_gate():
    command = f"git commit -F - <<'EOF'\nfeat: rewire {DEEP_PATH}\nEOF"
    result = _run(command, 'heredoc-body')
    assert result.returncode == 0, (
        f'a commit message naming {DEEP_PATH} was read as a command touching it:\n'
        f'{result.stderr}')


def test_a_redirection_target_outside_the_body_still_gates():
    """The bypass this gate exists for stays closed — the target is not inside the body."""
    command = f"cat > {DEEP_PATH} <<'EOF'\nunrelated prose\nEOF"
    result = _run(command, 'heredoc-target')
    assert result.returncode == 2, 'a heredoc write to an unread subtree must still gate'
    assert 'CONTEXT' in result.stderr


def test_a_plain_command_still_gates():
    """Guards the guard: if stripping ate the whole command, every case above would pass."""
    result = _run(f'grep -n foo {DEEP_PATH}', 'plain-command')
    assert result.returncode == 2, 'the cat/grep bypass must still be closed'


def test_a_command_after_the_heredoc_is_still_read():
    """Only the body is dropped. Anything after the closing marker is command again."""
    command = f"git commit -F - <<'EOF'\nmessage\nEOF\ngrep -n foo {DEEP_PATH}"
    result = _run(command, 'after-marker')
    assert result.returncode == 2, 'the command following a heredoc was dropped with its body'
