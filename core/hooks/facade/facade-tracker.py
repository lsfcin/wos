#!/usr/bin/env python3
# PostToolUse: Read — record facade file reads to session state for facade-gate.py.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from file_law import FACADES  # noqa: E402
from hook_input import capability, mark_facade, parse_stdin


def main() -> int:
	# This records what facade-gate.py consults, so it answers to the same switch: with
	# facade-discipline off the gate returns early and nothing reads this state, and a tracker
	# still writing it would leave the feature counted as active in an ablation that turned it off.
	if not feature_law.is_enabled('facade-discipline'):
		return 0
	_, tool, tool_input, session_id, _ = parse_stdin()
	if capability(tool, tool_input) != 'read':
		return 0
	file_path = str(tool_input.get('file_path', ''))
	if Path(file_path).name not in FACADES:
		return 0
	mark_facade(session_id, file_path)
	return 0


sys.exit(main())
