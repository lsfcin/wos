# T0 unanswered placeholders (first-line-comment rule, core/hooks/SPECS.md). Zero-token, runs in verify-fast.
#
# Split from test_entropy_list.py 2026-08-15, alongside the check itself. The branch
# these cover shipped with NO test, which is how it went a year labelled as the wrong
# defect: `← add` was reported as "prose describing finished work" and told the reader
# to cut it, when cutting it only makes the generator write it back on the next save.
# A check with no boundary test states a claim nobody ever read back.
from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine

import entropy_list  # noqa: E402


def _context(directory, body):
    doc = directory / 'CONTEXT.md'
    doc.write_text(body, encoding='utf-8', newline='\n')
    return doc


def test_a_placeholder_is_not_finished_work(tmp_path):
    """The defect that motivated the split — same glyph, opposite instruction."""
    doc = _context(tmp_path, '# d\n> blurb\n\n| [`a.sh`](a.sh) | ← add first-line comment |\n')
    assert entropy_list.finished_work_hits([doc], set()) == []
    hit = entropy_list.unanswered_placeholders([doc], set())[0]
    assert hit.startswith(f'{doc}:4:'), 'file:line, so the finding can be opened'
    assert 'Deleting the marker' in hit, 'the remedy must not be "cut it"'


def test_every_marker_variant_counts(tmp_path):
    """A routing row, an empty blurb and a template field are one defect, counted per file."""
    doc = _context(tmp_path,
                   '# d\n> ← add description\n\n| a | ← add first-line comment |\n'
                   '| **Domain** | ← add paper-specific domain tags here |\n')
    hits = entropy_list.unanswered_placeholders([doc], set())
    assert len(hits) == 1, 'one finding per file — the reader pays for the whole file'
    assert '3 unanswered placeholder(s)' in hits[0]


def test_only_context_files_carry_the_marker(tmp_path):
    """The glyph is ordinary prose anywhere else; only the generator's own type is checked."""
    other = tmp_path / 'NOTES.md'
    other.write_text('the arrow ← add first-line comment is quoted here\n', encoding='utf-8', newline='\n')
    assert entropy_list.unanswered_placeholders([other], set()) == []


def test_a_generated_mirror_has_no_placeholder_to_answer(tmp_path):
    """Same rule as the finished-work check: a mirror is fixed at its generator."""
    mirror = tmp_path / '.claude' / 'skills'
    mirror.mkdir(parents=True)
    assert entropy_list.unanswered_placeholders(
        [_context(mirror, '> ← add description\n')], set()) == []


def test_the_law_may_show_the_marker_it_defines():
    """core/SCHEMA.md and the enforcement layer have to be able to quote their own glyph."""
    exempt = entropy_list.enforcement_paths(WORKSPACE_ROOT)
    assert entropy_list.unanswered_placeholders(
        [WORKSPACE_ROOT / 'core/SCHEMA.md'], exempt) == []
