#!/usr/bin/env python3
# Usage: verify.py [fast|full] — this workspace's verification contract, the one the pre-commit
# gate discovers and /roundup runs at close.
#
# WHY THIS IS NOT A MAKEFILE TARGET ANY MORE. The contract used to be `make verify-fast`, and on a
# machine without `make` every commit printed a warning and ran nothing: the gate was fully green
# and fully blind (ISSUES.md B9). Installing `make` would not have fixed it, and that is the part
# worth keeping. The recipe named the POSIX venv bin directory, which is a different name on another machine —
# and globbed `core/hooks/*/*.sh` through a shell that is not everywhere. **A Makefile cannot ask
# platform_law.py anything**, so every per-machine answer inside one has to be spelled, and a
# spelled answer is the defect this port exists to remove. A Python entrypoint can just ask.
#
# Discovery is unchanged in spirit: core/hooks/commit/gates_project.py looks for this file first,
# then an npm "verify:fast", then a Makefile target, so a project keeps declaring a contract rather
# than wiring anything.
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path
from shutil import which

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'core/hooks'))
from platform_law import interpreter  # noqa: E402

SUITE = 'core/tools/test/'


def _run(command: list) -> int:
    """One step, with the child's stdin closed.

    NOT A DETAIL. A verification run is spawned from hooks, from /roundup and from CI, and a child
    that inherits an interactive stdin blocks there forever instead of failing — measured in this
    session, where the suite ran in 70s with stdin closed and hung indefinitely without it. A
    verifier that can hang is worse than one that can fail: nothing reports a hang.
    """
    return subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL).returncode


def shell_syntax() -> int:
    """`bash -n` over the shell hooks that are left, while any are.

    Skips loudly rather than failing when bash is absent: an uninstalled checker is not a red
    suite, and reporting it as one is the exact lie the missing `make` told. The arm retires
    itself — when the last .sh under core/hooks is ported, there is nothing here to check.
    """
    scripts = sorted(ROOT.glob('core/hooks/*.sh')) + sorted(ROOT.glob('core/hooks/*/*.sh'))
    if not scripts:
        return 0
    bash = which('bash')
    if not bash:
        print(f'⚠  bash not found — {len(scripts)} shell hook(s) not syntax-checked.')
        return 0
    return _run([bash, '-n', *[str(s) for s in scripts]])


def suite(network: bool) -> int:
    """T0 static + T1 unit. `full` adds the network-marked cases (live yt-dlp, real URLs).

    PARALLEL, AND FOR THE SAME REASON THE TOOLS WERE PORTED (2026-09-01). This suite is bound by
    process SPAWN, not by work: measured here, the 30 slowest cases account for 113 s of 171 s and
    nearly all of them shell out. That is the finding ISSUES.md recorded one level down about
    `sync-skills`, and the pre-commit gate runs this whole file on every commit at the workspace
    root -- so a commit cost 5-10 minutes on a Windows clone. 167 s -> 45 s over three consecutive
    green runs, 659 passed each.

    `auto`, never a number: how many cores this machine has is a per-machine value, and spelling
    one in a versioned file is the defect the whole port exists to remove.

    ASKED FOR, NOT ASSUMED. A clone without xdist would die on the flag it was handed and report a
    RED SUITE for a missing dependency -- the exact lie the absent `make` told (ISSUES.md B9), and
    the reason shell_syntax() below skips loudly instead of failing. Slower is not broken.

    TWO PASSES WHEN PARALLEL, and the second one is the price of the first. A case that dirties the
    real tree — the mirror heal has to, there is no root to point it at — is a true answer to the
    wrong question for every worker reading that tree beside it. It cost two of three red runs here
    on 2026-09-02 while the Windows clone had seen three greens: how wide the window opens is a core
    count, so a suite that is green on one machine proves nothing about the other. `serial` is the
    marker, conftest.py holds the reason, and the pass costs a few seconds because almost nothing
    wears it. Without xdist there is one pass and the marker means nothing.
    """
    base = [interpreter(), '-m', 'pytest', SUITE, '-q']
    marks = [] if network else ['not network']
    if not find_spec('xdist'):
        print('⚠  pytest-xdist not installed — suite runs serial (~4x slower). See SETUP.md.')
        return _run(base + (['-m', ' and '.join(marks)] if marks else []))
    code = _run(base + ['-m', ' and '.join([*marks, 'serial'])])
    return code or _run(base + ['-n', 'auto', '-m', ' and '.join([*marks, 'not serial'])])


def main(argv: list) -> int:
    level = argv[1] if len(argv) > 1 else 'fast'
    if level not in ('fast', 'full'):
        print(f'Usage: verify.py [fast|full] — got {level!r}', file=sys.stderr)
        return 64
    return shell_syntax() or suite(network=(level == 'full'))


if __name__ == '__main__':
    sys.exit(main(sys.argv))
