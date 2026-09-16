#!/usr/bin/env python3
# Level 0 list and vocabulary checks, parsed from core/SCHEMA.md. Zero-token, deterministic.
#
# Two assertions that make two recurring bugs catchable instead of re-discovered:
#   retired tokens  — a rename is finished only when its old spelling appears nowhere
#                     (core/SCHEMA.md § Retired tokens). This is what makes an
#                     incomplete rename visible at the generator instead of at the leaves.
#   duplicate item ids — a work item lives in exactly one list; a copy is a bug
#                     (ROADMAP.md header). This is v1 criterion 2, verified by scan.
import re
from pathlib import Path

from entropy_corpus import (enforcement_paths, is_generated_mirror,  # noqa: F401
                            tracked_files)

# A bracketed item id is an item ID only in item position: after the bullet and the optional
# checkbox, decoration allowed. Elsewhere in prose it is a reference to an item that lives
# somewhere else, which is exactly what a single list is supposed to produce.
ITEM_ID = re.compile(
    r'^\s*(?:[-*>]+\s*)*(?:\[[ xX]\]\s*)*\**`?\[([a-z0-9][a-z0-9-]+)\](?!\()', re.M)


# A URL is quoted, not written. Somebody else chose those words and no rename of ours can reach
# them, so a captured link whose item id happens to contain a retired token is not an unfinished
# rename — it is evidence. Found 2026-08-24 when an INBOX capture turned the suite red and the
# check's own advice was to delete the line, which would have deleted Lucas's capture.
_URL = re.compile(r'<?https?://\S+')


def retired_hits(files: list, retired: dict, exempt: set) -> list:
    """Every surviving occurrence of a retired token, in content or in a filename."""
    exempt = {path.resolve() for path in exempt}
    # Hyphen and underscore are boundaries, not word characters: a retired token survives just
    # as much inside `fable-loop-engineering.md` or `entropy_ledger.py` as standing alone, and
    # that compound form is how an unfinished rename hides at the leaves. `\w` covered the
    # hyphen and missed the underscore until 2026-09-14, blinding this to every identifier.
    patterns = {token: re.compile(rf'(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])')
                for token in retired}
    hits = []
    for path in files:
        if path.resolve() in exempt:
            continue
        try:
            text = _URL.sub(lambda m: ' ' * len(m.group()), path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError):
            continue
        for token, pattern in patterns.items():
            where = 'filename' if pattern.search(path.name) else None
            if not where and pattern.search(text):
                where = f'line {text[:pattern.search(text).start()].count(chr(10)) + 1}'
            if where:
                hits.append(f'{path}: retired token {token!r} survives ({where}).\n'
                            f'   Renamed to {retired[token]!r} — core/SCHEMA.md § Retired\n'
                            f'   tokens. If this line only *explains* the rename, delete it:\n'
                            f'   git holds the history.')
    return hits


def item_ids(path: Path) -> set:
    """Slugs this file claims as items — bracketed, in item position."""
    try:
        return set(ITEM_ID.findall(path.read_text(encoding='utf-8')))
    except (OSError, UnicodeDecodeError):
        return set()


def duplicate_ids(namespaces: dict) -> dict:
    """Item_id -> the namespaces claiming it, for every item_id claimed by more than one.

    Namespace, not file, is the unit. A goal file's achievement item_ids (`build-mvp`,
    `mvp-scope`, `first-class`) are private vocabulary repeated across sibling goals by
    design — six startapps all having a `build-mvp` is not six copies of one item. What
    criterion 2 forbids is the *same work item* tracked in two different lists, so the
    caller declares the namespaces and all goal files share one.
    """
    owners = {}
    for namespace, lists in namespaces.items():
        for path in lists:
            for item_id in item_ids(path):
                owners.setdefault(item_id, {})[namespace] = path
    return {item_id: claims for item_id, claims in owners.items() if len(claims) > 1}


STRIKETHROUGH = re.compile(r'~~[^~\n]+~~')
CODE_SPAN = re.compile(r'`[^`\n]*`')
DATED_REPORT = re.compile(
    r'\b(?:shipped|landed|deleted|removed|fixed|closed|merged|completed|resolved|retired)\b'
    r'[^.\n]{0,40}?\b20\d\d-\d\d-\d\d\b', re.I)
SETTLED = re.compile(r'\bSETTLED\b')
# Horizontal whitespace only: `\s` would swallow the preceding blank lines and report the
# finding against the top of the file instead of the line the reader has to go fix.
TICKED_ITEM = re.compile(
    r'^[ \t]*(?:[-*>]+[ \t]*)*(?:\d+[a-z]?\.[ \t]*)?(?:\[[xX]\]|✅)', re.M)
LIST_FILES = {'ROADMAP.md', 'GOALS.md', 'ISSUES.md'}
PLACEHOLDER = '← add'


def finished_work_hits(files: list, exempt: set) -> list:
    """Prose describing work that already landed — the corpse no link-checker can see.

    Completion is deletion (core/SCHEMA.md § No archive types): a list's length should
    measure remaining work. AGENTS.md bans strikethrough and SCHEMA bans the ticked item,
    both law with nothing enforcing them; the dated report is the general case.
    """
    exempt = {path.resolve() for path in exempt}
    hits = []
    for path in files:
        if path.suffix != '.md' or path.resolve() in exempt or is_generated_mirror(path):
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        # Strikethrough is read in PROSE only: inside a code span those four characters are DATA,
        # since a document about markdown must be able to write the spelling it converts. Position,
        # not presence — the test the vendor-directive check already applies to a model name.
        for label, match in (
            ('strikethrough', STRIKETHROUGH.search(CODE_SPAN.sub('', text))),
            ('a dated completion report', DATED_REPORT.search(text)),
            ('a SETTLED marker', SETTLED.search(text)),
            # A tick is a corpse only in a list; elsewhere the glyph is a legend marker,
            # which is how core/SCHEMA.md flags a required frontmatter field.
            ('a ticked item', TICKED_ITEM.search(text) if path.name in LIST_FILES else None),
        ):
            if not match:
                continue
            hits.append(f'{path}:{text[:match.start()].count(chr(10)) + 1}: {label} — '
                        f'prose describing finished work.\n'
                        f'   Cut it; git is the history (core/SCHEMA.md § No archive types).\n'
                        f'   Keep a line only if the next session needs it to *extend* the\n'
                        f'   work, and write that line as present-tense state.')
    return hits


def unanswered_placeholders(files: list, exempt: set) -> list:
    """A generator or a template asked a question, and nobody answered it.

    Split out of finished_work_hits 2026-08-15, which carried the remediation "cut it; git is the
    history". That advice is wrong here and acting on it is worse than ignoring it: the marker is a
    live request, not a record, and the generator writes it again on the next save. Three scaffolds
    emit the same glyph, and all three are answered at the source.

    Counted per file rather than per row, so the number means "files that lie to a reader"
    and matches the enforced-read unit: whoever opens this CONTEXT.md pays for all of them.
    """
    exempt = {path.resolve() for path in exempt}
    hits = []
    for path in files:
        if path.name != 'CONTEXT.md' or path.resolve() in exempt:
            continue
        if is_generated_mirror(path):
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        if (rows := text.count(PLACEHOLDER)) == 0:
            continue
        line = text[:text.index(PLACEHOLDER)].count(chr(10)) + 1
        hits.append(f'{path}:{line}: {rows} unanswered placeholder(s).\n'
                    f'   Answer at the source — the described file\'s first-line comment,\n'
                    f'   this file\'s own blurb, or the template field. Deleting the marker\n'
                    f'   only makes the generator write it again on the next save.')
    return hits


WIKI_LINK = re.compile(r'\[\[([a-z0-9][a-z0-9-]*)\]\]')


def goal_vocabulary(goals_dir: Path) -> set:
    """Every name a `[[name]]` is allowed to use: a goal file, or an item inside one.

    Decided 2026-07-30 (Lucas). Both halves are real pointers — `[[spec-driven-development]]`
    names the file, `[[prompt-dsl]]` names an item living inside `craft-flows.md` — and both
    are resolvable by scan, which is the only property a checker needs.
    """
    vocabulary = set()
    for goal in goals_dir.glob('*.md'):
        vocabulary.add(goal.stem)
        vocabulary |= item_ids(goal)
    return vocabulary


def wiki_link_hits(files: list, vocabulary: set, exempt: set) -> list:
    """Every `[[name]]` naming neither a goal file nor an item inside one."""
    exempt = {path.resolve() for path in exempt}
    hits = []
    for path in files:
        if path.suffix != '.md' or path.resolve() in exempt:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        for item_id in sorted(set(WIKI_LINK.findall(text)) - vocabulary):
            hits.append(f'{path}: [[{item_id}]] names no goal file and no item in one.\n'
                        f'   A `[[name]]` points at brain/goals/<name>.md or at a bracketed\n'
                        f'   item inside a goal file. Fix the item_id, or write the goal.')
    return hits
