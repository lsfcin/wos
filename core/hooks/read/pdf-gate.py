#!/usr/bin/env python3
# PreToolUse: Read + Bash — a PDF is read through its twin. Fresh twin: the PDF is blocked until the twin is read, which unlocks it. Missing or stale: refused with the command that makes it, or let through when no engine is installed.
#
# The twin is the PDF's interface, and this is the interface-first gate for it (pre-read.py is the
# one for code), with one difference ruled by Lucas 2026-09-26: a missing twin REFUSES where a
# missing stub only warns. A stub is regenerated on every save for free; a twin is made on purpose,
# and a PDF read raw loses every figure the twin describes, so the refusal is what makes one exist.
#
# Both arms share one verdict. The shell arm fires only when the command holds a raw reader AND a
# PDF path — `ls`, `mv`, `git add` and `core/run tools/pdf/docling` name PDFs all day and pass. What
# counts as a raw reader is pdf_meta.RAW_COMMANDS / RAW_MODULES, the list test_pdf_boundary.py
# holds the code to; it is imported, never restated. No subagent exemption: a research worker is the
# one most likely to open a PDF, and the twin is what it should read.
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from chain import prerequisites  # noqa: E402
from hook_input import capability, is_subagent, load_iface_seen, load_seen, normalise, parse_stdin  # noqa: E402
from platform_law import WORKSPACE_ROOT  # noqa: E402

PDF_PATH = re.compile(r"""(['"])([^'"\n]+?\.pdf)\1|([^\s'"|;&<>()=]+\.pdf)\b""", re.I)
SEGMENT = re.compile(r'\|\||&&|[|;&\n]')
HEREDOC = re.compile(r"""<<-?\s*(['"]?)([A-Za-z_]\w*)\1""")
LEAF_TEXT = re.compile(r'tools/pdf/poppler\s+text\b')


def _pdf_meta():
	"""Imported only once a PDF is in play: it pulls yaml, and this gate fires on every Read."""
	sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools/pdf'))
	import pdf_meta
	return pdf_meta


def _without_prose(command: str) -> str:
	"""Drop heredoc bodies that are prose (a commit message naming `pdftotext x.pdf`), keep code.

	A body fed to an interpreter IS the command — `python - <<EOF\\nimport fitz` reads the PDF —
	so only a heredoc on a line with no python/node on it is removed.
	"""
	out, pos = [], 0
	for match in HEREDOC.finditer(command):
		line = command[command.rfind('\n', 0, match.start()) + 1:match.start()]
		rest = command[match.end():]
		end = re.search(rf'^[ \t]*{re.escape(match.group(2))}[ \t]*$', rest, re.M)
		stop = match.end() + (end.end() if end else len(rest))
		if not re.search(r'python|node', line):
			out.append(command[pos:match.end()])
			pos = stop
	out.append(command[pos:])
	return ''.join(out)


def reads_raw(command: str, pm) -> bool:
	"""True when the command opens a PDF with something other than the twin."""
	if any(Path(word).name in pm.RAW_COMMANDS for word in command.split()) or LEAF_TEXT.search(command):
		return True
	modules = '|'.join(map(re.escape, pm.RAW_MODULES))
	if re.search(rf'(?:\bimport|\bfrom|-m)\s+({modules})\b', command):
		return True
	firsts = (seg.split()[0] for seg in SEGMENT.split(command) if seg.split())
	return any(Path(word).name in pm.RAW_MODULES for word in firsts)   # the `docling` / `markitdown` CLIs


def pdfs_in(command: str, cwd: str) -> list[Path]:
	found = []
	for match in PDF_PATH.finditer(command):
		path = Path(match.group(2) or match.group(3)).expanduser()
		path = (path if path.is_absolute() else Path(cwd) / path).resolve()
		if path.is_file() and path not in found:
			found.append(path)
	return found


def engine_installed() -> bool:
	"""Can a twin be made on this clone? `pdf` on is the switch (features.txt `needs`); this is the
	install. Refusing with a command whose .venv-pdf is not there leaves the PDF unreadable."""
	import platform_law
	sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools'))   # pdf_twin's siblings: describe, secret_law
	import pdf_twin
	return platform_law.venv_script('python', pdf_twin.ENGINE_VENV).exists()


def refuse(pdf: Path, state: str, twin: Path, needed: list[Path]) -> None:
	if state == 'fresh':
		print(f'⛔ PDF TWIN FIRST — {pdf}\n   Read these first, in ONE parallel batch, then retry:', file=sys.stderr)
		for path in needed:
			print(f'   {path}', file=sys.stderr)
		print(f'   {twin}   <- the twin: all the text, every figure described\n'
		      '   (Reading the twin unlocks the PDF for this session, for a look at the layout.)', file=sys.stderr)
		return
	print(f'⛔ NO FRESH TWIN — {pdf} ({state})\n   Make it, then read {twin}:\n'
	      f'   core/run tools/pdf/docling {pdf}    # GPU, scans and tables; agy describes each figure\n'
	      f'   core/run tools/pdf/pymupdf {pdf}    # CPU, seconds; fewer tables', file=sys.stderr)


def main() -> int:
	if not feature_law.is_enabled('pdf-twin-reads'):
		return 0
	raw, tool, tool_input, session_id, cwd = parse_stdin()
	kind = capability(tool, tool_input)
	if kind == 'read':
		target = str(tool_input.get('file_path', ''))
		if not target.lower().endswith('.pdf'):
			return 0
		pm = _pdf_meta()
		pdfs = [Path(normalise(target))]
	elif kind == 'shell':
		command = str(tool_input.get('command', ''))
		if '.pdf' not in command.lower():
			return 0
		pm = _pdf_meta()
		command = _without_prose(command)
		pdfs = pdfs_in(command, cwd or str(WORKSPACE_ROOT)) if reads_raw(command, pm) else []
	else:
		return 0

	unlocked = load_iface_seen(session_id)
	blocked = False
	for pdf in pdfs:
		state, twin = pm.twin_state(pdf)
		if state == 'fresh' and normalise(str(twin)) in unlocked:
			continue
		if state != 'fresh' and not engine_installed():
			continue
		# The chain is named with the twin (pre-read.py's rule: one list, not one gate's slice). A
		# worker is exempt from the chain gate, so it is handed only the twin.
		needed = [] if is_subagent(raw) else prerequisites(twin, load_seen(session_id), unlocked, False)
		refuse(pdf, state, twin, needed)
		blocked = True
	return 2 if blocked else 0


sys.exit(main())
