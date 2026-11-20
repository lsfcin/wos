# b20260922 regression — a session outlives a reboot, and its marker store has to outlive one too.
#
# WHAT HAPPENED. A session opened 2026-09-21 was resumed after the machine booted at 00:11 on
# 2026-09-22. Its seen-markers lived in the temp directory, which the boot emptied, so the context
# gate re-demanded three CONTEXT.md files the session still had whole in its window. Nothing was
# broken afterwards and nothing logged it: the only trace was tokens spent re-reading. A gate that
# asks "did this session read it" and is answered by a directory the operating system wiped cannot
# tell a forgotten read from one that never happened.
#
# WHY THE ASSERTION IS ABOUT PLACE AND NOT ABOUT REBOOTS. A test cannot reboot the machine. What it
# can pin is the property that made the reboot matter: session state is asked of one function, and
# that function answers with a directory the workspace owns rather than one the system may empty.
import subprocess

import platform_law
from conftest import WORKSPACE_ROOT

HOOKS = WORKSPACE_ROOT / 'core/hooks'


def test_session_state_lives_in_a_directory_the_workspace_owns():
    """The failure this guards is state the operating system is free to delete under a live session."""
    import tempfile

    marker = platform_law.session_state('claude_ctx_seen_any')
    assert WORKSPACE_ROOT in marker.parents, f'{marker} is outside the workspace'
    system_temp = tempfile.gettempdir()
    assert system_temp not in str(marker), f'{marker} is still under the system temp directory'


def test_asking_for_a_marker_is_enough_to_be_able_to_write_it():
    """The owner of the name creates the directory, or every caller grows its own mkdir.

    Under the temp directory that parent always existed, so no caller needed one. Moving the store
    into the repository removes that guarantee, and a caller that forgets is a PostToolUse hook
    whose exit status nobody reads — the exact shape of silent failure this store already survived
    once.
    """
    marker = platform_law.session_state('claude_ctx_seen_any')
    assert marker.parent.is_dir(), f'{marker.parent} was not created'


def test_per_machine_state_never_reaches_git():
    """State in the repository is only safe while git cannot see it.

    `core/` is an allowlist in .gitignore — everything is ignored and the tracked files are named
    one by one — so this holds without a rule being written for it. The check is here because that
    is a property of another file, and a future edit to the allowlist would break it silently.
    """
    marker = platform_law.session_state('claude_ctx_seen_any')
    done = subprocess.run(['git', 'check-ignore', str(marker)],
                          cwd=WORKSPACE_ROOT, capture_output=True, text=True, encoding='utf-8')
    assert done.returncode == 0, f'{marker} is not ignored by git'


def test_no_hook_builds_session_state_out_of_the_system_temp_directory():
    """One owner of the name, held at zero rather than asserted in prose.

    A branch-marker hook spelled it itself until 2026-09-22 and was wrong in exactly the same way,
    which is what a second spelling always costs: the fix reaches one copy. `mkdtemp` is a different
    thing and stays allowed — a scratch directory for an external tool's output is not session
    state, and nothing reads it after the process ends.
    """
    offenders = []
    for module in sorted(HOOKS.rglob('*.py')):
        if 'gettempdir' in module.read_text(encoding='utf-8'):
            offenders.append(module.relative_to(WORKSPACE_ROOT).as_posix())
    assert not offenders, ('session state is asked of platform_law.session_state, never built from '
                           f'the system temp directory: {offenders}')
