# T0 the subagent exemption (core/hooks/SPECS.md): a worker is not made to read the routing chain.
#
# Ruled 2026-08-15 (Lucas). The argument is the type system's own — CONTEXT.md carries *routing*,
# constraints live in SPECS.md — so a worker handed one explicit path does not need the chain, while
# spec-read-gate.py must keep firing for everyone. Measured in
# core/experiments/subagent-context-chain.md.
#
# Before this, the exemption existed by accident and was *arbitrary*: a worker inherited the
# parent's session_id and so inherited its seen-set, which left it ungated only for subtrees the
# parent happened to have visited. These tests hold the deliberate version.
import json
import subprocess
import uuid

import pytest

from conftest import WORKSPACE_ROOT
from platform_law import interpreter

CONTEXT_GATE = WORKSPACE_ROOT / 'core/hooks/read/context-gate.py'
BASH_GATE = WORKSPACE_ROOT / 'core/hooks/read/bash-context-gate.py'
# Any file under a subtree that carries a CONTEXT.md chain. Its content is irrelevant.
DEEP_FILE = WORKSPACE_ROOT / 'core/hooks/brain/brain_attention.py'


def _run(gate, payload: dict) -> subprocess.CompletedProcess:
	# A fresh session id every call, so the marker file cannot exist and the whole chain is unseen.
	payload.setdefault('session_id', f'test-{uuid.uuid4()}')
	payload.setdefault('cwd', str(WORKSPACE_ROOT))
	return subprocess.run([interpreter(), str(gate)], input=json.dumps(payload),
	                      capture_output=True, text=True, encoding='utf-8')


def _read_payload() -> dict:
	return {'tool_name': 'Read', 'tool_input': {'file_path': str(DEEP_FILE)}}


def _bash_payload() -> dict:
	return {'tool_name': 'Bash', 'tool_input': {'command': f'wc -l {DEEP_FILE}'}}


@pytest.mark.parametrize('gate,payload', [
	(CONTEXT_GATE, _read_payload()),
	(BASH_GATE, _bash_payload()),
])
def test_the_main_thread_is_still_gated(gate, payload) -> None:
	"""The exemption must not have turned the gate off for everyone."""
	done = _run(gate, dict(payload))
	assert done.returncode == 2
	assert 'CONTEXT GATE' in done.stderr


@pytest.mark.parametrize('gate,payload', [
	(CONTEXT_GATE, _read_payload()),
	(BASH_GATE, _bash_payload()),
])
def test_a_subagent_is_exempt(gate, payload) -> None:
	"""Same payload, same cold session — only `agent_id` differs, and it must be enough."""
	done = _run(gate, {**payload, 'agent_id': 'agent-abc123'})
	assert done.returncode == 0
	assert done.stderr == ''


def test_agent_type_alone_does_not_exempt() -> None:
	"""`agent_type` is set for the main thread too in --agent sessions; only `agent_id` discriminates."""
	done = _run(CONTEXT_GATE, {**_read_payload(), 'agent_type': 'Explore'})
	assert done.returncode == 2


def test_the_spec_gate_is_not_exempted() -> None:
	"""Editing a spec-locked module without its SPEC is a correctness failure, whoever does it.

	Asserted structurally: the exemption helper must not reach the one gate that guards contracts.
	"""
	body = (WORKSPACE_ROOT / 'core/hooks/read/spec-read-gate.py').read_text(encoding='utf-8')
	assert 'is_subagent' not in body


def test_the_rule_has_exactly_one_home() -> None:
	"""Both gates ask hook_input; neither restates what a subagent looks like."""
	for gate in (CONTEXT_GATE, BASH_GATE):
		body = gate.read_text(encoding='utf-8')
		assert 'is_subagent' in body
		assert "'agent_id'" not in body, f'{gate.name} restates the rule instead of importing it'
