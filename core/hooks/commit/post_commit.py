#!/usr/bin/env python3
# Auto-push feature/* after a commit, so work survives a dead session and reaches the other machine.
#
# main/develop are never auto-pushed: promoting them is a conscious gitflow merge, done in /roundup
# after the verification gate. Never blocks -- git ignores a post-commit's exit status, and every
# failure here is a warning.
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from pre_commit import git  # noqa: E402

for _stream in (sys.stdout, sys.stderr):
    _stream.reconfigure(encoding='utf-8', errors='replace')


def _authenticated() -> bool:
    """Whether this machine can push to GitHub at all.

    Asked through `gh` because it is the only question whose answer the reader cannot infer from
    push output they never saw. A machine with no gh installed answers False, which is correct:
    no gh and no push means nothing has told git who we are.
    """
    try:
        done = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True,
                              encoding='utf-8', errors='replace')
    except (FileNotFoundError, OSError):
        return False
    return done.returncode == 0


def main() -> int:
    gitdir = git('rev-parse', '--git-dir')
    if not gitdir:
        return 0

    # The switch, read through feature_law rather than a second reading of the registry -- same
    # law, one parser, same boundary as git/gitflow_gate.py. Off means the commit stays local.
    if not feature_law.is_enabled('auto-push'):
        return 0

    # Mid-rebase / mid-cherry-pick: pushing per replayed commit is noise and often rejected.
    if any((Path(gitdir) / d).is_dir() for d in ('rebase-merge', 'rebase-apply')):
        return 0

    branch = git('rev-parse', '--abbrev-ref', 'HEAD')
    if not branch.startswith('feature/'):
        return 0
    if not git('remote', 'get-url', 'origin'):
        return 0

    # THE FAILURE BRANCH NAMES ONE CAUSE, AND IT HAS TO BE THE RIGHT ONE. It used to print
    # "offline, or history diverged" for everything -- two causes, and on a machine with no
    # credential neither was the one. Worse, an unauthenticated push does not fail: it blocks on a
    # device-code prompt until the timeout kills it, so the slowest failure got the least accurate
    # message. Authentication is checked first for that reason.
    try:
        done = subprocess.run(['git', 'push', '-q', '--set-upstream', 'origin', branch],
                              capture_output=True, text=True, timeout=25,
                              encoding='utf-8', errors='replace')
        pushed, why = done.returncode == 0, (done.stderr or done.stdout).strip()
    except subprocess.TimeoutExpired:
        pushed, why = False, 'timed out after 25s -- a push waiting on an interactive prompt'

    if pushed:
        print(f'↑ auto-pushed {branch}')
    elif not _authenticated():
        print(f'⚠ auto-push failed for {branch} — this machine is not authenticated with GitHub.')
        print("  Run 'gh auth login', then 'gh auth setup-git'. SETUP-clone.md § GitHub account.")
    else:
        print(f'⚠ auto-push failed for {branch} — offline, or history diverged (force-push needed).')
        print('  Push manually before switching machines. git said:')
        print('\n'.join(f'    {line}' for line in why.splitlines()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
