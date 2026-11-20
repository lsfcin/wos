#!/usr/bin/env python3
# What each feature ACTUALLY did, counted at the moment it ran: how often it fired, and how often it
# blocked something real. The fourth question beside what a file IS, what a name MAY BE and which
# features are LIVE — those three read declarations, this one reads behaviour.
#
# WHY THIS EXISTS. 82 features are declared and every one of them is paid for on faith
# (/ROADMAP.md § Measurement): no hook has ever been measured, so no hook can be cut on evidence and
# every kept rule is a guess wearing a rule's coat. The ablation answers "what does the workspace
# cost without X"; this answers the cheaper question first — "does X ever fire at all".
#
# THREE SIGNALS, THREE CALL SITES, AND THEY ARE DIFFERENT QUESTIONS. `fired` is recorded in
# feature_law.is_enabled(), which is the one function every switched feature passes through, so one
# call site covers all six groups. `blocked` is recorded in dispatch.py, which is the only place
# that sees a gate's exit code. A feature can fire thousands of times and block nothing — that gap
# is the whole finding, and collapsing the two into one count would hide it.
#
# `found` is the third, added 2026-09-23, and it exists because the second one cannot answer for an
# INFORMING gate. Such a gate may never exit 2, so `blocked` is structurally zero and the scoreboard
# read `1088 fired, -` for retired-tokens: it counted that the gate RAN, never that it had anything
# to say. A gate that computes findings records `found` itself, at the moment it has them — the same
# shape as the other two, the fact written where it happens.
#
# A NORM RECORDS NO `found`, and that is not an omission. A norm is written into AGENTS.md and
# obeyed; it has no detector, so there is nothing for it to have found. Its `fired` count is a
# count of sessions, and reading it as anything else is the mistake this note exists to prevent.
#
# APPEND-ONLY, AND AGGREGATED ON READ. A counter file would be read-modify-write, which races
# between parallel sessions and silently loses rows — the failure this instrument exists to avoid.
# One line per event under PIPE_BUF is an atomic append on POSIX; the reader adds them up.
#
# FAIL-OPEN, ALWAYS. A measurement that can break a gate is worse than no measurement: every write
# here is wrapped, and a failure costs a lost row rather than a blocked tool call.
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE.parent

# WOS_SCOREBOARD points this at another file, and exists for the tests: the real store is per
# machine and must not be written by a suite that builds its own repo. Same shape as
# WOS_GATES_TABLE in dispatch.py.
#
# IT LIVES BESIDE profile.local.txt, gitignored, for that file's reason: this is per-machine state,
# and a versioned copy would be a diff to review on every commit and a merge conflict on every pull.
STORE = 'scoreboard.tsv'


def path() -> Path:
	return Path(os.environ.get('WOS_SCOREBOARD') or (CORE / STORE))


# REENTRANCY, NOT A SPECIAL CASE. record() asks feature_law whether it is switched on, and
# feature_law.is_enabled() calls record() — so the first call would recurse forever. The flag ends
# that without teaching either module about the other, and without exempting this feature from its
# own switch, which would make it the one unablatable thing in the registry.
_busy = False


def enabled() -> bool:
	global _busy
	if _busy:
		return False
	_busy = True
	try:
		import feature_law
		return feature_law.is_enabled('hook-scoreboard')
	except Exception:  # noqa: BLE001 — see the fail-open note in this file's head
		return False
	finally:
		_busy = False


def record(name: str, event: str) -> None:
	"""One row: the day, the feature, and what it did. Never raises."""
	if not name or not enabled():
		return
	try:
		import datetime
		row = f'{datetime.date.today().isoformat()}\t{name}\t{event}\n'
		with open(path(), 'a', encoding='utf-8', newline='\n') as fh:
			fh.write(row)
	except Exception:  # noqa: BLE001
		return


def tally(store: Path = None) -> dict:
	"""{feature: {'fired': n, 'blocked': n, 'found': n}}, and the first date seen, from the rows."""
	counts: dict = {}
	target = store or path()
	if not target.exists():
		return counts
	for line in target.read_text(encoding='utf-8', errors='replace').splitlines():
		parts = line.split('\t')
		if len(parts) != 3:
			continue
		day, name, event = parts
		seen = counts.setdefault(name, {'fired': 0, 'blocked': 0, 'found': 0, 'since': day})
		seen['since'] = min(seen['since'], day)
		if event in seen:
			seen[event] += 1
	return counts


def started() -> str:
	"""The day the clock started — the earliest row in the store, or '' when nothing was recorded."""
	days = [row['since'] for row in tally().values()]
	return min(days) if days else ''
