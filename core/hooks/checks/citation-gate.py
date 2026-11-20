#!/usr/bin/env python3
# Level 0: a roadmap item number is not a citable identifier outside the roadmap family.
#
# Why this is a check and not a paragraph. Completion is deletion in this workspace, so the
# day an item closes, every `Front 4.1` pointing at it becomes a pointer to nothing — or
# worse, to whatever item later takes that number. § How to read this has asked for durable
# pointers since 2026-08-15 and the corpus still reached 91 numbered citations across ~50
# files, including two pointing at Fronts 2 and 6, which have never existed. The rule was
# INDUCED; this is the ENFORCED half.
#
# It lives here rather than in entropy/ because the crowding gate said so: entropy/ was already
# at eight code files and the ceiling refused a ninth. That was the right refusal — the check
# belongs beside type-gate.py, which is the other Level 0 vocabulary gate, and being here made
# it a commit-time BLOCK instead of one more line in a report nobody is obliged to read.
#
# Not a ceiling, unlike type-gate.py: the corpus was swept to zero on 2026-08-16, so every
# staged file is checked rather than only the ones a commit adds. A ceiling is what you use
# when you inherit violations, and there are none left to inherit.
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402

# `Front 9`, `Front 4.1`, `Front 10.1b` — the bare form is the larger half of the corpus and
# the one a decimals-only pattern misses. Hyphen and word boundaries both count, so
# `Front 4`-in-a-compound is caught the same way a retired token is.
CITATION = re.compile(r'(?<!\w)Front \d+(?:\.\d+[a-z]?)?(?!\w)')

# The pre-2026-08-16 spelling. This check owns the rename rather than
# core/SCHEMA.md § Retired tokens, because that table matches a bare word and
# `frente` is an
# ordinary Portuguese noun — it means a work front, and `branches/casinhas/CONTEXT.md` uses it
# that way in a table header about construction. A retired-token row would have failed on
# honest Portuguese prose on the day it was written, which SCHEMA.md's own note says trains
# people to ignore a check. Matching the *citation shape* instead keeps the word legal and the
# pointer illegal. Unlike CITATION this is a hit EVERYWHERE, roadmaps included: a rename is
# finished only when the old spelling appears nowhere.
RETIRED_SPELLING = re.compile(r'(?<!\w)Frente \d+(?:\.\d+[a-z]?)?(?!\w)')

# The list family may number its own items: that is what numbering is FOR, and a commit
# message may cite one too, because git keeps commits forever. Matched on filename, not path,
# so a `ROADMAP-<name>.md` in any repo under the workspace is covered without enumeration.
LIST_NAMES = re.compile(r'^ROADMAP(-[a-z0-9-]+)?\.md$')

# THE SECOND DEAD POINTER, the same defect wearing numbers. `core/hooks/limits.env` owns every
# numeric limit and `file_law.py` is its only parser, because a checker that restates the law is
# the drift the checkers exist to catch. Prose was never held to that: on 2026-09-12 eight authored
# files still named the line law one ruling behind, six days after it moved. Ruled by Lucas that
# day, scope this law only. THE FIX IS NEVER TO CORRECT THE COPY — delete it and name the owner,
# the way `code/CONTEXT.md` does. A corrected copy rots at the next ruling; a pointer cannot.
#
# NOT A VALUE COMPARISON, deliberately: asking whether a number still MATCHES goes quiet the day
# the law moves off a value a stale line happens to share, which is the day the check is needed.
# The shape is banned, exactly as `Front 4.1` is whether or not that item exists.
#
# `cap` is NOT a law word. limits.env says "a WARN asks for a look, a BLOCK stops the commit", and
# `cap` is the general word: it pulled in four numeric laws that are not this one, which is a
# roadmap finding rather than something to smuggle in here. `LOC` is the SUBJECT and never the law
# word — `56 LOC now` measures, `200 LOC | Hard block` copies.
_WORD = r'(?:warns?|warning|blocks?|aviso)'
# `block of 16,000 tokens` composes; `block at 250 lines` limits. The preposition is the whole
# difference, so the window joining a law word to a count may not contain `of`.
_NEAR = r'(?:(?!\bof\b).){0,24}?'
_SIZED = r'\d{2,6}\s*[-–—]?\s*(?:lines?|linhas?|LOC|files?|arquivos?|cols?|columns?|chars?|tokens?)'
_BARE = r'\d{2,6}'
# Two shapes, because prose writes the law both ways: `150 LOC | Hard block` names what it measures,
# and `warn 150, block 200` lets the law word do that job. The second is TOUCHING only, which is
# what separates `block 200` from `block ran 48 lines`.
LIMIT_CLAIM = re.compile(
    rf'(?i)(?<!\w)(?:{_WORD}\W{_NEAR}{_SIZED}|{_SIZED}{_NEAR}\W{_WORD}'
    rf'|{_WORD}\s*[:=]?\s*{_BARE}|{_BARE}\s*{_WORD})(?!\w)')
# A generated block is authored by nobody: its rows come from first-line comments, so a finding
# inside one names a file that cannot be edited to clear it.
GENERATED_BLOCK = re.compile(r'(?m)^<!-- \w+:start -->$.*?^<!-- \w+:end -->$', re.DOTALL)
# The law's own file, its only parser, and the two checks that apply it may all name a number.
LIMIT_OWNERS = ('core/hooks/limits.env', 'core/hooks/file_law.py',
                'core/hooks/checks/line_counts.py', 'core/hooks/checks/size-gate.py')

# The two documents that state the rule, the report that quotes findings, and this checker
# with its tests all have to be able to NAME the shape they forbid. Nothing else may.
# core/hooks/SPECS.md joined this list by failing the check the moment it documented the gate,
# which is the same argument core/SCHEMA.md was already on it for.
ENFORCEMENT = ('core/SCHEMA.md', 'core/hooks/SPECS.md', 'ISSUES.md')
# Derived from __file__, never spelled out: a hard-coded path here stops exempting this
# checker the moment the hooks directory moves, which is what happened to the sibling
# exemption in entropy_corpus.py when the hooks moved into core/ (2026-07-31).
_CHECKER = 'citation-gate.py'
_CHECKER_TESTS = 'core/tools/test/**/test_citation_gate.py*'

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


def citation_exempt_paths(root: Path) -> set:
    """Files allowed to contain a Front number: the law, the report, and this check itself.

    A part of an exempt file inherits the exemption, derived rather than listed. Enumerating
    them would fail the first time one of these documents outgrew the line cap, which is exactly
    what happened to `core/hooks/SPECS.md` — its § Git pre-commit section, which has to name the
    shape this gate forbids, moved into a sibling and stopped being exempt on arrival.
    """
    named = [root / name for name in ENFORCEMENT]
    return ({p.resolve() for p in named}
            | {s.resolve() for p in named for s in p.parent.glob(f'{p.stem}-*{p.suffix}')}
            | {Path(__file__).resolve().parent / _CHECKER}
            | {p.resolve() for p in root.glob(_CHECKER_TESTS)})


def staged_files() -> list:
    """Every file this commit touches, added or modified — not only what it adds."""
    out = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=d'],
        capture_output=True, text=True, encoding='utf-8').stdout
    return [WORKSPACE_ROOT / line for line in out.splitlines()]


def citation_hits(files: list, exempt: set) -> list:
    """Item numbers cited outside a roadmap, plus the retired spelling cited anywhere."""
    exempt = {path.resolve() for path in exempt}
    hits = []
    for path in files:
        if path.resolve() in exempt:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        if match := RETIRED_SPELLING.search(text):
            line = text[:match.start()].count('\n') + 1
            hits.append(
                f'{path}: cites {match.group(0)!r} (line {line}).\n'
                f'   `Frente` was renamed to `Front` 2026-08-16 —\n'
                f'   core/SCHEMA.md § Vocabulary.\n'
                f'   Rename it, then apply the rule below: a number is legal only in ROADMAP*.md.')
            continue
        if LIST_NAMES.match(path.name):
            continue
        if match := CITATION.search(text):
            line = text[:match.start()].count('\n') + 1
            hits.append(
                f'{path}: cites {match.group(0)!r} (line {line}).\n'
                f'   A closed item is deleted, so its number becomes a dead pointer.\n'
                f'   Point at the SPECS.md or SCHEMA.md section that owns the rule, or\n'
                f'   name the concept. Numbering is legal only inside ROADMAP*.md.')
    return hits


def limit_exempt_paths(root: Path) -> set:
    """Everything allowed to write a number the numeric law owns: the law, its parser, the checks
    that apply it, and the documents that state the rule — which are already the citation set."""
    return citation_exempt_paths(root) | {(root / name).resolve() for name in LIMIT_OWNERS}


def limit_hits(files: list, exempt: set) -> list:
    """Lines restating a number `core/hooks/limits.env` owns, one hit per file."""
    exempt = {path.resolve() for path in exempt}
    hits = []
    for path in files:
        if path.resolve() in exempt or path.suffix not in ('.md', '.txt'):
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        text = GENERATED_BLOCK.sub(lambda m: '\n' * m.group(0).count('\n'), text)
        for number, line in enumerate(text.splitlines(), 1):
            if LIMIT_CLAIM.search(line):
                hits.append(
                    f'{path}: states a size limit in prose (line {number}).\n'
                    f'   core/hooks/limits.env owns every numeric limit here, and a copy of one\n'
                    f'   rots the day the law moves — eight files did, for six days.\n'
                    f'   Name the owner instead of the number, the way code/CONTEXT.md does.')
                break
    return hits


def main() -> int:
    if not feature_law.is_enabled('citation-gate'):
        return 0  # switched off: a disabled gate does not block, and does not pretend it ran
    if not (WORKSPACE_ROOT / 'core/SCHEMA.md').exists():
        return 0  # not the workspace repo; nothing to enforce against
    staged = [p for p in staged_files() if p.exists()]
    hits = (citation_hits(staged, citation_exempt_paths(WORKSPACE_ROOT))
            + limit_hits(staged, limit_exempt_paths(WORKSPACE_ROOT)))
    if hits:
        print('⛔ citation gate:')
        for hit in hits:
            print(f'   {hit}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
