#!/usr/bin/env python3
# PostToolUse: Read — record CONTEXT.md/SPEC.md reads (consumed by context-gate.py /
# bash-context-gate.py / spec-read-gate.py) and interface-file reads (consumed by pre-read.py:
# interface read unlocks its source; and by pdf-gate.py: a PDF's twin read unlocks the PDF). ROADMAP-verify.md W1.
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parent)]
import feature_law  # noqa: E402
import read_matrix  # noqa: E402
from hook_input import capability, mark_iface_seen, mark_seen, normalise, parse_stdin
from platform_law import WORKSPACE_ROOT  # noqa: E402

IFACE_SUFFIXES = ('.d.ts', '.pyi', '.dart.api', '.texif', '.csvif')


def _is_twin(path: Path) -> bool:
	"""A PDF's twin is its interface: reading it unlocks the PDF for pdf-gate.py. The shape test
	runs first so the Read of any other .md never imports pdf_meta (and yaml with it)."""
	if path.suffix != '.md' or path.parent.name != path.stem:
		return False
	sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools/pdf'))
	import pdf_meta
	return pdf_meta.source_of(path) is not None


def main() -> int:
	# THE `--seen` QUERY ARM IS GONE, and so is the `was_read()` it wrapped. Both existed for one
	# caller -- the interface gate, back when it was shell and could not import a module whose name
	# has a hyphen in it. That gate is Python now and asks hook_input directly, which also ends the
	# defect the arm was built to work around: shell compared three spellings of one file with
	# `grep -qxF` (`C:\\Users\\...` from Path.resolve, `c:\\Users\\...` from the payload, `c:/Users/...`
	# from a readlink), none ever matched, and the gate blocked every source read while promising
	# that reading the interface would unlock it. A comparison belongs to the side that owns the
	# marker; both sides are now that side.
	# THE SWITCH IS ASKED BEFORE ANYTHING RETURNS, which is a contract and not a style: a hook that
	# reaches its own switch only on some payloads reads exactly like one that has no switch, and
	# test_features_wiring observes the consultation by RUNNING the hook rather than by reading it.
	# The matrix owns the other switch and asks it itself, so this returns early for neither.
	tracking = feature_law.is_enabled('subtree-read-tracking')
	_, tool, tool_input, session_id, _ = parse_stdin()
	if capability(tool, tool_input) != 'read':
		return 0
	raw = str(tool_input.get('file_path', ''))
	if not raw:
		return 0
	path = normalise(raw)
	# COUNTED FOR EVERY FILE, not only the three shapes below: this hook is the one place every
	# harness passes through on a read, which is what makes the count travel where
	# core/tools/wos/session/reads cannot — that family replays a transcript one vendor writes.
	# Two features, and the chain gate being off must not stop the workspace measuring what reading
	# costs it: that is the ablation's whole question, and record() asks its own switch.
	if path.startswith(str(WORKSPACE_ROOT)):
		read_matrix.record(path)
	if not tracking:
		return 0  # switched off: nothing is recorded, so the chain gate fires per file again
	# A spec is recorded by SHAPE, never by one filename. spec-read-gate.py resolves whatever the
	# module's CONTEXT.md names in `> spec:`, so a module whose spec is called SPECS.md — the only
	# spelling core/SCHEMA.md's type allowlist actually permits — read its spec, got no marker, and
	# was refused forever. Found 2026-09-12 renaming code/aiwbot/frontend/SPEC.md to the legal name.
	if Path(raw).name == 'CONTEXT.md' or Path(raw).name.startswith('SPEC'):
		mark_seen(session_id, path)  # idempotent: one file per entry, named for the path
	elif raw.endswith(IFACE_SUFFIXES) or _is_twin(Path(raw)):
		mark_iface_seen(session_id, path)
	return 0


sys.exit(main())
