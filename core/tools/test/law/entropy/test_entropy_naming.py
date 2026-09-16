# T0 naming and placement (Level 0, law in core/SCHEMA.md). Zero-token, runs in verify-fast.
#
# The whole-tree test is a RATCHET, not a green light: it asserts the live violations are
# a subset of a named baseline, so a new one fails the build while the three inherited
# ones stay visible with the item that will remove them. Shrinking the baseline is the
# only edit this test should ever get.
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine
# sys.path for the enforcement layer is set once, by conftest.py — a second copy
# here would go stale the next time core/hooks is split.

import entropy_list  # noqa: E402
import entropy_naming  # noqa: E402
import schema_law  # noqa: E402

# Inherited violations, each with the item that retires it. Nothing else may join.
BASELINE = set()


def _live_violations():
    allowed, _ = schema_law.load_law()
    scopes = schema_law.load_scopes()
    found = set()
    for path in entropy_list.tracked_files(WORKSPACE_ROOT):
        for failure in (entropy_naming.check_shape(path, allowed),
                        entropy_naming.check_dirs(path, WORKSPACE_ROOT),
                        entropy_naming.check_placement(path, scopes, WORKSPACE_ROOT)):
            if failure:
                found.add(failure)
    return found


def _baselined(failure: str) -> bool:
    return any(known in failure for known in BASELINE)


def test_no_new_naming_violation():
    new = sorted(f for f in _live_violations() if not _baselined(f))
    assert new == [], '\n'.join(new)


def test_baseline_is_not_stale():
    """A baselined path that stopped violating must leave the baseline, or the ratchet
    silently stops protecting whatever reuses that name."""
    live = _live_violations()
    unused = sorted(k for k in BASELINE if not any(k in f for f in live))
    assert unused == [], f'fixed — drop from BASELINE: {unused}'


def test_spaces_and_accents_are_rejected(tmp_path):
    target = tmp_path / 'Restrições Curriculares.md'
    assert 'space or a non-ASCII' in entropy_naming.check_shape(target, set())


def test_received_documents_keep_their_names(tmp_path):
    """The 91 tracked .docx/.pdf from the PPC process ARE their provenance; renaming them
    would break the link to the official source. The rule governs what we author."""
    for name in ('RESOLUÇÃO CNE_CEB Nº 2.pdf', '1__PSICOLOGIA I.docx'):
        assert entropy_naming.check_shape(tmp_path / name, set()) is None


def test_kebab_instance_and_snake_module_both_pass(tmp_path):
    for name in ('some-notes.md', 'video_core.py', '_template.md', '.agentrc.json',
                 '__init__.py'):
        assert entropy_naming.check_shape(tmp_path / name, set()) is None


def test_type_name_shape_passes_only_for_a_known_type(tmp_path):
    allowed = {'ROADMAP.md'}
    assert entropy_naming.check_shape(tmp_path / 'ROADMAP-ementas.md', allowed) is None
    assert entropy_naming.check_shape(tmp_path / 'LEXICON-notes.md', allowed) is not None


def test_mixed_name_dot_type_shape_is_rejected(tmp_path):
    failure = entropy_naming.check_shape(tmp_path / 'video.SETUP.md', {'SETUP.md'})
    assert failure is not None and 'retired' in failure


def test_uppercase_type_is_left_to_the_allowlist(tmp_path):
    """check_shape must not double-judge a type name; type-gate.py owns that question."""
    assert entropy_naming.check_shape(tmp_path / 'LEXICON.md', set()) is None


def test_uppercase_directory_is_flagged(tmp_path):
    target = tmp_path / 'PDA' / 'pda_2026.tex'
    assert 'not lowercase' in entropy_naming.check_dirs(target, tmp_path)


def test_scaffolding_directory_is_allowed(tmp_path):
    target = tmp_path / '_templates' / 'notes.md'
    assert entropy_naming.check_dirs(target, tmp_path) is None


def test_root_only_type_outside_root_is_flagged(tmp_path):
    scopes = {'AGENTS.md': 'root'}
    nested = tmp_path / 'sub' / 'AGENTS.md'
    nested.parent.mkdir()
    assert 'root-only' in entropy_naming.check_placement(nested, scopes, tmp_path)
    assert entropy_naming.check_placement(tmp_path / 'AGENTS.md', scopes, tmp_path) is None


def test_readme_needs_a_repo_root(tmp_path):
    scopes = {'README.md': 'repo-root'}
    assert entropy_naming.check_placement(tmp_path / 'README.md', scopes, tmp_path)
    (tmp_path / '.git').mkdir()
    assert entropy_naming.check_placement(tmp_path / 'README.md', scopes, tmp_path) is None


def test_a_template_readme_is_not_a_claim(tmp_path):
    scopes = {'README.md': 'repo-root'}
    target = tmp_path / '_templates' / 'README.md'
    target.parent.mkdir()
    assert entropy_naming.check_placement(target, scopes, tmp_path) is None
