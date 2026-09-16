# session_reads.py — which files a session read, how often, and what each read served.
#
# Split from the `reads` CLI the way session_turns.py was split from `usage`: the walk is the
# reusable half and the printing is not. `roundup` is the intended second caller.
#
# One rule this file exists to respect: a Read's SIZE is the tool_result that answers it, never the
# arguments that requested it. An offset/limit read of a 2,000-line file costs what it was served,
# and the whole point of the interface-first gate is that the two differ.
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'core' / 'hooks'))
import platform_law
from session_log import _result_chars, blocks, project_name
from session_turns import paths_for

PROJECT = project_name()
STUB_SUFFIXES = ('.pyi', '.d.ts', '.dart.api', '.texif')


def kind_of(path: str) -> str:
	"""What the workspace served, in the terms its own gates are argued in."""
	name = path.rsplit('/', 1)[-1]
	if name == 'CONTEXT.md':
		return 'CONTEXT.md chain'
	if path.endswith(STUB_SUFFIXES):
		return 'interface stub'
	# `'ROADMAP.md'.isupper()` is False — the extension is lowercase — so the type check is on the
	# stem. Without it every list read was filed under 'prose' and the most expensive file in the
	# workspace hid inside the largest bucket.
	if name.endswith('.md'):
		return 'other UPPERCASE.md' if name.split('.')[0].isupper() else 'prose'
	return 'source'


def file_reads(project: str = PROJECT, session: str = '') -> tuple:
	"""Per-file read stats across a project's transcripts: {path: {count, chars, sessions}}.

	Subagent turns are skipped: they carry their own transcripts under `<session>/subagents/`, and a
	worker re-reading a chain the parent already read is a different question from this one.
	"""
	files: dict = defaultdict(lambda: {'count': 0, 'chars': 0, 'sessions': set()})
	sessions: set = set()
	for path in paths_for(project, session):
		target_of: dict = {}
		for line in path.open(errors='replace', encoding='utf-8'):
			try:
				event = json.loads(line)
			except json.JSONDecodeError:
				continue
			if event.get('isSidechain'):
				continue
			if event.get('type') == 'assistant':
				for block in blocks(event.get('message') or {}):
					if block.get('type') == 'tool_use' and block.get('name') == 'Read':
						target = str((block.get('input') or {}).get('file_path', ''))
						if target:
							target_of[block.get('id')] = target
			elif event.get('type') == 'user':
				for block in blocks(event.get('message')):
					target = target_of.get(block.get('tool_use_id'))
					if block.get('type') != 'tool_result' or not target:
						continue
					stat = files[target]
					stat['count'] += 1
					stat['chars'] += _result_chars(block)
					stat['sessions'].add(path.stem)
					sessions.add(path.stem)
	return dict(files), sessions


def weights(files: dict, population: int, root: Path) -> dict:
	"""Lines served per session — what a file costs the workspace's ATTENTION, not its disk.

	`size` counts a line once, wherever it sits. This counts it once per time a session was
	actually served it: `lines on disk × reads ÷ sessions`. The divisor is the WHOLE population,
	never the sessions that happened to open the file — read three times inside one session out of
	88 is nearly free per session, and dividing by 1 would call it the most expensive file we own.

	**A weight of 0 is a statement about READING, never a licence to delete.** `core/experiments/`
	weighs 0 and is the WOS paper's data (Lucas, 2026-09-15). Whoever prints this number prints the
	population beside it, so nobody reads a 0 without knowing what it is 0 out of.
	"""
	out: dict = {}
	for path, stat in files.items():
		p = Path(path)
		if not p.is_absolute() or root not in p.parents:
			continue
		try:
			# STRICT decode, unlike every other reader here: a weight is a count of LINES, and a
			# PNG's newline bytes are not lines. Read as `replace` a screenshot outweighed
			# ROADMAP.md on this report's first run. What has no lines gets no weight.
			lines = p.read_text(encoding='utf-8').count('\n')
		except (OSError, UnicodeDecodeError):
			continue  # deleted since, or not text — a weight nobody can pay
		out[platform_law.rel(p, root)] = {
			'lines': lines, 'count': stat['count'],
			'weight': lines * stat['count'] / max(1, population),
		}
	return out
