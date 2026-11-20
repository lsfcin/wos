#!/usr/bin/env python3
# PreToolUse: Read + Write + Bash — a handoff is opened by taking it. Every other way in is refused with the one command that does it.
#
# Taking prints every pending section and deletes the file under the lock writers share
# (core/tools/wos/close/handoff.py), so the session that opens a handoff owns its threads and no
# parallel session can append into a file already handed out. A plain read would leave it pending
# for the next session too, and a direct write would skip the append that keeps another session's
# section. The shell arm fires only on a handoff file that EXISTS, named in a command that is not the
# tool: `ls outputs/handoff-*` names no file and passes. Residual: a path built at run time escapes.
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from hook_input import capability, normalise, parse_stdin  # noqa: E402
from platform_law import WORKSPACE_ROOT  # noqa: E402

OUTPUTS = WORKSPACE_ROOT / 'outputs'
NAME = re.compile(r'\bhandoff-([a-z0-9-]+)\.md\b')
TOOL = 'tools/wos/handoff'


def handoffs_in(command: str) -> list[str]:
    """Keys of the pending handoffs a shell command names."""
    return [key for key in dict.fromkeys(NAME.findall(command)) if (OUTPUTS / f'handoff-{key}.md').is_file()]


def refuse(key: str) -> int:
    print(f'⛔ HANDOFF IS TAKEN, NOT READ — outputs/handoff-{key}.md\n'
          f'   core/run tools/wos/handoff --take {key}\n'
          '   Taking prints every pending section and deletes the file; a session adds its own with --write.\n'
          '   In plan mode: ask Lucas to lift it, take, then plan (core/skills/handoff.md § Output).',
          file=sys.stderr)
    return 2


def main() -> int:
    if not feature_law.is_enabled('handoff-gate'):
        return 0
    _, tool, tool_input, _, _ = parse_stdin()
    kind = capability(tool, tool_input)
    if kind in ('read', 'write'):
        target = Path(normalise(str(tool_input.get('file_path', ''))))
        match = NAME.fullmatch(target.name)
        return refuse(match.group(1)) if match and target.parent == OUTPUTS else 0
    if kind == 'shell':
        command = str(tool_input.get('command', ''))
        keys = [] if TOOL in command else handoffs_in(command)
        return refuse(keys[0]) if keys else 0
    return 0


sys.exit(main())
