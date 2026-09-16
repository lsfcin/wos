#!/usr/bin/env python3
# The `> key: value` header a document declares itself with, parsed once for everyone who reads it.
#
# Its own module rather than a function inside part_table.py, which renders: the header is now read
# by a generator AND by a check (core/hooks/entropy/entropy_fields.py, which asks whether the paths
# and names a field names exist). Two readers of one shape is the moment a second copy gets written,
# and a second copy of the law inside a checker is the exact drift the checkers exist to catch.
#
# The shape it parses: core/SCHEMA.md § What a part publishes about itself.
import re

# `> key: value` under the H1 — the shape CONTEXT.md already uses for `> spec:`, so no new parser
# and, unlike frontmatter, it renders where a person can see it.
FIELD = re.compile(r'^>\s*([a-z][a-z-]*):\s*(.+)$')


def header_fields(lines: list) -> dict:
    """The header block, as a dict. Pass the lines BELOW the description — usually `lines[2:]`.

    A WRAPPED FIELD IS ONE FIELD. A `>` line that is not itself a `key:` continues the field above
    it, because a value long enough to need a second line is exactly where this matters:
    core/SCHEMA.md names three enforcers, the third sits on the wrapped line, and it was
    dropped — so the index published two enforcers for a law that declares three, and the check
    below would have verified two of three while reporting the field clean.

    Continuation only counts AFTER a field has been seen: the `>` lines before the first one are the
    description, which hoist.md_blurb owns, and gluing those onto a value is how "Level 0 checks…"
    would have become part of `priority`.
    """
    facts, field = {}, None
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith('>'):
            break
        if match := FIELD.match(stripped):
            field = match.group(1)
            facts[field] = match.group(2).strip()
        elif field:
            facts[field] += ' ' + stripped.lstrip('>').strip()
    return facts
