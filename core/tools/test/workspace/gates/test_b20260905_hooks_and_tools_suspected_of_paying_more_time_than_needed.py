# b20260905 regression — a lifecycle hook pays for the moment it serves, and for no other.
#
# WHAT WAS MEASURED. core/tools/wos/session/hooktime, 2026-09-05, median of 5 on this clone. A tool
# call paid, PreToolUse plus PostToolUse: 0.211 s (read), 0.308 s (write), 0.221 s (shell),
# 0.222 s (Grep and friends). PreToolUse had been collapsed into one dispatcher (bf46b96);
# PostToolUse never was, so its three registrations each started an interpreter, parsed the same
# payload, asked capability() and returned 0. After the collapse: 0.116 / 0.273 / 0.121 / 0.118.
# The numbers live in core/experiments/hook-latency.md, which is where a re-run can contradict them.
#
# THE FIX THAT WAS REFUSED, AND WHY IT MATTERS MORE THAN THE ONE THAT LANDED. The cheap version was
# to match the tool names each hook serves — `Edit|Write` on post-edit.sh, `Read` on the trackers.
# test_b20260901_a_second_shell_tool_walks_past_every_read_gate refused it, and was right: a tracker
# that misses a harness's tool is worse than one that runs too often, because the gate it feeds
# keeps demanding a CONTEXT.md the session already read, and the agent cannot clear it. The saving
# had to come from running FEWER PROCESSES, never from asking FEWER TOOLS. That is what this file
# guards, and it is why the first assertion below is about matchers rather than about speed.
#
# WHY THE CONTRACT AND NOT THE CLOCK. Same reason as the sibling spec on the dispatcher: a wall
# time is a fact about one machine on one afternoon, so a threshold here would fail on a loaded CI
# box while a real regression passed on a fast one.
import json
import subprocess

import pytest
from conftest import WORKSPACE_ROOT

HOOKS = WORKSPACE_ROOT / 'core/hooks'
POST_EDIT = HOOKS / 'post-edit.sh'

# Tool names this workspace has never met, in the spirit of the b20260901 spec: a registration that
# serves these serves the next harness's tool too, which is the property a name list cannot have.
UNKNOWN_TOOLS = ('PowerShell', 'ViewFile', 'PatchFile', 'SomeFutureShell')


def configs() -> list:
	"""(harness, events dict) for every harness config in the tree that registers hooks."""
	found = []
	for harness, relative, nested in (('claude', '.claude/settings.json', False),
	                                  ('zcode', '.zcode/config.json', True)):
		path = WORKSPACE_ROOT / relative
		if not path.is_file():
			continue
		events = json.loads(path.read_text(encoding='utf-8')).get('hooks') or {}
		found.append((harness, (events.get('events') or {}) if nested else events))
	return found


def registrations(event: str) -> list:
	"""(harness, matcher, command) for one event, across every harness."""
	return [(harness, group.get('matcher', '.*'), hook.get('command', ''))
	        for harness, events in configs()
	        for group in events.get(event, []) for hook in group.get('hooks', [])]


def test_both_harness_configs_are_readable() -> None:
	"""The guard's floor: a parser that silently matched nothing would pass everything."""
	assert len(configs()) == 2, [harness for harness, _ in configs()]
	assert len(registrations('PostToolUse')) >= 2


@pytest.mark.parametrize('event', ['PreToolUse', 'PostToolUse'])
def test_no_harness_filters_a_lifecycle_hook_by_tool_name(event) -> None:
	"""b20260901's law, asked of EVERY harness rather than of Claude Code alone.

	That spec reads `.claude/settings.json` only, and ZCode had meanwhile been carrying
	`Edit|Write|ApplyPatch` and `Read` on its PostToolUse hooks — the whitelist shape, live, in the
	config the law was written about, unseen because nothing looked there. A law checked on one
	harness is a law two harnesses can disagree about.
	"""
	for harness, matcher, command in registrations(event):
		if command.endswith('agent-context.py'):
			continue  # exempt for the reason the b20260901 spec states: a moment, not a capability
		assert matcher == '.*', (
			f'{harness}: {command.rsplit("/", 1)[-1]} is registered on `{matcher}`. A matcher '
			f'naming tools goes stale the next time a harness adds one — decide in the gate.')


def test_the_two_harnesses_run_the_same_hooks_after_a_tool_call() -> None:
	"""A collapse done in one config and not the other is the enforcement layer quietly differing
	per harness, which is b20260901 one layer up."""
	by_harness: dict = {}
	for harness, _matcher, command in registrations('PostToolUse'):
		by_harness.setdefault(harness, set()).add(command.rsplit('/', 1)[-1])
	assert len(set(map(frozenset, by_harness.values()))) == 1, by_harness


@pytest.mark.parametrize('tool', UNKNOWN_TOOLS)
def test_post_edit_leaves_a_non_write_payload_without_starting_an_interpreter(tool) -> None:
	"""The saving itself. Registered on `.*`, this hook sees every tool call, so its refusal has to
	be cheaper than the question it used to ask a fresh Python to answer."""
	payload = json.dumps({'tool_name': tool, 'cwd': str(WORKSPACE_ROOT),
	                      'tool_input': {'file_path': str(WORKSPACE_ROOT / 'AGENTS.md')}})
	done = subprocess.run(['bash', str(POST_EDIT)], input=payload, capture_output=True,
	                      text=True, encoding='utf-8', cwd=WORKSPACE_ROOT)
	assert done.returncode == 0, done.stderr
	assert not done.stdout.strip(), done.stdout


def test_post_edit_refuses_before_it_resolves_the_interpreter() -> None:
	"""Structurally, because the cost being guarded is a process that never starts, and a test can
	only observe that by timing — which this file's header rules out. `gates/SPECS.md` names reading
	source as the standing exception for exactly this shape of claim."""
	body = POST_EDIT.read_text(encoding='utf-8')
	guard, interpreter = body.index('*) exit 0 ;;'), body.index('--python')
	assert guard < interpreter, (
		'post-edit.sh resolves the interpreter before deciding whether the payload is a write; '
		'that is the 0.058 s per ungated tool call this bug was about.')


@pytest.mark.parametrize('tool', UNKNOWN_TOOLS)
def test_post_edit_still_admits_a_write_from_a_tool_nobody_here_has_met(tool) -> None:
	"""The mirror half, and the one that would break silently: the shell guard is a SUPERSET test,
	so a write must reach the real capability check whatever the tool is called."""
	payload = json.dumps({'tool_name': tool, 'cwd': str(WORKSPACE_ROOT), 'tool_input': {
		'file_path': str(WORKSPACE_ROOT / 'AGENTS.md'), 'old_string': 'a', 'new_string': 'b'}})
	done = subprocess.run(['bash', str(POST_EDIT)], input=payload, capture_output=True,
	                      text=True, encoding='utf-8', cwd=WORKSPACE_ROOT)
	assert done.returncode == 0, done.stderr
