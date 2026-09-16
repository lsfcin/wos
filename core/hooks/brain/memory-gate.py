#!/usr/bin/env python3
# PreToolUse, capability write — a memory is written when Lucas asks for one, never on the agent's
# own initiative.
#
# WHY. `brain/memory/MEMORY.md` is folded into the system prompt of EVERY session, including the
# nine in ten that have nothing to do with any line in it, so a memory is the most expensive place
# in this workspace to put a fact — measured at its own row in `core/run tools/wos/session/context`.
# Harnesses write there unprompted and the store only grows: the index reached twenty entries, five
# of which restated a law that already held elsewhere or a reference the project already carried
# (cut 2026-09-15, with `brain/USER.md`, which had zero reads in 88 sessions).
#
# WHAT IT IS NOT. Not a claim that the store is worthless — it is a claim that WRITING to it is a
# decision, and a decision belongs to Lucas. The refusal names the durable file that owns the fact,
# because a gate that only says no gets the same text written again a turn later.
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

# The harness path is a symlink onto this one, so a write arrives spelled either way and resolving
# is what makes the two the same target. `brain/memory/CONTEXT.md` explains the symlink.
try:
    written = platform_law.rel(Path(file_path).resolve(), WORKSPACE_ROOT)
except OSError:
    sys.exit(0)

if written.startswith('brain/memory/'):
    block(f"⛔ MEMORY GATE — {written} is written when Lucas asks for a memory, not otherwise.",
          "   Every line under brain/memory/ is loaded into every session, including the ones it",
          "   has nothing to do with. Put the fact where its readers already are:",
          "     a rule the agent must obey      -> core/norms/, or the SPECS.md that owns it",
          "     something untrue about the repo -> ISSUES.md",
          "     work still to do                -> ROADMAP.md",
          "     what a folder holds or routes   -> that folder's CONTEXT.md",
          "   If Lucas asked for a memory, switch memory-gate off in core/profile.txt for the",
          "   write and back on after — the switch is the record that he asked.")

sys.exit(0)
