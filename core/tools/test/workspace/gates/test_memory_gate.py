#!/usr/bin/env python3
# T0 the memory gate: the workspace keeps no memory store, and a refused write is routed, not escalated.
#
# The gate reads only the payload's path — no repo state, no disk — so unlike the issues-gate trio
# beside it this needs no throwaway repo, just the two answers and the two paths.
import json
import os
import subprocess
import sys


from conftest import HOOKS, WORKSPACE_ROOT  # noqa: E402 — conftest puts its own directory first

GATE = HOOKS / 'brain' / 'memory-gate.py'
STORE = WORKSPACE_ROOT / 'brain' / 'memory' / 'anything.md'
ELSEWHERE = WORKSPACE_ROOT / 'ISSUES.md'


def run(path, enabled: bool = True) -> subprocess.CompletedProcess:
    """The gate over one Write payload, with the feature answered either way.

    The switch is thrown through `WOS_FEATURES_OFF`, the ablation switch feature_law already owns,
    rather than by editing core/profile.txt: no test in this suite may touch the real tree
    (b20260902). The off case is the half that matters — a gate nobody can turn off is not a
    feature, it is a wall.
    """
    payload = json.dumps({'tool_name': 'Write',
                          'tool_input': {'file_path': str(path), 'content': 'x'}})
    env = dict(os.environ)
    if not enabled:
        env['WOS_FEATURES_OFF'] = 'memory-gate'
    return subprocess.run([sys.executable, str(GATE)], input=payload, env=env,
                          capture_output=True, text=True, encoding='utf-8')


def test_a_write_into_the_memory_store_is_refused() -> None:
    result = run(STORE)
    assert result.returncode == 2, result.stdout + result.stderr
    assert 'MEMORY GATE' in result.stderr, result.stderr


def test_the_refusal_names_where_the_fact_goes_instead() -> None:
    """A gate that only says no gets the same text written again a turn later."""
    said = run(STORE).stderr
    for target in ('core/norms/', 'ISSUES.md', 'ROADMAP.md', 'CONTEXT.md'):
        assert target in said, f'the refusal does not route the fact to {target}: {said}'


def test_the_refusal_offers_no_switch_to_ask_lucas_for() -> None:
    """b20260924: the refusal ended with 'switch memory-gate off if Lucas asked', and an agent took
    that as the path — it passed the question to Lucas instead of routing the fact."""
    said = run(STORE).stderr
    assert 'profile.txt' not in said and 'switch' not in said, said
    assert 'Do not ask Lucas' in said, said


def test_a_write_anywhere_else_is_untouched() -> None:
    assert run(ELSEWHERE).returncode == 0


def test_the_switch_really_switches_it_off() -> None:
    assert run(STORE, enabled=False).returncode == 0


if __name__ == '__main__':
    sys.exit(0)
