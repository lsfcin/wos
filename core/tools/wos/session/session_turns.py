# session_turns.py — what counts as ONE assistant turn, and how much of it lands in the thread.
#
# Split out of `usage` when that file hit the size gate. It answers a question `usage` had been
# answering wrong: a transcript record is not a turn. Claude Code writes one record per content
# block and repeats the whole `usage` object on each, so a loop over records bills the same
# response several times — 1.97x over -mnt-workspace, 22,354 records against 11,370 responses,
# with `output_tokens` identical across every record of an id. `session_log.walk()` deduped on
# `requestId` from the start and has a test for it; `usage` ran its own loop and did not.
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_cost import UNPRICED, priced, turn_components
from session_log import output_chars


def trusted_model(event: dict, model: str) -> str:
	"""The model that answered, or `unpriced` when the transcript cannot be believed about it.

	THE STAMP IS THE HARNESS'S, NOT THE API'S. A session run through ZCode on GLM-5.3-flash wrote
	`"model":"claude-opus-5"` on all 70 of its assistant lines, so /roundup reported it as opus at
	100% of spend, at opus prices (b20260905). The id was VALID, so refusing unknown names would
	not have caught it.

	WHAT SEPARATES THEM IS `requestId`. Every real Anthropic API response carries one (`req_011C…`)
	and nothing else in the record does: across every transcript on this disk, 2026-09-05, all 168
	Anthropic-stamped responses had one and all 8 non-Anthropic ones (minimax-m3) had none —
	`entrypoint`, `version` and `userType` split neither way. So the rule is: believe the stamp when
	the record carries a request id AND we hold a rate for it; otherwise price nothing and say so.
	The failure direction is honest — a real turn reported as unpriced is visible and fixable, a
	foreign turn reported at opus rates is a number nobody can check.
	"""
	if not event.get('requestId') or not priced(model):
		return f'{UNPRICED} ({model})' if model else UNPRICED
	return model

ROOT = Path.home() / '.claude' / 'projects'

# Logged output is known in characters; only the whole turn is known in tokens. Declared, not
# derived: the obvious calibration — responses carrying no thinking block — measures 1.6 chars/tok,
# so it is not clean either. Tool-call JSON is denser than 3.6, which makes logged tokens an
# UNDERcount and every self-authored share computed from them a floor.
CHARS_PER_TOKEN = 3.6


def paths_for(project: str, session: str = '') -> list:
	"""The transcripts to read, or exit with the name that was not found."""
	directory = ROOT / project
	if not directory.is_dir():
		sys.exit(f'no such project: {directory}')
	paths = sorted(directory.glob('*.jsonl'))
	if session:
		paths = [p for p in paths if p.stem == session]
		if not paths:
			sys.exit(f'no such session: {session}')
	return paths


def responses(path: Path, sidechain: bool = False) -> dict:
	"""One transcript's API responses, merged by `requestId`: the rule, in one place.

	`sidechain` selects the population, exactly as `session_log.walk` does and for the same reason:
	a parent transcript mixes both and its subagent turns must be skipped, while a worker's OWN
	transcript under `<session>/subagents/` marks EVERY record `isSidechain: true`, so the skip that
	is right for the parent silently empties the worker. A caller that re-derived the merge instead
	of calling this is what `usage` did, and it billed every response 1.97 times.
	"""
	merged: dict = {}
	with path.open(errors='replace', encoding='utf-8') as handle:
		for line in handle:
			if '"usage"' not in line:
				continue
			try:
				event = json.loads(line)
			except json.JSONDecodeError:
				continue
			if event.get('type') != 'assistant' or bool(event.get('isSidechain')) != sidechain:
				continue
			message = event.get('message') or {}
			usage = message.get('usage') or {}
			model = message.get('model') or ''
			if not usage or model.startswith('<'):
				continue
			model = trusted_model(event, model)
			key = event.get('requestId') or f'_{len(merged)}'
			if key not in merged:
				context = (usage.get('input_tokens', 0)
				           + usage.get('cache_read_input_tokens', 0)
				           + usage.get('cache_creation_input_tokens', 0))
				merged[key] = [context, turn_components(model, usage), model, path.stem,
				               usage.get('output_tokens', 0), 0.0]
			merged[key][5] += output_chars(message) / CHARS_PER_TOKEN
	return merged


def turns(project: str, session: str = ''):
	"""Every main-chain API response: (context, cost, model, session, output tok, logged tok).

	One row per *response*, not per transcript record — see this file's header for why that is not
	the same thing. Logged chars are summed across the response's records, because its content is
	spread over them; `usage` is read from the first record and never added twice.
	"""
	for path in paths_for(project, session):
		for row in responses(path).values():
			yield tuple(row)
