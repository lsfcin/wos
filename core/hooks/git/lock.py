#!/usr/bin/env python3
# The branch is the lock: one agent session per repo, held by standing on the branch it created.
#
# A governed repo (it has `develop`, and its origin is the profile's GitHub owner) is FREE on a
# shared branch with a clean tree. A session's first write takes it — fetch, pull --ff-only, a new
# feature/<topic>-<MMDD> and a lock file naming the session, all under one flock — and the close
# gives it back. Every other session is refused until then; `core/run tools/wos/claim` hands it over
# on Lucas's word. The rules bind agents only: no session id, no gate (ruled 2026-11-19, Lucas).
# Contract: core/hooks/git/SPECS.md.
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

_HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HOOKS))
import feature_law  # noqa: E402
from platform_law import locked, rel, session_state  # noqa: E402

SHARED = ('main', 'master', 'develop')
WORKSPACE = _HOOKS.parents[1]
# The ids an agent's shell exports, so a git hook it spawns knows it is an agent's commit.
SESSION_ENV = ('CLAUDE_CODE_SESSION_ID', 'CODEX_THREAD_ID', 'CODEX_SESSION_ID', 'CLAUDE_SESSION_ID')


def git(repo, *args) -> subprocess.CompletedProcess:
    return subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True, encoding='utf-8')


def out(repo, *args) -> str:
    done = git(repo, *args)
    return done.stdout.strip() if done.returncode == 0 else ''


def repo_of(path) -> Path | None:
    folder = Path(path)
    while not folder.is_dir() and folder != folder.parent:
        folder = folder.parent
    top = out(folder, 'rev-parse', '--show-toplevel')
    return Path(top).resolve() if top else None


def owned(repo) -> bool:
    """Origin's GitHub owner is the profile's `github-owner`: a clone of someone else's repo, or a
    paper on Overleaf, is never merged or pushed by a hook or a close."""
    match = re.search(r'github\.com[:/]([^/]+)/', out(repo, 'config', '--get', 'remote.origin.url'))
    owner = feature_law.setting('github-owner')
    return bool(match and owner) and match.group(1).lower() == owner.lower()


def governed(repo) -> bool:
    """Owned and has `develop`: the repos the lock holds. An owned repo without one is a trunk."""
    return bool(out(repo, 'rev-parse', '--verify', '-q', 'refs/heads/develop')) and owned(repo)


def lock_file(repo) -> Path:
    return session_state('lock_' + re.sub(r'[^A-Za-z0-9]', '_', str(Path(repo).resolve())) + '.txt')


def holder(repo) -> tuple:
    """(session, branch) holding `repo`, or ('', '')."""
    path = lock_file(repo)
    parts = path.read_text(encoding='utf-8').split('\t') if path.is_file() else []
    return (parts[0], parts[1]) if len(parts) >= 3 else ('', '')


def _hold(repo, session: str, branch: str) -> None:
    lock_file(repo).write_text(f'{session}\t{branch}\t{Path(repo).resolve()}\t{date.today()}\n',
                               encoding='utf-8', newline='\n')


def held_by(session: str) -> list:
    """Every repo this session holds — what the close covers."""
    found = []
    for path in lock_file(WORKSPACE).parent.glob('lock_*.txt'):
        try:   # a lock another close is dropping right now is simply not held
            row = path.read_text(encoding='utf-8').split('\t')
        except OSError:
            continue
        if len(row) >= 3 and row[0] == session:
            found.append(Path(row[2]))
    return found


def release(repo, session: str) -> None:
    with locked(lock_file(repo).with_suffix('.flock')):
        if holder(repo)[0] == session:
            lock_file(repo).unlink(missing_ok=True)


def claim(repo, session: str) -> str:
    """Hand `repo` to `session` on the branch it stands on; returns the previous holder."""
    with locked(lock_file(repo).with_suffix('.flock')):
        before = holder(repo)[0]
        _hold(repo, session, out(repo, 'branch', '--show-current'))
    return before


def _name(repo) -> str:
    return 'the workspace' if repo == WORKSPACE else rel(repo, WORKSPACE)


def _topic(repo, path) -> str:
    try:
        first = Path(path).resolve().relative_to(repo).parts[0]
    except (ValueError, IndexError):
        first = 'work'
    return re.sub(r'[^a-z0-9]+', '-', Path(first).stem.lower()).strip('-') or 'work'


def _take(repo, session: str, path) -> tuple:
    """Clean shared branch, nobody holding: pull develop and branch off it."""
    if out(repo, 'status', '--porcelain'):
        return (f'⛔ BRANCH LOCK — {_name(repo)} has uncommitted changes nobody holds.\n'
                '   They are not this session\'s. Ask Lucas to commit or stash them, then retry.'), ''
    fetched = git(repo, 'fetch', '-q', 'origin').returncode == 0
    if git(repo, 'switch', '-q', 'develop').returncode != 0 or \
            (fetched and git(repo, 'merge', '-q', '--ff-only', 'origin/develop').returncode != 0):
        return (f'⛔ BRANCH LOCK — develop in {_name(repo)} cannot fast-forward to origin.\n'
                '   It diverged; that is Lucas\'s to settle.'), ''
    base = f'feature/{_topic(repo, path)}-{date.today():%m%d}'
    branch, n = base, 1
    while out(repo, 'rev-parse', '--verify', '-q', f'refs/heads/{branch}'):
        n += 1
        branch = f'{base}-{n}'
    if git(repo, 'switch', '-q', '-c', branch).returncode != 0:
        return f'⛔ BRANCH LOCK — could not create {branch} in {_name(repo)}.', ''
    _hold(repo, session, branch)
    return '', (f'[Git] {_name(repo)} is yours on {branch}' + ('' if fetched else ' (offline: not pulled)')
                + f'. The close merges it into develop. Session: {session}')


def verdict(path, session: str, take: bool = True) -> tuple:
    """(refusal, note) for this session acting on the repo holding `path`."""
    repo = repo_of(path)
    if not session or not repo or not feature_law.is_enabled('branch-lock') or not governed(repo):
        return '', ''
    with locked(lock_file(repo).with_suffix('.flock')):
        owner, branch = holder(repo)
        head = out(repo, 'branch', '--show-current')
        if owner == session:
            if head == branch or not head:
                return '', ''
            if head in SHARED:
                return (f'⛔ BRANCH LOCK — you hold {_name(repo)} on {branch}, but it is on {head}.\n'
                        f'   git -C {repo} switch {branch}'), ''
            _hold(repo, session, head)   # nobody else can switch a held repo: this was ours
            return '', ''
        if owner:
            return (f'⛔ BRANCH LOCK — {_name(repo)} is held by session {owner} on {branch}.\n'
                    '   Work elsewhere, or wait for its close. Only on Lucas\'s explicit word:\n'
                    f'     core/run tools/wos/claim {repo} --session {session}'), ''
        if head not in SHARED:
            return (f'⛔ BRANCH LOCK — {_name(repo)} is on {head or "a detached HEAD"}, held by nobody.\n'
                    '   Only on Lucas\'s explicit word:\n'
                    f'     core/run tools/wos/claim {repo} --session {session}'), ''
        return _take(repo, session, path) if take else ('', '')


def env_session() -> str:
    return next((os.environ[k] for k in SESSION_ENV if os.environ.get(k)), '')


def check(commit) -> None:
    """Pre-commit: an agent never commits on a shared branch of a governed repo. A person may."""
    from pre_commit import Blocked  # noqa: PLC0415
    branch = out(commit.toplevel, 'branch', '--show-current')
    if not env_session() or branch not in SHARED or not feature_law.is_enabled('branch-lock') \
            or Path(commit.toplevel, out(commit.toplevel, 'rev-parse', '--git-dir'), 'MERGE_HEAD').exists() \
            or not governed(commit.toplevel):
        return
    raise Blocked(f'⛔ BRANCH LOCK — an agent commits on a feature branch, never on {branch}.\n'
                  '   Write a file first: the lock creates the branch.')
