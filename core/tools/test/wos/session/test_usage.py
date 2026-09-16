# T1 the cost instrument: what counts as one turn, and which half of output is re-read.
#
# Both cases here are bugs the tool shipped with and quoted as authority for weeks. It summed
# transcript *records* rather than API responses — 1.97x over the real project — and it treated
# thinking as thread content, which it never is, inflating the self-authored share from 12% to 75%.
import os
import json
import subprocess
import sys

import pytest

import session_turns
from conftest import WORKSPACE_ROOT
from session_turns import CHARS_PER_TOKEN, turns

# From conftest, not from parents[n]: a hop count is a second copy of where things are, and it
# broke silently the day this file moved one directory deeper (2026-08-17).
USAGE = WORKSPACE_ROOT / 'core' / 'tools' / 'wos' / 'session' / 'usage'


def response(context: int, out: int, blocks: list, request: str = 'r1') -> dict:
	usage = {'input_tokens': 0, 'cache_read_input_tokens': context,
	         'cache_creation_input_tokens': 0, 'output_tokens': out}
	return {'type': 'assistant', 'requestId': request,
	        'message': {'id': f'msg_{request}', 'usage': usage,
	                    'model': 'claude-opus-5', 'content': blocks}}


def text(body: str) -> dict:
	return {'type': 'text', 'text': body}


def thinking() -> dict:
	"""Exactly what Claude Code persists: the signature, never the reasoning."""
	return {'type': 'thinking', 'thinking': '', 'signature': 'CAISggQKkQEIEBgCKkDJRi7e'}


@pytest.fixture
def project(tmp_path, monkeypatch):
	def build(sessions: dict):
		root = tmp_path / 'projects'
		(root / 'proj').mkdir(parents=True)
		for stem, records in sessions.items():
			(root / 'proj' / f'{stem}.jsonl').write_text(
				'\n'.join(json.dumps(r) for r in records) + '\n', encoding='utf-8', newline='\n')
		monkeypatch.setattr(session_turns, 'ROOT', root)
		return 'proj'
	return build


def test_one_response_split_across_records_is_one_turn(project):
	"""The 1.97x bug. Claude Code repeats the whole usage object on every content block it writes."""
	name = project({'s1': [
		response(1000, 500, [thinking()], 'r1'),
		response(1000, 500, [text('hello')], 'r1'),
		response(1000, 500, [{'type': 'tool_use', 'id': 't1', 'name': 'Bash',
		                      'input': {'command': 'ls'}}], 'r1'),
	]})
	rows = list(turns(name))
	assert len(rows) == 1
	assert rows[0][4] == 500, 'output_tokens must be read once, not once per record'


def test_the_records_of_one_response_pool_their_logged_output(project):
	"""Content is spread across the records, so the chars have to be summed even though usage is not."""
	name = project({'s1': [
		response(1000, 500, [text('a' * 36)], 'r1'),
		response(1000, 500, [text('b' * 36)], 'r1'),
	]})
	assert list(turns(name))[0][5] == pytest.approx(72 / CHARS_PER_TOKEN)


def test_thinking_is_billed_but_never_logged(project):
	"""It is paid once and never re-read, so it must not enter the tokens that land in the thread."""
	name = project({'s1': [response(1000, 900, [thinking(), text('ok')], 'r1')]})
	row = list(turns(name))[0]
	assert row[4] == 900
	assert row[5] == pytest.approx(2 / CHARS_PER_TOKEN), 'only the two chars of "ok" enter the thread'


def test_tool_call_arguments_are_logged_output(project):
	"""86% of what this workspace emits is tool_use input; excluding it would measure prose alone."""
	name = project({'s1': [response(1000, 500, [
		{'type': 'tool_use', 'id': 't1', 'name': 'Write', 'input': {'content': 'x' * 100}}], 'r1')]})
	payload = len(json.dumps({'content': 'x' * 100}))
	assert list(turns(name))[0][5] == pytest.approx(payload / CHARS_PER_TOKEN)


def test_the_same_request_id_in_two_sessions_stays_two_turns(project):
	"""Responses are keyed per transcript. Merging across files would delete a whole session's turn."""
	name = project({'s1': [response(1000, 500, [text('a')], 'r1')],
	                's2': [response(2000, 500, [text('b')], 'r1')]})
	assert len(list(turns(name))) == 2


def test_a_response_with_no_request_id_is_still_a_turn(project):
	"""Older transcripts predate requestId; dropping them would silently shrink the population."""
	record = response(1000, 500, [text('a')], 'r1')
	del record['requestId']
	name = project({'s1': [record, response(2000, 500, [text('b')], 'r2')]})
	assert len(list(turns(name))) == 2


def test_a_sidechain_response_never_enters_the_main_chain(project):
	"""Subagent turns are billed in their own transcript; counting them here doubles the worker."""
	side = response(1000, 500, [text('a')], 'r1')
	side['isSidechain'] = True
	name = project({'s1': [side, response(2000, 500, [text('b')], 'r2')]})
	assert len(list(turns(name))) == 1


def test_a_thinking_heavy_session_does_not_read_as_self_authored(tmp_path):
	"""End-to-end on the real script: the claim the whole cost model rested on.

	Ten turns whose output is almost entirely thinking. Nothing lands in the thread, so the
	self-authored share must stay near zero — the old `cum += output_tokens` drove it to the 1.0
	cap by turn three and reported 75%.
	"""
	root = tmp_path / '.claude' / 'projects' / 'proj'
	root.mkdir(parents=True)
	records = [response(10_000 * n, 5_000, [thinking(), text('ok')], f'r{n}')
	           for n in range(1, 11)]
	(root / 's1.jsonl').write_text('\n'.join(json.dumps(r) for r in records) + '\n', encoding='utf-8', newline='\n')
	# INHERIT, then override home under BOTH names. Replacing the environment outright is a POSIX
	# habit: a bare env has no USERPROFILE, and Path.home() reads USERPROFILE rather than HOME on
	# Windows — so the tool crashed resolving home. Setting both names redirects it on either
	# system with no branch, and inheriting the rest keeps the interpreter able to start at all.
	# Redirection is the point: without it this reads Lucas's real transcripts.
	home = {'HOME': str(tmp_path), 'USERPROFILE': str(tmp_path)}
	out = subprocess.run([sys.executable, str(USAGE), '--project', 'proj'],
	                     capture_output=True, text=True, env={**os.environ, **home}, encoding='utf-8')
	assert out.returncode == 0, out.stderr
	printed = ' '.join(out.stdout.split())
	assert '10 turns' in printed
	assert 'written ourselves 0.0%' in printed
	assert 'of which unlogged 100.0%' in printed
	assert 'really costs 1.0x list price' in printed
