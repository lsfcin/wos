# T0 the goal-file `>**owns**` block: a field ends where its block ends. Zero-token, verify-fast.
#
# The parser ran past the block into the goal's body and offered whole paragraphs as repo paths,
# printing nine warnings on every commit — each quoting an essay. Nothing was miscounted (an
# unresolvable path is skipped), which is exactly why it survived: the output was wrong in a way
# that changed no number. Noise on a warning channel is how a real warning gets missed.
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine
# sys.path for the enforcement layer is set once, by conftest.py — a second copy
# here would go stale the next time core/hooks is split.
sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/brain'))

from brain_attention import parse_owns  # noqa: E402

GOALS = WORKSPACE_ROOT / 'brain/goals'


def _goal(tmp_path: Path, body: str) -> Path:
    path = tmp_path / 'g.md'
    path.write_text(body, encoding='utf-8', newline='\n')
    return path


def test_a_blank_line_ends_the_block(tmp_path: Path) -> None:
    """The real shape: one content line, a blank, then unrelated prose in the goal's body."""
    owned = parse_owns(_goal(tmp_path,
        '# g\n\n>**owns**  \n`core/flows/craft` · `code/flows`\n\n'
        'Prose about the goal that names no path at all.\n'))
    assert owned == ['core/flows/craft', 'code/flows']


def test_a_following_blockquote_paragraph_is_not_owned(tmp_path: Path) -> None:
    """`> **Bold**` has a space after the caret, so it missed the next-field terminator too."""
    owned = parse_owns(_goal(tmp_path,
        '# g\n\n>**owns**  \n`code/x`\n\n'
        '> **Vocabulary note.** A paragraph that wraps\n'
        '> across several blockquote lines.\n'))
    assert owned == ['code/x']


def test_a_wrapped_list_still_reads_as_one_block(tmp_path: Path) -> None:
    """Breaking on a blank line must not break the case the block exists for."""
    owned = parse_owns(_goal(tmp_path,
        '# g\n\n>**owns**  \n`core/a` · `core/b`\n`core/c`\n\nprose\n'))
    assert owned == ['core/a', 'core/b', 'core/c']


def test_the_next_field_ends_the_block(tmp_path: Path) -> None:
    owned = parse_owns(_goal(tmp_path, '# g\n\n>**owns**  \n`code/x`\n>**timing**  \nnear\n'))
    assert owned == ['code/x']


def test_a_goal_with_no_block_owns_nothing(tmp_path: Path) -> None:
    """Life goals declare nothing and their file genuinely is the artifact — not a gap to fill."""
    assert parse_owns(_goal(tmp_path, '# dance\n\nBody prose, no owns block.\n')) == []


def test_no_live_goal_declares_a_sentence() -> None:
    """The end-to-end assertion: every declared path is path-shaped, across all real goal files.

    Deliberately not a count of warnings — a length ceiling catches the failure that happened
    (paragraphs read as paths) without pinning how many goals declare anything.
    """
    offenders = []
    for goal in sorted(GOALS.glob('*.md')):
        for declared in parse_owns(goal):
            if ' ' in declared or len(declared) > 60:
                offenders.append(f'{goal.name}: {declared[:60]}…')
    assert not offenders, 'owns entries that are prose, not paths:\n' + '\n'.join(offenders)
