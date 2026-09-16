# Text written for one file, made safe to show inside another file's table.
#
# Split out of workspace_scanner.py 2026-08-15 at the size gate, and the split is the
# design: hoisting is one operation with three parts — FIND the sentence, REBASE its links,
# BOUND its length — and those parts had drifted into two modules that each did some of it.
# A subdirectory row hoisted a blurb and got all three; a `.md` file row hoisted nothing and
# showed its H1 instead. One module, one rule: everything hoisted goes through hoist().
# The contract this serves: core/hooks/SPECS.md § The `CONTEXT.md` routing block.
import re
from pathlib import Path

# Two to three sentences, ruled by Lucas 2026-08-19: *"a 'Description' tão bem sucinta e muitas
# vezes não explica de que se trata o arquivo"*. It was 80, which cannot hold a question and its
# object, so the bound wrote the prose — thirty-odd part descriptions were shaped to fit it, and
# `core/tools/wos/session/reads` advertised itself as "which files a", cut mid-word.
#
# 360 is MEASURED, not chosen: the eight rewritten part descriptions run 304-347 characters at
# three sentences each. 240 was a guess at "two to three sentences" and truncated all eight, which
# would have made the bound write the prose a second time — the exact failure, one size up.
#
# Nothing measures a line's width since 2026-09-14 (limits.env § chars), so a long row costs only
# the characters it weighs, against a document cap no CONTEXT.md comes near. This can grow without
# restructuring the table into something else. Checked before changing it, not assumed.
DESC_LIMIT = 360
SCAFFOLD_BLURB = '← add description'
LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
# `> priority: essential`, `> goal: ...`, `> spec: none`, `> governs: ...`, `> blocked-by: ...`.
# A single lowercase word before a colon is a FIELD and never prose; a real sentence that happens
# to carry a colon ("The flow canvas: a Python WebSocket server…") has spaces before it and is kept.
FIELD_RE = re.compile(r'^>\s*[a-z][a-z0-9_-]*:')


def md_blurb(path: Path) -> str:
    """A `.md` file's `> ` blurb — the two or three sentences that say what the file IS.

    The `#` H1 is a *name*, not a description: `COMMENT_RE['.md']` captured it and stopped,
    so `tree.md` advertised "The Craft Tree" in every routing table while the sentence
    saying what it is sat one line below, unread. This line has always been read for a
    *child's* CONTEXT.md and for nothing else — same class as the missing `.sh` key in
    COMMENT_RE: the generator had the text and did not reach for it.

    It read line 2 and stopped until 2026-08-19, which is the other half of why descriptions
    said so little: a file whose blurb ran to three lines advertised its first line, and an
    author who wrote more got no credit for it. Now the whole `>` block is one description,
    stopping at the first FIELD line — `priority:`, `goal:`, `spec:`, `governs:`,
    `blocked-by:` are data the table has its own columns for, and reading them as prose is
    how "Level 0 checks…" would have become "Level 0 checks… priority: essential".
    """
    try:
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    except OSError:
        return ''
    if len(lines) < 2:
        return ''
    parts = []
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped.startswith('>') or FIELD_RE.match(stripped):
            break
        parts.append(re.sub(r'^>\s*', '', stripped).strip())
    blurb = ' '.join(p for p in parts if p).strip()
    return '' if blurb == SCAFFOLD_BLURB else blurb


def comment_paragraph(lines: list, start: int) -> str:
    """Consecutive `#` comment lines from `start`, joined — one paragraph, not one line.

    `md_blurb`'s twin for a code file or a shebang script: same rule, different comment
    syntax, so both live here rather than one drifting from the other. A description is two
    to three sentences (Lucas, 2026-08-19) and authors were already writing them; the
    generator read line one and stopped, so a sentence that wrapped got published cut in
    half. `core/tools/wos/session/reads` advertised itself as **"which files a"** — not a
    truncation, the literal end of its first comment line.

    Stops at the first non-comment line or bare `#`, which is the paragraph break every one
    of these headers already uses to separate what the file IS from why it exists. Without
    that stop this would hoist a whole rationale essay into a routing table.
    """
    parts = []
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped.startswith('#') or stripped == '#':
            break
        parts.append(re.sub(r'^#\s*', '', stripped).strip())
    return ' '.join(p for p in parts if p).strip()


def rebase_links(text: str, prefix: str) -> str:
    """Rewrite relative link targets so they resolve from the PARENT directory.

    A hoisted description travels verbatim into a table one directory up, where
    `[REFS.md](REFS.md)` silently names the *parent's* REFS.md — a different file, or none
    at all. Absolute paths, URLs and bare anchors already mean the same from either
    directory, so they are left alone.
    """
    # Underscored because `python_api` walks the whole AST, so a nested closure with a bare
    # name is advertised in the routing table as importable API. Real gap, open as ROADMAP.md
    # the `_` convention already carries the workaround.
    def _fix(match):
        target = match.group(2)
        if target.startswith(('/', '#')) or '://' in target or target.startswith('mailto:'):
            return match.group(0)
        return f'[{match.group(1)}]({prefix}{target})'
    return LINK_RE.sub(_fix, text)


def truncate_outside_links(text: str, limit: int) -> str:
    """Cut to `limit`, never mid-link and never mid-word, and say that you cut.

    Mid-link, because a half-copied `[REFS.md](RE` is a broken pointer and the
    pointer-integrity check would be right to fail on it. Mid-word, because `Level 0 checks
    t` reads as a typo rather than as a truncation — the reader cannot tell a cut from a
    mistake, which is half of why these descriptions read badly. The ellipsis is what makes
    the difference visible.
    """
    if len(text) <= limit:
        return text
    cut, at_link = limit, False
    for match in LINK_RE.finditer(text):
        if match.start() < cut < match.end():
            cut, at_link = match.start(), True
            break
    head = text[:cut]
    if not at_link and not text[cut].isspace():
        whole_words = head.rsplit(' ', 1)[0]
        if whole_words:
            head = whole_words
    return head.rstrip().rstrip('.,;:—-') + '…'


def hoist(text: str, prefix: str) -> str:
    """Rebase and bound in one call — the only way hoisted text enters a table.

    Both parts always, because either one alone is a bug that shipped: rebasing without
    bounding lets one file's paragraph set the width of somebody else's table, and bounding
    without rebasing leaves pointers aimed at the wrong directory.

    A code file's first-line comment does NOT come through here. It was authored as a
    one-liner, for this table, in this directory — there is nothing to rebase and cutting it
    would lose text that nothing else carries.
    """
    return truncate_outside_links(rebase_links(text, prefix), DESC_LIMIT)
