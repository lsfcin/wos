#!/usr/bin/env python3
# PreToolUse, capability write — a new file must open by saying what it is.
#
# Split out of checks/pre-edit.py 2026-09-14 so gates.txt can attribute a block. Two refusals, one
# feature (`first-line-comment`): a new code or content file whose first line is not a comment, and
# a new CONTEXT.md whose line 2 is not the `> description` the routing generator publishes. The
# second is the same rule one line down — a CONTEXT.md's line 1 is its `#` title — so it is folded
# in here rather than given a registry row of its own to describe one regex.
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from write_payload import block, target  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from file_law import EXAMPLE_COMMENT, is_authored  # noqa: E402

from write_payload import WORKSPACE_ROOT  # noqa: E402

CONTENT_EXTS = {'.md', '.yaml', '.yml', '.toml'}

FIRST_LINE_COMMENT = {
    '.py': r'^\s*#',     '.js':   r'^\s*//',   '.ts':   r'^\s*//',
    '.tsx': r'^\s*//',   '.dart': r'^\s*//',   '.css':  r'^\s*/\*',
    '.scss': r'^\s*/\*', '.html': r'^\s*<!--',
    '.yaml': r'^\s*#',   '.yml':  r'^\s*#',    '.toml': r'^\s*#',
    '.tex': r'^\s*%',    '.md':   r'^\s*(#|---\s*$)',  # md: title or YAML frontmatter (skills)
}

# Off means it stops refusing, not that it fails. Same arm, same reason, as every other gate — and
# it is what makes this row's `wired` cell in core/features.txt true rather than declared.
if not feature_law.is_enabled('first-line-comment'):
    sys.exit(0)

file_path, data = target()
basename = os.path.basename(file_path)

# Only a NEW file is asked: an existing one already answered, and re-asking would refuse every edit
# to a file that predates the rule.
if 'content' not in data or os.path.exists(file_path):
    sys.exit(0)
content = data.get('content', '')

if basename == 'CONTEXT.md':
    lines = content.splitlines()
    line2 = lines[1].strip() if len(lines) > 1 else ''
    if not re.match(r'^>\s*\S', line2):
        block(f"⛔ CONTEXT.md DESCRIPTION MISSING — {file_path}",
              "   Line 2 must be: > Short description of this directory")
    sys.exit(0)

_, ext = os.path.splitext(file_path)
if not (is_authored(Path(file_path), WORKSPACE_ROOT) or ext in CONTENT_EXTS):
    sys.exit(0)

pattern = FIRST_LINE_COMMENT.get(ext)
first = content.splitlines()[0] if content.strip() else ''
if pattern and not re.match(pattern, first):
    block(f"⛔ FIRST-LINE MISSING — {file_path}",
          "   New files must start with a description.",
          f"   Example: {EXAMPLE_COMMENT.get(ext, '# Description')}")

sys.exit(0)
