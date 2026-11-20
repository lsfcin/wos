# b20260922 regression — what a file costs in reads was measurable on one harness and no other.
#
# THE ASYMMETRY. core/tools/wos/session/* answers "which files did this session read" by replaying
# ~/.claude/projects/*.jsonl — an artifact one vendor leaves on disk. Built as archaeology, it was
# bound to one harness from its first line, while core/hooks/scoreboard.py, built as instrumentation,
# has been vendor-agnostic for free since the day it was written: it records the fact where the fact
# happens, inside a function every harness passes through. One workspace, two answers to "what did
# this session do", and only one of them travels. AGENTS.md calls symmetry a core value.
#
# WHAT THESE CASES PIN. Not the asymmetry itself — that is an absence, and a test cannot assert one
# usefully. They pin the properties that make the new count travel and stay honest: it is recorded at
# the read, it is arithmetic over a circular window with nothing to shift, a day that passed is
# cleared rather than believed, and the hook never writes the matrix it feeds.
import datetime
import sys

from conftest import WORKSPACE_ROOT

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/read'))
import read_matrix  # noqa: E402

DAY = datetime.date(2026, 9, 22)


def _folded(tmp_path, rows, today=DAY):
    """Write `rows` as events and fold them, in a sandbox. (matrix path, folded rows)."""
    events, matrix = tmp_path / 'reads.tsv', tmp_path / 'matrix.tsv'
    events.write_text(''.join(f'{day.isoformat()}\t{name}\n' for day, name in rows),
                      encoding='utf-8', newline='\n')
    return matrix, read_matrix.fold(events, matrix, today)


def test_a_day_and_the_same_day_a_year_later_share_one_column():
    """The window is circular, which is what keeps the file from growing and the diff from lying.

    A shifting window rewrites every row daily — ~900KB of diff that means only that the numbers
    moved one place left. Modulo arithmetic moves nothing.
    """
    assert read_matrix.column(DAY) == read_matrix.column(DAY + datetime.timedelta(days=365))
    assert read_matrix.column(DAY) != read_matrix.column(DAY + datetime.timedelta(days=1))


def test_a_read_lands_in_the_column_of_the_day_it_happened(tmp_path):
    """Two reads of one file on one day are two, and yesterday is not today."""
    _matrix, rows = _folded(tmp_path, [(DAY, 'a.md'), (DAY, 'a.md'),
                                       (DAY - datetime.timedelta(days=1), 'a.md')])
    assert rows['a.md'][read_matrix.column(DAY)] == 2
    assert rows['a.md'][read_matrix.column(DAY - datetime.timedelta(days=1))] == 1


def test_a_column_a_year_stale_is_cleared_before_it_is_believed(tmp_path):
    """The one failure a circular window can have, and the only reason the header carries a date.

    Overwriting rather than deleting means a column nobody cleared still holds what it held a year
    ago. Read as today's, that is not a stale number — it is a fabricated one.
    """
    matrix, rows = _folded(tmp_path, [(DAY, 'a.md')])
    at = read_matrix.column(DAY)
    assert rows['a.md'][at] == 1
    later = DAY + datetime.timedelta(days=366)
    _again, after = _folded(tmp_path, [(later, 'b.md')], today=later)
    assert after.get('a.md', [0] * read_matrix.WINDOW)[at] == 0, 'a year-old count survived'
    assert matrix.exists()


def test_a_range_is_a_sum_of_columns_and_nothing_is_stored_per_range(tmp_path):
    """Week, month and semester are one function with a different argument — the matrix's whole point."""
    days = [(DAY - datetime.timedelta(days=step), 'a.md') for step in range(10)]
    _matrix, rows = _folded(tmp_path, days + [(DAY, 'b.md')])
    assert dict(read_matrix.span(rows, 3, DAY))['a.md'] == 3
    assert dict(read_matrix.span(rows, 10, DAY))['a.md'] == 10
    assert read_matrix.span(rows, 3, DAY)[0][0] == 'a.md', 'busiest first'


def test_a_file_nothing_read_all_year_loses_its_row(tmp_path):
    """What holds the file's size still. Without it the matrix grows with every file ever opened."""
    _matrix, rows = _folded(tmp_path, [(DAY, 'gone.md')])
    assert 'gone.md' in rows
    later = DAY + datetime.timedelta(days=400)
    _again, after = _folded(tmp_path, [(later, 'kept.md')], today=later)
    assert 'gone.md' not in after and 'kept.md' in after


def test_the_hook_only_ever_appends(tmp_path):
    """A matrix is read-modify-write and parallel sessions would lose rows in it.

    One line under PIPE_BUF is an atomic append, which is why the hook writes events and the close
    folds them. This pins the split: recording touches the event file and nothing else.
    """
    events, matrix = tmp_path / 'reads.tsv', tmp_path / 'matrix.tsv'
    read_matrix.record(str(WORKSPACE_ROOT / 'AGENTS.md'), events)
    assert events.exists() and not matrix.exists()
    assert events.read_text(encoding='utf-8').strip().endswith('\tAGENTS.md')


def test_folding_twice_does_not_count_a_read_twice(tmp_path):
    """The events are truncated by the fold, so a close that runs twice is not a doubled day."""
    events, matrix = tmp_path / 'reads.tsv', tmp_path / 'matrix.tsv'
    events.write_text(f'{DAY.isoformat()}\ta.md\n', encoding='utf-8', newline='\n')
    read_matrix.fold(events, matrix, DAY)
    rows = read_matrix.fold(events, matrix, DAY)
    assert rows['a.md'][read_matrix.column(DAY)] == 1
