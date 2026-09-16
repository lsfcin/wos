# T0 the agent-context briefing (core/hooks/SPECS.md): the orchestrator's duty, done by a hook.
#
# Subagents are exempt from the context gate, which moves the duty of supplying context to the
# orchestrator. This hook is what stops that duty being a discipline nobody keeps. It induces and
# never blocks.
#
# The two-event split is measured, not assumed: PreToolUse:Agent sees the prompt but has no
# agent_id and its additionalContext returns to the PARENT; SubagentStart can inject into the worker
# but never sees the prompt. `prompt_id` is identical across both and is the join key.
import json
import subprocess
import uuid
from pathlib import Path

import pytest

from conftest import WORKSPACE_ROOT
from platform_law import interpreter

HOOK = WORKSPACE_ROOT / 'core/hooks/read/agent-context.py'


def _run(payload: dict) -> subprocess.CompletedProcess:
	return subprocess.run([interpreter(), str(HOOK)], input=json.dumps(payload),
	                      capture_output=True, text=True, encoding='utf-8')


@pytest.fixture
def prompt_id():
	value = f'test-{uuid.uuid4()}'
	yield value
	Path(f'/tmp/claude_agent_ctx_{value}.txt').unlink(missing_ok=True)


def _spawn(prompt_id: str, prompt: str) -> subprocess.CompletedProcess:
	return _run({'hook_event_name': 'PreToolUse', 'tool_name': 'Agent', 'prompt_id': prompt_id,
	             'cwd': str(WORKSPACE_ROOT), 'tool_input': {'prompt': prompt, 'description': ''}})


def _start(prompt_id: str) -> subprocess.CompletedProcess:
	return _run({'hook_event_name': 'SubagentStart', 'prompt_id': prompt_id,
	             'agent_id': 'agent-xyz', 'agent_type': 'general-purpose'})


def test_a_path_in_the_prompt_becomes_a_briefing(prompt_id) -> None:
	_spawn(prompt_id, 'Please edit core/hooks/brain/brain_attention.py and report back.')
	done = _start(prompt_id)
	assert done.returncode == 0
	body = json.loads(done.stdout)['hookSpecificOutput']['additionalContext']
	assert 'core/hooks/brain/CONTEXT.md' in body
	assert 'core/hooks/CONTEXT.md' in body


def test_the_briefing_carries_one_line_each_not_the_whole_head(prompt_id) -> None:
	"""Handing over the full head would recreate the cost the exemption exists to avoid."""
	_spawn(prompt_id, 'Look at core/hooks/brain/brain_attention.py')
	body = json.loads(_start(prompt_id).stdout)['hookSpecificOutput']['additionalContext']
	entries = [line for line in body.splitlines() if line.startswith('- ')]
	assert entries
	assert all(len(line) < 200 for line in entries)
	# The `>` self-description is what a worker needs, and it must actually be there.
	assert any('attention stats' in line for line in entries)


@pytest.mark.parametrize('prose', [
	'Your task concerns the file core/hooks/brain/brain_attention.py.',
	'Look at core/hooks/brain/brain_attention.py, then stop.',
	'See (core/hooks/brain/brain_attention.py) for detail.',
	'Is core/hooks/brain/brain_attention.py correct?',
])
def test_a_path_ending_a_sentence_is_still_found(prompt_id, prose) -> None:
	"""The first live check found nothing because the path ended a sentence.

	The unit tests all happened to put a space after the path, so they passed while the feature did
	not work at all. Prose punctuation is the normal case in an agent prompt, not the edge case.
	"""
	_spawn(prompt_id, prose)
	body = json.loads(_start(prompt_id).stdout)['hookSpecificOutput']['additionalContext']
	assert 'core/hooks/brain/CONTEXT.md' in body


def test_a_prompt_naming_nothing_injects_nothing(prompt_id) -> None:
	"""Induce, never block: a thin prompt yields a thin briefing, not an error."""
	done = _spawn(prompt_id, 'Summarise the discussion so far.')
	assert done.returncode == 0
	started = _start(prompt_id)
	assert started.returncode == 0
	assert started.stdout.strip() == ''


def test_workers_in_one_turn_share_the_turn_briefing(prompt_id) -> None:
	"""Accepted over-breadth: the only worker id arrives after the prompt is gone, so the blob is
	per-turn. Union, never mismatch."""
	_spawn(prompt_id, 'Edit core/hooks/brain/brain_attention.py')
	_spawn(prompt_id, 'Edit core/tools/wos/session/session_log.py')
	body = json.loads(_start(prompt_id).stdout)['hookSpecificOutput']['additionalContext']
	assert 'core/hooks/brain/CONTEXT.md' in body
	assert 'core/tools/wos/session/CONTEXT.md' in body


def test_a_repeated_path_is_not_briefed_twice(prompt_id) -> None:
	_spawn(prompt_id, 'Edit core/hooks/brain/brain_attention.py')
	_spawn(prompt_id, 'Also core/hooks/brain/brain_stats.py, same directory')
	body = json.loads(_start(prompt_id).stdout)['hookSpecificOutput']['additionalContext']
	assert body.count('core/hooks/brain/CONTEXT.md') == 1


def test_an_unknown_turn_injects_nothing(prompt_id) -> None:
	"""A worker whose turn parked no paths must start clean, not crash."""
	done = _start(f'never-collected-{uuid.uuid4()}')
	assert done.returncode == 0
	assert done.stdout.strip() == ''


def test_the_hook_ignores_events_it_does_not_own(prompt_id) -> None:
	done = _run({'hook_event_name': 'PreToolUse', 'tool_name': 'Bash', 'prompt_id': prompt_id,
	             'tool_input': {'command': 'wc -l core/hooks/brain/brain_attention.py'}})
	assert done.returncode == 0
	assert done.stdout.strip() == ''
