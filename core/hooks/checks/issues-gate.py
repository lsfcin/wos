#!/usr/bin/env python3
# PreToolUse: Edit|Write on ISSUES.md — the FIXED gate. A bug may not leave this file without
# executable proof: flipping one to FIXED, or deleting its section, requires a matching regression
# spec (a file named *b<N>[_-]* under a test/ directory of this repo).
#
# Deleting an open bug used to bypass the flip check, so the gate reads the removal too.
# See ROADMAP-verify.md I2.
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from hook_input import capability, parse_stdin

BUG_ID_RE = re.compile(r'^##\s+(b[\w-]+)', re.IGNORECASE | re.MULTILINE)
# The capture group is load-bearing: findall returns whole heading lines without one, and a whole
# heading can never match a spec filename — every FIXED flip would block forever. Found 2026-09-04
# by the first flip that used the gate (B5): a valid spec on disk, and the gate still demanded one.
FIXED_RE = re.compile(r'^##\s+(b[\w-]+)\b[^\n]*\bFIXED\b', re.IGNORECASE | re.MULTILINE)
SKIP_DIRS = {'.venv', 'node_modules', '__pycache__'}


def bug_ids(text: str) -> set[str]:
	return {i.lower() for i in BUG_ID_RE.findall(text or '')}


def fixed_ids(text: str) -> set[str]:
	return {i.lower() for i in FIXED_RE.findall(text or '')}


def repo_root(path: Path) -> Path | None:
	try:
		out = subprocess.check_output(
			['git', '-C', str(path.parent), 'rev-parse', '--show-toplevel'],
			text=True, stderr=subprocess.DEVNULL, encoding='utf-8').strip()
		return Path(out)
	except Exception:
		return None


def has_spec(root: Path, bug_id: str) -> bool:
	"""A regression spec is any file named *<bug_id>* under a test/ directory.

	The id ends at a non-alphanumeric boundary, so `b1` does not borrow `test_b19_x.py`, and
	hyphen (ids) and underscore (module names) stand in for each other: `b20260831-the-bug`
	matches `test_b20260831_the_bug.py`. Tests live at core/tools/test here and at each repo's
	own layout, so the walk accepts any directory named test and skips the heavy non-test trees.
	"""
	parts = re.split('[-_]', bug_id.lower())
	pat = re.compile(rf'(?<![a-z0-9]){"[._-]".join(re.escape(p) for p in parts)}(?![a-z0-9])',
	                 re.IGNORECASE)
	for base, dirs, files in os.walk(root):
		dirs[:] = [d for d in dirs if d != '.git' and d not in SKIP_DIRS]
		rel = Path(base).relative_to(root)
		if not any(part == 'test' or part.startswith('test.') for part in rel.parts):
			continue
		for f in files:
			if pat.search(f):
				return True
	return False


def main() -> int:
	if not feature_law.is_enabled('issues-gate'):
		return 0  # switched off: a disabled gate does not block, and does not pretend it ran
	_, tool, tool_input, _, _ = parse_stdin()
	if capability(tool, tool_input) != 'write':
		return 0  # by capability, never by name — a harness may name its write tool anything
	file_path = Path(str(tool_input.get('file_path', '')))
	if file_path.name != 'ISSUES.md':
		return 0

	# Which SHAPE of write, asked of the payload: whole content, or a patch over what is there.
	if 'content' in tool_input:
		new_full = str(tool_input.get('content', ''))
	else:
		old_text = str(tool_input.get('old_string', ''))
		new_text = str(tool_input.get('new_string', ''))
		current_text = file_path.read_text(encoding='utf-8') if file_path.exists() else ''
		new_full = current_text.replace(old_text, new_text, 1) if old_text in current_text else current_text

	current = file_path.read_text(encoding='utf-8') if file_path.exists() else ''
	newly_fixed = fixed_ids(new_full) - fixed_ids(current)
	removed = bug_ids(current) - bug_ids(new_full) - newly_fixed
	if not newly_fixed and not removed:
		return 0

	root = repo_root(file_path)
	if root is None:
		return 0
	missing = sorted(b for b in set(newly_fixed) | set(removed) if not has_spec(root, b))
	if not missing:
		return 0

	print('ISSUES GATE - leaving the list needs executable proof.', file=sys.stderr)
	for b in missing:
		print(f'   {b}: no regression spec found (expected a test/ file naming the id, e.g. test_{b.replace("-", "_")}_*.py).', file=sys.stderr)
	print('   Write the regression spec first, verify it passes, then flip or delete the section.', file=sys.stderr)
	return 2


sys.exit(main())
