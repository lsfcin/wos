# T1 the trace instrument: who a session spawned, where its clock went, and what came back loudest.
#
# The cases here are the three traps this measurement fell into before it was an instrument. A
# worker's transcript marks EVERY record `isSidechain: true`, so the skip that is right for a parent
# empties the worker — that one cost the subagent report its entire population once. A worker file
# on disk that no spawn claimed is the hand-check `core/experiments/delegation.md` owes. And a Bash
# call that runs one of our own tools is that tool's output, not Bash's.
import json

import pytest

import session_turns
from session_trace import IDLE_SECONDS, clock, loudest, main_cost, spawns

STAMP = '2026-09-15T10:00:00.000Z'


def response(cost_model: str = 'claude-opus-5', out: int = 500, request: str = 'r1',
             sidechain: bool = False) -> dict:
	usage = {'input_tokens': 0, 'cache_read_input_tokens': 1000,
	         'cache_creation_input_tokens': 0, 'output_tokens': out}
	record = {'type': 'assistant', 'requestId': request, 'timestamp': STAMP,
	          'message': {'usage': usage, 'model': cost_model, 'content': [{'type': 'text',
	                                                                       'text': 'ok'}]}}
	if sidechain:
		record['isSidechain'] = True
	return record


def spawn(tool_id: str, agent: str, kind: str = 'Explore', task: str = 'look') -> list:
	"""The two records a delegation writes: the ask, and the result that names the worker."""
	return [
		{'type': 'assistant', 'timestamp': STAMP, 'message': {'content': [
			{'type': 'tool_use', 'id': tool_id, 'name': 'Agent',
			 'input': {'subagent_type': kind, 'description': task, 'prompt': 'go'}}]}},
		{'type': 'user', 'timestamp': STAMP, 'toolUseResult': {'agentId': agent},
		 'message': {'content': [{'type': 'tool_result', 'tool_use_id': tool_id,
		                          'content': 'done'}]}},
	]


def call(tool_id: str, name: str, sent: dict, back: str) -> list:
	return [
		{'type': 'assistant', 'timestamp': STAMP, 'message': {'content': [
			{'type': 'tool_use', 'id': tool_id, 'name': name, 'input': sent}]}},
		{'type': 'user', 'timestamp': STAMP, 'message': {'content': [
			{'type': 'tool_result', 'tool_use_id': tool_id, 'content': back}]}},
	]


@pytest.fixture
def project(tmp_path, monkeypatch):
	"""A transcript directory shaped the way the harness shapes one: workers live in a folder named
	after the parent's own stem, never beside it. Reading the flat directory alone is what produced
	the retired "nothing has ever been delegated" claim."""
	def build(sessions: dict, workers: dict = None):
		root = tmp_path / 'projects'
		(root / 'proj').mkdir(parents=True)
		for stem, records in sessions.items():
			(root / 'proj' / f'{stem}.jsonl').write_text(
				'\n'.join(json.dumps(r) for r in records) + '\n', encoding='utf-8', newline='\n')
		for (stem, agent), records in (workers or {}).items():
			folder = root / 'proj' / stem / 'subagents'
			folder.mkdir(parents=True, exist_ok=True)
			(folder / f'agent-{agent}.jsonl').write_text(
				'\n'.join(json.dumps(r) for r in records) + '\n', encoding='utf-8', newline='\n')
		monkeypatch.setattr(session_turns, 'ROOT', root)
		return 'proj'
	return build


def test_a_worker_is_read_even_though_every_record_is_sidechain(project):
	"""The trap that emptied the subagent report: a worker's OWN transcript marks all of itself
	sidechain, so the skip that is correct for the parent deletes the whole file."""
	name = project({'s1': spawn('t1', 'a1')},
	               {('s1', 'a1'): [response(request='w1', sidechain=True),
	                               response(request='w2', sidechain=True)]})
	rows = spawns(name)
	assert len(rows) == 1 and rows[0]['claimed']
	assert rows[0]['turns'] == 2, 'both worker responses must be counted'
	assert rows[0]['cost'] > 0 and rows[0]['models'] == {'claude-opus-5': 2}


def test_the_spawn_names_the_type_and_the_worker_names_the_cost(project):
	"""Neither half is on its own record: the parent knows what it asked for, the worker what it
	spent, and `toolUseResult.agentId` is the only thing joining them."""
	name = project({'s1': spawn('t1', 'a1', kind='general-purpose', task='sweep the tree')},
	               {('s1', 'a1'): [response(request='w1', sidechain=True)]})
	row = spawns(name)[0]
	assert row['type'] == 'general-purpose' and row['task'] == 'sweep the tree'


def test_a_worker_no_spawn_claimed_is_still_counted_and_named(project):
	"""The hand-check delegation.md owes — workers must equal spawns — failed on 2026-09-15: 55 files
	against 51 spawns, the four being SendMessage continuations of background agents, which open a
	transcript no `Agent` tool_use can claim. Dropping them understates delegated spend, which is
	the direction of error every correction in output-cost.md had to undo."""
	name = project({'s1': spawn('t1', 'a1')},
	               {('s1', 'a1'): [response(request='w1', sidechain=True)],
	                ('s1', 'a9'): [response(request='w2', sidechain=True)]})
	rows = spawns(name)
	assert len(rows) == 2, 'every worker transcript on disk is a row'
	loose = [row for row in rows if not row['claimed']]
	assert [row['agent'] for row in loose] == ['a9']
	assert loose[0]['type'] == 'continued' and loose[0]['cost'] > 0


def test_a_worker_on_an_unbelievable_stamp_is_never_priced_at_opus(project):
	"""b20260905, one level down. The worker path inherits `trusted_model` rather than re-deriving
	it: no request id means no rate, and a worker reported at opus rates is a number nobody checks."""
	blind = response(request='w1', sidechain=True)
	del blind['requestId']
	name = project({'s1': spawn('t1', 'a1')}, {('s1', 'a1'): [blind]})
	row = spawns(name)[0]
	assert row['cost'] == 0.0
	assert list(row['models']) == ['unpriced (claude-opus-5)']


def test_a_session_that_spawned_nothing_still_prices_its_main_thread(project):
	"""The common case. It must not read as a session that delegated and spent zero."""
	name = project({'s1': [response(request='r1')]})
	assert spawns(name) == []
	turns, cost = main_cost(name)
	assert turns == 1 and cost > 0


def test_a_gap_wider_than_the_threshold_is_waiting_and_a_narrower_one_is_work(project):
	"""The split a transcript can actually support: it records when a record was WRITTEN, never how
	long the machine worked on it, so waiting is a gap over a declared threshold and nothing more."""
	idle = IDLE_SECONDS + 60
	stamps = ['2026-09-15T10:00:00.000Z', '2026-09-15T10:00:30.000Z',
	          f'2026-09-15T10:{int(30 + idle) // 60:02d}:{int(30 + idle) % 60:02d}.000Z']
	name = project({'s1': [{'type': 'user', 'timestamp': s, 'message': {'content': 'x'}}
	                       for s in stamps]})
	split = clock(name)
	assert split['gaps'] == 1, 'the 30s gap is work, the long one is not'
	assert split['waiting'] == pytest.approx(idle)
	assert split['working'] == pytest.approx(split['span'] - idle)


def test_our_own_tool_is_ranked_under_its_own_name_not_under_bash(project):
	"""The ROADMAP asked what OUR tools print. A ranking that says `Bash` and stops answers a
	question about the harness instead, and two spellings of one path are one tool."""
	name = project({'s1': [
		*call('t1', 'Bash', {'command': 'core/run tools/wos/size --scope repo'}, 'a' * 100),
		*call('t2', 'Bash', {'command': 'core/tools/wos/size/'}, 'b' * 50),
		*call('t3', 'Bash', {'command': 'ls -la'}, 'c' * 10),
		*call('t4', 'Read', {'file_path': '/x'}, 'd' * 200),
	]})
	ranked = dict((n, (c, calls)) for n, c, calls in loudest(name))
	assert ranked['core/tools/wos/size'] == (150, 2), 'one tool, one row, both spellings'
	assert ranked['Bash'] == (10, 1), 'a call that is not ours stays Bash'
	assert ranked['Read'] == (200, 1)


def test_reading_a_tool_s_source_is_not_that_tool_printing(project):
	"""Running a tool and reading its source are opposite facts, and a bare path search cannot tell
	them apart: `sed -n 1,200p core/tools/wos/roundup` billed 11,003 chars to roundup on this
	report's first run. The path is sed's argument there, and sed is what printed."""
	name = project({'s1': [
		*call('t1', 'Bash', {'command': 'sed -n 1,200p core/tools/wos/roundup'}, 'a' * 500),
		*call('t2', 'Bash', {'command': 'grep -n STATE core/tools/wos/roundup'}, 'b' * 100),
		*call('t3', 'Bash', {'command': 'python3 core/tools/wos/roundup --leave-dirty'}, 'c' * 40),
		*call('t4', 'Bash', {'command': 'git status && core/run tools/wos/size'}, 'd' * 20),
	]})
	ranked = dict((n, (c, calls)) for n, c, calls in loudest(name))
	assert ranked['Bash'] == (600, 2), 'sed and grep printed, not the file they were pointed at'
	assert ranked['core/tools/wos/roundup'] == (40, 1), 'an interpreter still leaves the tool running'
	assert ranked['core/tools/wos/size'] == (20, 1), 'a tool after && is still the tool that ran'


def test_a_read_is_sized_by_what_came_back_not_by_what_was_asked(project):
	"""session_log rule 1, inherited: the JSON envelope is not the text, and an offset read costs
	what it was served. Sizing the request would rank a one-line Read beside a whole file."""
	name = project({'s1': call('t1', 'Read', {'file_path': '/very/long/path/' + 'x' * 200}, 'hi')})
	assert loudest(name) == [('Read', 2, 1)]
