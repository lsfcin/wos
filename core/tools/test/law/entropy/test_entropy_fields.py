# T0 the header-field check (core/SCHEMA.md § Every field that names our own code is verified): a field naming our own
# code names something that is there. Zero-token, runs in verify-fast.
#
# The boundary IS the design here, the same way it is for every check in this directory: a path and
# a sentence look identical inside `governs`, and charging the sentence would be the switched-off-in-
# a-week failure the front ruled against. Most cases below are about staying silent.
#
# The declarations are clean, so the check is total and the live corpus is asserted clean at the
# bottom rather than ridden on a ceiling.
from pathlib import Path

import entropy_fields as fields
from conftest import WORKSPACE_ROOT
from entropy_corpus import tracked_files

GATE = 'core/hooks/checks/type-gate.py'


def _doc(tmp_path: Path, header: str, name: str = 'SPECS-thing.md') -> list:
    path = tmp_path / name
    path.write_text(f'# A thing\n> What it is, in a sentence.\n{header}\n\n## Body\n',
                    encoding='utf-8', newline='\n')
    return fields.field_hits([path])


def test_a_field_naming_a_real_path_passes(tmp_path):
    assert _doc(tmp_path, f'> enforced-by: {GATE}') == []


def test_a_field_naming_a_path_that_is_not_there_is_a_finding(tmp_path):
    hits = _doc(tmp_path, '> enforced-by: core/hooks/checks/no-such-gate.py')
    assert len(hits) == 1 and 'does not exist' in hits[0]


def test_every_item_in_the_list_is_checked(tmp_path):
    """A comma list is as true as its weakest item; checking only the first is how a second
    enforcer gets named and never verified."""
    hits = _doc(tmp_path, f'> enforced-by: {GATE}, core/hooks/checks/no-such-gate.py')
    assert len(hits) == 1 and 'no-such-gate' in hits[0]


def test_a_wrapped_field_is_one_field(tmp_path):
    """The specimen that opened this: core/SCHEMA.md names three enforcers and the third
    sits on the wrapped line, where the parser dropped it — so the field read clean while a third of
    it was never looked at."""
    hits = _doc(tmp_path, f'> enforced-by: {GATE},\n> core/hooks/checks/no-such-gate.py')
    assert len(hits) == 1 and 'no-such-gate' in hits[0]


def test_the_description_is_not_glued_onto_the_first_field(tmp_path):
    """The `>` lines above the first field are prose that hoist.md_blurb owns. Reading them as a
    continuation would make every description an unresolvable path."""
    path = tmp_path / 'SPECS-thing.md'
    path.write_text(f'# A thing\n> What it is.\n> A second line of description.\n'
                    f'> enforced-by: {GATE}\n', encoding='utf-8', newline='\n')
    assert fields.field_hits([path]) == []


def test_a_sentinel_is_an_answer_not_a_path(tmp_path):
    """`spec: none` means the author was asked and said no. Charging it would make the honest
    answer the violation."""
    for value in ('none', '-', 'n/a'):
        assert _doc(tmp_path, f'> spec: {value}') == []


def test_a_path_in_governs_is_checked(tmp_path):
    assert len(_doc(tmp_path, '> governs: core/hooks/nowhere/')) == 1


def test_prose_in_governs_is_left_alone(tmp_path):
    """`governs` mixes both in one list — `engine/runtime/, libraries/` beside `frontend/ streaming`
    and `every file under code/`. Only the first token of an item can be a path, and only if it is
    shaped like one; the qualifier after it is written for a person."""
    assert _doc(tmp_path, '> governs: every file under code/, core/hooks/ and the gates in it') == []


def test_a_placeholder_names_a_shape_not_a_file(tmp_path):
    """`code/<project>/` is doing its job. A finding whose only fix is deleting the placeholder is
    a finding nobody can act on."""
    assert _doc(tmp_path, '> governs: code/<project>/, core/skills/*.md') == []


def test_the_commit_gate_does_not_read_governs(tmp_path):
    """`mixed=False` is what type-gate.py passes. A token misread inside a mixed list would stop a
    commit; the dashboard is where being wrong costs a reader ten seconds instead."""
    path = tmp_path / 'SPECS-thing.md'
    path.write_text('# A thing\n> What it is.\n> governs: core/hooks/nowhere/\n', encoding='utf-8', newline='\n')
    assert fields.field_hits([path], mixed=False) == []
    assert len(fields.field_hits([path], mixed=True)) == 1


def test_a_field_that_must_be_a_path_and_is_a_word_is_a_finding(tmp_path):
    """`enforced-by: the pre-commit hook` names no file anyone can open — the exact shape this
    front is about, one field away from being checkable."""
    hits = _doc(tmp_path, '> enforced-by: nobody')
    assert len(hits) == 1 and 'is not a path' in hits[0]


def test_a_feature_field_names_the_registry(tmp_path):
    hits = _doc(tmp_path, '> feature: not-a-declared-feature', name='SETUP-thing.md')
    assert len(hits) == 1 and 'core/features.txt' in hits[0]


def test_an_install_step_is_accepted_where_it_is_not_a_name(tmp_path):
    """The join core/features.txt declares is to its INSTALL column: a SETUP part names steps, and
    `git-hooks` is one step four features share. Holding the field to the name column would report
    the registry's own vocabulary as wrong."""
    assert _doc(tmp_path, '> feature: git-hooks, declared-deps', name='SETUP-thing.md') == []


def test_the_real_corpus_is_clean():
    """The rule is in force over the live tree, which is what makes this a fact about the workspace
    rather than a capability sitting beside it."""
    hits = fields.field_hits(tracked_files(WORKSPACE_ROOT, nested=True))
    assert hits == [], '\n'.join(hits)
