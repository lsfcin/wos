#!/usr/bin/env python3
# How big a file got, and whether anything can read its interface. Zero-token, deterministic.
#
# Moved out of dashboard/entropy-dashboard.py 2026-08-20, when that file hit the 200-line block.
# The gate was right and the boundary was already written down: dashboard/CONTEXT.md says the checks
# stay next door and that directory owns nobody's rule — but these two were rules, living in the
# renderer. Every sibling here answers one question about the corpus and hands back findings; so do
# these, now from the same place.
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from entropy_corpus import is_generated_mirror  # noqa: E402
from file_law import (FACADES, is_authored, is_authored_prose,  # noqa: E402
                      is_generated_artifact, is_vendored, load_limits)
from platform_law import rel  # noqa: E402
from schema_law import WORKSPACE_ROOT  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stubgen'))
from stubs import STUB_FOR, interface_for  # noqa: E402


def _rel(path) -> str:
    return rel(path, WORKSPACE_ROOT)


def _added_by(path: Path) -> str:
    """The commit that introduced a file — a --no-verify bypass leaves no other trace."""
    repo = next((p for p in path.parents if (p / '.git').exists()), WORKSPACE_ROOT)
    out = subprocess.run(
        ['git', '-C', str(repo), 'log', '--diff-filter=A', '--format=%h %an',
         '-1', '--', rel(path, repo)],
        capture_output=True, text=True, encoding='utf-8').stdout.strip()
    return out or 'unknown'


def size_signals(files: list) -> list:
    """Authored files over the line cap, and over the document character cap.

    One number for both kinds since 2026-08-18. Prose used to carry its own DOC_SIGNAL_LINES=300,
    a second number answering the question BLOCK_LINES already answers, which is the drift
    file_law.py exists to prevent — and it reported a file it never held to anything.

    The second signal measured one LINE's width until 2026-09-14; it now weighs the whole document,
    so it fires once per file rather than once per line and applies to code as well as prose.
    limits.env § chars says why the unit moved.
    """
    limits = load_limits()
    block, chars = limits['BLOCK_LINES'], limits['BLOCK_CHARS']
    signals = []
    for path in files:
        if is_generated_mirror(path):
            continue
        prose = is_authored_prose(path, WORKSPACE_ROOT)
        if not prose and not is_authored(path, WORKSPACE_ROOT):
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        if len(lines) > block:
            signals.append(f'{_rel(path)} — {len(lines)} lines, over the {block} cap; '
                           f'introduced by {_added_by(path)}')
        if len(text) > chars:
            signals.append(f'{_rel(path)} — {len(text)} characters, over the {chars} cap')
    return signals


def stub_signals(files: list) -> list:
    """Source files with no interface stub beside them.

    The read gate only fires when a stub EXISTS, so a missing one does not break —
    it silently switches the interface-first discipline off for that file, and nothing
    said so. The commit hook stubs what a commit stages; a file that arrived any other
    way was never stubbed and was never counted. This is the counting.
    """
    signals = []
    for path in files:
        stub = interface_for(path)
        if not stub or is_vendored(path, WORKSPACE_ROOT) or \
                is_generated_artifact(path, WORKSPACE_ROOT):
            continue
        if path.name.endswith('.d.ts') or '__pycache__' in path.parts or path.name in FACADES:
            continue
        if not stub.exists():
            signals.append(f'{_rel(path)} — no {STUB_FOR[path.suffix]}')
    return signals
