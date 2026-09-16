# T0 the retired-token check (core/SCHEMA.md § Retired tokens): a rename is finished only
# when its old spelling appears nowhere. Zero-token, runs in verify-fast.
#
# Split from test_entropy_list.py 2026-08-24 at the 200-line cap. The boundary was already there —
# `entropy_list.py` answers several questions and this is the one that asserts against the LIVE
# workspace and is meant to be green at all times rather than baselined.
from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine

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


def test_a_retired_token_inside_a_url_is_not_a_hit(tmp_path):
    """Somebody else chose those words; no rename of ours can reach them.

    Found 2026-08-24 by an INBOX capture — a link whose short_name contained a retired token turned the
    suite red, and the check's own advice was to delete the line, which would have deleted Lucas's
    capture. A quoted URL is evidence, not an unfinished rename.
    """
    target = tmp_path / 'INBOX.md'
    target.write_text('https://example.com/a-gone-token-post\n', encoding='utf-8', newline='\n')
    assert entropy_list.retired_hits([target], {'gone-token': 'kept'}, set()) == []


def test_the_line_number_survives_a_blanked_url(tmp_path):
    """The URL is blanked in place rather than cut, so offsets — and line numbers — still hold."""
    target = tmp_path / 'notes.md'
    target.write_text('https://example.com/gone-token\n\nreal gone-token here\n', encoding='utf-8', newline='\n')
    hits = entropy_list.retired_hits([target], {'gone-token': 'kept'}, set())
    assert len(hits) == 1 and 'line 3' in hits[0]
