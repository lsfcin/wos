# T1 the context instrument (core/hooks/SPECS.md): what fills the window, attributed from the transcript.
#
# Every case here is a bug the instrument actually shipped with, kept as an invariant:
# scanning only attachments found 1 CONTEXT GATE firing where the transcripts hold 518, and a
# global chars/token constant would have smeared each turn's density across every other turn.
import json

import pytest

from session_log import attribute, walk


def turn(context: int, content=None, request: str = 'r1') -> dict:
	usage = {'input_tokens': 0, 'cache_read_input_tokens': context, 'cache_creation_input_tokens': 0}
	# A real assistant turn always says something, and its output is what enters the next turn's
	# context. An empty content list leaves nothing to calibrate on, which no transcript does.
	return {'type': 'assistant', 'requestId': request, 'model': 'claude-opus-5',
	        'message': {'usage': usage, 'model': 'claude-opus-5',
	                    'content': content or [{'type': 'text', 'text': 'ok'}]}}


def result(tool_use_id: str, body: str, is_error=None) -> dict:
	block = {'type': 'tool_result', 'tool_use_id': tool_use_id, 'content': body}
	if is_error is not None:
		block['is_error'] = is_error
	return {'type': 'user', 'message': {'content': [block]}}


def use(tool_use_id: str, name: str, path: str = '') -> dict:
	return {'type': 'tool_use', 'id': tool_use_id, 'name': name, 'input': {'file_path': path}}


@pytest.fixture
def transcript(tmp_path):
	def build(records):
		path = tmp_path / 'session.jsonl'
		path.write_text('\n'.join(json.dumps(r) for r in records) + '\n', encoding='utf-8', newline='\n')
		return path
	return build


def test_a_blocking_gate_is_counted_from_the_failed_tool_result(transcript):
	"""The bug that made gates read 1 of 131 sessions instead of 69: gates are not attachments."""
	path = transcript([
		turn(1000, [use('t1', 'Read', '/ws/x/y.py')], 'r1'),
		result('t1', 'CONTEXT GATE (Bash) - command touches files in a subtree', is_error=True),
		turn(2000, [], 'r2'),
	])
	assert walk(path)['gates'] == 1


def test_the_agent_quoting_the_gate_is_not_a_firing(transcript):
	"""Only a *failed* result is a block; the same words in a successful one are just text."""
	path = transcript([
		turn(1000, [use('t1', 'Read', '/ws/x/y.py')], 'r1'),
		result('t1', 'the hook prints CONTEXT GATE when it blocks', is_error=False),
		turn(2000, [], 'r2'),
	])
	assert walk(path)['gates'] == 0


def test_only_context_md_reads_count_as_chain_reads(transcript):
	path = transcript([
		turn(1000, [use('t1', 'Read', '/ws/core/CONTEXT.md'),
		            use('t2', 'Read', '/ws/core/tools/CONTEXT.md'),
		            use('t3', 'Read', '/ws/core/tools/wos/roundup')], 'r1'),
		turn(2000, [], 'r2'),
	])
	assert walk(path)['reads'] == 2


def test_one_turn_split_across_records_is_counted_once(transcript):
	"""A thinking block and a text block arrive as two records sharing one requestId."""
	path = transcript([
		turn(1000, [], 'r1'),
		turn(1000, [], 'r1'),
		turn(2500, [], 'r2'),
	])
	assert len(walk(path)['turns']) == 2


def test_a_sidechain_turn_never_enters_the_main_chain(transcript):
	path = transcript([
		turn(1000, [], 'r1'),
		{**turn(9999, [], 'sub'), 'isSidechain': True},
		turn(2000, [], 'r2'),
	])
	turns = walk(path)['turns']
	assert [delta for delta, _parts in turns] == [1000, 1000]


def test_attribution_is_exact_in_aggregate(transcript):
	"""Every token of growth after turn 1 lands on some source — none invented, none dropped."""
	path = transcript([
		turn(1000, [use('t1', 'Bash', '')], 'r1'),
		result('t1', 'x' * 400),
		turn(1800, [use('t2', 'Read', '/ws/a.py')], 'r2'),
		result('t2', 'y' * 4000),
		turn(6000, [], 'r3'),
	])
	_start, growth, _first, _ratio = attribute(walk(path))
	assert round(sum(tokens for tokens, _chars in growth.values())) == (1800 - 1000) + (6000 - 1800)


def test_each_turn_calibrates_on_its_own_density(transcript):
	"""Two turns of identical char count but very different token cost must not average together.

	A global chars/token constant would split the growth evenly; per-turn calibration gives the
	expensive turn its own tokens. This is the difference between measuring and estimating.
	"""
	path = transcript([
		turn(1000, [use('t1', 'Bash', '')], 'r1'),
		result('t1', 'a' * 1000),
		turn(1100, [use('t2', 'Bash', '')], 'r2'),
		result('t2', 'b' * 1000),
		turn(6100, [], 'r3'),
	])
	_start, growth, _first, _ratio = attribute(walk(path))
	# Both turns carried ~the same characters; the second cost 50x the tokens and must show it.
	assert growth['tool Bash'][0] > 4000
	# ...and the raw char column stays honest about how little text that actually was.
	assert growth['tool Bash'][1] == 2000


def test_turn_one_is_the_session_start_payload_not_growth(transcript):
	"""What is already in the window at turn 1 is reported separately, never mixed into growth."""
	path = transcript([
		{'type': 'attachment', 'attachment': {'type': 'skill_listing', 'content': 'z' * 800}},
		turn(20000, [], 'r1'),
		turn(21000, [], 'r2'),
	])
	start, growth, first, _ratio = attribute(walk(path))
	assert first == 20000
	assert 'skill listing' in start
	assert 'skill listing' not in growth


def test_a_session_with_nothing_to_calibrate_on_reports_no_ratio(transcript):
	"""One turn gives no second measurement, so the caller must be able to skip it, not divide."""
	path = transcript([turn(20000, [], 'r1')])
	_start, _growth, first, ratio = attribute(walk(path))
	assert first == 20000
	assert ratio == 0.0


def test_a_hook_payload_stored_twice_is_counted_once(transcript):
	"""`hook_success` holds the same bytes in `content` AND `stdout`.

	Sizing the JSON envelope counted both, plus every escape character — which is how the first
	release overstated the caveman activation 3.5x and the skill listing 1.8x.
	"""
	body = 'x' * 1000
	path = transcript([
		{'type': 'attachment', 'attachment': {
			'type': 'hook_success', 'hookName': 'SessionStart:startup',
			'content': body, 'stdout': body, 'command': 'node activate.js', 'exitCode': 0}},
		turn(20000, [], 'r1'),
		turn(21000, [], 'r2'),
	])
	start, _growth, _first, _ratio = attribute(walk(path))
	assert start['hook SessionStart:startup'][1] == 1000


def test_a_subagent_transcript_is_read_not_skipped(transcript):
	"""A worker's own transcript marks EVERY record isSidechain, so the main-chain skip empties it.

	This cost the subagent report its entire population of 47 once. The parent's transcript needs
	the opposite rule, guarded by test_a_sidechain_turn_never_enters_the_main_chain.
	"""
	records = [{**turn(9000, [], 'r1'), 'isSidechain': True},
	           {**turn(12000, [], 'r2'), 'isSidechain': True}]
	path = transcript(records)
	assert walk(path)['turns'] == []
	worker = walk(path, sidechain=True)
	assert [delta for delta, _parts in worker['turns']] == [9000, 3000]


def test_spend_is_measured_per_turn_from_the_shared_rate_model(transcript):
	"""Token share and spend share are different rankings; the rates have exactly one home."""
	path = transcript([turn(1000, [], 'r1'), turn(2000, [], 'r2')])
	assert walk(path)['spend'] > 0


def test_a_source_is_counted_once_per_turn_it_appears_in(transcript):
	"""Appearance frequency is what exposes a block riding along with unlogged material."""
	path = transcript([
		turn(1000, [use('t1', 'Bash', '')], 'r1'),
		result('t1', 'a' * 100),
		turn(2000, [use('t2', 'Bash', '')], 'r2'),
		result('t2', 'b' * 100),
		turn(3000, [], 'r3'),
	])
	assert walk(path)['appears']['tool Bash'] == 2
