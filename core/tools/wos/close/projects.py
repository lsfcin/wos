#!/usr/bin/env python3
# Every nested project at session close: push what its remote has not seen, promote what it owes main.
#
# Split out of core/tools/wos/roundup 2026-09-09, at the second recurrence of b20260831. The sweep
# lived in the caller as one function that answered "is there anything to push" with a string that
# was empty both when there was nothing and when the question could not be asked. Six projects held
# 22 unpushed commits each while every close called them quiet, and nine held develop 22 commits
# ahead of main while close/branches.py already said code/* projects promote. Both halves are here
# now, where the difference between an empty answer and a failed question is a returncode.
from pathlib import Path

import branches
from artifacts import git, out


def push(repo, branch: str) -> str:
    """'' when the remote already has this branch, else 'pushed' or 'failed'.

    A branch with no upstream is the case that went blind: `git log @{upstream}..HEAD` FAILS
    there, and the caller read the failure as an empty answer. It gets one, with `-u`, so the
    next close can ask.
    """
    tracked = git(repo, 'rev-parse', '--abbrev-ref', '@{upstream}').returncode == 0
    if tracked and not out(repo, 'log', '--oneline', '@{upstream}..HEAD'):
        return ''
    args = ('push', '-q', 'origin', 'HEAD') if tracked else ('push', '-q', '-u', 'origin', branch)
    return 'pushed' if git(repo, *args).returncode == 0 else 'failed'


def sweep(root: Path) -> str:
    """Push and promote every nested project, and say what happened. Silent about the quiet ones.

    Ruled 2026-09-04 (Lucas). The workspace's list stopped counting these projects, because they
    are IGNORED by its git and a count of them described this disk rather than the repo (b20260902).
    Each project now writes and commits its own list at its own pre-commit; what was missing was
    the push, and a session close is where a person is present to see it. A repo with no remote is
    named, never pushed: that one cannot be fixed from here.
    """
    from entropy_corpus import nested_repos
    from platform_law import posix
    pushed, promoted, stuck, homeless = [], [], [], []
    for repo in sorted(nested_repos(root)):
        name = posix(repo.relative_to(root))
        if not out(repo, 'remote', 'get-url', 'origin'):
            homeless.append(name)
            continue
        git(repo, 'fetch', '--quiet')
        landed = push(repo, out(repo, 'rev-parse', '--abbrev-ref', 'HEAD'))
        if landed:
            (pushed if landed == 'pushed' else stuck).append(name)
        if not branches.gitflow(root, repo):
            continue
        was = out(repo, 'rev-parse', 'main')
        refused = branches.promote(repo, out(repo, 'rev-parse', '--abbrev-ref', 'HEAD'), False)
        if refused:
            stuck.append(f'{name} — {refused}')
        elif out(repo, 'rev-parse', 'main') != was:
            promoted.append(name)
    said = [f'{len(pushed)} pushed' if pushed else '',
            f'{len(promoted)} promoted' if promoted else '',
            f'{len(stuck)} failed: {", ".join(stuck)}' if stuck else '',
            f'{len(homeless)} with no remote: {", ".join(homeless)}' if homeless else '']
    return ' · '.join(part for part in said if part)
