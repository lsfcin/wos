#!/usr/bin/env python3
# PreToolUse: Edit|Write — a spec-locked module (its CONTEXT.md carries `> spec:` and the referenced
# SPEC.md header is `status: locked`) requires that SPEC.md be Read this session before editing the
# module's files. See code/ROADMAP-spec-drive.md.
#
# Ratchet coverage: creating a new file in a code/ module with no spec prints a non-blocking nudge.
# Session-dedup via the context-tracker marker.
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from hook_input import capability, load_seen, parse_stdin
from platform_law import WORKSPACE_ROOT  # noqa: E402

CODE_ROOT = WORKSPACE_ROOT / 'code'
EXEMPT_NAMES = {'CONTEXT.md', 'AGENTS.md', 'CLAUDE.md', 'MEMORY.md', 'README.md'}
SKIP_PARTS = {'.git', 'node_modules', 'dist', '.codegraph', '__pycache__', '.vscode'}
SPEC_LINE_RE = re.compile(r'^>\s*spec:\s*(\S.*?)\s*$', re.MULTILINE)
STATUS_RE = re.compile(r'^status:\s*(\w+)', re.MULTILINE)


def find_spec_module(target: Path):
	"""Nearest ancestor dir whose CONTEXT.md declares `> spec:`.
	Returns (module_dir, spec_path_or_None, status) or None. status ∈ {locked, draft, optout}."""
	start = target if target.is_dir() else target.parent
	current = start
	result = None
	while current != WORKSPACE_ROOT and current != current.parent:
		ctx = current / 'CONTEXT.md'
		if ctx.is_file():
			match = SPEC_LINE_RE.search(ctx.read_text(errors='ignore', encoding='utf-8'))
			if match:
				spec_val = match.group(1).strip()
				if spec_val.lower() == 'none':
					result = (current, None, 'optout')
				else:
					spec_path = (current / spec_val).resolve()
					status = 'draft'
					if spec_path.is_file():
						status_match = STATUS_RE.search(spec_path.read_text(errors='ignore', encoding='utf-8'))
						if status_match:
							status = status_match.group(1).lower()
					result = (current, spec_path, status)
				break
		current = current.parent
	return result


def block(module_dir: Path, spec_path: Path) -> int:
	print('SPEC GATE - module is spec-locked; read its SPEC.md before editing its code.', file=sys.stderr)
	print(f'   Module:      {module_dir}', file=sys.stderr)
	print(f'   Read first:  {spec_path}', file=sys.stderr)
	print('   The SPEC is the contract — its inputs/outputs/invariants govern this change.', file=sys.stderr)
	return 2


def nudge() -> None:
	print('SPEC NUDGE - this code/ module has no SPECS.md.', file=sys.stderr)
	print('   Author one (code/_templates/SPECS-module.md) and add `> spec: SPECS.md` to its', file=sys.stderr)
	print('   CONTEXT.md to spec-lock it. Non-blocking — coverage grows as modules are touched.', file=sys.stderr)


def main() -> int:
	if not feature_law.is_enabled('spec-read-gate'):
		return 0  # switched off: a disabled gate does not block, and does not pretend it ran
	_, tool, tool_input, session_id, _ = parse_stdin()
	result = 0
	if capability(tool, tool_input) == 'write':
		raw = str(tool_input.get('file_path', ''))
		target = Path(raw) if raw else None
		if target is not None and target.is_absolute():
			try:
				target = target.resolve()
			except OSError:
				target = None
		else:
			target = None
		in_code = target is not None and target.is_relative_to(CODE_ROOT)
		gated = in_code and target.name not in EXEMPT_NAMES and not SKIP_PARTS.intersection(target.parts)
		if gated:
			found = find_spec_module(target)
			if found is None:
				if not target.exists():
					nudge()  # a write to a path that is not there yet is a file being created
			else:
				module_dir, spec_path, status = found
				if status == 'optout':
					result = 0
				elif spec_path is None or not spec_path.is_file():
					print('SPEC GATE - CONTEXT.md declares `> spec:` but the spec file is missing.', file=sys.stderr)
					print(f'   Expected: {spec_path}', file=sys.stderr)
					result = 2
				elif status != 'locked' or target == spec_path:
					result = 0
				elif str(spec_path) in load_seen(session_id):
					result = 0
				else:
					result = block(module_dir, spec_path)
	return result


sys.exit(main())
