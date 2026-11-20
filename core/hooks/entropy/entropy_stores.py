#!/usr/bin/env python3
# Level 0 for the two stores that record what we know and how sure we are: core/experiments/ and
# core/refs/REFS.md. Zero-token, deterministic.
#
# These are the two rules this workspace cites as proof it knows how to doubt — a runnable `Method`
# with dated `Results` and `Limitations` never omitted, and a level marker on every reference — and
# until 2026-08-18 neither was verified by anything. They held because a few careful sessions
# followed them, which is INDUCED wearing ENFORCED's costume (core/SPECS.md § AD-16 band 1).
#
# Both stores are small and closed, so the check is total rather than sampled: no allowlist, no
# ceiling inside this module. The ceiling is the CALLER's — type-gate.py asks only about files a
# commit adds, the dashboard asks about all of them.
import re
from pathlib import Path

EXPERIMENTS = 'core/experiments'
REFS = 'core/refs/REFS.md'
# The family, not the one file: REFS.md cut, and a suffix matcher would have gone
# silent on every part while still passing — the same shape as reading only an index.
REFS_DIR, REFS_STEM = 'core/refs/', 'REFS'

# The format core/experiments/SPECS.md declares. `What changed` is required even when the answer is
# `nothing yet`: a measurement nobody acted on is a finding, and an absent section hides it.
SECTIONS = ('## Method', '## Results', '## What changed', '## Limitations')

# A reference is a bullet carrying a link. The level comes first so a reader can sort by weight
# without reading the line — core/refs/SPECS.md § Source levels.
LEVELLED = re.compile(r'^- `\[[ABPVC]\]`')
LINKED = re.compile(r'\]\(https?://')


def _is_experiment(path: Path) -> bool:
    """A measurement file, not the directory's own two documents about measurement files."""
    return (EXPERIMENTS in path.as_posix() and path.suffix == '.md'
            and path.name not in ('CONTEXT.md', 'SPECS.md'))


def experiment_hits(files: list) -> list:
    """Every core/experiments/ file missing a section its own SPECS.md requires.

    `Limitations` is the one that earned the check: the output-cost number was wrong by 2x for three
    weeks, and what would have caught it is the section saying what the instrument cannot tell you.
    """
    hits = []
    for path in files:
        if not _is_experiment(path):
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        missing = [s for s in SECTIONS if s not in text]
        if len(lines) < 2 or not lines[1].startswith('> '):
            missing.insert(0, '> question (line 2)')
        if missing:
            hits.append(f'{path}: missing {", ".join(missing)}.\n'
                        f'   An experiment states what it measured, how to re-run it, what changed\n'
                        f'   and what it cannot tell you (core/experiments/SPECS.md § The format).')
    return hits


def ref_level_hits(files: list) -> list:
    """Every reference with no source level. The Unjudged section is the intake queue and is exempt.

    That exemption is read from REFS.md's own heading rather than configured here: a captured link
    earns its level when it is promoted, and demanding one at capture time would make capture cost
    something, which is the whole reason the queue exists.
    """
    hits = []
    for path in files:
        posix = path.as_posix()
        if REFS_DIR not in posix or not path.stem.split('-')[0] == REFS_STEM:
            continue
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        unjudged = False
        for number, line in enumerate(lines, 1):
            if line.startswith('## '):
                unjudged = 'njudged' in line
            elif not unjudged and line.startswith('- ') and LINKED.search(line) \
                    and not LEVELLED.match(line):
                hits.append(f'{path}:{number}: reference carries no source level.\n'
                            f'   Open the line with `[A]`/`[B]`/`[P]`/`[V]`/`[C]`, or leave it in\n'
                            f'   the Unjudged queue until it is judged (core/refs/SPECS.md).')
    return hits
