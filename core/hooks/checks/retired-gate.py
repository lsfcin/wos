#!/usr/bin/env python3
# PostToolUse, capability `write` — a retired token reaches the agent at the edit, not at the close.
#
# THE CHECK ALREADY EXISTED AND WAS MERELY LATE. `entropy_list.retired_hits` is exact and costs
# zero tokens, and its only caller was the entropy dashboard — a report written into ISSUES.md
# after the fact, which means a rename could stay unfinished for a whole session and be found by
# the close. Same law, same function, one moment earlier.
#
# WHY NOT AN AUTO-REPLACE, asked by Lucas 2026-09-13 and answered no: a word-for-word rewrite is
# blind to the four contexts this workspace actually has — a filename (`citation-gate.py`), a
# quoted error, a code block, and § Retired tokens itself, which must WRITE the dead token to
# declare it dead. A silent rewrite is also an edit nobody reviewed. core/SCHEMA.md § Vocabulary
# already rules that a spelling which is also a real word needs a shape rather than a token, and
# a replacer has no sense of shape at all. So: inform, and let the writer choose.
#
# WHY POST AND NOT PRE: pre-write carries the pending content in the payload rather than on disk,
# and asking `retired_hits` about it would mean a second copy of the scanning loop. The law has
# one reader (core/hooks/CONTEXT.md), so the moment moved instead of the code.
import json
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(HOOKS / 'entropy'))
import feature_law  # noqa: E402
import schema_law  # noqa: E402
import scoreboard  # noqa: E402
from entropy_corpus import enforcement_paths  # noqa: E402
from entropy_list import retired_hits  # noqa: E402
from hook_input import capability, parse_stdin  # noqa: E402
from platform_law import WORKSPACE_ROOT  # noqa: E402


def main() -> int:
    # Off means it stops reporting, not that it fails — the arm every other gate uses.
    if not feature_law.is_enabled('retired-tokens'):
        return 0
    _, tool, data, _, _ = parse_stdin()
    if capability(tool, data) != 'write':
        return 0

    target = Path(data.get('file_path', ''))
    if not target.is_file():
        return 0
    try:
        target.relative_to(WORKSPACE_ROOT)
    except ValueError:
        return 0

    hits = retired_hits([target], schema_law.load_retired(), enforcement_paths(WORKSPACE_ROOT))
    if not hits:
        return 0
    # An informing gate never exits 2, so dispatch.py has no exit code to attribute and `blocked`
    # is structurally zero for it. This is the honest yield: the gate RAN 1088 times by 2026-09-23
    # and nobody could say whether it had ever advised anything (core/hooks/scoreboard.py).
    scoreboard.record('retired-tokens', 'found')
    print(json.dumps({'hookSpecificOutput': {
        'hookEventName': 'PostToolUse',
        'additionalContext': '⚠ RETIRED TOKEN — this rename was finished; the spelling was not.\n'
                             + '\n'.join(hits),
    }}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
