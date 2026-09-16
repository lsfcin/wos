#!/usr/bin/env python3
# Nested-gitlink gate: block committing an undeclared gitlink (mode 160000) into the workspace repo.
#
# Internal projects use their own git repos (AGENTS.md); they must NOT be embedded as gitlinks. A
# fresh clone cannot fetch them, so the pin is broken on arrival, and every commit made inside one
# shows up as recurring "M" noise in the parent. A genuine submodule declared in .gitmodules is fine
# -- the gate is about what was never declared, not about submodules as such.
import sys
from pathlib import Path

_HOOKS = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(_HOOKS), str(_HOOKS / 'commit')]
import feature_law  # noqa: E402
from pre_commit import Blocked, git  # noqa: E402

GITLINK_MODE = '160000'


def check(commit):
    # Switched off: a disabled gate does not block, and does not pretend it ran.
    if not feature_law.is_enabled('gitlink-gate'):
        return
    # Only the workspace structural repo: a nested repo's own gitlinks are its own business.
    if not commit.is_workspace:
        return

    # `--raw` field 2 is the NEW mode, which is the one that matters: an entry becoming a gitlink is
    # the event, not one that already was.
    staged = [line.split('\t')[-1]
              for line in git('diff', '--cached', '--raw', cwd=commit.toplevel).splitlines()
              if len(line.split()) > 1 and line.split()[1] == GITLINK_MODE]
    if not staged:
        return

    offenders = [path for path in staged if path not in _declared(commit)]
    if offenders:
        raise Blocked(
            f"⛔ Undeclared gitlink(s) staged: {' '.join(offenders)}\n"
            "   Internal projects use their own repos — don't embed them in the workspace.\n"
            '   Untrack:  git rm --cached <path>   then add the dir to .gitignore.\n'
            '   (A genuine submodule must be declared in .gitmodules.)')


def _declared(commit) -> set:
    """Paths .gitmodules declares as real submodules."""
    if not (commit.toplevel / '.gitmodules').is_file():
        return set()
    listed = git('config', '--file', '.gitmodules', '--get-regexp', r'^submodule\..*\.path$',
                 cwd=commit.toplevel)
    return {line.split(maxsplit=1)[1] for line in listed.splitlines() if ' ' in line}
