# T0 roadmap item numbers may not be cited outside a roadmap. Zero-token, runs in verify-fast.
#
# The live-workspace assertion here is meant to be green at all times, not baselined. It was
# red when written — 91 numbered citations across ~50 files, two of them naming Fronts that
# have never existed — and the fix was to rewrite every pointer, not to widen the test.
import importlib.util
from pathlib import Path

from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine
# sys.path for the enforcement layer is set once, by conftest.py — a second copy
# here would go stale the next time core/hooks is split.
import entropy_corpus  # noqa: E402

spec = importlib.util.spec_from_file_location(
    'citation_gate', WORKSPACE_ROOT / 'core/hooks/checks/citation-gate.py')
entropy_citations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entropy_citations)


def test_no_item_number_is_cited_outside_a_roadmap():
    """A closed item is deleted, so a number cited elsewhere is a pointer to nothing."""
    hits = entropy_citations.citation_hits(
        entropy_corpus.tracked_files(WORKSPACE_ROOT),
        entropy_citations.citation_exempt_paths(WORKSPACE_ROOT))
    assert hits == [], '\n'.join(hits)


def test_a_citation_in_source_is_a_hit(tmp_path):
    source = tmp_path / 'gate.py'
    source.write_text('# Level 0 gate (Front 4.1): the allowlist.\n', encoding='utf-8', newline='\n')
    hits = entropy_citations.citation_hits([source], set())
    assert len(hits) == 1
    assert "'Front 4.1'" in hits[0]


def test_the_bare_form_is_a_hit(tmp_path):
    """`Front 9` outnumbered `Front 9.2` in the real corpus; a decimals-only pattern misses it."""
    source = tmp_path / 'notes.md'
    source.write_text('The lesson Front 9 paid for twice.\n', encoding='utf-8', newline='\n')
    assert len(entropy_citations.citation_hits([source], set())) == 1


def test_a_lettered_subitem_is_a_hit(tmp_path):
    source = tmp_path / 'notes.md'
    source.write_text('downstream of Front 10.1b, which gates it\n', encoding='utf-8', newline='\n')
    assert len(entropy_citations.citation_hits([source], set())) == 1


def test_a_roadmap_may_number_its_own_items(tmp_path):
    roadmap = tmp_path / 'ROADMAP.md'
    roadmap.write_text('See Front 4.1 above.\n', encoding='utf-8', newline='\n')
    assert entropy_citations.citation_hits([roadmap], set()) == []


def test_a_scoped_roadmap_may_too(tmp_path):
    """ROADMAP-<name>.md is the same type wearing a scope suffix, so it carries the same right."""
    roadmap = tmp_path / 'ROADMAP-verify.md'
    roadmap.write_text('Advances Front 3.1.\n', encoding='utf-8', newline='\n')
    assert entropy_citations.citation_hits([roadmap], set()) == []


def test_a_lookalike_name_is_not_a_roadmap(tmp_path):
    """Only the type and its suffix form are exempt — not any file starting with the word."""
    other = tmp_path / 'ROADMAPPING.md'
    other.write_text('Front 4.1 is cited here.\n', encoding='utf-8', newline='\n')
    assert len(entropy_citations.citation_hits([other], set())) == 1


def test_the_retired_spelling_is_a_hit_even_in_a_roadmap(tmp_path):
    """The number exemption is for the current spelling only — a rename must reach everywhere."""
    roadmap = tmp_path / 'ROADMAP.md'
    roadmap.write_text('See Frente 4.1 above.\n', encoding='utf-8', newline='\n')
    hits = entropy_citations.citation_hits([roadmap], set())
    assert len(hits) == 1
    assert 'renamed to `Front`' in hits[0]


def test_the_retired_word_alone_is_legal_portuguese(tmp_path):
    """`frente` means a work front; branches/casinhas uses it that way. Only the shape is banned."""
    source = tmp_path / 'obra.md'
    source.write_text('| Frente | Onde | Status |\n', encoding='utf-8', newline='\n')
    assert entropy_citations.citation_hits([source], set()) == []


def test_the_law_may_name_the_shape_it_forbids(tmp_path):
    law = tmp_path / 'SCHEMA.md'
    law.write_text('Never cite `Front 4.1` from code.\n', encoding='utf-8', newline='\n')
    assert entropy_citations.citation_hits([law], {law}) == []


def test_a_front_without_a_number_is_prose(tmp_path):
    """The word itself is legal English — only the numbered pointer is a dead reference."""
    source = tmp_path / 'notes.md'
    source.write_text('progress on several fronts, and the Front holds\n', encoding='utf-8', newline='\n')
    assert entropy_citations.citation_hits([source], set()) == []


def test_a_longer_token_is_not_a_hit(tmp_path):
    source = tmp_path / 'notes.md'
    source.write_text('Frontier 4 models and Fronting 9 requests\n', encoding='utf-8', newline='\n')
    assert entropy_citations.citation_hits([source], set()) == []


def test_the_documents_stating_the_rule_may_quote_it():
    """SCHEMA.md and hooks/SPECS.md describe the shape; both fail the check without an exemption."""
    exempt = entropy_citations.citation_exempt_paths(WORKSPACE_ROOT)
    assert (WORKSPACE_ROOT / 'core/SCHEMA.md').resolve() in exempt
    assert (WORKSPACE_ROOT / 'core/hooks/SPECS.md').resolve() in exempt


def test_a_part_of_an_exempt_document_inherits_the_exemption():
    """Derived, never listed. `core/hooks/SPECS.md` outgrew the line cap and its § Git pre-commit
    section — which has to name the shape this gate forbids — moved into a sibling and stopped
    being exempt on arrival. Enumerating parts would fail again at the next split."""
    exempt = entropy_citations.citation_exempt_paths(WORKSPACE_ROOT)
    for part in (WORKSPACE_ROOT / 'core/hooks').glob('SPECS-*.md'):
        assert part.resolve() in exempt, part


def test_no_prose_restates_a_number_the_numeric_law_owns():
    """The live assertion, green at all times. It was red when written: eight authored files still
    named 150/200 six days after the law moved to 200/250, and one named the crowding law's previous
    pair. Ruled by Lucas 2026-09-12, scope the law only — a measured number in prose is a separate
    question with a separate owner."""
    hits = entropy_citations.limit_hits(
        entropy_corpus.tracked_files(WORKSPACE_ROOT),
        entropy_citations.limit_exempt_paths(WORKSPACE_ROOT))
    assert hits == [], '\n'.join(hits)


def test_a_stale_copy_of_the_line_law_is_a_hit(tmp_path):
    """The shape that actually rotted, in the two spellings the corpus used."""
    for text in ('under the 150 warn / 200 block thresholds\n', '| 150 LOC | Warning at commit |\n'):
        doc = tmp_path / 'notes.md'
        doc.write_text(text, encoding='utf-8', newline='\n')
        assert len(entropy_citations.limit_hits([doc], set())) == 1, text


def test_naming_the_owner_instead_of_the_number_passes(tmp_path):
    """The fix is a pointer, never a corrected copy: a copy rots again at the next ruling."""
    doc = tmp_path / 'notes.md'
    doc.write_text('Both numbers live in `core/hooks/limits.env`.\n', encoding='utf-8', newline='\n')
    assert entropy_citations.limit_hits([doc], set()) == []


def test_block_as_an_ordinary_word_beside_a_count_is_not_a_hit(tmp_path):
    """`a 16,000-token block of bodies` is a sentence about reading. A whole-line conjunction
    called it a limit, which is why the law word has to TOUCH the number it governs."""
    doc = tmp_path / 'notes.md'
    doc.write_text("no room for a block of 16,000 tokens, and last session's ran to 48 lines\n",
                   encoding='utf-8', newline='\n')
    assert entropy_citations.limit_hits([doc], set()) == []


def test_a_generated_block_is_authored_by_nobody(tmp_path):
    """A routing row is written from a first-line comment, so a finding inside one names a file
    that cannot be edited to clear it — the gate would block that commit forever."""
    doc = tmp_path / 'CONTEXT.md'
    doc.write_text('<!-- routing:start -->\n| x | blocks a file at 250 lines |\n<!-- routing:end -->\n',
                   encoding='utf-8', newline='\n')
    assert entropy_citations.limit_hits([doc], set()) == []


def test_the_checker_exempts_itself_and_its_tests():
    """Otherwise the check fails on the file that defines it — the corpse of a self-referring rule."""
    exempt = entropy_citations.citation_exempt_paths(WORKSPACE_ROOT)
    here = Path(__file__).resolve()
    checker = WORKSPACE_ROOT / 'core/hooks/checks/citation-gate.py'
    assert here in exempt
    assert checker.resolve() in exempt
