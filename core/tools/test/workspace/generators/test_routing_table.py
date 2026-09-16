# The routing table's generated columns (core/hooks/SPECS.md). Zero-token, runs in verify-fast.
#
# warn-exempt: a suite file grows by CASE, and cutting to the warn deletes coverage of a generator
# whose failures are silent by construction. The block cap still applies.
#
# The rule here was measured on 2026-07-30 across 159 CONTEXT.md / 1242 rows: a generated column
# empty on EVERY row is not emitted. 773 of 1242 rows carried an em-dash Interface, paying table
# width to say "nothing here".
#
# What the API column may name is the sibling question, in test_api_column.py.
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine
# sys.path for the enforcement layer is set once, by conftest.py — a second copy
# here would go stale the next time core/hooks is split.

from file_law import described  # noqa: E402  (the second describing route, asked not restated)
from hoist import DESC_LIMIT  # noqa: E402  (the bound is imported, never restated)
from workspace_meta import ALL_EXTS, COMMENT_RE, extract_api, file_description  # noqa: E402
from workspace_scanner import build_file_rows, carried, parse_preserved_files  # noqa: E402


def _table(tmp_path, **sources) -> str:
    files = []
    for name, body in sources.items():
        p = tmp_path / name
        p.write_text(body, encoding='utf-8', newline='\n')
        files.append((p, name))
    return build_file_rows(files, {}, tmp_path)


def test_an_all_empty_interface_column_is_dropped(tmp_path) -> None:
    table = _table(tmp_path, **{'a.py': '# alpha\n', 'b.py': '# beta\n'})
    assert '| Interface |' not in table
    assert '| File |' in table and 'Description |' in table


def test_a_column_with_one_real_value_survives(tmp_path) -> None:
    (tmp_path / 'a.pyi').write_text('def go() -> None: ...\n', encoding='utf-8', newline='\n')
    table = _table(tmp_path, **{'a.py': '# alpha\ndef go():\n    pass\n', 'b.py': '# beta\n'})
    assert '| Interface |' in table


def test_file_and_description_are_never_dropped(tmp_path) -> None:
    """Even when every description is the placeholder, the column is the table."""
    table = _table(tmp_path, **{'a.py': 'x = 1\n', 'b.py': 'y = 2\n'})
    assert table.splitlines()[0].startswith('| File |')
    assert table.splitlines()[0].rstrip().endswith('Description |')


def test_every_scanned_extension_has_a_way_to_be_described() -> None:
    """Every extension the scanner picks up must have SOME route to a description.

    Two lists that have to match, with nothing checking that they did: `.sh` and `.jsx`
    were in ALL_EXTS and absent from COMMENT_RE, so 59 tracked files were undescribable by
    construction. Each got `← add first-line comment` in its routing row no matter how well
    it was commented — including `core/hooks/post-edit.sh`, inside the enforcement
    directory, which was read as evidence of a discipline hole until the generator was asked.

    Two routes since 2026-09-04, because a format can have no comment syntax at all: a first-line
    comment where the format allows one, and core/hooks/described.txt where it does not. `.json`
    is the second route's whole reason — every config a harness dictates is one.
    """
    declared = {Path(p).suffix for p in described()}
    missing = sorted(ALL_EXTS - set(COMMENT_RE) - declared)
    assert not missing, (
        f'{missing} are scanned and have no route to a description, so file_description() returns '
        f"'' for every one of them and the generator asks for a comment the file may already "
        f'carry. Add a COMMENT_RE pattern in core/hooks/routing/workspace_meta.py, or — for a '
        f'format with no comment syntax — a line in core/hooks/described.txt.')


def test_a_shell_script_is_described_below_its_shebang(tmp_path) -> None:
    """The concrete case: a shebang is not the description, the comment under it is."""
    p = tmp_path / 'thing.sh'
    p.write_text('#!/usr/bin/env bash\n# does the thing\n', encoding='utf-8', newline='\n')
    assert file_description(p) == 'does the thing'


# ── a `.md` row describes the file, not just names it ─────────────────────────────────
#
# `COMMENT_RE['.md']` captured the `#` H1 and stopped, so every `.md` row in the corpus
# advertised a NAME where the sentence saying what the file is sat one line below, unread:
# `tree.md` read "The Craft Tree", `INBOX.md` read "inbox". The line-2 `>` blurb was already
# being hoisted — but only from a *child's* CONTEXT.md into its parent's subdirectory table.

def test_an_md_row_shows_its_blurb_not_its_heading(tmp_path) -> None:
    table = _table(tmp_path, **{'tree.md': '# The Craft Tree\n> Canonical map of `/craft`.\n'})
    assert 'Canonical map' in table
    assert 'The Craft Tree' not in table


def test_an_md_row_falls_back_to_its_heading(tmp_path) -> None:
    """No blurb is not a defect — GOALS.md is a dashboard under a bare H1."""
    table = _table(tmp_path, **{'GOALS.md': '# goals\n\nbody\n'})
    assert '| goals |' in table


def test_frontmatter_still_outranks_the_blurb(tmp_path) -> None:
    """A skill declares its description in frontmatter; that is the authored answer."""
    table = _table(tmp_path, **{
        's.md': '---\ndescription: the declared one\n---\n# s\n> the blurb\n'})
    assert 'the declared one' in table
    assert 'the blurb' not in table


def test_an_unanswered_scaffold_blurb_is_not_hoisted(tmp_path) -> None:
    """A generated marker is a question, not a description — hoisting one would answer it
    with itself, and the placeholder check would stop seeing it."""
    table = _table(tmp_path, **{'x.md': '# x\n> ← add description\n'})
    assert '← add description' not in table


def test_a_multiline_module_docstring_describes_the_module(tmp_path) -> None:
    """PEP 257's answer counts. The one-line-docstring pattern was the whole of it, so a
    docstring that opened on line 1 and closed three lines down read as undescribed."""
    p = tmp_path / 'a.py'
    p.write_text('#!/usr/bin/env python3\n"""Does the thing.\n\nAt length.\n"""\n',
                 encoding='utf-8', newline='\n')
    assert file_description(p) == 'Does the thing.'


def test_a_line_one_comment_outranks_the_docstring(tmp_path) -> None:
    """This workspace's convention is the `#` line, and the gate enforces it there. The
    docstring is a fallback — if it could outrank the comment, every row would move."""
    p = tmp_path / 'a.py'
    p.write_text('# the convention\n"""The docstring.\n\nMore.\n"""\n', encoding='utf-8', newline='\n')
    assert file_description(p) == 'the convention'


def test_a_folded_md_blurb_has_its_links_rebased(tmp_path) -> None:
    """A blurb from a folded subdirectory names files relative to ITS directory."""
    sub = tmp_path / 'sub'
    sub.mkdir()
    (sub / 'a.md').write_text('# a\n> see [SPECS.md](SPECS.md)\n', encoding='utf-8', newline='\n')
    table = build_file_rows([(sub / 'a.md', 'sub/a.md')], {}, tmp_path)
    assert '(sub/SPECS.md)' in table
    assert '](SPECS.md)' not in table


def test_a_long_md_blurb_is_bounded(tmp_path) -> None:
    """One file's paragraph must not set the width of another file's table.

    The bound is imported, never restated. It was hardcoded at 160 here — calibrated to a
    DESC_LIMIT of 80 — so raising the limit to hold two or three sentences (Lucas, 2026-08-19)
    failed this test for the one reason a limit test must never fail: a second copy of the
    number.
    """
    blurb = ('word ' * 200).strip()
    table = _table(tmp_path, **{'a.md': f'# a\n> {blurb}\n'})
    assert '…' in table, 'a blurb past the limit must say that it was cut'
    assert blurb not in table, 'the whole paragraph reached the table uncut'
    longest = max(len(line) for line in table.splitlines())
    assert longest <= DESC_LIMIT + 200, (
        f'longest row is {longest}; the description cell should be bounded by '
        f'DESC_LIMIT={DESC_LIMIT} plus the row chrome around it'
    )


def test_a_long_first_line_comment_is_bounded_too(tmp_path) -> None:
    """A code comment takes the same bound as a blurb, for the same reason.

    It was exempt until 2026-09-11 on the grounds that it is authored as this table's
    one-liner. It is not a line: `comment_paragraph` reads the whole opening paragraph for
    every `#`-commented language, so an author explaining a bug at length published the
    explanation into a table one directory up. One row in
    `core/tools/test/workspace/CONTEXT.md` — a mandatory read — held 1,300 characters of two
    bugs' history. Nothing is lost; the paragraph is still in the file it was written in.
    """
    comment = 'x ' * 400
    table = _table(tmp_path, **{'a.py': f'# {comment}\n'})
    assert '…' in table, 'a comment past the limit must say that it was cut'
    assert comment.strip() not in table, 'the whole paragraph reached the table uncut'


def test_a_short_first_line_comment_is_untouched(tmp_path) -> None:
    """The bound cuts essays, not descriptions — the ordinary row must survive verbatim."""
    comment = 'what this module is, in one line'
    table = _table(tmp_path, **{'a.py': f'# {comment}\n'})
    assert comment in table
    assert '…' not in table


def test_no_row_is_written_for_a_path_this_repo_is_told_to_ignore() -> None:
    """The table is generated from disk but SHIPS in git, so an ignored path is a row naming
    what the reader does not have. Ten had accumulated by 2026-09-01, one of them a scaffold
    the generator wrote itself inside an ignored directory — it made both the row and its file."""
    kept = WORKSPACE_ROOT / 'core/CONTEXT.md'
    assert carried([WORKSPACE_ROOT / 'outputs/report.md']) == []
    assert carried([kept]) == [kept]


def test_a_nested_repo_and_a_generated_mirror_keep_their_rows(tmp_path: Path) -> None:
    """Both are ignored HERE and carried by something else — the nested repo's own index, and
    sync-skills. Filtering on this repo's .gitignore alone emptied code/CONTEXT.md of all 15
    project rows the first time this ran."""
    (tmp_path / '.git').mkdir()
    mirror = WORKSPACE_ROOT / '.claude/skills/inbox/SKILL.md'
    assert carried([tmp_path]) == [tmp_path]
    assert carried([mirror]) == [mirror]


def test_preserved_descriptions_survive_a_narrower_table() -> None:
    """Descriptions are re-read from tables of any arity — first cell file, last cell desc."""
    four = '| [`a.py`](a.py) | — | `go` | does the thing |'
    two = '| [`a.py`](a.py) | does the thing |'
    assert parse_preserved_files(four) == {'a.py': 'does the thing'}
    assert parse_preserved_files(two) == {'a.py': 'does the thing'}
