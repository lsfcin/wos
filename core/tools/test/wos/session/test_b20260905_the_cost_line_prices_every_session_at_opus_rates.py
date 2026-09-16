# b20260905 regression — the cost line believes the model stamp only when the record proves it.
#
# THE STAMP IS THE HARNESS'S, NOT THE API'S. A session run through ZCode on GLM-5.3-flash wrote
# `"model":"claude-opus-5"` on all 70 of its assistant lines, so /roundup reported it as opus-5 at
# 100% of spend and priced it through RATES at $5/$25 per Mtok. The id was VALID, which is why
# "refuse an unknown model" would not have caught it and is not the rule that landed.
#
# WHAT SEPARATES THEM IS `requestId`. Measured across every transcript on this disk 2026-09-05:
# 168 Anthropic-stamped responses, all carrying `req_011C…`; 8 non-Anthropic (minimax-m3), none
# carrying one. `entrypoint`, `version` and `userType` split neither way. Ruled by Lucas the same
# day: believe the stamp when the record carries a request id AND a rate is held for it, otherwise
# price nothing and print `unpriced`.
#
# The cases below are written the way the bug arrived — a foreign turn wearing an Anthropic name —
# because a spec that only tries an unknown model name would pass against the code that shipped it.
import json
import os
import subprocess
import sys

import pytest

import session_turns
from conftest import WORKSPACE_ROOT
from session_cost import RATES, UNPRICED, turn_components
from session_turns import turns

USAGE = WORKSPACE_ROOT / 'core' / 'tools' / 'wos' / 'session' / 'usage'


def response(model: str, request: str | None, out: int = 500) -> dict:
	"""One assistant record. `request=None` is a response no Anthropic API produced."""
	record: dict = {'type': 'assistant', 'message': {
		'id': f'msg_{request or "none"}', 'model': model, 'content': [{'type': 'text', 'text': 'ok'}],
		'usage': {'input_tokens': 0, 'cache_read_input_tokens': 1_000_000,
		          'cache_creation_input_tokens': 0, 'output_tokens': out}}}
	if request:
		record['requestId'] = request
	return record


@pytest.fixture
def project(tmp_path, monkeypatch):
	def build(records: list):
		root = tmp_path / 'projects'
		(root / 'proj').mkdir(parents=True)
		(root / 'proj' / 's1.jsonl').write_text(
			'\n'.join(json.dumps(r) for r in records) + '\n', encoding='utf-8', newline='\n')
		monkeypatch.setattr(session_turns, 'ROOT', root)
		return 'proj'
	return build


def test_the_bug_itself_a_foreign_turn_stamped_opus_is_not_billed_as_opus(project) -> None:
	"""The ZCode/GLM report, reproduced: a valid Anthropic id on a record with no request id."""
	name = project([response('claude-opus-5', None)])
	(_context, comp, model, _session, _out, _logged) = next(iter(turns(name)))
	assert model.startswith(UNPRICED), f'a stamp with no request id was believed: {model!r}'
	assert sum(comp.values()) == 0.0, 'an unpriceable turn must cost nothing, not opus rates'


def test_the_claimed_model_survives_in_the_label(project) -> None:
	"""Unpriced is not anonymous. What the transcript claimed is the only lead anyone has for
	working out what actually answered, so it is carried rather than dropped."""
	name = project([response('claude-opus-5', None)])
	assert 'claude-opus-5' in next(iter(turns(name)))[2]


def test_a_real_anthropic_turn_is_still_priced(project) -> None:
	"""The mirror half, and the one that would break silently: over-refusing reports every session
	as free, which is the same class of unchecked number in the other direction."""
	name = project([response('claude-opus-5', 'req_011Cabc')])
	(_context, comp, model, _session, _out, _logged) = next(iter(turns(name)))
	assert model == 'claude-opus-5'
	assert sum(comp.values()) > 0.0


def test_a_model_we_hold_no_rate_for_is_unpriced_even_with_a_request_id(project) -> None:
	"""The other half of the rule. `minimax-m3` stamps honestly and had no rate, so RATES' old
	(5.0, 25.0) default billed 8 sessions on this disk at the most expensive level it knows."""
	name = project([response('minimax-m3', 'req_011Cabc')])
	assert next(iter(turns(name)))[2].startswith(UNPRICED)


def test_no_rate_table_entry_prices_at_zero() -> None:
	"""The fallback is gone, so a model IN the table must still cost something — otherwise this
	whole guard would pass against a tool that had simply stopped pricing anything."""
	for model in RATES:
		cost = sum(turn_components(model, {'input_tokens': 1_000_000}).values())
		assert cost > 0.0, f'{model} is in RATES and prices at zero'


def test_the_roundup_line_says_unpriced_instead_of_naming_a_model(tmp_path) -> None:
	"""End-to-end on the real script — the line Lucas reads at every close, which was `opus-5 100%`
	for a session no Anthropic model answered."""
	root = tmp_path / '.claude' / 'projects' / 'proj'
	root.mkdir(parents=True)
	records = [response('claude-opus-5', None, out=5_000) for _ in range(4)]
	(root / 's1.jsonl').write_text('\n'.join(json.dumps(r) for r in records) + '\n',
	                               encoding='utf-8', newline='\n')
	# Both names, for the reason test_usage.py states: Path.home() reads USERPROFILE on Windows.
	home = {'HOME': str(tmp_path), 'USERPROFILE': str(tmp_path)}
	done = subprocess.run([sys.executable, str(USAGE), '--project', 'proj', '--session', 's1'],
	                      capture_output=True, text=True, encoding='utf-8',
	                      env={**os.environ, **home})
	assert done.returncode == 0, done.stderr
	printed = ' '.join(done.stdout.split())
	assert UNPRICED in printed, printed
	assert 'opus-5 100%' not in printed, printed
	assert '$' not in printed, f'an unpriceable session must not print dollars: {printed}'
