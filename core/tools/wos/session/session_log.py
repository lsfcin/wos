# session_log.py — replay a Claude Code transcript and attribute each turn's context growth.
#
# The reusable half of `context`. Sibling `usage` reads the same *.jsonl for cost; both share the
# price model in session_cost.py.
#
# Four rules, each one a bug this file shipped with:
#   1. **Size the text, not the envelope.** `len(json.dumps(att))` counts JSON escaping and, for
#      `hook_success`, the payload TWICE — it is stored in both `content` and `stdout`. That
#      inflated every attribution 1.6-3.5x in the first release.
#   2. Per-turn context is exact (the usage fields); what *entered* is known only in characters. So
#      the chars-per-token ratio is measured per turn, never a global /4. A measured ratio well
#      under ~3.5 means material enters that the transcript does not log.
#   3. **A source present on every turn absorbs that unlogged material.** Attribution splits a
#      turn's delta by logged char share, so a small constant block soaks up growth it did not
#      cause. `walk` counts appearances so the caller can flag it; it is not a finding.
#   4. A blocking gate is a failed `tool_result`, never an attachment. Scanning only attachments
#      found 1 CONTEXT GATE firing where there are 518.
import json
import re
from collections import defaultdict
from pathlib import Path

from session_cost import turn_cost

# Attachments store their text in one of these; `hook_success` carries `content` AND `stdout`
# holding the same bytes, so the first hit wins and the duplicate is never counted.
TEXT_FIELDS = ('content', 'addedLines', 'stdout')

PROJECTS = Path.home() / '.claude' / 'projects'


def project_name(root=None) -> str:
	"""The transcript directory this workspace's sessions are logged into, DERIVED not spelled.

	All three tools defaulted to the authoring machine's path in the harness's notation, so on any
	other clone they read an empty directory and said "no such project" while the transcripts sat one
	name over. The I6 ratchet missed it: it greps that path spelled with slashes, and this is the same
	path spelled with dashes. The harness's rule is one substitution — every character outside
	[A-Za-z0-9] becomes a dash — so a slash and a drive letter fall out of it alike, named nowhere.
	"""
	root = Path(root) if root else Path(__file__).resolve().parents[4]
	return re.sub(r'[^A-Za-z0-9]', '-', str(root))


def label(att: dict) -> str:
	"""One source name per injected block. Hooks carry their event, so they can be told apart."""
	kind = att.get('type', '?')
	if kind.startswith('hook_'):
		return f"hook {att.get('hookName') or att.get('command', '')[:30]}"
	return kind.replace('_', ' ')


def att_chars(att: dict) -> int:
	"""The characters a block actually contributes — its text, not its JSON envelope."""
	for field in TEXT_FIELDS:
		value = att.get(field)
		if isinstance(value, str) and value:
			return len(value)
		if isinstance(value, list) and value:
			return sum(len(v) if isinstance(v, str) else len(json.dumps(v)) for v in value)
	return len(json.dumps(att))


def blocks(message: dict) -> list:
	content = (message or {}).get('content')
	return content if isinstance(content, list) else [{'type': 'text', 'text': content or ''}]


def output_chars(message: dict) -> int:
	"""What a response actually put INTO the thread: its text and its tool-call arguments.

	Not the same as `output_tokens`. Thinking is billed there but never persisted — the block
	arrives as `{'type': 'thinking', 'thinking': '', 'signature': …}` — and it does not re-enter
	later turns, so it is paid once. Counting it as thread content is what made `usage` report a
	75% self-authored share; on the logged content alone it is 12%.
	"""
	total = 0
	for block in blocks(message):
		if block.get('type') == 'text':
			total += len(block.get('text') or '')
		elif block.get('type') == 'tool_use':
			total += len(json.dumps(block.get('input') or {}))
	return total


def _result_chars(block: dict) -> int:
	body = block.get('content')
	if isinstance(body, str):
		return len(body)
	if isinstance(body, list):
		return sum(len(b.get('text', '')) if isinstance(b, dict) else len(str(b)) for b in body)
	return len(json.dumps(body))


def walk(path: Path, sidechain: bool = False) -> dict:
	"""Replay one transcript: what entered before each turn, and what that turn's context measured.

	`sidechain` selects which population the file belongs to. A parent transcript mixes both and its
	subagent turns must be skipped; a worker's OWN transcript under `<session>/subagents/` marks
	*every* record `isSidechain: true`, so the same skip silently empties the file. That is why this
	is a parameter and not a constant — it cost the subagent report its entire population once.
	"""
	tool_of: dict = {}
	pending: dict = defaultdict(int)
	seen: set = set()
	turns: list = []
	appears: dict = defaultdict(int)
	reads = gates = prev = 0
	spend = 0.0

	for line in path.open(errors='replace', encoding='utf-8'):
		try:
			event = json.loads(line)
		except json.JSONDecodeError:
			continue
		if bool(event.get('isSidechain')) != sidechain:
			continue
		kind = event.get('type')

		if kind == 'attachment':
			att = event.get('attachment') or {}
			pending[label(att)] += att_chars(att)
		elif kind == 'user':
			for block in blocks(event.get('message')):
				if block.get('type') != 'tool_result':
					pending['user prompt'] += len(json.dumps(block))
					continue
				name = tool_of.get(block.get('tool_use_id'), '?')
				pending[f'tool {name}'] += _result_chars(block)
				gates += (block.get('is_error') is True
				          and 'CONTEXT GATE' in json.dumps(block.get('content')))
		elif kind == 'assistant':
			message = event.get('message') or {}
			for block in blocks(message):
				if block.get('type') != 'tool_use':
					continue
				target = str((block.get('input') or {}).get('file_path', ''))
				is_ctx = block.get('name') == 'Read' and target.endswith('CONTEXT.md')
				tool_of[block.get('id')] = 'ctxread' if is_ctx else block.get('name', '?')
				reads += is_ctx
			usage = message.get('usage') or {}
			request = event.get('requestId')
			if not usage or (request and request in seen):
				continue
			seen.add(request)
			context = (usage.get('input_tokens', 0) + usage.get('cache_read_input_tokens', 0)
			           + usage.get('cache_creation_input_tokens', 0))
			spend += turn_cost(message.get('model') or '', usage)
			turns.append((context - prev, dict(pending)))
			for name in pending:
				appears[name] += 1
			prev = context
			pending.clear()
			pending['assistant output'] = sum(
				len(json.dumps(b)) for b in blocks(message))

	return {'turns': turns, 'reads': reads, 'gates': gates, 'peak': prev,
	        'appears': dict(appears), 'spend': spend}


def attribute(session: dict) -> tuple:
	"""Turn 1 and the growth after it, in tokens AND raw chars, self-calibrating per turn.

	Each source maps to [tokens, chars]. Tokens answer "what share of the window is this"; chars
	answer "what do I save by deleting it". They are not the same question.
	"""
	turns = session['turns']
	if not turns:
		return {}, {}, 0, 0.0
	body = [(d, p) for d, p in turns[1:] if d > 0 and sum(p.values())]
	chars = sum(sum(p.values()) for _d, p in body)
	tokens = sum(d for d, _p in body)
	if not tokens:
		return {}, {}, turns[0][0], 0.0
	per_token = chars / tokens

	start = {k: [v / per_token, v] for k, v in turns[0][1].items()}
	growth: dict = defaultdict(lambda: [0.0, 0])
	for delta, parts in body:
		ratio = delta / sum(parts.values())
		for name, size in parts.items():
			growth[name][0] += size * ratio
			growth[name][1] += size
	return start, growth, turns[0][0], per_token


def median(values: list) -> float:
	ordered = sorted(values)
	return ordered[len(ordered) // 2] if ordered else 0.0


def spread(values: list) -> tuple:
	"""Median plus the quartiles either side — a few-percent move is not real without them."""
	ordered = sorted(values)
	if not ordered:
		return 0.0, 0.0, 0.0
	return (ordered[len(ordered) // 4], median(ordered),
	        ordered[min(len(ordered) - 1, 3 * len(ordered) // 4)])
