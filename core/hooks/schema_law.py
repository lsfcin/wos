#!/usr/bin/env python3
# The law parser. Every Level 0 check reads core/SCHEMA.md through this module, and none
# of them restates it — a second copy of the law inside a checker is the exact drift the
# checks exist to catch.
#
# Extracted from type-gate.py 2026-07-30 when the second and third checks (naming and
# retired tokens) needed the same parse. See core/SCHEMA.md.
import re
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = WORKSPACE_ROOT / 'core/SCHEMA.md'

TRANSIENT_HEADING = '### The one exception: transient initiative docs'
RETIRED_HEADING = '### Retired tokens'

TYPE_ROW = re.compile(r'^\|\s*`([A-Z][A-Z0-9_-]*\.md)`\s*\|', re.M)
SCOPED_ROW = re.compile(r'^\|\s*`([A-Z][A-Z0-9_-]*\.md)`\s*\|([^|]*)\|', re.M)
RETIRED_ROW = re.compile(r'^\|\s*`([^`|]+)`\s*\|\s*`([^`|]+)`\s*\|', re.M)
BACKTICKED_MD = re.compile(r'`([^`]+\.md)`')

# Scope phrases the type table writes in prose, longest first so "repo root only" is not
# read as "root only".
SCOPES = (('repo root only', 'repo-root'), ('root only', 'root'))


def _law(schema_path: Path) -> str:
    """The whole law: the index plus every part, in name order.

    SCHEMA.md outgrew the line cap and split. Reading only the index would have silently
    dropped § Retired tokens — the parse would still succeed and return an empty dict, which
    is the failure shape this module exists to prevent: a check that passes because it can no
    longer see what it was checking.
    """
    parts = [schema_path] + sorted(schema_path.parent.glob(f'{schema_path.stem}-*.md'))
    return '\n\n'.join(p.read_text(encoding='utf-8') for p in parts if p.exists())


def _section(text: str, heading: str) -> str:
    """Body of one '### ...' section, up to the next heading of the same or higher level."""
    start = text.find(heading)
    if start < 0:
        return ''
    body = text[start + len(heading):]
    end = re.search(r'^#{1,3}\s', body, re.M)
    return body[:end.start()] if end else body


def load_law(schema_path: Path = SCHEMA) -> tuple[set, set]:
    """(allowed type names, exempt transient-doc names) read straight from the law."""
    text = _law(schema_path)
    allowed = set(TYPE_ROW.findall(text))
    exempt = {Path(name).name
              for name in BACKTICKED_MD.findall(_section(text, TRANSIENT_HEADING))}
    return allowed, exempt


def load_scopes(schema_path: Path = SCHEMA) -> dict:
    """Type name -> where it is allowed to live, for types whose row declares a scope.

    The scope is written in the table as prose ("(root only)") because that is where a
    reader meets it; parsing it here is what stops the rule from having a second home.
    """
    text = _law(schema_path)
    scopes = {}
    for name, question in SCOPED_ROW.findall(text):
        for phrase, scope in SCOPES:
            if phrase in question.lower():
                scopes[name] = scope
                break
    return scopes


def load_retired(schema_path: Path = SCHEMA) -> dict:
    """Retired token -> its replacement (§ Retired tokens)."""
    return dict(RETIRED_ROW.findall(_section(_law(schema_path), RETIRED_HEADING)))
