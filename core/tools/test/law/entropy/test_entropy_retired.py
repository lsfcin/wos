# T0 the retired-token check (core/SCHEMA.md § Retired tokens): a rename is finished only
# when its old spelling appears nowhere. Zero-token, runs in verify-fast.
#
# Split from test_entropy_list.py 2026-08-24 at the 200-line cap. The boundary was already there —
# `entropy_list.py` answers several questions and this is the one that asserts against the LIVE
# workspace and is meant to be green at all times rather than baselined.
from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine

import pytest
import entropy_list  # noqa: E402
import schema_law  # noqa: E402


def test_no_retired_token_survives():
    """A rename is finished only when its old spelling appears nowhere."""
    hits = entropy_list.retired_hits(
        entropy_list.tracked_files(WORKSPACE_ROOT),
        schema_law.load_retired(),
        entropy_list.enforcement_paths(WORKSPACE_ROOT))
    assert hits == [], '\n'.join(hits)


def test_the_law_may_name_what_it_retires(tmp_path):
    law = tmp_path / 'SCHEMA.md'
    law.write_text('| `gone-token` | `kept` | 2026-01-01 |\n', encoding='utf-8', newline='\n')
    assert entropy_list.retired_hits([law], {'gone-token': 'kept'}, {law}) == []


def test_retired_token_in_a_filename_is_a_hit(tmp_path):
    """The `fable-loop-engineering.md` shape: hyphen is a boundary, so a retired token
    hiding inside a compound name is still found. That is where a half-done rename
    survives longest."""
    target = tmp_path / 'prefix-gone-token.md'
    target.write_text('clean body\n', encoding='utf-8', newline='\n')
    hits = entropy_list.retired_hits([target], {'gone-token': 'kept'}, set())
    assert len(hits) == 1
    assert 'filename' in hits[0]


def test_an_inflection_of_a_retired_token_is_a_hit(tmp_path):
    """An inflection is the same word, and until 2026-09-18 none of them counted.

    The check matched the exact token only, so `tiers`, `sharding` and `Slugs` sat in tracked files
    while it reported zero and core/SCHEMA.md claimed three finished renames. A trailing `e` is
    dropped before suffixing, or `probe` would never reach `probing`.
    """
    target = tmp_path / 'notes.md'
    target.write_text('the gone-tokens were gone-tokening\n', encoding='utf-8', newline='\n')
    assert len(entropy_list.retired_hits([target], {'gone-token': 'kept'}, set())) == 1
    ending_in_e = tmp_path / 'other.md'
    ending_in_e.write_text('still probing it\n', encoding='utf-8', newline='\n')
    assert len(entropy_list.retired_hits([ending_in_e], {'probe': 'metadata'}, set())) == 1


def test_an_accented_letter_is_part_of_the_word(tmp_path):
    """pt-br words run on past ASCII: until 2026-09-25 `á` counted as a boundary, so retiring
    `mal` would have failed on `malária`. The token standing alone is still a hit."""
    target = tmp_path / 'notas.md'
    target.write_text('a malária voltou\n', encoding='utf-8', newline='\n')
    assert entropy_list.retired_hits([target], {'mal': 'kept'}, set()) == []
    target.write_text('fez mal\n', encoding='utf-8', newline='\n')
    assert len(entropy_list.retired_hits([target], {'mal': 'kept'}, set())) == 1


def test_a_retired_token_inside_a_url_is_not_a_hit(tmp_path):
    """Somebody else chose those words; no rename of ours can reach them.

    Found 2026-08-24 by an INBOX capture — a link whose short_name contained a retired token turned the
    suite red, and the check's own advice was to delete the line, which would have deleted Lucas's
    capture. A quoted URL is evidence, not an unfinished rename.
    """
    target = tmp_path / 'INBOX.md'
    target.write_text('https://example.com/a-gone-token-post\n', encoding='utf-8', newline='\n')
    assert entropy_list.retired_hits([target], {'gone-token': 'kept'}, set()) == []


def test_a_vendored_file_is_not_policed():
    """core/hooks/vendored.txt promises exemption from every authoring rule, and this check
    never read it — so a draft another harness wrote sat in the report as a finding nobody could
    clear, because clearing it edits the artifact being compared (2026-09-18)."""
    import entropy_corpus
    import file_law
    exempt = entropy_corpus.enforcement_paths(WORKSPACE_ROOT)
    vendored = [p for p in entropy_list.tracked_files(WORKSPACE_ROOT)
                if file_law.is_vendored(p, WORKSPACE_ROOT)]
    if not vendored:   # the vendored drafts left with brain/ (2026-11-19): no subject in this repo
        pytest.skip('no vendored file is tracked in this checkout')
    assert all(p.resolve() in exempt for p in vendored)


def test_the_line_number_survives_a_blanked_url(tmp_path):
    """The URL is blanked in place rather than cut, so offsets — and line numbers — still hold."""
    target = tmp_path / 'notes.md'
    target.write_text('https://example.com/gone-token\n\nreal gone-token here\n', encoding='utf-8', newline='\n')
    hits = entropy_list.retired_hits([target], {'gone-token': 'kept'}, set())
    assert len(hits) == 1 and 'line 3' in hits[0]
