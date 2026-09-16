# T0/T1 the work→level map and its renderer: which capacity a kind of work gets, written once and
# rendered into each harness rather than inherited from whatever the parent happened to be running.
#
# The sharpest case here is test_the_registry_never_names_a_model. The whole design rests on the
# split — a level is a capacity in the registry, a vendor's name only in the adapter — and the
# failure it guards is the one Lucas named on 2026-08-17: "nothing in WOS should be tied to a
# specific vendor/company/model." A model id that leaks into the registry rots silently, because a
# stale id still reads like a decision.
import importlib.machinery as machinery
import importlib.util as importutil

import pytest

from conftest import WORKSPACE_ROOT

TOOL = WORKSPACE_ROOT / 'core/tools/wos/levels'
REGISTRY = WORKSPACE_ROOT / 'core/levels.txt'
AGENTS = WORKSPACE_ROOT / 'core/agents'


def _tool():
	"""Load the extensionless CLI as a module — the house pattern for testing one."""
	spec = importutil.spec_from_loader('leveltool', machinery.SourceFileLoader('leveltool', str(TOOL)))
	module = importutil.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def _body() -> str:
	return '\n'.join(line for line in REGISTRY.read_text(encoding='utf-8').splitlines()
	                 if not line.startswith('#'))


def test_every_kind_of_work_says_how_to_recognise_it_and_what_it_costs_to_go_lower():
	"""A row with no `tell` cannot be applied to a task, and a row with no `why` is asking for
	headroom it has not justified — which is how everything ended up at the top level."""
	known = _tool().declared()
	assert known, 'core/levels.txt declares no kinds of work'
	for work, row in known.items():
		assert row['tell'].strip(), f'{work} gives no way to recognise the case'
		assert row['why'].strip(), f'{work} names no cost to running one level down'
		assert row['level'] in {'low', 'medium', 'high'}, f'{work} claims level {row["level"]!r}'


def test_the_registry_never_names_a_model():
	"""The property that makes a second harness a second table instead of a second policy, and the
	one core/hooks/entropy/entropy_vendor.py exists to keep. See this file's head."""
	body = _body().lower()
	for vendor in ('claude', 'opus', 'sonnet', 'haiku', 'gpt', 'gemini', 'anthropic', 'openai'):
		assert vendor not in body, (
			f'{vendor!r} is a vendor name in core/levels.txt — a level is a capacity; which model '
			f'fills it belongs to the adapter in core/tools/wos/levels')


def test_the_adapter_fills_every_level_the_registry_declares():
	"""A level with no model behind it fails at spawn time, on a harness, in someone else's session.
	The registry and the adapter are two files and nothing but this case makes them agree."""
	module = _tool()
	wanted = {row['level'] for row in module.declared().values()}
	for harness, (table, _dir) in module.HARNESSES.items():
		missing = wanted - set(table)
		assert not missing, f'{harness} has no model for level(s) {sorted(missing)}'


def test_every_agent_declares_a_level_the_registry_defines():
	"""An agent naming a level nobody declared renders nothing, and renders it silently."""
	module = _tool()
	live = {row['level'] for row in module.declared().values()}
	for name, (level, _source) in module.agents().items():
		assert level in live, f'core/agents/{name}.md declares level {level!r}, undeclared'


def test_a_rendered_definition_points_at_the_role_instead_of_copying_it():
	"""A mirror carries the three fields a harness needs to list and route a worker, and a pointer
	to the one file that defines it. Copying the role whole put 460 lines of operating context into
	`.claude/` — a second definition of every worker, which is the drift this tool exists to prevent.
	Run against a real role, because the pointer has to resolve on disk."""
	module = _tool()
	source = AGENTS / 'writer.md'
	rendered = module.render(source, 'sonnet')
	assert 'model: sonnet' in rendered and '\nlevel:' not in rendered
	assert 'core/agents/writer.md' in rendered, 'the mirror does not say where the role is'
	assert len(rendered) < len(source.read_text(encoding='utf-8')), \
		'the mirror is not smaller than the role it points at — it is copying again'


def test_check_notices_a_rendered_definition_that_drifted(tmp_path, monkeypatch):
	"""--check is this tool's Verify check, so it has to catch a hand-edited mirror.

	Rendered into tmp_path rather than asserted against the live tree: a case that edits
	`.claude/agents/` to prove a point leaves the workspace one crash away from a drifted mirror,
	which is the law core/tools/test/wos/CONTEXT.md states and b20260902 broke three times.
	"""
	module = _tool()
	monkeypatch.setattr(module, '_mirror', lambda harness, name: tmp_path / harness / f'{name}.md')
	assert module._set() == 0
	assert module._check() == 0, 'a freshly rendered tree does not match itself'

	name = next(iter(module.agents()))
	drifted = module._mirror('claude', name)
	drifted.write_text(drifted.read_text(encoding='utf-8').replace('model:', 'model: zz-', 1),
	                   encoding='utf-8', newline='\n')
	assert module._check() == 1, '--check passed a mirror that no longer matches its source'


def test_the_live_tree_matches_what_it_declares():
	"""The other half, and the one that catches a real drift: whatever is rendered in this repo
	right now must still be a function of core/agents/."""
	assert _tool()._check() == 0, 'a rendered agent definition drifted — run `levels --set`'


def test_the_map_is_not_sold_as_the_cost_answer():
	"""Delegated work is 2.5% of spend (core/experiments/delegation.md). A map that let a reader
	believe routing subagents fixes the bill would aim the next session at a rounding error, which
	is exactly why the narrow version of this was refused."""
	head = REGISTRY.read_text(encoding='utf-8')
	assert 'main thread' in head, 'core/levels.txt no longer says what it cannot reach'


@pytest.mark.parametrize('flag', ['--check', '--set'])
def test_both_switches_exist_and_are_reachable(flag):
	"""AD-14: a row claiming a switch must really have one."""
	assert f"'{flag}'" in TOOL.read_text(encoding='utf-8')
