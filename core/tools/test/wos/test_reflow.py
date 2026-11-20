# T1 reflow: a join only ever happens mid-sentence, and never crosses something that meant to end.
#
# The cases here are the ones that nearly went wrong on 2026-09-18, not the ones that obviously
# work: the round trip proves no WORD moved and is blind to structure, so every case below is a
# structure the first draft destroyed while the assertion passed.
import importlib.util
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT

_spec = importlib.util.spec_from_loader(
    'reflow_tool',
    importlib.machinery.SourceFileLoader(
        'reflow_tool', str(WORKSPACE_ROOT / 'core' / 'tools' / 'wos' / 'reflow')))
reflow_tool = importlib.util.module_from_spec(_spec)
sys.modules['reflow_tool'] = reflow_tool
_spec.loader.exec_module(reflow_tool)


def test_a_wrapped_sentence_becomes_one_line():
    text = 'a sentence that was wrapped by a width\nlimit nobody measures any more.\n'
    new, removed = reflow_tool.reflow(text)
    assert removed == 1
    assert new == 'a sentence that was wrapped by a width limit nobody measures any more.\n'


def test_a_field_separator_survives():
    """ROADMAP.md writes one field per line and none of them ends mid-sentence.

    The literal reading of "one paragraph, one line" fused *What*, *Why* and *Done when* into a
    run-on line in the most-read file in the workspace, and nothing caught it.
    """
    text = ('**a bold title**\n*What* — the thing.\n*Why* — the reason.\n'
            '*Done when* — the observable.\n')
    assert reflow_tool.reflow(text) == (text, 0)


def test_a_hard_break_ends_a_backlog_item():
    """Two trailing spaces separate one goal-file item from the next; fusing them fuses the list."""
    text = '> [ ] [one] an item that wraps\n> over two lines  \n> [ ] [two] the next item  \n'
    new, removed = reflow_tool.reflow(text)
    assert removed == 1
    assert new == '> [ ] [one] an item that wraps over two lines  \n> [ ] [two] the next item  \n'


def test_two_bullets_never_fuse():
    text = '- first bullet ending open\n- second bullet\n'
    assert reflow_tool.reflow(text) == (text, 0)


def test_an_indented_continuation_joins_its_bullet():
    text = '- a bullet whose text ran past the\n  width limit of the day\n'
    new, removed = reflow_tool.reflow(text)
    assert removed == 1
    assert new == '- a bullet whose text ran past the width limit of the day\n'


def test_a_fence_and_a_generated_block_are_untouched():
    fenced = '```\nline one of code\nline two of code\n```\n'
    generated = '<!-- routing:start -->\nrow one that wraps\nrow two\n<!-- routing:end -->\n'
    assert reflow_tool.reflow(fenced) == (fenced, 0)
    assert reflow_tool.reflow(generated) == (generated, 0)


def test_frontmatter_is_untouched():
    text = '---\ndescription: a value that wraps\n  onto a second line\n---\n\nbody here.\n'
    assert reflow_tool.reflow(text) == (text, 0)


def test_the_header_block_is_untouched():
    """`> key: value` lines are FIELDS, and joining two loses one silently.

    header.py reads the first `key:` on a line and treats the rest as that field's value, so a
    fused pair reports clean while the second field has stopped existing — 18 files, first run.
    """
    text = ('# Title\n> a description that wraps\n> onto a second line\n'
            '> governs: every repo under code/\n> enforced-by: core/hooks/git/lock.py\n\n'
            'body that wraps\nonto two lines.\n')
    new, removed = reflow_tool.reflow(text)
    assert removed == 1                                  # the body only
    assert '> governs: every repo under code/\n> enforced-by:' in new
    assert '> a description that wraps\n> onto a second line\n' in new


def test_a_table_is_untouched():
    text = '| a | b |\n|---|---|\n| one | two |\n'
    assert reflow_tool.reflow(text) == (text, 0)


def test_the_round_trip_loses_no_word():
    """The guard itself, over the live corpus: every file this tool would rewrite comes back with
    exactly the words it went in with."""
    root = Path(WORKSPACE_ROOT)
    checked = 0
    for rel in reflow_tool.candidates(root, [])[:400]:
        try:
            text = (root / rel).read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        new, removed = reflow_tool.reflow(text)
        if removed:
            checked += 1
            assert reflow_tool.words(new) == reflow_tool.words(text), rel
    assert checked, 'nothing was reflowable — the guard above asserted nothing'
