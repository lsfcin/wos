# b20260905 regression — no case in this suite decides anything by reading a clock.
#
# test_the_mirror_check_is_not_slow_again wrapped `sync-skills --check` in time.monotonic() and
# asserted a 5 s ceiling. It failed twice on 2026-09-05 under `pytest -n auto` and passed both
# times on a rerun with nothing changed: sixteen workers were competing for the same cores, and the
# ceiling was measuring the machine rather than the code. The pre-commit gate runs this suite at
# the workspace root, so that is a commit refused at random -- b20260902's operator experience from
# a different cause -- and a bound that cries wolf gets raised until it means nothing.
#
# ZERO, NOT A CEILING, and it opens at zero with nothing grandfathered: there was exactly one such
# assertion in the whole suite and it is gone. The replacement asserts what actually regressed --
# forks, ~300 of them at ~48 ms -- which is a property of the code on any machine on any day.
#
# WHAT IS STILL LEGAL, because the line matters more than the rule: `subprocess.run(timeout=...)`.
# A timeout is a backstop that stops a hung child, not a verdict about speed; it never decides that
# something was too slow, only that it never finished. It reaches no clock in this process.
import ast

from conftest import WORKSPACE_ROOT

SUITE = WORKSPACE_ROOT / 'core/tools/test'

# A STOPWATCH, NOT A CALENDAR, and the difference is the whole rule. These three measure how long
# something took in THIS process, which is what a loaded box changes. `datetime` is deliberately
# absent: two cases here build fixed timestamps and date arithmetic as DATA — a debounce window in
# a manifest, a baseline date for the entropy trend — and neither decides that anything was slow.
# Banning it would have been a check firing on the word rather than on the defect.
CLOCKS = {'time', 'timeit', 'resource'}


def _clock_imports(source: str) -> set:
    """Stopwatch modules a test module pulls in. Parsed, never grepped — the word `time` is in half
    the prose in this tree, and this file's own head is the proof."""
    tree = ast.parse(source)
    names = {alias.name.split('.')[0]
             for node in ast.walk(tree) if isinstance(node, ast.Import)
             for alias in node.names}
    names |= {node.module.split('.')[0]
              for node in ast.walk(tree)
              if isinstance(node, ast.ImportFrom) and node.module}
    return names & CLOCKS


def test_no_case_in_the_suite_reads_a_clock():
    live = sorted(path.relative_to(WORKSPACE_ROOT).as_posix()
                  for path in SUITE.rglob('test_*.py')
                  if _clock_imports(path.read_text(encoding='utf-8')))
    assert not live, (
        f'these test modules import a clock: {live}. A duration is a property of the machine on '
        'the day, not of the code, and this suite runs under `pytest -n auto` inside the '
        'pre-commit gate. Assert the thing that actually regressed — a fork count, a process '
        'count, a call count — or use subprocess timeout as a backstop, which decides nothing.')


def test_the_check_would_catch_the_assertion_it_was_written_for():
    """Guards the guard. A parser that stopped matching would make the case above vacuous, and the
    body below is the shape the original really had."""
    original = ('import time\n'
                'def test_it():\n'
                '    started = time.monotonic()\n'
                '    assert time.monotonic() - started < 5.0\n')
    assert _clock_imports(original) == {'time'}
    assert not _clock_imports('import subprocess\ndef test_it():\n    pass\n')
