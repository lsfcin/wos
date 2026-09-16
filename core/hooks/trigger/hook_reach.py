#!/usr/bin/env python3
# Which files a hook ENTRYPOINT actually reaches. The sibling of hook_input.py one level up: that
# one parses what comes INTO a hook, this one says what a hook goes on to RUN.
#
# Deliberately moment-free, and that is what keeps it acyclic: trigger_law.py owns the vocabulary
# of when things fire and hands this module bare seed paths, so the walk knows nothing about
# harnesses, events or matchers and cannot drift from them.
#
# The walk is over NAMES A FILE SPELLS OUT, which is a static approximation of a call graph across
# two languages. Two rules keep it honest, both learned from its first run: a call is code and not
# a comment, and an ambiguous name is dropped rather than guessed.
import re
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1]
for _dir in (HOOKS, HOOKS / 'entropy'):
    sys.path.insert(0, str(_dir))

from entropy_corpus import tracked_files  # noqa: E402
from platform_law import rel as _rel  # noqa: E402
from schema_law import WORKSPACE_ROOT  # noqa: E402

# A dispatcher names its stages through a shell variable, so no text match can follow it — those
# two are expanded through chain() instead.
DISPATCHERS = ('core/hooks/pre-commit', 'core/hooks/post-edit.sh')
HOPS = 4          # dispatcher -> stage -> check -> the module that check imports. Deeper than
                  # that, a name appearing in a file is coincidence rather than a call.


def target(token: str, root: Path = WORKSPACE_ROOT) -> str:
    """The repo-relative file a command token names, or '' when it names none.

    THE SECOND ARM IS THE LAUNCHER'S CONVENTION, and its absence blanked every gate's moment. Since
    2026-08-29 a shim spawns `core/run hooks/read/pre-read.py` — the argument is relative to
    `core/`, not to the repo — so `root / 'hooks/read/pre-read.py'` is not a file, and the only
    token in such a command that resolved was `core/run` itself. Every hook spawned that way seeded
    nothing, which is all of them; trigger_law.py reported 25 of 37 hook features as having no
    moment, and nothing was red because an unplaced feature is only ever counted.
    """
    rel = _rel(token, root)
    if (root / rel).is_file():
        return rel
    return f'core/{rel}' if (root / 'core' / rel).is_file() else ''


def chain(entry: str = DISPATCHERS[0], root: Path = WORKSPACE_ROOT) -> list:
    """The stages a dispatcher SOURCES, in execution order, read from its own `for part in` list.
    That order is load-bearing — lint runs last because it needs the stubs the generators just
    wrote — so anything that re-typed it would be free to disagree with the hook that runs it."""
    text = (root / entry).read_text(encoding='utf-8', errors='replace')
    listed = re.search(r'for part in\b(.*?)\bdo\b', text, re.S)
    if not listed:
        return []
    prefix = re.search(r'\$HOOKS_DIR/([\w/-]*)\$part', text)
    parts = [part.strip().rstrip(';') for part in listed.group(1).replace('\\', ' ').split()]
    return [f'core/hooks/{prefix.group(1) if prefix else ""}{part}.sh'
            for part in parts if part and not part.startswith('#')]


def code(text: str) -> str:
    """The text with its prose removed — comment lines, and the docstrings that are prose in
    quotes. A CALL IS CODE AND A MENTION IS PROSE: the files here explain themselves at length, and
    matching a name inside that prose put type-gate at all nine session moments on the first run,
    then routed half the enforcement layer through hook_input.py's docstring on the second."""
    text = re.sub(r'("""|\'\'\')(?:.|\n)*?\1', '', text)
    return '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('#'))


def index(root: Path = WORKSPACE_ROOT) -> tuple:
    """({path token: file}, {module stem: file}) — how a hook can name the file it calls: by path
    in shell, by stem in a Python import. THE TWO ARE MATCHED DIFFERENTLY AND THAT IS THE POINT: a
    stem like `norms`, `compress` or `detect` is an ordinary English word, and matching it as bare
    text put ten session moments on norms.py and on four caveman scripts. A stem only counts inside
    import syntax. AMBIGUOUS TOKENS ARE DROPPED TOO: `lint.sh` sits under both gates/ and postedit/,
    which run at different moments, and a wrong answer is worse than a missing one."""
    paths: dict = {}
    stems: dict = {}
    for path in tracked_files(root):
        rel = _rel(path, root)
        if not rel.startswith('core/') or path.suffix not in ('.py', '.sh', '.js'):
            continue
        token = '/'.join(rel.split('/')[-2:])
        paths[token] = rel if paths.get(token, rel) == rel else ''
        if path.suffix == '.py':
            stems[path.stem] = rel if stems.get(path.stem, rel) == rel else ''
    return ({t: rel for t, rel in paths.items() if rel},
            {t: rel for t, rel in stems.items() if rel})


def _named(root: Path, rel: str, names: tuple, cache: dict) -> list:
    if rel in DISPATCHERS:
        return chain(rel, root)
    if rel not in cache:
        path = root / rel
        cache[rel] = code(path.read_text(encoding='utf-8', errors='replace')) if path.is_file() else ''
    text, (paths, stems) = cache[rel], names
    imported = set(re.findall(r'^\s*(?:from|import)\s+([\w.]+)', text, re.M))
    return sorted({target for token, target in paths.items() if token in text and target != rel}
                  | {target for stem, target in stems.items()
                     if stem in imported and target != rel})


def reaches(seeds: list, root: Path = WORKSPACE_ROOT) -> dict:
    """{repo-relative path: [the seeds that reach it]} — a seed reaches itself.

    Breadth-first and capped at HOPS, so the walk terminates on a cycle and never claims a
    relationship it had to travel a long way to find.
    """
    names, cache, out = index(root), {}, {}
    frontier = [(seed, seed) for seed in seeds]
    for _hop in range(HOPS):
        nxt: list = []
        for seed, rel in frontier:
            owners = out.setdefault(rel, [])
            if seed in owners:
                continue
            owners.append(seed)
            nxt += [(seed, child) for child in _named(root, rel, names, cache)]
        frontier = nxt
    return out
