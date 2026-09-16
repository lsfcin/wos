# session_trace.py — what a session DID: who it spawned, where its clock went, what came back loudest.
#
# The three siblings here price a session (`usage`), attribute what filled it (`context`) and rank
# what it read (`reads`). None of them could say a session delegated at all: subagent turns are
# billed in their own transcripts under `<session>/subagents/`, which no instrument opened, and
# `core/experiments/output-cost.md` carried "subagent turns are excluded" as a standing limitation.
#
# NOTHING HERE IS NEW INSTRUMENTATION. `subagent_type`, the spawn's own description, each worker's
# `usage` and every record's `timestamp` were already on disk; what was missing was a reader.
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_cost import UNPRICED
from session_log import _result_chars, blocks
from session_turns import paths_for, responses

# DECLARED, NOT DERIVED — the same discipline as session_turns.CHARS_PER_TOKEN, and for the same
# reason: there is no clean calibration. A transcript records when a record was WRITTEN, never how
# long the machine worked on it, so "waiting" can only be a gap wider than some threshold. At 120s
# the split counts a long tool call as work and a coffee as waiting. Move it and both numbers move
# together; what it can never do is invent time the span does not contain.
IDLE_SECONDS = 120.0

# A Bash call that RUNS one of our own tools is that tool's output, not Bash's. Without this the
# loudest-tools ranking says `Bash` and stops, which answers a question about the harness where the
# ROADMAP asked one about us. `core/run tools/…` and a direct `core/tools/…` are the same call.
#
# ANCHORED AT THE START OF A COMMAND, because running a tool and READING ITS SOURCE are opposite
# facts and a bare search cannot tell them apart. `sed -n 1,200p core/tools/wos/roundup` reported
# 11,003 chars as roundup's own output on the first run of this report; the path is an argument to
# sed there, and sed is the tool that printed.
OURS = re.compile(r'^core/(?:run\s+)?tools/([\w.\-/]+)')
# Words that may precede the path and still leave it the thing being run.
RUNNERS = re.compile(r'^(?:\w+=\S+\s+|(?:python3?|sh|bash|uv\s+run|exec)\s+)+')
SEGMENT = re.compile(r'\|\||&&|[|;\n]')


def _tool_name(name: str, command: str) -> str:
	"""One tool, one name. A path's trailing slash and a pytest `::case` suffix are the same call as
	the path without them, and left alone they split one tool's volume across two rows."""
	if name != 'Bash':
		return name
	for segment in SEGMENT.split(command):
		bare = RUNNERS.sub('', segment.strip())
		if found := OURS.match(bare):
			return f'core/tools/{found.group(1).split("::")[0].rstrip("/")}'
	return name


def _stamps(path: Path) -> list:
	"""Every timestamp in one transcript, in order. Records without one are not events."""
	found = []
	for line in path.open(errors='replace', encoding='utf-8'):
		if '"timestamp"' not in line:
			continue
		try:
			stamp = (json.loads(line) or {}).get('timestamp')
		except json.JSONDecodeError:
			continue
		if stamp:
			found.append(datetime.fromisoformat(stamp.replace('Z', '+00:00')))
	return sorted(found)


# What a worker no spawn record claims is called on screen. One spelling: the report counts these
# rows separately and must recognise them without re-deriving the rule.
UNCLAIMED = 'continued'


def _worker(path: Path, agent: str) -> dict:
	"""One worker's own numbers, read from its own transcript. An unpriced model keeps its name, so
	a worker we cannot price is visible rather than averaged in as free."""
	file = path.parent / path.stem / 'subagents' / f'agent-{agent}.jsonl'
	cost = 0.0
	models: dict = defaultdict(int)
	rows = list(responses(file, True).values()) if file.is_file() else []
	for _context, components, model, _stem, _out, _logged in rows:
		cost += sum(components.values())
		models[model] += 1
	return {'agent': agent, 'turns': len(rows), 'cost': cost, 'models': dict(models),
	        'session': path.stem, 'transcript': file.is_file()}


def spawns(project: str, session: str = '') -> list:
	"""One row per worker a session ran, joined to the spawn that asked for it where there was one.

	The join is `tool_result.toolUseResult.agentId`, the ONLY link between a spawn and its worker:
	the file is `<session>/subagents/agent-<agentId>.jsonl`, and the parent's `tool_use` knows the
	type and the task but not the id.

	EVERY WORKER TRANSCRIPT IS A ROW, spawned or not. `core/experiments/delegation.md` owes the
	hand-check "worker transcripts must equal spawns", and on 2026-09-15 it did not hold: 55 files
	against 51 spawns. The four were `SendMessage` continuations of background agents, which open a
	fresh transcript with no `Agent` tool_use anywhere to claim them. Dropping them would have
	understated delegated spend — the direction of error every correction in
	`core/experiments/output-cost.md` had to undo — so they are rows typed `continued` instead.
	"""
	rows = []
	for path in paths_for(project, session):
		asked: dict = {}
		claimed: set = set()
		for line in path.open(errors='replace', encoding='utf-8'):
			try:
				event = json.loads(line)
			except json.JSONDecodeError:
				continue
			for block in blocks(event.get('message') or {}):
				if block.get('type') == 'tool_use' and block.get('name') == 'Agent':
					asked[block.get('id')] = (block.get('input') or {})
				elif block.get('type') == 'tool_result' and block.get('tool_use_id') in asked:
					result = event.get('toolUseResult')
					agent = result.get('agentId') if isinstance(result, dict) else ''
					if not agent:
						continue
					claimed.add(agent)
					sent = asked[block.get('tool_use_id')]
					rows.append({**_worker(path, agent), 'claimed': True,
					             'type': sent.get('subagent_type') or 'claude',
					             'task': sent.get('description') or ''})
		folder = path.parent / path.stem / 'subagents'
		for file in sorted(folder.glob('agent-*.jsonl')):
			agent = file.stem.removeprefix('agent-')
			if agent not in claimed:
				rows.append({**_worker(path, agent), 'claimed': False,
				             'type': UNCLAIMED, 'task': 'no spawn record — a SendMessage'})
	return rows


def clock(project: str, session: str = '') -> dict:
	"""How long a session took, split into working and waiting. Never what it cost.

	The three instruments beside this one measure spend; none could tell "ran ten hours" from
	"Lucas was away for eight". Spans are summed per transcript, so a `--project` run over many
	sessions adds their spans rather than measuring the wall between the first and the last.
	"""
	span = waiting = 0.0
	gaps = 0
	for path in paths_for(project, session):
		stamps = _stamps(path)
		if len(stamps) < 2:
			continue
		span += (stamps[-1] - stamps[0]).total_seconds()
		for before, after in zip(stamps, stamps[1:]):
			idle = (after - before).total_seconds()
			if idle > IDLE_SECONDS:
				waiting += idle
				gaps += 1
	return {'span': span, 'working': span - waiting, 'waiting': waiting, 'gaps': gaps}


def loudest(project: str, session: str = '') -> list:
	"""[(name, chars, calls)] by what each tool RETURNED, descending.

	Returned, not requested: a tool's output enters the context whether it is read or not, and that
	is the cost `core/hooks/compact/` exists as a threshold question about. Arguments are the other
	half and belong to `usage`, which already prices them as logged output.
	"""
	chars: dict = defaultdict(int)
	calls: dict = defaultdict(int)
	for path in paths_for(project, session):
		named: dict = {}
		for line in path.open(errors='replace', encoding='utf-8'):
			try:
				event = json.loads(line)
			except json.JSONDecodeError:
				continue
			if event.get('isSidechain'):
				continue
			for block in blocks(event.get('message') or {}):
				if block.get('type') == 'tool_use':
					command = str((block.get('input') or {}).get('command', ''))
					named[block.get('id')] = _tool_name(block.get('name') or '?', command)
				elif block.get('type') == 'tool_result' and block.get('tool_use_id') in named:
					name = named[block['tool_use_id']]
					chars[name] += _result_chars(block)
					calls[name] += 1
	return sorted(((n, c, calls[n]) for n, c in chars.items()), key=lambda row: -row[1])


def main_cost(project: str, session: str = '') -> tuple:
	"""(turns, cost) of the main thread alone — the denominator the delegation share is read against.

	Unpriced turns are counted and never averaged in, the same way `usage.brief` does it: dividing
	by every turn would report a session as cheaper the less we know about it (b20260905).
	"""
	count = 0
	cost = 0.0
	for path in paths_for(project, session):
		for _ctx, components, model, _stem, _out, _logged in responses(path).values():
			if model.startswith(UNPRICED):
				continue
			count += 1
			cost += sum(components.values())
	return count, cost
