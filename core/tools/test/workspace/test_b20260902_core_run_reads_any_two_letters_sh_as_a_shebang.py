# core/run runs what it says it runs: a bash target runs as bash, a python target reaches the
# interpreter, and a python target whose comment merely contains those two letters is still python.
#
# Two bugs, the same launcher failing from either side. B12: it exec'd every target with the venv
# interpreter, so the two bash tools died with `SyntaxError: unmatched ')'`. It gained shebang
# dispatch (ruled 2026-08-31, Lucas: add capabilities, never exceptions). b20260902: that dispatch
# matched `*bash*` and `*sh*` as a SUBSTRING OF THE WHOLE FIRST LINE, so a tool whose opening
# comment contained them inside a word went to `sh`. `gdrive` and `gdocs` both list `share` among
# their subcommands, and every call to either died with `import: not found` — the shell blaming
# Python for a choice core/run made, with nothing in the message naming the launcher.
#
# THE BASH ARM HAS CHANGED SUBJECT TWICE, and the reason is worth keeping: it ran
# `tools/wos/sync-skills --check` until the port took that tool (2026-09-01, and it was 21 s of this
# suite -- the slowest case in it), then `hooks/session/session-prune.sh` until the port took that
# one too (2026-09-02). The capability the launcher owes is unchanged and still has to be held, so
# the arm keeps naming whichever bash target still exists. If a day comes when none does, this arm
# is deleted rather than retargeted -- a dispatch nothing dispatches to is not a capability.
import subprocess

from conftest import WORKSPACE_ROOT


def _run(target, *args):
    return subprocess.run(['bash', str(WORKSPACE_ROOT / 'core/run'), target, *args],
                          cwd=WORKSPACE_ROOT, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=180, encoding='utf-8')


def test_a_bash_target_runs_as_bash():
    out = _run('hooks/session/start-session.sh')
    assert out.returncode == 0, out.stdout + out.stderr
    assert 'SyntaxError' not in out.stderr


def test_a_python_target_still_reaches_the_interpreter():
    out = _run('tools/wos/size')
    assert out.returncode == 0, out.stderr
    assert '.md files' in out.stdout


# THE FIXTURE IS A REAL TOOL, NOT A TEMPORARY FILE. core/run only runs targets under core/, so a
# fixture would have to be written into the real tree and deleted again — the shape
# b20260902-nothing-forbids-a-test-from-dirtying-the-real-tree exists to forbid. `gdrive`'s first
# line is a comment listing `share`, which is the exact string that broke it, and it is permanent.
# ASSERT ON STDERR, NEVER ON THE EXIT CODE: called with no subcommand the tool prints usage and
# exits non-zero on purpose, and that is not the bug.
def test_a_comment_containing_sh_does_not_make_a_python_tool_a_shell_script():
    out = _run('tools/files/gdrive')
    assert 'import: not found' not in out.stderr, out.stderr
    assert 'Syntax error' not in out.stderr, out.stderr
