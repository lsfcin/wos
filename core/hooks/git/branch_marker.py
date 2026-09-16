#!/usr/bin/env python3
# Branch drift warning: HEAD is shared mutable state between parallel sessions, and nothing said so.
#
# `record` stores the branch a session started on; `check` warns at commit time when HEAD has moved
# since. Three properties carry the design, and each is load-bearing:
#   WARN, NEVER BLOCK -- a deliberate mid-session switch is legitimate and common.
#   ONCE PER DIVERGENCE -- a warning that repeats after being understood is one people learn to skip.
#   ONE MARKER PER REPO, not per session -- `record` runs at SessionStart, where only the repo is
#     known, and `check` runs inside a git hook, which has no session id to pair with. A repo with
#     no marker is silent, so nested repos and non-agent commits are unaffected.
#
# Decided 2026-08-14 (Lucas) over one-worktree-per-session, which fights the branch sweep in
# core/skills/roundup.md Phase 5 -- a checked-out worktree makes `git branch -d` refuse.
import re
import sys
import tempfile
from pathlib import Path

_HOOKS = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(_HOOKS), str(_HOOKS / 'commit')]
from pre_commit import git  # noqa: E402


def marker_for(repo) -> Path:
    """The marker file for one repo. The ONE place this path is spelled.

    Asked of tempfile rather than spelled `/tmp`, which is not a directory Windows has -- the
    marker was written to a path that could not exist, so the warning could never fire there.
    A test that restates this path instead of calling this function is testing its own copy.
    """
    name = re.sub(r'[^A-Za-z0-9]', '_', str(repo))
    return Path(tempfile.gettempdir()) / f'claude_branch_{name}.txt'


def _current(repo) -> tuple:
    """(marker, branch) for `repo`, or (None, None) when there is nothing to compare.

    `--show-current`, not rev-parse: it names a branch that has no commit yet, and it prints
    nothing on a detached HEAD -- a rebase or a bisect, where a branch warning is noise.
    """
    top = git('rev-parse', '--show-toplevel', cwd=repo)
    if not top:
        return None, None
    branch = git('branch', '--show-current', cwd=repo)
    return (marker_for(top), branch) if branch else (None, None)


def record(repo=None):
    """Store the branch this session started on."""
    marker, branch = _current(repo)
    if marker:
        marker.write_text(f'{branch}\n', encoding='utf-8', newline='\n')


def check(commit):
    """Warn when HEAD has moved under this session. Never raises -- warn, never block."""
    marker, branch = _current(commit.toplevel)
    if not marker or not marker.is_file():
        return
    started = marker.read_text(encoding='utf-8', errors='replace').strip()
    if not started or started == branch:
        return
    print(f"[Git] ⚠ HEAD moved since this session started: '{started}' → '{branch}'.")
    print('   A parallel session may have switched the shared checkout, and this commit is')
    print('   about to land on their branch. If it should be yours:')
    print(f'   git merge-base --is-ancestor {started} HEAD  &&  git branch -f {started} HEAD')
    print('   Never reset or force-push theirs. See core/hooks/SPECS.md § Branch drift.')
    marker.write_text(f'{branch}\n', encoding='utf-8', newline='\n')


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    if mode == 'record':
        record()
        return 0
    if mode == 'check':
        from pre_commit import collect
        check(collect())
        return 0
    print('usage: branch_marker.py record|check', file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
