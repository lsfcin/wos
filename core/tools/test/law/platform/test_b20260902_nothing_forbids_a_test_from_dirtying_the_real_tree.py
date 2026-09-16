# b20260902 regression — the law that no test touches the real workspace is now checked.
#
# core/tools/test/wos/CONTEXT.md has said it in as many words since it was written — "Each test
# builds its own repo and bare origin; nothing touches the real workspace" — and nothing read that
# sentence. Two of three full runs were red here on 2026-09-02 on a suite the Windows clone had
# seen green three times, and the operator's evidence was always a failure in a file they had not
# touched: the sync-skills check, the diagram's determinism, and test_present_tense_state_is_not_a
# _corpse dying on `code/_nudgeprobe5b974581`.
#
# BESIDE THE b20260901 SIBLINGS, because the invisibility is the cross-clone kind this directory
# covers: how wide the mutation window opens is a core count, so a green run on one machine says
# nothing about the other. That is the same shape as one-answers-file-is-shared, one layer down,
# and it is why "it passes here" was never evidence.
#
# THE AUDIT, done 2026-09-05. 48 test files reference WORKSPACE_ROOT and contain a write; 45 of
# them write under tmp_path. The three that do not are named below. Two shapes, which is why a
# checker watching only tracked files would have closed this while it was still open: one mutates
# a tracked file's CONTENT, two create and remove a real PATH.
#
# NOT DONE, and named here rather than left to be rediscovered: `--root` on sync-skills and
# mirror-heal.py. Both derive the workspace from their own __file__, so the mirror-heal case has
# nowhere but the real tree to seed its drift; a root argument would let it build one in tmp_path
# and drop its marker. That removes ONE exemption. It does not close the class, which is why it is
# a residual and not the fix — the guard below holds whether or not it is ever built.
#
# WHAT ACTUALLY CLOSES IT is not this file but the autouse fixture in core/tools/test/conftest.py,
# which snapshots the two watched subtrees around every unmarked test. This file proves that
# fixture detects both shapes, that it is autouse rather than opt-in, and that the three known
# offenders declare themselves. The fixture is what makes forgetting the marker a failure in the
# offending test instead of a random red somewhere else.
import sys

import pytest
from conftest import WORKSPACE_ROOT, _shape

SUITE = WORKSPACE_ROOT / 'core/tools/test'

# The three, and the shape each one has. Every other case in the suite writes under tmp_path.
#
# FOUND BY NAME, NEVER BY DIRECTORY (2026-09-06). These three were resolved against
# `workspace/gates/` until the 21-file split moved two of them into `gates/vcs/` and
# `gates/checks/`. A law that hard-codes where its subject lives does not fail when the subject
# moves — it fails when someone MOVES it, which is the same red for the opposite reason, and it
# would have gone green again the moment a file of that name reappeared anywhere.
OFFENDERS = {
	'test_b20260901_a_mirror_never_reaches_the_machine_that_pulled_it.py': 'mutates core/skills',
	'test_b20260901_the_codegraph_nudge_only_fires_when_a_stub_is_stale.py': 'creates under code/',
	'test_b4_gate_messages.py': 'creates under code/',
}


@pytest.fixture
def fake_root(tmp_path, monkeypatch):
	"""The watched subtrees, rebuilt somewhere harmless.

	The detector is pointed at a throwaway root rather than exercised against the real one — a spec
	for "nothing dirties the tree" that dirtied the tree to prove it would be the joke version of
	this bug, and would need the very marker it is here to make unnecessary.
	"""
	import conftest
	for relative in ('code', 'core/skills'):
		(tmp_path / relative).mkdir(parents=True)
	(tmp_path / 'core/skills/compass.md').write_text('# compass\n', encoding='utf-8', newline='\n')
	monkeypatch.setattr(conftest, 'WORKSPACE_ROOT', tmp_path)
	return tmp_path


def test_a_created_path_is_seen(fake_root) -> None:
	"""The codegraph-nudge and gate-messages shape: a real directory under code/, then gone."""
	before = _shape()
	(fake_root / 'code/_probe1234').mkdir()
	assert _shape() != before


def test_a_removed_path_is_seen(fake_root) -> None:
	"""The same shape at its other end — the half a parallel worker actually trips over."""
	(fake_root / 'code/_probe1234').mkdir()
	before = _shape()
	(fake_root / 'code/_probe1234').rmdir()
	assert _shape() != before


def test_a_tracked_file_whose_content_changed_is_seen(fake_root) -> None:
	"""The mirror-heal shape: content mutated and restored in a `finally`, invisible to a serial
	runner and a coin flip to a parallel one. A watcher of names alone would miss this."""
	target = fake_root / 'core/skills/compass.md'
	before = _shape()
	target.write_text('# compass\n<!-- arrived by merge -->\n', encoding='utf-8', newline='\n')
	assert _shape() != before, 'a content change inside a watched file went unseen'


def test_an_untouched_tree_reads_identical(fake_root) -> None:
	"""The mirror half, and the one that decides whether the guard survives its first week: a
	detector that fires on an unchanged tree gets switched off within days."""
	assert _shape() == _shape()


def test_the_guard_is_autouse_rather_than_something_a_test_opts_into() -> None:
	"""Opt-in would have caught none of the three: not one of their authors knew the law existed."""
	import conftest
	guard = conftest._no_test_dirties_the_real_tree
	# `_fixture_function_marker` on pytest 9; older versions spell it `_pytestfixturefunction`.
	marker = getattr(guard, '_fixture_function_marker',
	                 getattr(guard, '_pytestfixturefunction', None))
	assert marker is not None, f'cannot read the fixture marker off {type(guard).__name__}'
	assert marker.autouse, 'the tree guard stopped being autouse'


@pytest.mark.parametrize('name, shape', sorted(OFFENDERS.items()))
def test_each_known_offender_declares_itself_serial(name, shape) -> None:
	"""`serial` is the exemption, and verify.py gives these a pass with no worker beside them.
	Two of the three were unmarked until 2026-09-05; b20260902 records only one of those two."""
	found = sorted(SUITE.rglob(name))
	assert len(found) == 1, (
		f'expected exactly one {name} under the suite, found {[str(p) for p in found]}. A second '
		'copy would let one carry the marker while the other dirties the tree.')
	body = found[0].read_text(encoding='utf-8')
	assert 'pytest.mark.serial' in body, f'{name} {shape} and no longer declares `serial`'


def test_the_suite_can_still_import_its_own_conftest() -> None:
	"""Cheap, and it has earned its place: the fixture above is imported by name from conftest, so
	a rename there would otherwise fail this file with an ImportError at collection rather than
	with a sentence about what broke."""
	assert 'conftest' in sys.modules
