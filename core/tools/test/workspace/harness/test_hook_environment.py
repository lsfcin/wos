# T0 harness invariant: the suite must mean the same thing run by hand and run by a git hook.
# Zero-token, verify-fast.
#
# THE INCIDENT THIS PINS (2026-08-19). A git hook exports GIT_DIR and GIT_INDEX_FILE, and every
# child inherits them. Dozens of tests here build a throwaway repo under tmp_path and run git in
# it; under those variables git ignores the cwd and operates on the WORKSPACE repo instead. Two
# consequences, and the second is the reason this file exists rather than a comment:
#
#   1. 19 tests failed whenever verify:fast ran from pre-commit -- the one moment it acts as a
#      gate -- and passed every time a human re-ran it. The gate was red and said green.
#   2. A fixture's `git add` wrote through to the real index and REPLACED it: 947 tracked files
#      became 1, leaving 946 staged deletions. Nothing was committed and the working tree was
#      untouched, so `git reset` restored it -- but a session that did not look would have
#      committed the wipe.
#
# The fix is in conftest.py, which strips the variables before any test runs. These assert the
# behaviour rather than the strip, because the strip is a means: what must be true is that git,
# inside a fixture, answers about the fixture.
import os
import subprocess
from pathlib import Path  # noqa: F401  -- tmp_path is a Path; kept for the signature below

GIT_VARS = ('GIT_DIR', 'GIT_INDEX_FILE', 'GIT_WORK_TREE', 'GIT_OBJECT_DIRECTORY',
            'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_PREFIX', 'GIT_COMMON_DIR')


def test_no_git_variable_survives_into_the_suite():
    leaked = [v for v in GIT_VARS if v in os.environ]
    assert not leaked, (
        f'{leaked} reached the tests. A hook exported them and conftest.py must strip them, '
        'or every fixture repo silently becomes the workspace repo.'
    )


def test_a_fixture_write_cannot_reach_the_workspace_index(tmp_path: Path):
    """The damaging half: `git add` in a fixture must not touch the workspace's index.

    GIT_INDEX_FILE is the vector, not GIT_DIR. Measured 2026-08-19 against a COPY of the real
    index: a fixture's `git add -A` under an inherited GIT_INDEX_FILE took it from 947 entries
    to 3. A `git rev-parse --show-toplevel` check would NOT have caught this -- a fixture with
    its own .git still reports itself -- which is why this asserts on what got staged.
    """
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    (tmp_path / 'CONTEXT.md').write_text('# fixture\n', encoding='utf-8', newline='\n')
    subprocess.run(['git', 'add', '-A'], cwd=tmp_path, check=True)

    staged = subprocess.run(
        ['git', 'ls-files'], cwd=tmp_path, capture_output=True, text=True, check=True, encoding='utf-8'
    ).stdout.split()
    assert staged == ['CONTEXT.md'], 'the fixture staged something that is not its own'
