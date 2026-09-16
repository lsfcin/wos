# T0 no-hand-inventory rule (Level 0, law in core/SCHEMA.md). Zero-token, runs in verify-fast.
#
# Split out of law/test_type_gate.py 2026-08-15 at the size gate, and the split fixes a
# misfiling: `check_inventory` lives in `entropy_context.py` with the goal-link and
# misplaced-answer checks, and its coverage was the one piece left behind in the type
# gate's file. A surface and its coverage are one word apart (see this directory's head).
#
# The rule: CONTEXT.md never hand-lists files; the generated routing block owns inventory
# (core/SCHEMA.md § Boundaries where types nearly touch). Every case here is a shape that
# list has actually taken in this workspace, and the boundary each shape blurs — a glob is
# not a file, an area name is not a file, a generated block is not a hand-written one.
from entropy_context import check_inventory


def _context(tmp_path, body):
    target = tmp_path / 'CONTEXT.md'
    target.write_text(body, encoding='utf-8', newline='\n')
    return target


def _with_files(tmp_path, *names):
    for name in names:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('x\n', encoding='utf-8', newline='\n')


def test_ascii_tree_is_flagged(tmp_path):
    # The code/isoroll-content/CONTEXT.md '## Repository Shape' class of violation.
    target = _context(tmp_path, '# d\n> desc\n\n## Repository Shape\n\n'
                                '```\nsrc/\n├── a.py\n└── b.py\n```\n')
    failure = check_inventory(target)
    assert failure is not None
    assert 'ASCII directory tree' in failure


def test_inventory_heading_is_flagged(tmp_path):
    target = _context(tmp_path, '# d\n> desc\n\n## File Map\n\nprose only, no bullets\n')
    failure = check_inventory(target)
    assert failure is not None
    assert 'File Map' in failure


def test_path_bullets_are_flagged(tmp_path):
    _with_files(tmp_path, 'src/a.py', 'src/b.py', 'src/c.py')
    target = _context(tmp_path, '# d\n> desc\n\n'
                                '- `src/a.py` — does a\n'
                                '- `src/b.py` — does b\n'
                                '- `src/c.py` — does c\n')
    failure = check_inventory(target)
    assert failure is not None
    assert '3 bullets/table rows listing real files' in failure


def test_a_backticked_link_bullet_is_still_a_bullet(tmp_path):
    """`- [`a.py`](a.py)` — the backtick INSIDE the link defeated the old pattern, so the
    most common way this workspace writes a file pointer was the one shape that escaped."""
    _with_files(tmp_path, 'a.py', 'b.py', 'c.py')
    target = _context(tmp_path, '# d\n> desc\n\n'
                                '- [`a.py`](a.py) — does a\n'
                                '- [`b.py`](b.py) — does b\n'
                                '- [`c.py`](c.py) — does c\n')
    assert check_inventory(target) is not None


def test_two_path_bullets_are_allowed(tmp_path):
    """Pointing at a couple of files in prose is navigation, not an inventory."""
    _with_files(tmp_path, 'src/a.py', 'src/b.py')
    target = _context(tmp_path, '# d\n> desc\n\n'
                                '- `src/a.py` — the entry point\n'
                                '- `src/b.py` — the parser\n')
    assert check_inventory(target) is None


def test_path_table_rows_are_flagged(tmp_path):
    """The brain/CONTEXT.md class: a hand-written `| File / Folder | Role |` above the
    generated block, saying the same thing. A table is the same inventory as a bullet
    list, and this check — written for exactly this defect — could not see one."""
    _with_files(tmp_path, 'a.py', 'b.py', 'c.py')
    target = _context(tmp_path, '# d\n> desc\n\n'
                                '| File | Role |\n|------|------|\n'
                                '| [`a.py`](a.py) | does a |\n'
                                '| [`b.py`](b.py) | does b |\n'
                                '| [`c.py`](c.py) | does c |\n')
    failure = check_inventory(target)
    assert failure is not None
    assert '3 bullets/table rows listing real files' in failure


def test_two_path_table_rows_are_allowed(tmp_path):
    """Same threshold as bullets: naming a couple of files is navigation."""
    _with_files(tmp_path, 'a.py', 'b.py')
    target = _context(tmp_path, '# d\n> desc\n\n'
                                '| File | Role |\n|------|------|\n'
                                '| [`a.py`](a.py) | the entry point |\n'
                                '| [`b.py`](b.py) | the parser |\n')
    assert check_inventory(target) is None


def test_bullets_and_table_rows_are_counted_together(tmp_path):
    """One list split across two shapes is still one list — otherwise the fix for a
    flagged bullet list is to redraw half of it as a table."""
    _with_files(tmp_path, 'a.py', 'b.py', 'c.py')
    target = _context(tmp_path, '# d\n> desc\n\n'
                                '- `a.py` — does a\n'
                                '- `b.py` — does b\n\n'
                                '| File | Role |\n|------|------|\n'
                                '| [`c.py`](c.py) | does c |\n')
    assert check_inventory(target) is not None


def test_a_table_that_is_not_about_files_is_allowed(tmp_path):
    """brain/CONTEXT.md's `| Area | Covers |` and core/tools' `| Runtime | ... |` are the
    directory describing itself. The path must be the SUBJECT of the row — its first cell
    — and must exist; a table keyed on anything else is not an inventory."""
    _with_files(tmp_path, 'health.md', 'career.md', 'finances.md')
    target = _context(tmp_path, '# brain\n> desc\n\n'
                                '| Area | Covers |\n|------|--------|\n'
                                '| `health` | body, sleep, exercise |\n'
                                '| `career` | research, papers, teaching |\n'
                                '| `finances` | money, taxes, admin |\n')
    assert check_inventory(target) is None


def test_a_table_of_files_that_do_not_exist_is_allowed(tmp_path):
    """The bullets' escape hatch, kept symmetric: a table of naming PATTERNS, or of files
    that live elsewhere, describes the directory rather than listing it."""
    target = _context(tmp_path, '# d\n> desc\n\n'
                                '| File | Role |\n|------|------|\n'
                                '| `*_sq.png` | square crops |\n'
                                '| `*_wide.png` | wide crops |\n'
                                '| `*_thumb.png` | thumbnails |\n')
    assert check_inventory(target) is None


def test_naming_convention_globs_are_allowed(tmp_path):
    """academy/papers/*/images/CONTEXT.md documents filename PATTERNS, not files.

    This was a real false positive: five bullets of glob patterns read as an
    inventory until the check required the path to exist on disk.
    """
    target = _context(tmp_path, '# images\n> All manuscript figures\n\n'
                                'Naming conventions:\n'
                                '- `grav_cam2_gXX_sq.png` — gravity gradient panels\n'
                                '- `spin_s4_*.sq.png` — spin gradient panels\n'
                                '- `newton_sX_sq.png` — scene gallery\n'
                                '- `*_rk4_s3_front_480p.png` — metric comparison\n')
    assert check_inventory(target) is None


def test_generated_routing_block_is_not_an_inventory(tmp_path):
    """Everything below routing:start is generated and owns inventory by design — which
    is why the table criterion reads the head alone, or it would flag every CONTEXT.md."""
    _with_files(tmp_path, 'a.py', 'b.py', 'c.py')
    target = _context(tmp_path, '# d\n> desc\n\n<!-- routing:start -->\n## Routing\n\n'
                                '| File | Interface | API | Description |\n'
                                '|---|---|---|---|\n'
                                '| [`a.py`](a.py) | — | — | does a |\n'
                                '| [`b.py`](b.py) | — | — | does b |\n'
                                '| [`c.py`](c.py) | — | — | does c |\n'
                                '<!-- routing:end -->\n')
    assert check_inventory(target) is None


def test_clean_context_passes(tmp_path):
    target = _context(tmp_path, '# thing\n> What this directory is, in one line.\n\n'
                                'Prose about the subtree and its rules.\n')
    assert check_inventory(target) is None


def test_non_context_file_is_not_inventory_checked(tmp_path):
    target = tmp_path / 'ROADMAP.md'
    target.write_text('## File Map\n\n- `a.py` — a\n- `b.py` — b\n- `c.py` — c\n',
                      encoding='utf-8', newline='\n')
    assert check_inventory(target) is None
