#!/usr/bin/env python3
# Self-healing .gitignore allowlist (decided 2026-07-24). Contract: core/hooks/SPECS.md.
#
# Every domain folder (core/, code/, academy/, branches/, brain/, models/, datasets/) uses a
# denylist-first pattern -- `<domain>/*` plus explicit `!<domain>/<dir>/` allow lines -- so a
# brand-new domain subdir is silently untracked until someone remembers to add its line. That
# already bit core/refs/. A subdir with a CONTEXT.md is structural by construction (the existing
# "this is workspace scaffold" signal): add its allow line and stage it, no human action. A subdir
# with no CONTEXT.md stays ignored, correctly project-internal. A subdir in
# gitignore-exceptions.txt is a deliberate, reviewed exception.
import re
import sys
from pathlib import Path

_HOOKS = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(_HOOKS), str(_HOOKS / 'commit')]
import feature_law  # noqa: E402
from pre_commit import Blocked, git  # noqa: E402

DOMAIN = re.compile(r'^([a-zA-Z0-9_-]+)/\*$', re.MULTILINE)


def heal(commit, root=None):
    """Repair the allowlist, then STOP the commit if the repair uncovered unstaged files."""
    # Switched off: the allowlist stops repairing itself. A generator that is disabled writes
    # nothing rather than writing an empty artifact, which would be worse than not running.
    if not feature_law.is_enabled('gitignore-self-heal'):
        return
    # Scoped to the workspace repo. This hook is wired globally (core.hooksPath), but the
    # domain-denylist pattern only exists here; a nested project repo has its own unrelated
    # .gitignore and healing it would write lines into a file that never asked for them.
    root = Path(root) if root else commit.toplevel
    if root == commit.toplevel and not commit.is_workspace:
        return

    ignore = root / '.gitignore'
    if not ignore.is_file():
        return
    healed = _add_missing_lines(root, ignore)
    if not healed:
        return

    # HEAL, THEN STOP -- the commit in flight cannot carry what it could not see.
    #
    # Staging happens before this hook runs, so every file under a directory healed above was
    # ignored at `git add` time and is not in the index. Committing anyway ships a directory's
    # CONTEXT.md without the files it describes, and a clone at that commit regenerates an empty
    # artifact. That is what happened when core/norms/ landed: it self-corrected one commit later
    # and nothing was lost, which is exactly why it would keep happening.
    #
    # The alternative was to `git add` the missing files here so one commit always suffices.
    # Rejected 2026-08-19 (Lucas): a commit hook that stages files the caller did not stage is
    # worse than the bug it fixes. Fail loud instead.
    missing = [name for name in healed
               if git('ls-files', '--others', '--exclude-standard', '--', name, cwd=root)]
    if not missing:
        return
    listed = ' ' + ' '.join(missing)
    raise Blocked(
        f'GITIGNORE HEALED -- rerun the commit\n'
        f'  .gitignore now allows:{listed}\n'
        f'  Those files were ignored when this commit was staged, so it would ship without them.\n'
        f'  Run: git add{listed} && git commit ...')


def main() -> int:
    """`gitignore_heal.py [root]` -- the standalone arm, as the bash had it.

    An EXPLICIT root skips the workspace-repo scope check: naming a directory is a caller saying it
    knows which tree it means, which is what the tests and a one-off repair both need. With no
    argument the scope check applies, because then the answer comes from wherever git put us.
    """
    from pre_commit import collect
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    try:
        heal(collect(), root=root)
    except Blocked as refusal:
        print(str(refusal), file=sys.stderr)
        return 1
    return 0


def _add_missing_lines(root, ignore) -> list:
    """Append an allow line for every structural subdir that lacks one. Returns what it added."""
    text = ignore.read_text(encoding='utf-8', errors='replace')
    exceptions = root / 'core/hooks/gitignore-exceptions.txt'
    excepted = set(exceptions.read_text(encoding='utf-8', errors='replace').split()) \
        if exceptions.is_file() else set()
    allowed = {line.strip() for line in text.splitlines()}
    healed = []
    for domain in DOMAIN.findall(text):
        if not (root / domain).is_dir():
            continue
        for directory in sorted(p for p in (root / domain).iterdir() if p.is_dir()):
            # A nested git repo is unreachable from the outer repo: git cannot track files inside
            # it without submodules, which the 2026-07-22 nested-gitlink decision deliberately
            # killed. An allow line would track nothing and leave a permanent `?? <dir>` in every
            # git status -- what the first version of this hook did to 13 code/ projects. Routing
            # reads their CONTEXT.md off-disk instead. Corrected 2026-07-29.
            if (directory / '.git').exists() or not (directory / 'CONTEXT.md').is_file():
                continue
            name = f'{domain}/{directory.name}'
            if name in excepted or f'!{name}/' in allowed:
                continue
            with ignore.open('a', encoding='utf-8', newline='\n') as handle:
                handle.write(f'!{name}/\n')
            git('add', str(ignore), cwd=root)
            healed.append(name)
    return healed


if __name__ == '__main__':
    sys.exit(main())
