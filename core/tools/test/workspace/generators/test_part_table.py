# A cut type's index table (core/SCHEMA.md § What a part publishes about itself).
#
# The table exists so a session can decide "open or skip" without opening anything, and its two
# errors are not symmetric: skipping a part that mattered is silent. So the cases here are mostly
# about what must SURVIVE into the table, not about formatting.
#
# Every derived number is derived on purpose. ROADMAP.md kept one by hand and it went stale four
# times, twice while the paragraph asking to keep it true sat directly above it — so a test that a
# count comes from the body is a test of the whole design.
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine

from part_table import build_part_rows, index_for, part_facts, parts_of  # noqa: E402

ALPHA = """# Alpha
> Level 0 checks and the ratchet that makes the count fall.
> priority: essential

1. 🔴 do the thing.
2. 🟢 `[ratchet]` do the other thing.
"""

BETA = """# Beta
> Where session spend goes.
> priority: important
> blocked-by: ROADMAP-alpha.md

1. 🟡 measure it, with no id at all.
"""


def _cut(tmp_path, **parts) -> Path:
    index = tmp_path / 'ROADMAP.md'
    index.write_text('# Index\n> Index only.\n', encoding='utf-8', newline='\n')
    for name, body in parts.items():
        (tmp_path / name).write_text(body, encoding='utf-8', newline='\n')
    return index


def test_the_open_count_is_derived_from_the_body(tmp_path) -> None:
    """Numbered items, not declared totals — the count no one can forget to update."""
    facts = part_facts(_cut(tmp_path, **{'ROADMAP-alpha.md': ALPHA}).parent
                        / 'ROADMAP-alpha.md')
    assert facts['open'] == '2'
    assert 'open' not in ALPHA  # nothing declared it


def test_needs_lucas_is_counted_not_declared(tmp_path) -> None:
    _cut(tmp_path, **{'ROADMAP-alpha.md': ALPHA})
    assert part_facts(tmp_path / 'ROADMAP-alpha.md')['needs-lucas'] == '1'


def test_a_sentence_about_the_marker_is_not_a_marked_item(tmp_path) -> None:
    """Caught on the first real run: a bare count read 13 where the list holds 12, because one
    part carries a sentence ABOUT the count with the marker inside it. Mark versus mention is
    exactly the confusion that made the hand-kept number wrong four times."""
    (tmp_path / 'ROADMAP.md').write_text('# I\n> i.\n', encoding='utf-8', newline='\n')
    (tmp_path / 'ROADMAP-alpha.md').write_text(
        '# A\n> a.\n\ntwo items need Lucas while three were marked 🔴 — the count went stale.\n\n'
        '1. 🔴 a real one.\n', encoding='utf-8', newline='\n')
    assert part_facts(tmp_path / 'ROADMAP-alpha.md')['needs-lucas'] == '1'


def test_an_item_id_survives_the_marker_in_front_of_it(tmp_path) -> None:
    """`2. 🟢 [ratchet]` — the emoji sits between the number and the id, and ate it once."""
    _cut(tmp_path, **{'ROADMAP-alpha.md': ALPHA})
    assert '`ratchet`' in part_facts(tmp_path / 'ROADMAP-alpha.md')['items']


def test_declared_fields_come_from_the_header_lines(tmp_path) -> None:
    _cut(tmp_path, **{'ROADMAP-beta.md': BETA})
    facts = part_facts(tmp_path / 'ROADMAP-beta.md')
    assert facts['priority'] == 'important'
    assert facts['blocked-by'] == 'ROADMAP-alpha.md'


def test_a_column_empty_on_every_part_is_not_emitted(tmp_path) -> None:
    """What lets ONE builder serve ROADMAP, SCHEMA and SPECS without being told which it is."""
    index = _cut(tmp_path, **{'ROADMAP-alpha.md': ALPHA, 'ROADMAP-beta.md': BETA})
    table = build_part_rows(parts_of(index))
    assert '| Prio |' in table and '| Open |' in table
    assert '| Governs |' not in table and '| Answers |' not in table


def test_the_marker_column_is_named_in_words(tmp_path) -> None:
    """A column headed with the emoji asks the reader to have read what they are deciding to read."""
    index = _cut(tmp_path, **{'ROADMAP-alpha.md': ALPHA})
    table = build_part_rows(parts_of(index))
    assert 'Needs Lucas' in table and '| 🔴 |' not in table


def test_only_a_roadmap_part_is_counted_for_open_items(tmp_path) -> None:
    """A numbered list in prose looks exactly like a numbered item. Counting it read a SPECS part
    as having 13 open items — a meaningless number is worse than an absent column."""
    (tmp_path / 'SPECS.md').write_text('# S\n> s.\n', encoding='utf-8', newline='\n')
    (tmp_path / 'SPECS-alpha.md').write_text(
        '# A\n> a.\n\n1. first rule.\n2. second rule.\n', encoding='utf-8', newline='\n')
    assert 'open' not in part_facts(tmp_path / 'SPECS-alpha.md')


def test_a_type_with_parts_and_no_index_is_left_alone(tmp_path) -> None:
    """`code/` holds ROADMAP-verify.md and no ROADMAP.md. Writing one is a decision, not a save."""
    (tmp_path / 'ROADMAP-verify.md').write_text('# V\n> v.\n', encoding='utf-8', newline='\n')
    assert index_for(tmp_path / 'ROADMAP-verify.md') is None


def test_an_uncut_type_is_not_an_index(tmp_path) -> None:
    (tmp_path / 'ROADMAP.md').write_text('# R\n> r.\n', encoding='utf-8', newline='\n')
    assert index_for(tmp_path / 'ROADMAP.md') is None


def test_the_index_is_found_from_the_part_and_from_itself(tmp_path) -> None:
    index = _cut(tmp_path, **{'ROADMAP-alpha.md': ALPHA})
    assert index_for(tmp_path / 'ROADMAP-alpha.md') == index
    assert index_for(index) == index


def test_a_lowercase_instance_never_looks_like_a_part(tmp_path) -> None:
    """`read-amplification.md` splits on the hyphen too; only an UPPERCASE stem is a type."""
    (tmp_path / 'read.md').write_text('# r\n> r.\n', encoding='utf-8', newline='\n')
    (tmp_path / 'read-amplification.md').write_text('# r\n> r.\n', encoding='utf-8', newline='\n')
    assert index_for(tmp_path / 'read-amplification.md') is None
