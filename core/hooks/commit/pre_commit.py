#!/usr/bin/env python3
# The git pre-commit pipeline: what every stage shares, and the one place a commit is refused.
#
# WHY THIS REPLACED A SOURCED BASH CHAIN. The dispatcher used to `source` eight .sh fragments
# rather than execute them, for two reasons that were real: they shared `$STAGED`, and they
# rejected the commit by calling `exit`. Both are shell facts, not design — running any fragment
# as a subprocess broke both silently. Here the first is a value passed to a function and the
# second is an exception, so a stage is an ordinary function and the coupling is visible.
#
# WHY THE PORT WAS NOT OPTIONAL. Every path in those fragments was the literal string
# the workspace root. The hook is applied globally via core.hooksPath, so on any clone that is not
# that one directory the dispatcher could not resolve a single tool it calls -- while both config
# files read as correct. The enforcement layer had never once fired on a Windows clone.
#
# THE TWO ROOTS ARE NOT THE SAME DIRECTORY, and conflating them is how this port breaks. `root`
# is where the MACHINERY lives; `toplevel` is the repo BEING COMMITTED. They differ whenever a
# nested repo under code/ commits, which is most of what this pipeline exists to police.
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Every directory this pipeline imports from, named once. The stages live beside each other but the
# checks they call are filed by responsibility (git/, checks/, stubgen/), and a module that fixes up
# sys.path for itself is how one of them ends up importing a different copy of the law.
_HOOKS = Path(__file__).resolve().parents[1]
for _dir in ('', 'commit', 'git', 'checks', 'stubgen'):
    sys.path.insert(0, str(_HOOKS / _dir))

import file_law  # noqa: E402
from platform_law import WORKSPACE_ROOT  # noqa: E402

# Every message this pipeline prints carries ⛔ ✓ → ⚠, and a git hook's stdout is whatever pipe
# git handed it -- on Windows that resolves to the console codepage, where those characters raise
# UnicodeEncodeError and the gate dies printing its own verdict. Named here so no stage has to
# think about it, per core/SCHEMA.md: a text stream never inherits the machine's encoding.
for _stream in (sys.stdout, sys.stderr):
    _stream.reconfigure(encoding='utf-8', errors='replace')


class Blocked(Exception):
    """A stage refusing the commit.

    THE ONLY WAY OUT THAT IS NOT SUCCESS. `core/hooks/SPECS.md` promises that a hook which blocks
    names the fix, and ISSUES.md B4 records the shape that breaks it -- a rejection path exiting
    non-zero with nothing on stderr, costing a round of investigation per occurrence. One
    exception type caught in one place means a message is structurally impossible to omit: there
    is no second way to leave this pipeline unhappy.
    """


def git(*args, cwd=None) -> str:
    """A git query's stdout, stripped. Failure is empty, never an exception.

    Every call site in the bash ended in `2>/dev/null || true` -- a hook that dies because git
    was asked something in a state it did not like is worse than one that reads nothing.
    """
    done = subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True,
                          encoding='utf-8', errors='replace')
    return done.stdout.strip() if done.returncode == 0 else ''


def spawn(commit, relative, *args, stdin=None):
    """Run one of the workspace's own Python gates, from wherever this clone lives.

    ALWAYS THROUGH interpreter(), NEVER THE BARE WORD `python3`. That name is not one Windows has:
    it reaches a Microsoft Store execution alias which prints an advert and exits 9009, so the gate
    never runs and the caller reads the advert as the gate's own output -- a silent pass wearing a
    failure's coat. Every invocation in the bash this replaced was spelled that way.

    `relative` is resolved against the MACHINERY root, because that is where the gate lives; cwd
    stays the committing repo, because that is what the gate must read.

    THE CHILD'S ENCODING IS NAMED, NOT INHERITED. Every gate here prints ⛔ ✓ ⚠, and a spawned
    Python encodes its stdout with the console codepage -- cp1252 on this machine, where those
    characters raise UnicodeEncodeError. A gate then dies *inside its own warning path*, so the
    caller sees a traceback where a skip message belonged. Set once here, it covers every child
    rather than being re-fixed in each one.
    """
    from platform_law import interpreter
    environment = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    return subprocess.run([interpreter(), str(commit.root / relative), *args],
                          input=stdin, cwd=commit.toplevel, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', env=environment)


@dataclass
class Commit:
    """What the stages share -- the `$STAGED` that eight sourced fragments passed by shell state.

    `staged` is --diff-filter=ACM and stays that way on purpose: every gate reads a file's
    CONTENT, which a deleted path does not have. `deleted` is collected separately for the one
    consumer that needs it -- the routing generator, because a directory that LOSES a file is
    exactly the one whose CONTEXT.md now names something gone, and nothing else re-syncs it.
    """
    root: Path                       # the machinery: this workspace, wherever it is cloned
    toplevel: Path                   # the repo being committed -- NOT necessarily the same
    staged: list = field(default_factory=list)
    deleted: list = field(default_factory=list)

    @property
    def is_workspace(self) -> bool:
        """Whether the repo committing IS the workspace, not a nested repo under it."""
        return self.toplevel == self.root

    @property
    def code_files(self) -> list:
        """Staged files the law calls code. Asked of file_law, never re-derived from a suffix
        list -- core/hooks/SPECS.md: a checker that restates the law is the drift it exists to
        catch, and an extension table had already been copied three times."""
        return [p for p in self.staged if file_law.is_code_file(Path(p))]

    def matching(self, *suffixes, exclude=()) -> list:
        """Staged paths ending in any of `suffixes` and none of `exclude`."""
        return [p for p in self.staged
                if p.endswith(suffixes) and not p.endswith(exclude)]

    def existing(self, paths) -> list:
        """Those of `paths` still on disk, resolved against the committing repo.

        A staged path is relative to `toplevel`, and the pipeline's cwd is that repo -- but a
        stage that walks up looking for a tsconfig.json or a terms.yaml needs the absolute form,
        and getting it from the wrong root is the failure this class exists to prevent.
        """
        return [p for p in paths if (self.toplevel / p).is_file()]


def collect() -> Commit:
    """The commit under way, or None when there is nothing this pipeline can act on."""
    toplevel = git('rev-parse', '--show-toplevel')
    commit = Commit(root=WORKSPACE_ROOT,
                    toplevel=Path(toplevel) if toplevel else Path.cwd(),
                    staged=git('diff', '--cached', '--name-only',
                               '--diff-filter=ACM').splitlines(),
                    deleted=git('diff', '--cached', '--name-only',
                                '--diff-filter=D').splitlines())
    return commit


def stages() -> list:
    """The pipeline, in the order the bash ran it -- which is not alphabetical and not arbitrary.

    `lint` is last because ESLint needs the .d.ts files `interfaces` writes. `prepare` is first
    because it stages files the later stages then see. The 2026-07-31 split recorded this order
    after the previous 385-line single file had drifted out of it (1, 2, 1a, 1c, 1d, 1e, 1g, 1f,
    1b, 2b, 3, 4 ...), so it is preserved deliberately rather than inherited.

    `list` runs after every generator and before `lint`: it counts what this commit will really
    contain, so it must see the routing tables and stubs the stages above just wrote.
    """
    import gates
    import gates_project
    import generators
    return [generators.prepare,
            gates.source_quality,
            gates_project.project_contract,
            gates.duplication_and_terms,
            generators.routing,
            generators.interfaces,
            generators.skills,
            generators.issues,
            gates.lint]


def main() -> int:
    commit = collect()
    if not commit.staged and not commit.deleted:
        return 0
    for stage in stages():
        try:
            stage(commit)
        except Blocked as refusal:
            print(str(refusal), file=sys.stderr)
            return 1
    return 0


if __name__ == '__main__':
    # Re-imported under its real name before running, and this is not ceremony. Executed directly
    # this file is the module `__main__`, while every stage reaches it as `pre_commit` -- two module
    # objects, so two distinct Blocked classes, and the `except` below would never match the one a
    # gate raised. A refusal would then surface as a traceback: the commit still stops, but the
    # message naming the fix is buried, which is the exact contract this pipeline owes.
    import pre_commit
    sys.exit(pre_commit.main())
