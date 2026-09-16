#!/usr/bin/env python3
# A generated block inside an authored file: found by its markers, rewritten in place.
#
# Extracted from context_synchronizer.py 2026-08-20, when ISSUES.md gained a second and a third
# generated block (core/SCHEMA.md § ISSUES.md hand-written vs generated). That function was
# hardcoded to the routing markers AND standardized the block to end-of-file — right for a routing
# table, which is always last, and wrong for a block with hand-written text below it. The two
# behaviours are now one function and a flag, so the marker convention has one implementation
# instead of one per generator.


import sys
from pathlib import Path


def markers(name: str) -> tuple:
    """The two sentinels of a named block. One spelling, so no caller invents a second."""
    return f'<!-- {name}:start -->', f'<!-- {name}:end -->'


def line_pos(text: str, sentinel: str) -> int:
    """Position of `sentinel` only when it stands on its own line, else -1.

    A marker quoted inside prose — a SPECS.md explaining the convention, this file's own header —
    must not be mistaken for the real one, which is why the whole line has to match.
    """
    for prefix in ('\n', ''):
        idx = text.find(prefix + sentinel)
        if idx == -1:
            continue
        pos = idx + len(prefix)
        after = pos + len(sentinel)
        if after >= len(text) or text[after] in ('\n', '\r'):
            return pos
    return -1


def replace_block(text: str, body: str, start: str, end: str, at_end: bool = False) -> str:
    """Swap the block delimited by `start`/`end` for `body`; append it when there is none yet.

    `body` carries its own markers — the caller renders one string, so nothing here has to know
    what a routing table or an entropy report looks like.

    `at_end=True` lifts the block to the end of the file, which is the routing table's rule: it is
    an index, and an index that drifts into the middle of a document stops being one. Everything
    else is rewritten where it already sits, because a file may hold several blocks in an order its
    author chose.
    """
    si, ei = line_pos(text, start), line_pos(text, end)
    if si == -1 or ei == -1:
        return text.rstrip('\n') + '\n\n' + body
    before = text[:si].rstrip('\n')
    after = text[ei + len(end):].lstrip('\n')
    if at_end:
        kept = '\n\n'.join(p for p in (before, after) if p)
        return kept.rstrip('\n') + '\n\n' + body
    head = before + '\n\n' if before else ''
    tail = '\n\n' + after if after else '\n'
    return head + body.rstrip('\n') + tail


def main() -> int:
    """`blocks.py <file> <name> < body` — the boundary for shell generators.

    A block written from bash would otherwise be a second implementation of the marker convention,
    in a language with no way to find a sentinel that stands on its own line. The body arrives on
    stdin without markers; this wraps it, so a caller cannot spell one of them differently.
    """
    if len(sys.argv) != 3:
        print('usage: blocks.py <file> <block-name> < body', file=sys.stderr)
        return 64
    target, name = Path(sys.argv[1]), sys.argv[2]
    start, end = markers(name)
    body = '\n'.join((start, sys.stdin.read().strip(), end))
    text = target.read_text(encoding='utf-8') if target.exists() else ''
    target.write_text(replace_block(text, body, start, end), encoding='utf-8', newline='\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
