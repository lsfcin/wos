# T0 the vendor-name guard (core/SCHEMA.md): a list assigns a LEVEL, never a model.
# Zero-token, runs in verify-fast.
#
# The boundary is the whole check, so it is what these cases are about. A model name is legitimate
# as data and illegitimate as a directive, and the two look identical to a token ban — which is why
# the sweep that moved 26 directives to `level:` shipped without a guard, and why one directive
# survived in `code/ROADMAP-spec-drive.md` for three days after the sweep was called done.
from pathlib import Path

from conftest import WORKSPACE_ROOT

import entropy_corpus  # noqa: E402
import entropy_vendor  # noqa: E402


def test_no_list_assigns_a_model():
    """Asserted at ZERO over every list this repo tracks — the survivor was fixed first."""
    hits = entropy_vendor.vendor_directive_hits(
        entropy_corpus.tracked_files(WORKSPACE_ROOT),
        entropy_corpus.enforcement_paths(WORKSPACE_ROOT))
    assert hits == [], '\n'.join(hits)


def _list(tmp_path, line, name='ROADMAP.md'):
    doc = tmp_path / name
    doc.write_text(f'# r\n> a list\n\n1. an item. {line}\n', encoding='utf-8', newline='\n')
    return doc


def test_a_bolded_model_assignment_is_a_finding(tmp_path):
    hits = entropy_vendor.vendor_directive_hits(
        [_list(tmp_path, '→ **model: opus** for the contract')], set())
    assert len(hits) == 1
    assert 'level: low|medium|high' in hits[0], 'the finding must name the fix'
    assert 'routing.md' in hits[0], 'and where the model→level mapping actually lives'


def test_a_level_assignment_passes(tmp_path):
    assert entropy_vendor.vendor_directive_hits(
        [_list(tmp_path, '→ **level: high**, with Lucas')], set()) == []


def test_a_model_name_as_DATA_passes(tmp_path):
    """The case a flat token ban gets wrong, and the reason this check reads position.

    Both of these are honest: one reports a measurement, the other describes what a provider's
    frontmatter contains. Neither tells anyone which model to run.
    """
    assert entropy_vendor.vendor_directive_hits(
        [_list(tmp_path, 'cost: 375 turns, `model: opus` 100% of them')], set()) == []
    assert entropy_vendor.vendor_directive_hits(
        [_list(tmp_path, 'the agents file carries `model: haiku`, a provider-name violation')],
        set()) == []


def test_a_part_is_a_list_too(tmp_path):
    """By NAME, so a ROADMAP-<name>.md in any repo is covered without enumeration."""
    hits = entropy_vendor.vendor_directive_hits(
        [_list(tmp_path, '→ **model: sonnet**', name='ROADMAP-spec-drive.md')], set())
    assert len(hits) == 1


def test_a_file_that_is_not_a_list_is_not_asked(tmp_path):
    """core/flows/craft/routing.md is SUPPOSED to name models — it is the mapping."""
    assert entropy_vendor.vendor_directive_hits(
        [_list(tmp_path, '→ **model: opus**', name='SPECS.md')], set()) == []


def test_an_exempt_path_may_name_the_shape_it_forbids(tmp_path):
    doc = _list(tmp_path, '→ **model: opus**')
    assert entropy_vendor.vendor_directive_hits([doc], {Path(doc).resolve()}) == []
