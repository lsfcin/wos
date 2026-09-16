#!/usr/bin/env python3
# PreToolUse, capability write — refuse a write that would put an authored code file over the cap.
#
# Split out of checks/pre-edit.py 2026-09-14 so gates.txt can attribute a block. One refusal, one
# feature (`line-limit`), which is the point of the split: the file it came from blocked for three
# reasons owned by two features, and a row has one feature cell (/ROADMAP.md § Measurement).
#
# BOTH HALVES OF THE SIZE LAW, since the unit moved on 2026-09-14: lines and characters, at the
# BLOCK level only. The WARN level is the commit's to give — checks/line_counts.py — because a warn
# that cannot be waived at write time would just be a block with a softer word.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from write_payload import WORKSPACE_ROOT, block, target, written_size  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from file_law import is_authored, load_limits  # noqa: E402

if not feature_law.is_enabled('line-limit'):
    sys.exit(0)

file_path, data = target()

# Code only, which is the scope this gate has always had. Prose is held to the same two numbers by
# checks/line_counts.py at commit; moving that forward to write time is a change to what is
# enforced, not to who is charged for it, so it is not smuggled in here.
if not is_authored(Path(file_path), WORKSPACE_ROOT):
    sys.exit(0)

size = written_size(file_path, data)
if size is None:
    sys.exit(0)
lines, chars = size

limits = load_limits()
if lines >= limits['BLOCK_LINES']:
    block(f"⛔ SIZE GATE — {file_path} would reach {lines} lines "
          f"(limit: {limits['BLOCK_LINES']}).",
          "   Extract shared logic into a new module and import it from existing callers.",
          "   Do NOT copy existing functions into a new file — copies are blocked at commit.")

if chars >= limits['BLOCK_CHARS']:
    block(f"⛔ SIZE GATE — {file_path} would reach {chars} characters "
          f"(limit: {limits['BLOCK_CHARS']}).",
          "   The document cap, which the line cap cannot be traded against: reflowing is not",
          "   cutting. Delete what repeats or what nobody reads — core/norms/cap.md.")

sys.exit(0)
