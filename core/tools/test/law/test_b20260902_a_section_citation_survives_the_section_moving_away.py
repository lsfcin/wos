# T0 a `<file>.md § <Section>` citation names a section that is really there.
#
# b20260902-a-section-citation-survives-the-section-moving-away regression. core/SPECS.md requires
# a section be cited BY NAME because a number ages silently — and the named form ages silently too,
# in the one operation this workspace has now blessed. Sharding SETUP.md moved 17 of its 21 steps
# into siblings; nine tracked files went on citing `SETUP.md § <step>`, and the suite was green
# throughout, because test_pointer_integrity.py resolves the `](path)` half and a link whose FILE
# exists and whose SECTION does not reads as healthy. They were found by grep, by hand.
#
# IT PREDATES THE PART. `SETUP.md § Workspace path` had pointed at a section deleted 2026-08-29,
# and `SETUP.md §12` — a numbered citation core/SPECS.md forbids outright — sat in a tool's
# first-line comment where the routing generator republished it. Renaming one heading in
# `.zcode/SPECS.md` killed two more citations on 2026-09-04, while this check was being written.
#
# WHY HERE AND NOT IN citation-gate.py, which owns the other half of the same rule (a number is
# not a citable identifier — point at the section that owns it): that file reached the 200-line
# cap, and the law says a file over the cap is CUT, never squeezed. The cut put this beside
# test_pointer_integrity.py instead, which is the honest boundary — that check resolves the `](path)`
# half of a pointer and this one resolves the `§` half, and pre-commit runs both.
#
# NOT A RATCHET. The corpus was swept to zero when this landed, so every tracked .md is checked
# rather than only what a commit adds.
import re
import subprocess
from pathlib import Path

import file_law
from conftest import WORKSPACE_ROOT

CITATION = re.compile(r'(?:\[[^\]]*\]\(([^)\s]+\.md)\)|`([^`\s]+\.md)`|(?<![\w/])([\w./-]+\.md))'
                      r'[`\s]*§\s*(.*)')
# A heading, or a bold label at the head of a line. This corpus names sub-rules in bold —
# `**Push policy**` in code/SPECS-git.md is cited from the always-loaded AGENTS.md — and promoting
# every one of them to a heading would grow the .md corpus to satisfy a checker, which is backwards.
NAMES = re.compile(r'^#{2,6}\s+(.*)$|^\s*(?:[-*]\s*)?\*\*(.+?)\*\*', re.MULTILINE)
# Where the name stops and the sentence carrying it resumes: `—` and `(` open an aside, the rest
# close a clause.
SECTION_END = re.compile(r'[)|`,;:]|\s—|\s\(|\.\s|\.$')
_ARTICLE = re.compile(r'^(the|a|an) ')


def _norm(text: str) -> str:
    return _ARTICLE.sub('', re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', text.lower())).strip())


# A heading names itself and then explains itself: `### AD-16 — Doubt is not charged`,
# `## Placement: level × read-frequency`. A citation is written against the naming half, so the
# half before the first separator is a section name in its own right.
_LEAD = re.compile(r'\s—|:|\s\(')


def _sections(path: Path) -> set:
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return set()
    found = set()
    for pair in NAMES.findall(text):
        for raw in pair:
            if not (whole := _norm(raw)):
                continue
            found.add(whole)
            if (cut := _LEAD.search(raw)) and len(lead := _norm(raw[:cut.start()])) >= 3:
                found.add(lead)
    return found


def section_hits(files: list, root: Path) -> list:
    """Citations whose target file exists and whose named section does not.

    THE CITATION IS JOINED WITH THE LINE BELOW IT before the name is cut out. This corpus wraps at
    column 120, so a citation lands across two lines often enough that a single-line parser reads
    half the names in the tree as the bare word `The`.

    A citation is matched by NAME PREFIX in both directions: `§ AD-16 band 1` points inside
    `### AD-16 — Doubt is not charged when asserting`, and `§ Placement` points at
    `## Placement: level × read-frequency`. Both are honest pointers and neither is an exact match.
    """
    hits = []
    for path in files:
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        # A generated block is not the author's to fix, and core/SCHEMA.md forbids hand-editing
        # one: ISSUES.md's verify block QUOTES a red suite log, so a traceback that named a since
        # renamed section was reported as a citation nobody could correct (2026-09-11).
        owned = file_law.generated_spans(text)
        for number, line in enumerate(lines, 1):
            if any(start <= number <= end for start, end in owned):
                continue
            if not (match := CITATION.search(line)):
                continue
            target = match.group(1) or match.group(2) or match.group(3)
            tail = f'{match.group(4)} {lines[number] if number < len(lines) else ""}'.strip()
            stop = SECTION_END.search(tail)
            name = ' '.join((tail[:stop.start()] if stop else tail).split()[:7])
            if not name or '<' in name:
                continue  # `SETUP.md § <name>` is a template, not a pointer
            cited = path.parent / target
            cited = cited if cited.exists() else root / target
            if not cited.exists():
                continue  # a missing FILE is test_pointer_integrity.py's finding, not this one
            if any(n.startswith(_norm(name)) or _norm(name).startswith(n) for n in _sections(cited)):
                continue
            hits.append(
                f'{path.relative_to(root)}:{number}: cites {target} § {name!r}, '
                f'which has no such section.\n'
                f'   A section is renamed or moves and the citation does not follow — the named\n'
                f'   form ages as silently as the numbered one. Cite a heading or a **bold label**\n'
                f'   that is really there, or point at the file alone.')
    return hits


def _tracked_md(root: Path) -> list:
    out = subprocess.run(['git', '-C', str(root), 'ls-files', '*.md'],
                         capture_output=True, text=True, encoding='utf-8').stdout
    return [root / line for line in out.splitlines() if (root / line).is_file()]


def test_every_section_citation_names_a_section_that_exists():
    hits = section_hits(_tracked_md(WORKSPACE_ROOT), WORKSPACE_ROOT)
    assert not hits, 'Citations naming no section:\n' + '\n'.join(hits)


def _fixture(tmp_path, cited_body, citing_body):
    (tmp_path / 'SPECS.md').write_text(cited_body, encoding='utf-8', newline='\n')
    (tmp_path / 'CONTEXT.md').write_text(citing_body, encoding='utf-8', newline='\n')
    return section_hits([tmp_path / 'CONTEXT.md'], tmp_path)


def test_a_citation_of_a_section_that_moved_away_is_a_finding(tmp_path):
    hits = _fixture(tmp_path, '## Git Flow\n', 'see `SPECS.md` § Workspace path for the rule.\n')
    assert len(hits) == 1
    assert 'Workspace path' in hits[0]


def test_a_bold_label_counts_as_a_section(tmp_path):
    """code/SPECS-git.md names its sub-rules in bold and AGENTS.md cites one of them."""
    assert _fixture(tmp_path, '## Git Flow\n\n**Push policy** (moved here).\n',
                    'the push policy: [`SPECS.md`](SPECS.md) § Push policy.\n') == []


def test_a_pointer_inside_a_section_still_resolves(tmp_path):
    """`§ AD-16 band 1` names a place inside AD-16, not a heading of its own."""
    assert _fixture(tmp_path, '### AD-16 — Doubt is not charged when asserting\n',
                    'the rule is `SPECS.md` § AD-16 band 1, which says so.\n') == []


def test_a_citation_wrapped_at_the_column_cap_is_read_whole(tmp_path):
    """Without joining the next line the name reads as `The`, and half the corpus goes red."""
    assert _fixture(tmp_path, '## The four disposal routes\n',
                    'route it via `SPECS.md` § The\nfour disposal routes, never by hand.\n') == []


def test_a_template_placeholder_is_not_a_pointer(tmp_path):
    assert _fixture(tmp_path, '## Git Flow\n', 'nine files cite `SPECS.md` § <name>, and\n') == []
