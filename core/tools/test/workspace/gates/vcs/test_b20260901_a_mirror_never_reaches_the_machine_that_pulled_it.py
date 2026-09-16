# b20260901-a-mirror-never-reaches-the-machine-that-pulled-it regression.
#
# The ruling that let the skill mirrors leave git (core/hooks/postedit/sync.sh) allows untracked
# generated content PROVIDED regeneration is automatic, and enumerates where: install, edit, create,
# and delete one commit behind. Every one belongs to the machine that AUTHORS. None belongs to the
# machine that RECEIVES, so the Windows clone arrived with no skill mirrors at all -- no /inbox,
# /compass, /roundup, /craft or /install -- every source present, every check that could run silent.
#
# These hold the SessionStart heal that closes it, and the property that separates a heal from a
# nag: it is silent unless it acted.
import os
import subprocess
import sys

import pytest

from conftest import WORKSPACE_ROOT

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools/wos/skills'))
import mirror  # noqa: E402

HOOK = 'hooks/session/mirror-heal.py'
SOURCES = WORKSPACE_ROOT / 'core' / 'skills'
COMMANDS = WORKSPACE_ROOT / '.claude' / 'commands'


def _run(target, *args):
    return subprocess.run(['sh', str(WORKSPACE_ROOT / 'core/run'), target, *args],
                          cwd=WORKSPACE_ROOT, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=180, encoding='utf-8', errors='replace')


def _in_sync() -> bool:
    return _run('tools/wos/sync-skills', '--check').returncode == 0


def test_the_hook_is_silent_when_nothing_changed():
    """The property that separates a heal from a nag. A SessionStart hook that speaks every session
    spends context every session, and this one has nothing to say on almost all of them."""
    assert _in_sync(), 'precondition: the working tree must start in sync'
    out = _run(HOOK)
    assert out.returncode == 0
    assert out.stdout == '', f'the hook spoke with nothing to report: {out.stdout!r}'


@pytest.mark.serial
def test_a_mirror_dirtied_by_a_merge_is_healed_in_one_line():
    """What a `git pull` does: the SOURCE arrives changed and the copies do not follow. Nothing on
    the receiving machine regenerates them, which is the whole bug.

    SERIAL, because there is no boundary to seed the drift anywhere but the real tree: mirror-heal.py
    and sync-skills both work on WORKSPACE_ROOT with nothing to point elsewhere. Restoring in a
    `finally` closes the window afterwards and not during, and a parallel worker inside it reads a
    workspace that is genuinely out of sync — which is a true answer to the wrong question.
    """
    assert _in_sync(), 'precondition: the working tree must start in sync'
    source = SOURCES / 'compass.md'
    original = source.read_bytes()
    try:
        with open(source, 'a', encoding='utf-8', newline='') as handle:
            handle.write('\n<!-- arrived by merge -->\n')
        assert not _in_sync(), 'the seeded drift did not register'

        out = _run(HOOK)
        assert out.returncode == 0
        assert _in_sync(), 'the hook ran and the mirrors still disagree'
        # The line it cares about, never the line COUNT. Asserting the count made this case fail
        # on output that was entirely correct: the heal line plus a true permissions-drift warning
        # from the same hook. A gate may grow a second thing to say without a mirror test going red.
        spoke = [line for line in out.stdout.splitlines() if 'skill mirrors regenerated' in line]
        assert len(spoke) == 1, f'expected one heal line, got {out.stdout!r}'
    finally:
        source.write_bytes(original)
        _run('tools/wos/sync-skills')


def test_the_hook_never_blocks():
    """It runs before the session exists. core/hooks/SPECS.md: a reporting hook that dies inside
    its own message hands the caller a traceback where a verdict belonged."""
    out = _run(HOOK)
    assert out.returncode == 0
    assert 'Traceback' not in out.stderr


def test_permissions_are_reported_and_never_written():
    """A mirror is a derived copy, so rewriting one can lose nothing. A permission LEVEL is a
    choice, and one arriving over the network must not apply itself. Same drift, opposite answer.
    """
    rendered = WORKSPACE_ROOT / '.claude' / 'settings.local.json'
    before = rendered.read_bytes() if rendered.is_file() else None
    _run(HOOK)
    after = rendered.read_bytes() if rendered.is_file() else None
    assert before == after, 'the hook wrote a permission config; it may only report one'


def test_a_command_link_is_rebased_with_posix_separators():
    """os.path.relpath returns the OS-native separator, so on a Windows clone render_command
    published a backslash link -- 16 dead ones across 5 command files, the SAME failure that
    function exists to fix, reintroduced by the platform underneath it."""
    dead = [path.name for path in sorted(COMMANDS.glob('*.md'))
            if any('\\' in chunk.split(')')[0]
                   for chunk in path.read_text(encoding='utf-8').split('](')[1:])]
    assert not dead, f'command files carry a backslash in a link target: {dead}'


def test_the_switch_still_reaches_the_mirror():
    """AD-14: the skills group's one wiring point. Asked through the module core/features.txt now
    names, so the fourteen rows stay honest after the port moved it from mirror.sh to mirror.py."""
    previous = os.environ.get('WOS_FEATURES_OFF')
    os.environ['WOS_FEATURES_OFF'] = 'compass'
    try:
        assert 'compass' not in mirror.list_skills(SOURCES)
    finally:
        if previous is None:
            del os.environ['WOS_FEATURES_OFF']
        else:
            os.environ['WOS_FEATURES_OFF'] = previous
    assert 'compass' in mirror.list_skills(SOURCES)
