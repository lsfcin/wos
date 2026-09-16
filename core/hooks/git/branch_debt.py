#!/usr/bin/env python3
# What the entropy dashboard counts about branches: work that lives in only one place, and labels
# whose commits already landed.
#
# It sits in git/ rather than beside the other entropy checks because it is the one that reads
# git state instead of file content — every module in entropy/ takes a list of files, this one
# takes a root and shells out. That difference is also what put entropy/ over the crowding cap
# when it briefly lived there, which is the check doing its job.
#
# Warn-only, like every other dashboard section. Widened 2026-08-31 after a hand audit found what
# the first version could not see: 117 merged local branches, three holding unpromoted work that
# simply was not checked out, 16 repos ahead of their remote and two with no remote at all.
# code/SPECS-git.md had stated "unpushed work is invisible work" since July and nothing measured
# it — a law nobody counts is a sentence.
import subprocess
from pathlib import Path

# nested_repos is deliberately NOT imported: these four signals answer for one repo (see `repos`).
from platform_law import rel

# In base order. `master` is not legacy noise here: branches/instituto is on it, and a repo whose
# base is master has the same question asked of it as one on main.
BASES = ('main', 'master', 'develop')


def _git(repo: Path, *args) -> str:
    done = subprocess.run(['git', '-C', str(repo), *args],
                          capture_output=True, text=True, encoding='utf-8')
    return done.stdout.strip() if done.returncode == 0 else ''


def _rel(repo: Path, root: Path) -> str:
    return '.' if repo == root else rel(repo, root)


def _base_of(repo: Path) -> str:
    """The branch this repo promotes into, or '' when it has none to compare against."""
    for base in BASES:
        if _git(repo, 'rev-parse', '--verify', '--quiet', f'refs/heads/{base}'):
            return base
    return ''


def _locals(repo: Path) -> list:
    return [b for b in _git(repo, 'branch', '--format=%(refname:short)').splitlines() if b]


def _merged(repo: Path, base: str, branch: str) -> bool:
    return _git(repo, 'rev-list', '--count', f'{base}..{branch}') == '0'


def _deletable(repo: Path, base: str) -> list:
    """The branches `git branch -d` would really delete, by git's own rule rather than a guess.

    Merged into base, not checked out in any worktree, and — when it tracks a remote — already
    contained in that remote. Guessing instead cost three of the first run's lines: one branch was
    live in a parallel session's worktree and two sat ahead of their own upstream, so the emitted
    command was one git refused. A report that names an action has to name one that runs.
    """
    fmt = '%(refname:short)\t%(worktreepath)\t%(upstream:short)'
    out = []
    for line in _git(repo, 'branch', f'--format={fmt}').splitlines():
        name, worktree, upstream = (line.split('\t') + ['', ''])[:3]
        if not name or name in BASES or worktree:
            continue
        if not _merged(repo, base, name):
            continue
        if upstream and not _merged(repo, upstream, name):
            continue
        out.append(name)
    return out


def repos(root: Path) -> list:
    """The repos these four signals answer for: exactly the one asked about.

    It was `[root] + nested_repos(root)` until 2026-09-04, so the workspace's own list carried
    the branch debt of 27 projects its git ignores — a count that described THIS DISK, red on the
    clone that has none of them (b20260902). Each project now answers for itself, in its own
    ISSUES.md, and the cross-repo sweep that PUSHES them lives in `core/tools/wos/roundup`, where
    a session close can act on it. Named rather than inlined: four callers, one rule.
    """
    return [root]


def unmerged_branches(root: Path, promoting: str = '') -> list:
    """One line per local branch holding commits its base does not have.

    Every local branch, not only the checked-out one: the branch nobody switched back to is
    exactly the one that holds forgotten work, so asking about HEAD alone asked about the safest
    branch in the repo. A repo with no base at all is the finding itself — it has nowhere to
    promote to, which is how a repo on a lone feature branch reported clean.

    `promoting` NAMES THE BRANCH THIS CLOSE IS ABOUT TO MERGE, and excuses it. Without it every
    close published a finding against its own branch: `roundup` regenerates this block BEFORE it
    promotes, so the branch was ahead when the check ran and level seconds later — true when
    written, false when read. Reordering cures nothing, because the artifact is written on the
    feature branch in order to ride into develop, and after promotion the Git Flow gate leaves no
    branch to carry it. The cost is that a reader who discounts this section discounts every other
    finding in it.

    Only `roundup` can answer: it holds the verify verdict, `--no-promote` and the gitflow scope
    before it regenerates, so it names a branch only when a merge will be attempted. A REFUSED
    merge then under-reports for one cycle — the better failure, since refusal makes `roundup` exit
    non-zero and say so, where a false finding every close is silent by design.
    """
    signals = []
    for repo in repos(root):
        name = _rel(repo, root)
        base = _base_of(repo)
        if not base:
            signals.append(f'{name} — no main/master/develop to promote into')
            continue
        for branch in _locals(repo):
            # Only for the repo the close is actually promoting in: `promoting` is one branch name
            # in one repo, and `repos()` answers for exactly that repo today. Guarding on `base`
            # too keeps a branch NAMED main from excusing itself.
            if branch in BASES or (promoting and branch == promoting):
                continue
            ahead = _git(repo, 'rev-list', '--count', f'{base}..{branch}')
            if ahead.isdigit() and int(ahead) > 0:
                signals.append(f'{name} — {branch} is {ahead} ahead of {base}')
    return signals


def merged_local_branches(root: Path) -> list:
    """Local labels whose every commit is already in the base branch.

    The remote twin below has been counted since July; the local side never was, and by the time
    anything looked there were a hundred and fifteen. Deleting one is safe and purely local —
    `git branch -d` refuses exactly the branches this check does not list — so the line is the
    command, the same way its twin is.
    """
    signals = []
    for repo in repos(root):
        base = _base_of(repo)
        if not base:
            continue
        stale = _deletable(repo, base)
        if stale:
            name = _rel(repo, root)
            signals.append(f'{name} — {len(stale)} merged into {base}: '
                           f'git -C {name} branch -d {" ".join(stale)}')
    return signals


def unpushed_work(root: Path) -> list:
    """Commits that exist on this disk and nowhere else.

    Two machines share this workspace, so code/SPECS-git.md rules that unpushed work is invisible
    work; this is that rule as a number. A repo with no remote can never satisfy it and is named
    first. A branch already merged into its base is skipped — it holds nothing unique, and
    merged_local_branches above owns it.
    """
    signals = []
    for repo in repos(root):
        name = _rel(repo, root)
        if not _git(repo, 'remote', 'get-url', 'origin'):
            signals.append(f'{name} — no remote: nothing here exists anywhere else')
            continue
        base = _base_of(repo)
        for branch in _locals(repo):
            if branch not in BASES and base and _merged(repo, base, branch):
                continue
            if not _git(repo, 'rev-parse', '--verify', '--quiet',
                        f'refs/remotes/origin/{branch}'):
                signals.append(f'{name} — {branch} was never pushed')
                continue
            ahead = _git(repo, 'rev-list', '--count', f'origin/{branch}..{branch}')
            if ahead.isdigit() and int(ahead) > 0:
                signals.append(f'{name} — {branch} is {ahead} ahead of origin/{branch}')
    return signals


def merged_remote_branches(root: Path) -> list:
    """Remote `feature/*` labels whose every commit is already in the base branch.

    Deleting one is an outward-facing act, so this counts and never acts. It was a list note
    saying eleven such branches were waiting for Lucas; by the time anything read it again the
    real number was six times that, across seventeen repos. A count that regenerates cannot rot
    the way that note did.
    """
    signals = []
    for repo in repos(root):
        base = _base_of(repo)
        if not base or not _git(repo, 'rev-parse', '--verify', '--quiet',
                                f'refs/remotes/origin/{base}'):
            continue
        merged = [ln.strip() for ln in
                  _git(repo, 'branch', '-r', '--merged', f'origin/{base}').splitlines()]
        stale = [b for b in merged
                 if b.startswith(('origin/feature/', 'origin/release/', 'origin/hotfix/'))]
        if stale:
            # The line IS the command. One action per repo, because one push deletes many
            # branches, and a report that names the action beats one that names the problem.
            names = ' '.join(b.replace('origin/', '') for b in stale)
            signals.append(f'{_rel(repo, root)} — {len(stale)} merged into {base}: '
                           f'git -C {_rel(repo, root)} push origin --delete {names}')
    return signals
