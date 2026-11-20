#!/usr/bin/env python3
# How often each file was READ, per day, for the last year — counted at the moment of the read.
#
# WHY THIS EXISTS. AGENTS.md cuts where a line is READ, never where it sits, and until now that
# question could only be asked of one session at a time: core/tools/wos/session/reads replays a
# transcript and dies with it. Nothing accumulated, so "what cost me most this month" had no answer.
#
# WHY IT IS COUNTED HERE AND NOT READ OUT OF A TRANSCRIPT. The session tools read
# ~/.claude/projects/*.jsonl — an artifact one vendor leaves on disk, which is why that whole family
# serves one harness and always would have. This module is the other shape, the one core/hooks/
# scoreboard.py already proved: record the fact where it happens. context-tracker.py runs on every
# read under every harness, so the count travels for free.
#
# WHAT IS LOST BY COUNTING HERE, stated rather than discovered later. Two things, both in the same
# direction. At the moment of the event this knows the file, not the tokens the API billed for it —
# volume, not price, and the transcript keeps the half only a transcript can answer. And the unit is
# a read REQUESTED, not a read served: a harness that recognises a repeat and hands back nothing runs
# this hook anyway, so such a call is counted here and cost nothing. Asking which is which would mean
# reading one vendor's refusal message, which is the coupling this module exists to remove. Demand is
# the honest name for what these numbers are, and it is still the number a cut is argued from.
#
# TWO FILES, TWO SHAPES, AND THE SPLIT IS THE DESIGN. Events are appended one line at a time, which
# is atomic under PIPE_BUF and therefore safe between parallel sessions; a matrix is read-modify-
# write and would lose rows if a hook touched it. So the hook only ever appends, and the close folds
# the events into the matrix, once, alone.
#
# THE COLUMN OF A DAY IS ITS ORDINAL MODULO 365, so the window is circular with nothing to move:
# writing today never shifts another column, and the row for a file changes only on the days it was
# actually read. A shifting window would rewrite every row daily and commit a diff that means
# nothing. What the header carries is how far the fold has run, which is what says which columns are
# stale and must be cleared before they are believed.
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_law import WORKSPACE_ROOT, rel  # noqa: E402

WINDOW = 365
EVENTS = WORKSPACE_ROOT / 'core' / 'reads.tsv'
MATRIX = WORKSPACE_ROOT / 'core' / 'read-matrix.tsv'
HEADER = '# read-matrix\tasof\t'


def column(day: datetime.date) -> int:
	"""Which of the WINDOW columns holds this day. The one definition; never restated."""
	return day.toordinal() % WINDOW


def enabled() -> bool:
	"""Whether this feature is switched on, asked HERE rather than at the call site.

	The registry names this file for the feature that carries its name, and `test_features_wiring`
	holds that claim to a consultation it can observe — so a switch thrown in a caller is a switch
	the ablation cannot find. Same shape as core/hooks/scoreboard.py, for the same reason.
	"""
	try:
		import feature_law
		return feature_law.is_enabled('read-matrix')
	except Exception:  # noqa: BLE001 — a measurement may never break the call it measures
		return False


def record(path: str, store: Path = None) -> None:
	"""Append one read. Never raises: a lost count must never cost a tool call.

	One line under PIPE_BUF is an atomic append on POSIX, which is what lets every parallel session
	write here without a lock — the same reason core/hooks/scoreboard.py has the shape it has.
	"""
	if not enabled():
		return
	try:
		row = f'{datetime.date.today().isoformat()}\t{rel(path)}\n'
		with open(store or EVENTS, 'a', encoding='utf-8', newline='\n') as fh:
			fh.write(row)
	except Exception:  # noqa: BLE001 — see this function's first line
		return


def load(matrix: Path = None) -> tuple:
	"""(asof, {path: [counts]}) — the matrix as it stands, or (None, {}) when there is none."""
	target = matrix or MATRIX
	if not target.exists():
		return None, {}
	lines = target.read_text(encoding='utf-8', errors='replace').splitlines()
	asof = None
	rows: dict = {}
	for line in lines:
		if line.startswith(HEADER):
			asof = datetime.date.fromisoformat(line[len(HEADER):].strip())
			continue
		if not line or line.startswith('#'):
			continue
		name, _, counts = line.partition('\t')
		rows[name] = [int(n) for n in counts.split()]
	return asof, rows


def _expire(rows: dict, asof, today: datetime.date) -> None:
	"""Zero every column for a day that has passed since the fold last ran.

	A circular window overwrites rather than deletes, so a column nobody cleared still holds what it
	held a year ago — the one failure this shape can have, and the only reason the header exists.
	Days are cleared one at a time rather than by range, because more than WINDOW days away every
	column is stale and the loop is the same either way.
	"""
	if asof is None:
		return
	gap = min((today - asof).days, WINDOW)
	for step in range(1, gap + 1):
		stale = column(asof + datetime.timedelta(days=step))
		for counts in rows.values():
			counts[stale] = 0


def fold(events: Path = None, matrix: Path = None, today: datetime.date = None) -> dict:
	"""Read the events, add them into the matrix, write it, and delete what was folded.

	Deleting the events is what keeps this O(one day) instead of O(all history): a row that has been
	counted must never be counted twice, and truncating after the write is the only ordering where a
	crash costs a day of counts rather than doubling them.
	"""
	today = today or datetime.date.today()
	source, target = events or EVENTS, matrix or MATRIX
	asof, rows = load(target)
	_expire(rows, asof, today)
	if source.exists():
		for line in source.read_text(encoding='utf-8', errors='replace').splitlines():
			day, _, name = line.partition('\t')
			if not name:
				continue
			try:
				at = column(datetime.date.fromisoformat(day))
			except ValueError:
				continue
			rows.setdefault(name, [0] * WINDOW)[at] += 1
		source.write_text('', encoding='utf-8', newline='\n')
	alive = {name: counts for name, counts in rows.items() if any(counts)}
	write(alive, today, target)
	return alive


def write(rows: dict, today: datetime.date, matrix: Path = None) -> None:
	"""One row per file, sorted by name — so a new file moves no row but its own."""
	body = [f'{HEADER}{today.isoformat()}']
	body += [f'{name}\t{" ".join(str(n) for n in rows[name])}' for name in sorted(rows)]
	(matrix or MATRIX).write_text('\n'.join(body) + '\n', encoding='utf-8', newline='\n')


def span(rows: dict, days: int, today: datetime.date = None) -> list:
	"""[(path, reads)] over the last `days`, busiest first. A range is a sum of columns, nothing more.

	This is the whole reason the matrix is worth its size: week, month and semester are the same
	function with a different argument, and none of them needed storing.
	"""
	today = today or datetime.date.today()
	wanted = {column(today - datetime.timedelta(days=step)) for step in range(min(days, WINDOW))}
	totals = [(name, sum(counts[at] for at in wanted)) for name, counts in rows.items()]
	return sorted(((name, n) for name, n in totals if n), key=lambda row: (-row[1], row[0]))
