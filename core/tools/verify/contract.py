#!/usr/bin/env python3
# How a repo declares its verification, and how to run what it declared. One definition.
#
# The extraction this directory's CONTEXT.md said was waiting on a second consumer: the pre-commit
# gate (core/hooks/commit/gates_project.py) discovers `fast`, and core/tools/wos/roundup discovers
# `full` at session close. They were about to hold two copies of the same ordered list, differing
# only in a word — which is exactly how the two of them would drift on what counts as declared.
#
# WHY verify.py LEADS. It is the only form that can ask platform_law which interpreter to use. The
# other two are programs that must already be installed AND already spelled right for this machine:
# the workspace declared `make verify-fast`, the gate discovered it, and on a machine without make
# nothing ran while the gate stayed green (ISSUES.md B9).
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from shutil import which

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'hooks'))
from platform_law import interpreter  # noqa: E402


def _declared(root: Path, level: str) -> list:
    """[label, *argv] for `level` ('fast'|'full') exactly, or [] when this repo declares none."""
    if (root / 'verify.py').is_file():
        return [f'verify.py {level}', interpreter(), 'verify.py', level]
    package = root / 'package.json'
    text = package.read_text(encoding='utf-8', errors='replace') if package.is_file() else ''
    if f'"verify:{level}"' in text:
        return [f'npm run verify:{level}', 'npm', 'run', '--silent', f'verify:{level}']
    makefile = root / 'Makefile'
    recipes = makefile.read_text(encoding='utf-8', errors='replace') if makefile.is_file() else ''
    if any(line.startswith(f'verify-{level}:') for line in recipes.splitlines()):
        return [f'make verify-{level}', 'make', f'verify-{level}']
    return []


def discover(root: Path, level: str = 'fast') -> list:
    """[label, *argv], or []. `full` falls back to `fast` — a close runs the best thing declared."""
    found = _declared(root, level)
    return found if found or level == 'fast' else _declared(root, 'fast')


def run(root: Path, declared: list, timeout: int = 900) -> tuple:
    """(returncode, log) for a discovered contract, or (None, reason) when its runner is absent.

    RESOLVED, AND NEVER THROUGH A SHELL. `which` honours PATHEXT so `npm` is found however this
    machine spells it, while a bare name handed to subprocess resolves only against `.exe`.

    STDIN IS CLOSED, and the output goes to a FILE rather than a pipe. Both guard the same thing:
    a verifier that can hang is worse than one that can go red, because a hang is reported by
    nobody. The pipe is the subtler half — a suite spawns processes of its own, and one that
    outlives it inherits the write end, so the parent waits for an EOF that never comes long after
    the suite itself has finished. The shell this replaced redirected into a temp file and was
    immune; the port reintroduced the deadlock by capturing, and hung the commit gate for as long
    as anyone was willing to wait. The timeout is the backstop for everything else.
    """
    _, program, *rest = declared
    resolved = program if Path(program).is_file() else which(program)
    if not resolved:
        return None, f'{program}: not installed on this machine'
    # GIT_* IS STRIPPED. When the pre-commit hook is the caller, git has exported GIT_DIR,
    # GIT_INDEX_FILE and the author identity into the environment, and every `git` a suite runs
    # then inherits them — so a test building its own throwaway repo silently addresses the repo
    # being committed instead. It is a correctness hazard before it is a speed one: `git add -A`
    # in a fixture would stage the real workspace. A verification run must not inherit the
    # identity of the commit that triggered it.
    environment = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    handle, log = tempfile.mkstemp(suffix='.log', prefix='wos-verify-')
    try:
        with os.fdopen(handle, 'w', encoding='utf-8', errors='replace') as sink:
            try:
                done = subprocess.run([resolved, *rest], cwd=root, stdout=sink,
                                      stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                      env=environment, timeout=timeout)
                code = done.returncode
            except subprocess.TimeoutExpired:
                code = None
        text = Path(log).read_text(encoding='utf-8', errors='replace')
        if code is None:
            return 1, f'{text}\n{declared[0]}: still running after {timeout}s — killed'
        return code, text
    finally:
        Path(log).unlink(missing_ok=True)
