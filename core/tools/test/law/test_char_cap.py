# T0 document cap: how big one authored file may be in characters, at the two declared levels.
# Zero-token, runs in verify-fast.
#
# The unit moved from the LINE to the DOCUMENT on 2026-09-14 (limits.env § chars). What it replaced
# was 95 lines because measuring a line's width owed four exemptions and each needed a bound tested;
# a document measure has none, so what is left to hold is the law's shape: two levels, both read
# from limits.env, block above warn, and nothing in the tree blocked today.
#
# The reasoning lives in core/hooks/limits.env and is not restated here — these only hold it to it.
from conftest import WORKSPACE_ROOT, git_lines  # noqa: F401  (also sets sys.path for the law)

from file_law import (is_authored, is_authored_prose,  # noqa: E402
                      load_limits)

LIMITS = load_limits()


def test_both_levels_are_declared() -> None:
    """The unit exists in the one file that holds every number, at the same two levels as lines."""
    assert LIMITS['WARN_CHARS'] < LIMITS['BLOCK_CHARS']


def test_the_column_cap_is_gone() -> None:
    """The rename is only finished when the old number cannot be read back. A reader still asking
    limits.env for BLOCK_COLS would get a KeyError rather than a stale answer, and this says so."""
    assert 'BLOCK_COLS' not in LIMITS


def test_the_implied_width_keeps_the_line_cap_in_front() -> None:
    """core/SCHEMA.md ruled 2026-08-31 that the line cap outranks the size cap beside it. That only
    holds while the implied width sits above what our prose actually measures: at 62.7 characters
    per line a file hits BLOCK_LINES first, and only an abnormally wide one reaches BLOCK_CHARS."""
    implied = LIMITS['BLOCK_CHARS'] / LIMITS['BLOCK_LINES']
    assert 65 < implied < 120


def test_no_tracked_file_is_blocked_today() -> None:
    """A cap that retroactively blocks the tree is one nobody can land. This is the hand-check the
    experiments format demands of a new number, kept as a test so it stays true.

    Asked of what git TRACKS, never of what the directory holds: the workspace root also carries
    Downloads/ and a venv, and a cap answering for those would report on one machine's disk."""
    over = []
    for name in git_lines('ls-files'):
        path = WORKSPACE_ROOT / name
        if not path.is_file():
            continue
        if not (is_authored(path, WORKSPACE_ROOT)
                or is_authored_prose(path, WORKSPACE_ROOT)):
            continue
        try:
            size = len(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError):
            continue
        if size >= LIMITS['BLOCK_CHARS']:
            over.append(f'{name} ({size})')
    assert not over, f'over BLOCK_CHARS: {over}'
