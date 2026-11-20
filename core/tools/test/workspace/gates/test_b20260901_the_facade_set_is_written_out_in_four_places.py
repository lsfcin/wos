# b20260901-the-facade-set-is-written-out-in-four-places regression — what a file IS has one home.
#
# `{'index.ts','index.tsx','index.js','index.jsx','__init__.py','index.dart'}` was spelled out
# identically in stubgen/stubs.py (FACADES), facade/facade-gate.py, facade/facade-tracker.py and
# routing/workspace_scanner.py (under a second name, in the last three). Found 2026-09-01 adding a
# gate that would have been the fifth. core/hooks/CONTEXT.md says the law lives in that directory's
# root and a checker restating any of it is the drift the checkers exist to catch — this was that
# drift four times over, inside the enforcement layer, and the four had ALREADY diverged in name,
# which is how a fifth nearly got written without anyone noticing the other four. The set is not
# stable by luck either: `index.dart` was added once, and nothing would have carried it to a copy.
#
# A CEILING OF ONE WITH A NAMED HOLDER, the shape test_port_ceiling.py uses. If this has to rise, the
# thing to write down is why that file cannot ask file_law, not a bigger number.
import sys

from conftest import WORKSPACE_ROOT, git_lines
from file_law import FACADES

HOME = 'core/hooks/file_law.py'
# The needle is the SET, not any member of it. `'index.tsx'` alone also matches facade-scan.py's
# suffix→name map, which is a different question (what facade would a NEW file here belong to) and
# is deliberately left alone; this adjacency appears only in the set literal.
#
# BUILT IN TWO HALVES so this file is not its own first offender — the rule
# core/tools/test/law/entropy/CONTEXT.md states for the checks that hunt a literal.
NEEDLE = "'index.jsx'," + " '__init__.py'"


def test_only_one_versioned_file_spells_the_set() -> None:
	live = sorted(git_lines('grep', '-lF', NEEDLE, '--', '*.py'))
	assert live == [HOME], (
		f'the facade set is spelled in {live}, not only in {HOME}. Import it — '
		f'`from file_law import FACADES` — and delete the copy')


def test_the_name_is_the_same_everywhere_it_is_read() -> None:
	"""Two names for one set is the drift that hid the duplication — they read as two questions.

	The retired spelling is written HERE and nowhere else, the rule core/tools/test/law/entropy's
	CONTEXT.md states for its own checks: prose quoting a token a checker hunts is indistinguishable
	from prose that failed to update, to the checker and to a reader skimming it.
	"""
	stale = sorted(git_lines('grep', '-lF', 'FACADE_' + 'NAMES', '--', '*.py', '*.pyi'))
	assert not stale, (
		f'these still use the retired name for the set: {stale}. One question, one name — '
		'file_law.FACADES')


def test_every_reader_gets_the_definition_and_not_a_copy() -> None:
	"""The point of one home is that a reader cannot hold a different answer. Asked of the loaded
	modules rather than of their text, because agreeing in source and disagreeing at run time is
	exactly what a second copy does."""
	sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/read'))
	sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/routing'))
	import workspace_scanner
	from chain import FACADES as via_chain

	assert via_chain is FACADES
	assert workspace_scanner.FACADES is FACADES


def test_a_facade_is_never_gated_on_its_own_stub() -> None:
	"""What the set is FOR, held at the one call site a reader meets: a facade already is a minimal
	interface, so redirecting a read of one to a generated stub would serve a worse file."""
	sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/read'))
	from chain import interface_state

	for name in FACADES:
		state, iface = interface_state(WORKSPACE_ROOT / f'code/check/{name}')
		assert (state, iface) == ('none', None), f'{name} was treated as a gateable source'
