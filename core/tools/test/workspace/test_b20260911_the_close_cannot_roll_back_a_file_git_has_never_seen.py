# b20260911 regression — settle() undoes a CREATE by deleting, not by checking out.
#
# `git checkout -- <name>` needs a committed version to restore. A generated artifact landing in a
# repo that never carried it has none, so under --leave-dirty the rollback failed silently and the
# artifact stayed in the other session's tree — the one outcome settle() exists to make impossible.
# It was found 2026-09-09 by the map generator, the first caller that could reach it; that generator
# now refuses to invent the file, which sidesteps the bug without fixing it.
#
# The same branch fixes the commit side: `git diff --quiet` says "no change" about an untracked
# file too, so a brand-new artifact was never committed either.
import subprocess
import sys

from conftest import WORKSPACE_ROOT

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools/wos/close'))
import artifacts  # noqa: E402


def _repo(tmp_path):
    """A real git repo with one commit, because settle() speaks to git and nothing else.

    `core.hooksPath` is pointed at an empty directory rather than passing `--no-verify`: settle()
    runs the commit itself and takes no such flag, and this workspace's own gates have no business
    judging a two-line fixture. The `--no-verify` protocol is about THIS repo's commits.
    """
    empty = tmp_path.parent / (tmp_path.name + '-nohooks')
    empty.mkdir(exist_ok=True)
    subprocess.run(['git', 'init', '-q', '-b', 'main', str(tmp_path)], check=True)
    for key, value in (('user.email', 'test@example.com'), ('user.name', 'test'),
                       ('core.hooksPath', str(empty))):
        subprocess.run(['git', '-C', str(tmp_path), 'config', key, value], check=True)
    (tmp_path / 'seed.txt').write_text('seed\n', encoding='utf-8', newline='\n')
    subprocess.run(['git', '-C', str(tmp_path), 'add', 'seed.txt'], check=True)
    subprocess.run(['git', '-C', str(tmp_path), 'commit', '-qm', 'seed'], check=True)
    return tmp_path


def test_an_untracked_artifact_is_removed_rather_than_checked_out(tmp_path):
    """The incident itself: under --leave-dirty a created artifact must not survive the close."""
    repo = _repo(tmp_path)
    made = repo / 'PROJECTS.md'
    made.write_text('# Projects\n', encoding='utf-8', newline='\n')

    note = artifacts.settle(repo, 'PROJECTS.md', was_clean=True, message='irrelevant here',
                            leave_dirty=True)

    assert not made.exists(), "the artifact rode into the other session's tree"
    assert 'reported only' in note


def test_an_untracked_artifact_is_committed_when_the_tree_is_ours(tmp_path):
    """The other half of the same branch. `git diff --quiet` answers "unchanged" for a file git has
    never seen, so the early return swallowed every first-ever artifact before it was committed."""
    repo = _repo(tmp_path)
    (repo / 'PROJECTS.md').write_text('# Projects\n', encoding='utf-8', newline='\n')

    note = artifacts.settle(repo, 'PROJECTS.md', was_clean=True, message='chore: first map',
                            leave_dirty=False)

    assert note == '', f'settle reported a problem: {note}'
    assert artifacts.out(repo, 'log', '-1', '--pretty=%s') == 'chore: first map'
    assert artifacts.git(repo, 'ls-files', '--error-unmatch', 'PROJECTS.md').returncode == 0


def test_a_tracked_artifact_that_did_not_move_is_still_silent(tmp_path):
    """The common case, and the property the new branch must not cost: deterministic output means a
    file changes when the WORKSPACE changed, never merely because a generator ran."""
    repo = _repo(tmp_path)
    assert artifacts.settle(repo, 'seed.txt', was_clean=True, message='unused',
                            leave_dirty=False) == ''


def test_a_tracked_artifact_is_still_restored_and_not_deleted(tmp_path):
    """The path that already worked. Undoing an EDIT is a checkout; only a create is a delete."""
    repo = _repo(tmp_path)
    (repo / 'seed.txt').write_text('dirtied by a generator\n', encoding='utf-8', newline='\n')

    artifacts.settle(repo, 'seed.txt', was_clean=True, message='unused', leave_dirty=True)

    assert (repo / 'seed.txt').read_text(encoding='utf-8') == 'seed\n'
