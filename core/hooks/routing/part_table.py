# A cut type's index table: what each TYPE-<name>.md publishes, rendered so the index answers
# "open or skip" without anything being opened.
#
# Its own module rather than a third job for workspace_scanner.py, whose sentence is *directory*
# discovery and assembly — a cut index is not a directory, and the scanner was two lines from
# the cap. render_table came with it: both builders drop a column that is empty on every row, and
# that rule was about to exist twice.
#
# The law it serves: core/SCHEMA.md § What a part publishes about itself.
import re
from pathlib import Path

from header import header_fields
from hoist import hoist, md_blurb

# An open item is a NUMBERED one — `1.`, `10b.` — which is the shape a roadmap actually uses and
# the same one entropy_list.TICKED_ITEM recognises. Counting `[name]` instead would have read
# most fronts as empty: the bracketed id is optional and most items carry prose alone.
#
# THE MARK IS PART OF THE SHAPE, and every pattern in this file requires it for one reason: a
# numbered line in prose looks exactly like an item, and a marked one does not. Without it these
# matched `1. **Fold**` — a nested sub-step inside one list item — and the two numbered rules
# inside a legibility front's opening paragraph, so the index advertised 6 open where 4 were and 8
# where 6 were (corrected 2026-08-19). ROADMAP.md § How to read this requires the mark on every item.
ITEM = re.compile(r'^\d+[a-z]?\.[ \t]*[🔴🟡🟢]', re.M)
# The marker counts only in ITEM position. A bare substring count read 13 where the list holds
# 12, because one part has a sentence ABOUT the count with the marker inside it — the same
# confusion between a mark and a mention that made the hand-kept count wrong four times.
LUCAS_ITEM = re.compile(r'^[ \t]*\d+[a-z]?\.[ \t]*🔴', re.M)
# The optional id, when an item declares one. Narrower than entropy_list's copy on purpose: an
# index only needs to NAME items, never to decide whether two lists claim the same one.
NAME = re.compile(r'^\s*(?:[-*>]+\s*)*(?:\d+[a-z]?\.\s*)?(?:\[[ xX]\]\s*)*[^\S\n]*'
                  r'(?:[🔴🟡🟢]\s*)?\**`?\[([a-z0-9][a-z0-9-]+)\](?!\()', re.M)
EMPTY_CELL = {'—', '-', ''}
# The headline an item already carries: the bold lead-in right after its number and mark. This is
# the column the index was missing — `Items` reads the optional `[name]` id, which almost no item
# declares, so it rendered empty for every part but one while the generator was ALREADY parsing
# the item text to produce Open and Needs Lucas. It read what would let a reader skip a part and
# threw it away. Ruled 2026-08-19 (Lucas), after a session opened all seven parts to answer one
# question. Bold is not decoration here: every item in the family opens with it, so it is an
# authored one-line summary and the generator never has to write prose.
#
# Carries the mark requirement above, plus a start at column 0 — the same separation for the same
# reason.
ITEM_HEADLINE = re.compile(r'^(\d+[a-z]?)\.[ \t]*([🔴🟡🟢])[ \t]*\*\*(.+?)\*\*', re.M | re.S)

# Column order is reading order: what it is, then how much is live, then what stops you.
PART_COLUMNS = (('Part', None), ('Description', 'description'), ('Prio', 'priority'),
                 ('Open', 'open'), ('Needs Lucas', 'needs-lucas'), ('Answers', 'answers'),
                 ('Governs', 'governs'), ('Feature', 'feature'),
                 ('Enforced by', 'enforced-by'), ('Blocked by', 'blocked-by'),
                 ('Items', 'items'))


def part_facts(path: Path) -> dict:
    """What a part publishes about itself, plus what can be counted instead of published.

    The declared half is the `> key: value` lines; the derived half is everything countable, by
    core/SCHEMA.md § Everything countable is counted, never declared.
    """
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return {}
    lines = text.splitlines()
    facts = {'lines': str(len(lines))}
    facts.update(header_fields(lines[2:]))
    # The three counts are ROADMAP-only, as core/SCHEMA.md's field table says. Deriving them for
    # every type read a SPECS part as having 13 open items, because a numbered list in prose looks
    # exactly like a numbered item — a count that is meaningless is worse than no column.
    if path.stem.split('-')[0] != 'ROADMAP':
        return facts
    if items := ITEM.findall(text):
        facts['open'] = str(len(items))
    if names := NAME.findall(text):
        facts['items'] = ' '.join(f'`{name}`' for name in names)
    if red := LUCAS_ITEM.findall(text):
        facts['needs-lucas'] = str(len(red))
    return facts


def render_table(headers: tuple, rows: list, always: tuple) -> str:
    """A markdown table minus every column that is EMPTY_CELL on every row.

    Measured 2026-07-30: 773 of 1242 rows workspace-wide carried an em-dash Interface, paying table
    width in every read to say "nothing here". A column that says nothing for every row is not
    information about the thing it describes.
    """
    if not rows:
        return ''
    keep = [i for i in range(len(headers))
            if i in always or any(r[i] not in EMPTY_CELL for r in rows)]
    out = ['| ' + ' | '.join(headers[i] for i in keep) + ' |',
           '|' + '|'.join('-' * (len(headers[i]) + 2) for i in keep) + '|']
    out += ['| ' + ' | '.join(r[i] for i in keep) + ' |' for r in rows]
    return '\n'.join(out)


def parts_of(index: Path) -> list:
    """Every `TYPE-<name>.md` beside `TYPE.md`, in name order. Empty when the type has not split."""
    return sorted(index.parent.glob(f'{index.stem}-*{index.suffix}'))


def index_for(path: Path) -> Path | None:
    """The index a `.md` belongs to, when it is part of a cut type — else None.

    Answers for a part AND for the index itself, so editing either one re-syncs the same table.
    A type with parts but no index (`code/` holds ROADMAP-verify.md and ROADMAP-spec-drive.md
    and no ROADMAP.md) returns None rather than inventing a file: an index nobody wrote is a
    decision, not a side effect of saving.
    """
    if path.suffix != '.md' or not path.stem.split('-')[0].isupper():
        return None
    index = path.parent / f'{path.stem.split("-")[0]}{path.suffix}'
    return index if index.exists() and parts_of(index) else None


def item_headlines(path: Path) -> list:
    """`(mark, headline)` per open item — what the index needs so a part can be skipped.

    ROADMAP-only for the same reason the counts are, and headlines for a prose list would be noise
    presented as an index. Whitespace is collapsed: a headline may wrap across lines in the source.
    """
    if path.stem.split('-')[0] != 'ROADMAP':
        return []
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return []
    out = []
    for _number, mark, headline in ITEM_HEADLINE.findall(text):
        out.append((mark or '·', ' '.join(headline.split())))
    return out


def build_open_items(parts: list) -> str:
    """The open items of every part, one line each, under the table that names the parts.

    A list rather than a table cell: fourteen headlines in one cell is not something anybody reads.
    """
    blocks = []
    for part in parts:
        rows = item_headlines(part)
        if not rows:
            continue
        lines = [f'**[`{part.name}`]({part.name})**', '']
        lines += [f'- {mark} {headline}' for mark, headline in rows]
        blocks.append('\n'.join(lines))
    if not blocks:
        return ''
    return ('### What is open, per part\n\n'
            '*Generated from each part\'s item headlines — open a part only when one of these '
            'is the thing you came for.*\n\n' + '\n\n'.join(blocks))


def build_part_rows(parts: list) -> str:
    """One row per part. Which columns survive is what tells a reader which type this index is:
    a cut ROADMAP keeps Prio/Open/Needs Lucas, a cut SPECS keeps Governs/Enforced by, and
    neither builder had to be told which one it was looking at."""
    rows = []
    for part in parts:
        facts = part_facts(part)
        facts['description'] = hoist(md_blurb(part), '') or '← add description'
        rows.append([f'[`{part.name}`]({part.name})']
                    + [facts.get(key, '—') or '—' for _, key in PART_COLUMNS[1:]])
    headers = tuple(name for name, _ in PART_COLUMNS)
    table = render_table(headers, rows, (0, 1))
    items = build_open_items(parts)
    return f'{table}\n\n{items}' if items else table
