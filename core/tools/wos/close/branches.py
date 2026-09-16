#!/usr/bin/env python3
# Branch promotion at session close: feature → develop → main, and what to say when it did not run.
#
# Imported by core/tools/wos/roundup, which keeps the sequence and the decisions. Same scope as
# core/hooks/git/gitflow_gate.py — the workspace repo and code/* project repos promote; every other
# nested repo just pushes its current branch.
import tempfile

from artifacts import git, out


def gitflow(workspace, repo) -> bool:
    """Which repos promote develop → main: the workspace itself, and the projects under code/.

    The scope this file's head has always declared, in the one place both callers read it — the
    close's own repo and the project sweep beside it. It was a line inside roundup while the sweep
    promoted nothing, which is how nine projects sat 22 commits behind their own develop.
    """
    return repo == workspace or (repo.parent.name == 'code' and repo.parent.parent == workspace)


def promote(root, branch: str, leave_dirty: bool) -> str:
    """'' when every hop landed, else the reason nothing was promoted.

    The whole thing aborts on the first conflict rather than leaving develop ahead of main.
    """
    for target, source in (('develop', branch), ('main', 'develop')):
        if git(root, 'rev-parse', '--verify', '-q', target).returncode != 0 or target == source:
            continue
        behind = out(root, 'rev-list', '--count', f'{target}..origin/{target}')
        if behind.isdigit() and int(behind) > 0:
            return f'{target} is behind origin — a parallel session is mid-flight; not promoted'
        # A fast-forward needs no checkout, so it never touches the working tree. Real merges run
        # in a throwaway worktree so HEAD in the caller's working tree never moves.
        if target != branch:
            if git(root, 'merge-base', '--is-ancestor', target, source).returncode == 0:
                if git(root, 'fetch', '-q', '.', f'{source}:{target}').returncode != 0:
                    return f'fast-forward of {target} failed; not promoted'
            else:
                with tempfile.TemporaryDirectory() as wt:
                    if git(root, 'worktree', 'add', '-q', wt, target).returncode != 0:
                        return f'checkout of {target} failed; not promoted'
                    try:
                        if git(wt, 'merge', '--no-edit', '-q', source).returncode != 0:
                            return f'conflict merging {source} → {target} — aborted, branches untouched'
                    finally:
                        git(root, 'worktree', 'remove', '--force', wt)
        else:
            if git(root, 'merge', '--no-edit', '-q', source).returncode != 0:
                git(root, 'merge', '--abort')
                return f'conflict merging {source} → {target} — aborted, branches untouched'
        if git(root, 'push', '-q', 'origin', target).returncode != 0:
            return f'{target} merged but push failed'
    return ''


def promoted_line(root, branch: str) -> str:
    """What a successful promotion reports: where each branch now points, and what is unpushed."""
    shas = ''
    for name in ('main', 'develop', branch):
        if git(root, 'rev-parse', '--verify', '-q', name).returncode == 0:
            shas += f' {name}@{out(root, "rev-parse", "--short", name)}'
    tracked = out(root, 'for-each-ref', '--format=%(refname:short)%(upstream:track)', 'refs/heads')
    unpushed = sum(1 for line in tracked.splitlines() if 'ahead' in line)
    state = ' all pushed' if unpushed == 0 else f' {unpushed} branch(es) unpushed'
    return f'promoted ·{shas} ·{state}'
