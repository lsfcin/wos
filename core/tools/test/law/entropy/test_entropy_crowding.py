# T0 directory crowding (Level 0, law in core/SCHEMA.md). Zero-token, runs in verify-fast.
#
# The law is not new: a files-per-directory threshold has always existed and
# context_synchronizer.sync has always warned on it — to stdout, during a sync nobody
# reads, which is why the tail grew to 51 files in one directory. These tests hold the
# same law where it is visible.
#
# The whole-tree test is a RATCHET: live violations must be a subset of a named baseline,
# so a new one fails the build while the inherited ones stay visible. Shrinking the
# baseline is the only edit this test should ever get.
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine
# sys.path for the enforcement layer is set once, by conftest.py — a second copy
# here would go stale the next time core/hooks is split.

import entropy_crowding  # noqa: E402
import entropy_list  # noqa: E402
from file_law import load_limits  # noqa: E402
from platform_law import rel  # noqa: E402

WARN = load_limits()['WARN_FILES']

# Inherited crowding, each a directory that owes a split. Nothing else may join.
#
# EMPTY SINCE 2026-09-06, and how it emptied is the part worth keeping. Eight of the ten rows read
# the same way: the directory's NAME had not drifted — every file in it really did the one job the
# directory claimed — so the count was the cost of that design working rather than a responsibility
# problem. Two of those eight had been costed and REJECTED outright (`core/hooks/entropy/` and
# `core/hooks/routing/`, 2026-08-24, Lucas) and were still reported at every session close, because
# the ruling lived in prose no checker reads. A threshold overruled twice and never moved is a
# threshold nobody believes, so the numbers moved instead: WARN_FILES 7 → 10, BLOCK_FILES 10 → 15.
#
# The other two were real, and were split rather than waved through: `workspace/gates/` at 21 held
# tests for four different hook directories under a name claiming one, and `workspace/` at 15 held
# the ratchets and the shim coverage beside the whole-tree invariants.
#
# COST THE HOP BEFORE TAKING IT — a new directory is a CONTEXT.md the whole tree pays to read, and
# that is why raising the number was the cheaper answer for eight of these and no answer at all for
# the other two.
BASELINE = set()


def _live() -> set:
    counts = entropy_crowding.crowding_counts(
        entropy_list.tracked_files(WORKSPACE_ROOT), WORKSPACE_ROOT)
    return {rel(d, WORKSPACE_ROOT)
            for d, n in counts.items() if n > WARN}


def test_no_new_directory_exceeds_the_crowding_signal() -> None:
    assert _live() <= BASELINE, (
        f'new over-full directories: {sorted(_live() - BASELINE)} — split by '
        f'responsibility, or add to BASELINE with the item that retires it')


def test_baseline_is_not_stale() -> None:
    assert BASELINE <= _live(), (
        f'these are fixed and must leave BASELINE: {sorted(BASELINE - _live())}')


def test_a_small_directory_is_clean(tmp_path) -> None:
    files = [tmp_path / f'mod_{i}.py' for i in range(WARN)]
    assert entropy_crowding.crowding_signals(files, tmp_path) == []


def test_an_over_full_directory_is_flagged(tmp_path) -> None:
    files = [tmp_path / f'mod_{i}.py' for i in range(WARN + 1)]
    signals = entropy_crowding.crowding_signals(files, tmp_path)
    assert len(signals) == 1
    assert f'{WARN + 1} code files' in signals[0]


def test_warn_and_block_are_reported_differently(tmp_path) -> None:
    """Symmetric with the file pair: a WARN asks for a look, a BLOCK is the cap."""
    block = load_limits()['BLOCK_FILES']
    warned = entropy_crowding.crowding_signals(
        [tmp_path / f'm{i}.py' for i in range(WARN + 1)], tmp_path)
    blocked = entropy_crowding.crowding_signals(
        [tmp_path / f'm{i}.py' for i in range(block + 1)], tmp_path)
    assert 'WARN_FILES signal' in warned[0]
    assert 'BLOCK_FILES cap' in blocked[0]


def test_a_flat_document_collection_is_not_crowding(tmp_path) -> None:
    """brain/goals is 57 goal files and splitting it would be wrong. Only code counts."""
    files = [tmp_path / f'goal-{i}.md' for i in range(40)]
    assert entropy_crowding.crowding_signals(files, tmp_path) == []


def test_interface_stubs_do_not_count_toward_crowding(tmp_path) -> None:
    """A stub rides in its source's Interface column; it is not a second thing to hold."""
    files = []
    for i in range(WARN):
        files += [tmp_path / f'mod_{i}.py', tmp_path / f'mod_{i}.pyi']
    assert entropy_crowding.crowding_signals(files, tmp_path) == []


def test_the_threshold_has_exactly_one_home() -> None:
    """The number is read from limits.env, never restated — a second copy is drift."""
    source = (WORKSPACE_ROOT / 'core/hooks/entropy/entropy_crowding.py').read_text(encoding='utf-8')
    assert 'load_limits' in source
    assert f'= {WARN}' not in source
