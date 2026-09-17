#!/usr/bin/env python3
# rebuild.py — what the DESTINATION runs after the copy, so what it generates describes ITS tree.
#
# WHY THE SYNC CANNOT JUST COPY A BLOCK. The public tree holds a subset of this one, so the CORRECT
# routing table differs on the two sides: this root routes to six subdirectories and the target's to
# one. Copying the bytes makes the file STALE forever and the sync copy it back every run, which is
# an oscillation rather than a cleanup — that is why repo's comparison ignored generated blocks, and
# ignoring them is what let the target drift silently for weeks. Measured 2026-09-17: 34 pointers
# inside a generated block in the target aimed at a file the floor refuses or never sent, including
# core/CONTEXT.md routing to core/experiments/, a REFUSED tree.
#
# SO THE BLOCK IS NOT COPIED AND NOT COMPARED — IT IS REGENERATED THERE, by the generator that
# crossed, reading the target's own tree. That is not the clone authoring anything: it authors no
# content and decides nothing, the same way a .pyi is not authored by the file it sits beside.
# Whatever the target holds came from here; this only finishes the sentence at the destination.
#
# RUN AFTER THE COPY AND BEFORE ANY COMPARISON. Once this has run, repo compares whole bytes.
from __future__ import annotations
import pathlib
import subprocess
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import crossing as core  # noqa: E402

# Through `core/run`, never a spelled interpreter: the launcher is what finds the TARGET's venv, and
# a hardcoded `python3` would run the target's generators against this clone's site-packages.
LAUNCHER = ('sh', 'core/run')


def _run(target: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([*LAUNCHER, *args], cwd=target, capture_output=True,
                          text=True, encoding='utf-8', errors='replace')


def leaves(target: pathlib.Path) -> list[str]:
    """Every directory in the target that owns a routing table, plus the root.

    Asked of the target's git rather than of its disk, for the reason `crossing.tracked()` gives:
    the generated mirrors and the venv are on the disk and are nobody's to regenerate. The root is
    added unconditionally because it carries AGENTS.md rather than a CONTEXT.md, which
    context_synchronizer handles as its workspace mode — a directory with no CONTEXT.md and no
    AGENTS.md simply returns, so a root that lost its entrypoint costs one no-op instead of a crash.
    """
    listed = subprocess.run(['git', '-C', str(target), 'ls-files'], capture_output=True,
                            text=True, encoding='utf-8', check=True).stdout.split('\n')
    dirs = {pathlib.PurePosixPath(p).parent.as_posix()
            for p in listed if p.endswith('CONTEXT.md')}
    return sorted(dirs | {'.'})


def generators(target: pathlib.Path) -> list[str]:
    """Run every generator the target owns, over the whole target rather than over a diff.

    THE SAME THREE core/hooks/commit/generators.py RUNS AT A COMMIT, and deliberately not through
    it: that pipeline is driven by what a commit STAGED — routing only for directories whose code
    files are in it, norms only when core/norms/ or the registry is — and a sync that copies nothing
    but markdown stages none of those. Trusting it is how the target's tables went stale while every
    run reported clean.

    Returns one line per generator that failed, empty when all of them ran. A FAILURE IS REPORTED,
    NEVER RAISED: the caller is mid-sync with a tree already copied, and refusing there would leave
    the target half-rebuilt with nothing said about which half. repo decides what a failure costs.
    """
    failed = []
    for leaf in leaves(target):
        done = _run(target, 'hooks/routing/context_synchronizer.py', leaf)
        if done.returncode != 0:
            failed.append(f'routing {leaf}: {done.stderr.strip() or done.stdout.strip()}')
    # Once, not per-directory: it publishes core/norms/*.md into the one always-loaded file, in the
    # order core/features.txt gives, reading the TARGET's registry and profile — so a norm the public
    # repo ships switched off leaves the public AGENTS.md rather than sitting inert in it.
    done = _run(target, 'hooks/routing/norms.py')
    if done.returncode != 0:
        failed.append(f'norms: {done.stderr.strip() or done.stdout.strip()}')
    # The mirrors are gitignored, so nothing here COPIES them and nothing compares them — which left
    # them the one generated thing in the target that a sync could not reach. A skill crossing for
    # the first time then failed the target's own suite on a precondition, found 2026-09-17 by that
    # suite refusing the commit. Pruning is the half that matters: `rm` of a skill is not an edit, so
    # no hook ever removes the copies of one the floor stopped sending.
    done = _run(target, 'tools/wos/sync-skills')
    if done.returncode != 0:
        failed.append(f'skills: {done.stderr.strip() or done.stdout.strip()}')
    return failed


if __name__ == '__main__':   # run alone to inspect a rebuild without syncing first
    problems = generators(core.floor().target)
    for line in problems:
        print(f'  FAILED   {line}')
    print(f'rebuild: {len(problems)} generator failure(s)')
    sys.exit(1 if problems else 0)
