#!/usr/bin/env python3
# PreToolUse: Edit|Write — block code/ module edits until the module's facade has been read.
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law
from file_law import FACADES  # noqa: E402
from hook_input import capability, load_facades, parse_stdin
from platform_law import WORKSPACE_ROOT  # noqa: E402

# NOT the file_law CODE set: this is "languages that have a facade convention", a genuinely
# narrower question than "is this code". Named apart so the two never get conflated again —
# `FACADES` beside it answers a third question, which file IS one, and comes from there too.
FACADE_EXTS  = {'.ts', '.tsx', '.js', '.jsx', '.py', '.dart'}
TEST_RE      = re.compile(r'(?:^|/)(?:test_[^/]+|[^/]+_test|[^/]+\.(?:test|spec))\.[^/]+$')


def find_nearest_facade(path: Path) -> Path | None:
	code_idx = next((i for i, p in enumerate(path.parts) if p == 'code'), None)
	if code_idx is None:
		return None
	project_root = Path(*path.parts[:code_idx + 2])
	current = path.parent
	while True:
		for name in FACADES:
			candidate = current / name
			if candidate.exists():
				return candidate
		if current == project_root or current == current.parent:
			break
		current = current.parent
	return None


def main() -> int:
	# The read-gate half of facade-discipline; the import-block half is
	# facade/check-facade-imports.py, which is the path the registry names.
	if not feature_law.is_enabled('facade-discipline'):
		return 0
	_, tool, tool_input, session_id, _ = parse_stdin()
	if capability(tool, tool_input) != 'write':
		return 0
	file_path = Path(str(tool_input.get('file_path', '')))
	if 'code' not in file_path.parts:
		return 0
	if file_path.suffix not in FACADE_EXTS:
		return 0
	if file_path.name in FACADES:
		return 0
	if TEST_RE.search(str(file_path)):
		return 0

	facade = find_nearest_facade(file_path)
	if not facade or str(facade) in load_facades(session_id):
		return 0

	try:
		rel_f = facade.relative_to(WORKSPACE_ROOT)
		rel_p = file_path.relative_to(WORKSPACE_ROOT)
	except ValueError:
		rel_f, rel_p = facade, file_path
	print(f"⛔ READ FACADE FIRST — {rel_p}", file=sys.stderr)
	print(f"   Read {rel_f} before editing this module.", file=sys.stderr)
	print(f"   Source reads then auto-redirect to .d.ts/.pyi via pre-read.py.", file=sys.stderr)
	return 2


sys.exit(main())
