#!/usr/bin/env python3
# PreToolUse, capability write — this workspace keeps no memory store, so a harness writing one is
# refused and handed the file that owns the fact.
#
# WHY. A harness memory index is folded into the system prompt of EVERY session, including the nine
# in ten it has nothing to do with, and harnesses write to it unprompted. Lucas ruled 2026-09-15 that
# the store goes, with `brain/USER.md`: AGENTS.md, the CONTEXT.md chain, core/ and brain/ carry what
# an agent needs; each rule the store carried now lives with its owner.
#
# The harness path `~/.claude/projects/<name>/memory` stays a symlink onto `brain/memory/`, so a
# write arrives here spelled either way and resolving makes the two one target. Without the
# symlink the write would land outside the workspace, where nothing sees it.
#
# The refusal offers no switch: offered, it became the path — an agent passed the question to
# Lucas instead of routing the fact (2026-09-24). The refusal names the owner instead, because a
# gate that only says no gets the same text written again a turn later.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'checks'))
from write_payload import WORKSPACE_ROOT, block, target  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
import platform_law  # noqa: E402

if not feature_law.is_enabled('memory-gate'):
    sys.exit(0)

file_path, _data = target()
if not file_path:
    sys.exit(0)

try:
    written = platform_law.rel(Path(file_path).resolve(), WORKSPACE_ROOT)
except OSError:
    sys.exit(0)

if written.startswith('brain/memory/'):
    block(f"⛔ MEMORY GATE — {written}: this workspace keeps no memory store.",
          "   Put the fact where its readers already are:",
          "     a rule the agent must obey      -> core/norms/, or the SPECS.md that owns it",
          "     something untrue about the repo -> ISSUES.md",
          "     work still to do                -> ROADMAP.md",
          "     what a folder holds or routes   -> that folder's CONTEXT.md",
          "   Pick the destination yourself and write it there. Do not ask Lucas about memory.")

sys.exit(0)
