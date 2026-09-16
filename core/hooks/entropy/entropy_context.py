#!/usr/bin/env python3
# Level 0 CONTEXT.md rules, parsed from core/SCHEMA.md. Zero-token, deterministic.
#
# Split out of type-gate.py 2026-07-30 when the goal-link check joined the inventory
# check: type-gate.py is the ratchet that decides WHEN to run a check, these are the
# rules about what a CONTEXT.md must and must not say.
import re
import sys
from pathlib import Path

from entropy_corpus import is_generated_mirror

# The routing generator is one directory over, and it is deliberately the source of truth for
# what "describable" means — see check_description below.
_HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HOOKS / 'routing'))

import feature_law  # noqa: E402
from file_law import EXAMPLE_COMMENT, is_generated_artifact, is_vendored  # noqa: E402
from hoist import DESC_LIMIT  # noqa: E402
from workspace_meta import PLACEHOLDER, file_description  # noqa: E402
from workspace_scanner import is_scanned  # noqa: E402

WORKSPACE_ROOT = _HOOKS.parents[1]

# core/SCHEMA.md § Boundaries where types nearly touch: CONTEXT never hand-lists files.
ROUTING_START = '<!-- routing:start -->'
ROUTING_END = '<!-- routing:end -->'
# The first cell of a truncated row, so the finding names the file whose description to shorten
# rather than the row it was rendered into.
TRUNCATED_ROW = re.compile(r'^\|\s*\[`([^`]+)`\]')
TREE_GLYPH = re.compile(r'[├└│]──')
PATH_BULLET = re.compile(r'^\s*[-*]\s+[`\[]+([\w./-]+\.\w+|[\w./-]+/)', re.M)
# The same list, drawn as a table. Anchored at the FIRST cell, because a path named in a
# later cell is a pointer inside a description, not the thing the row is about — that is
# how `| Area | Covers |` and `| Runtime | How to spawn |` stay legitimate CONTEXT content.
PATH_TABLE_ROW = re.compile(r'^\|\s*[`\[]+([\w./-]+\.\w+|[\w./-]+/)', re.M)
INVENTORY_HEADING = re.compile(
    r'^#+\s+.*\b(file map|repository shape|project layout|file list|directory structure|'
    r'folder structure|files?\s+in\s+this|inventory)\b', re.I)

GOAL_LINE = re.compile(r'^>\s*goal:\s*(none|\[([^\]]+)\]\(([^)]+)\))\s*$')


def check_inventory(path: Path) -> str | None:
    """CONTEXT.md must not hand-list files above its generated routing block."""
    if path.name != 'CONTEXT.md':
        return None
    text = path.read_text(encoding='utf-8')
    head = text.split(ROUTING_START, 1)[0]
    reasons = []
    heading = next((l for l in head.splitlines() if INVENTORY_HEADING.match(l)), None)
    if heading:
        reasons.append(f'inventory heading {heading.strip()!r}')
    if TREE_GLYPH.search(head):
        reasons.append('an ASCII directory tree')
    # A row counts only when the path REALLY EXISTS beside the CONTEXT.md. Documenting a
    # naming convention with globs (`grav_cam2_gXX_sq.png` in a paper's images/) is
    # legitimate CONTEXT content — describing the directory, which is its whole job. Only
    # a list of actual files duplicates the generated block.
    #
    # A table is the same inventory as a bullet list and was invisible to this check for
    # months: brain/CONTEXT.md, the workspace's most-read file, carried a hand-written
    # `| File / Folder | Role |` above its generated block saying the same thing — the
    # defect this check was written for, in the file it was written to protect. Bullets and
    # rows are counted TOGETHER: splitting one list across both shapes is still one list.
    listed = [m for m in (PATH_BULLET.findall(head) + PATH_TABLE_ROW.findall(head))
              if (path.parent / m).exists()]
    if len(listed) >= 3:
        reasons.append(f'{len(listed)} bullets/table rows listing real files')
    if not reasons:
        return None
    return (f"{path}: hand-written file inventory ({', '.join(reasons)}).\n"
            f"   The generated routing block owns inventory (core/SCHEMA.md § Boundaries\n"
            f"   where types nearly touch). Describe the directory; do not list it.")


# A constraint reads as an obligation, which is the SPECS question. Answering it in a
# CONTEXT.md head charges every session in the subtree, because this is the only
# enforced-read type — core/SCHEMA.md § Placement, the REDIRECT cell.
CONSTRAINT = re.compile(
    r'\b(?:must|never|always|required|forbidden|blocked|do not|don\'t)\b', re.I)


def context_head(path: Path) -> str:
    """The curated prose above the generated routing block — the part a human wrote."""
    try:
        return path.read_text(encoding='utf-8').split(ROUTING_START, 1)[0]
    except (OSError, UnicodeDecodeError):
        return ''


def check_misplaced_answer(path: Path, head_warn: int) -> str | None:
    """A contract trapped in an over-size CONTEXT.md head.

    core/SCHEMA.md says each type answers exactly one question, but nothing verified that a
    file answers only *its own*. Size alone is a weak signal — a long head may be honest
    navigation — so this fires only where an over-size head is also *shaped* like a
    contract. The sibling's existence decides whether the fix is a move or a create.
    """
    if not feature_law.is_enabled('context-head-budget'):
        return None
    if path.name != 'CONTEXT.md' or is_generated_mirror(path):
        return None
    head = context_head(path)
    tokens, modals = len(head) // 4, len(CONSTRAINT.findall(head))
    if tokens <= head_warn or not modals:
        return None
    sibling = path.parent / 'SPECS.md'
    verb = 'move them to the' if sibling.exists() else 'create a'
    return (f'{path}: head is {tokens} tok carrying {modals} constraint(s).\n'
            f'   CONTEXT.md is the only enforced-read type, so this is charged to every\n'
            f'   session in the subtree. {verb} sibling SPECS.md and leave one pointer\n'
            f'   (core/SCHEMA.md § Placement, REDIRECT).')


def check_description(path: Path) -> str | None:
    """A file the routing table will list must give it something to write.

    Asks the generator, never a second pattern table — why, and what it cost the one time the
    two were allowed to disagree: core/hooks/SPECS.md § First-line descriptions.
    """
    if not feature_law.is_enabled('first-line-comment'):
        return None
    if not is_scanned(path) or is_generated_mirror(path) or \
            is_vendored(path, WORKSPACE_ROOT) or is_generated_artifact(path, WORKSPACE_ROOT):
        return None
    if file_description(path).strip():
        return None
    # A format with no comment syntax cannot be told to grow a first line, and JSON is the class:
    # every config a harness dictates is one. Its route is core/hooks/described.txt, so the fix
    # this names has to be that one — a gate naming an impossible fix is a gate nobody can obey.
    if path.suffix not in EXAMPLE_COMMENT:
        return (f'{path}: nothing to put in the routing table, and its format carries no comment.\n'
                f"   Its CONTEXT.md row would read '{PLACEHOLDER}'.\n"
                f'   Describe it in core/hooks/described.txt: <path><TAB><description>')
    return (f'{path}: nothing to put in the routing table.\n'
            f"   Its CONTEXT.md row would read '{PLACEHOLDER}'.\n"
            f'   Give it a first line: {EXAMPLE_COMMENT[path.suffix]}')


def check_truncation(path: Path) -> str | None:
    """A `…` inside a generated routing block means an author wrote past `hoist.DESC_LIMIT`.

    The twin of check_description, and the same rule section
    (core/SCHEMA.md § What a description must say): that one catches a row with nothing
    in it, this one a row with half a sentence in it. **Fix the source, never the cut** — the
    generator is doing exactly what it was told, so editing the table just regenerates the ellipsis
    on the next commit.

    Only inside the block: an author may write `…` in prose, and several do.
    """
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return None
    if ROUTING_START not in text or ROUTING_END not in text:
        return None
    block = text.split(ROUTING_START, 1)[1].split(ROUTING_END, 1)[0]
    rows = [ln for ln in block.splitlines() if '…' in ln]
    if not rows:
        return None
    named = [m.group(1) for ln in rows if (m := TRUNCATED_ROW.match(ln))]
    return (f'{path}: {len(rows)} truncated description(s) — '
            f'{", ".join(named) if named else "in the routing block"}.\n'
            f'   The source wrote past the {DESC_LIMIT}-character bound. Shorten the description\n'
            f'   at its source, then regenerate; never edit the table.')


def is_project(path: Path) -> bool:
    """A project = a directory sitting directly under code/. Scaffolding is not one."""
    return (path.name == 'CONTEXT.md' and path.parent.parent.name == 'code'
            and not path.parent.name.startswith('_'))


def check_goal_link(path: Path) -> str | None:
    """Every project declares on line 3 which goal it serves, or `none` deliberately.

    The link is what stops a project from quietly outliving the reason it was started —
    the one question a repo cannot answer about itself.
    """
    if not is_project(path):
        return None
    lines = path.read_text(encoding='utf-8').splitlines()
    line = lines[2] if len(lines) > 2 else ''
    match = GOAL_LINE.match(line.strip())
    if not match:
        return (f'{path}: line 3 must declare the goal this project serves.\n'
                f'   Write `> goal: [<name>](../../brain/goals/<name>.md)`, or\n'
                f'   `> goal: none` if it deliberately serves no goal. Found: {line[:60]!r}')
    if match.group(1) == 'none':
        return None
    target = (path.parent / match.group(3)).resolve()
    if not target.exists():
        return (f'{path}: line 3 points at a goal file that does not exist.\n'
                f'   {match.group(3)} — a dead goal link is worse than `none`, because it\n'
                f'   reads as an answer.')
    return None
