#!/usr/bin/env python3
# Git Flow branch gate: block direct commits to main/master/develop, require feature|release|hotfix.
#
# Scoped to code/ project repos AND the workspace structural repo. Paper repos (academy/papers/*),
# branches/* and any other nested repo are exempt -- the convention is ours, not git's, and applying
# it where it was never agreed would be a gate nobody opted into.
# Convention: AGENTS.md (workspace) / code/SPECS-git.md (projects).
import sys
from pathlib import Path

_HOOKS = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(_HOOKS), str(_HOOKS / 'commit')]
import feature_law  # noqa: E402
from pre_commit import Blocked, git  # noqa: E402

SHARED = ('main', 'master', 'develop')


def check(commit):
    # Switched off: a disabled gate does not block, and does not pretend it ran.
    if not feature_law.is_enabled('gitflow-gate'):
        return
    if not _enforced(commit):
        return

    # A merge in progress leaves MERGE_HEAD. That is a merge, not a hand-typed commit -- the
    # sanctioned gitflow integration step (feature → develop → main) must pass even on a shared
    # branch. Direct commits are still blocked below.
    gitdir = git('rev-parse', '--git-dir', cwd=commit.toplevel)
    if gitdir and (commit.toplevel / gitdir / 'MERGE_HEAD').is_file():
        return

    # `--show-current`, not `rev-parse --abbrev-ref`: on a branch with no commit yet the latter
    # answers nothing, and the gate then refused `feature/check` as a branch named ''. The bash had
    # the same hole -- the first commit into a fresh project repo was blocked by a message naming a
    # branch the operator could see was right. `--show-current` names an unborn branch, and prints
    # nothing on a detached HEAD, which is the case the next line was already written for.
    branch = git('branch', '--show-current', cwd=commit.toplevel)
    if not branch:
        return
    if branch in SHARED:
        raise Blocked(
            f"⛔ Git Flow: direct commits to '{branch}' are not allowed.\n"
            '   Branch first:  git checkout -b feature/<name>   (or release/*, hotfix/*).\n'
            '   See code/SPECS-git.md. (Emergency bypass: git commit --no-verify —\n'
            '   state the reason in the commit message and file a TODO to pay it back.)')
    # HEAD = detached, which is a rebase or a bisect. Not a branch anyone chose; not blocked.
    if branch == 'HEAD' or branch.startswith(('feature/', 'release/', 'hotfix/')):
        return
    raise Blocked(
        f"⛔ Git Flow: branch '{branch}' doesn't match feature/*, release/*, or hotfix/*.\n"
        '   Rename:  git branch -m feature/<name>. See code/SPECS-git.md.')


def _enforced(commit) -> bool:
    """Whether this repo is one the convention covers -- the workspace, or a project under code/."""
    if commit.is_workspace:
        return True
    try:
        return commit.toplevel.relative_to(commit.root).parts[:1] == ('code',)
    except ValueError:
        return False
