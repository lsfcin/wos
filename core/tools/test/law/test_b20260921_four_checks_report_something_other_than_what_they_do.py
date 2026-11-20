# b20260921 regression — four checks whose report did not match what they do.
#
# ONE FILE FOR FOUR IDS, deliberately. They are one finding: a check that reports something other
# than what is true, found four times in one session. Four spec files naming one class would cost
# the corpus four headers to say the same sentence, against core/norms/reduce.md — so the four
# ISSUES entries share the id `b20260921` and this is the proof for all of them.
#
# What each one was:
#   crowding   — the signal said which number was crossed and never that it had not refused, while
#                the ceiling failed the suite at the WARN. One number reading as one law, acting
#                as two. Lucas, 2026-09-21: "WARN é WARN" — every WARN names its BLOCK.
#   size       — every ISSUES.md is declared generated, which is right for the authoring rules and
#                dropped the file out of the corpus AND the weight. Exempt from a RULE is not
#                exempt from a MEASUREMENT.
#   wiring     — the name witness read raw text, so any word the file already used passed it.
#   FIXED gate — it demanded a `## b<id>` heading no ISSUES.md in this workspace has ever used:
#                937 runs, 0 blocks, while the list's own head claimed it governed the file.
import importlib.machinery
import importlib.util
import re
import sys

from conftest import WORKSPACE_ROOT
from file_law import authored_line_count, load_limits

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/entropy'))
import entropy_crowding  # noqa: E402

WARN, CAP = load_limits()['WARN_FILES'], load_limits()['BLOCK_FILES']


def _load(rel: str, name: str):
    """Import a module by PATH, never by name.

    Two of the four surfaces are not importable any other way: `core/tools/wos/size` has no
    extension, and the crowding ceiling is a test module whose directory only reaches sys.path if
    pytest happens to have collected it first. A spec that depends on collection order proves
    nothing on the run where the order changes.
    """
    path = WORKSPACE_ROOT / rel
    # The loader is named rather than inferred: `size` is an extensionless CLI, and
    # spec_from_file_location hands back None for a name Python does not recognise as source.
    spec = importlib.util.spec_from_file_location(
        name, path, loader=importlib.machinery.SourceFileLoader(name, str(path)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- crowding: a WARN that did not refuse must say so, and name where refusal starts ------------

def test_the_crowding_warning_says_it_did_not_refuse(tmp_path):
    """The pattern core/hooks/checks/line_counts.py earned on 2026-09-15 and crowding never got:
    a summary says WHAT HAPPENED, not which number was crossed."""
    signal = entropy_crowding.crowding_signals(
        [tmp_path / f'm{i}.py' for i in range(WARN + 1)], tmp_path)[0]
    assert 'NOT REFUSED' in signal, signal
    assert str(CAP) in signal, f'the warning must name the cap it has not reached: {signal}'


def test_the_crowding_refusal_says_it_refused(tmp_path):
    signal = entropy_crowding.crowding_signals(
        [tmp_path / f'm{i}.py' for i in range(CAP + 1)], tmp_path)[0]
    assert 'REFUSED' in signal and 'NOT REFUSED' not in signal, signal


def test_the_crowding_ceiling_holds_the_cap_not_the_signal():
    """A suite that fails IS a refusal, whatever the message calls it. So the whole-tree ceiling
    keys on BLOCK_FILES; below that the report is the only consequence."""
    ceiling = _load('core/tools/test/law/entropy/test_entropy_crowding.py', '_crowding_ceiling')
    assert ceiling.CAP == CAP, 'the ceiling must refuse at the cap, not at the signal'


# --- size: a half-generated file is measured by its authored half -------------------------------

def test_a_generated_block_is_not_charged_to_the_author():
    text = ('# Title\n'
            'authored one\n'
            '<!-- entropy:start -->\n'
            'generated one\n'
            'generated two\n'
            '<!-- entropy:end -->\n'
            'authored two\n')
    # Three, not four: the two marker lines belong to the generator that writes between them.
    assert authored_line_count(text) == 3


def test_a_wholly_generated_document_counts_zero():
    """The half that must NOT change: a file that is nothing but a block still weighs nothing."""
    assert authored_line_count('<!-- verify:start -->\nx\ny\n<!-- verify:end -->\n') == 0


def test_size_sees_the_list_it_had_been_blind_to():
    size = _load('core/tools/wos/size', '_size_under_test')
    assert 'ISSUES.md' in size.authored_md(WORKSPACE_ROOT), (
        'ISSUES.md is declared generated for the AUTHORING rules; that is not a reason for the '
        'measurement to lose the hand-written half')


# --- wiring: the name witness reads code, not prose ---------------------------------------------

def test_the_name_witness_refuses_a_name_that_is_only_prose():
    wiring = _load('core/tools/test/wos/test_features_wiring.py', '_wiring_under_test')
    says = wiring.names_itself
    assert not says('# the symmetry rule is explained here\nrun()\n', 'symmetry', 'x.py')
    assert not says('call_the_law(symmetry)\n', 'symmetry', 'x.py')
    assert says("is_enabled('symmetry')\n", 'symmetry', 'x.py')
    assert says('sh "$RUN" hooks/feature_law.py --enabled symmetry\n', 'symmetry', 'x.sh')


# --- the FIXED gate: it must be able to see the list it governs ---------------------------------

def test_the_fixed_gate_reads_the_shape_the_lists_are_really_written_in():
    """937 runs and 0 blocks, because every entry is a bullet and the gate wanted a heading."""
    gate = _load('core/hooks/checks/issues-gate.py', '_issues_gate_under_test')
    items = gate._items((WORKSPACE_ROOT / 'ISSUES.md').read_text(encoding='utf-8'))
    assert items, 'the gate cannot see a single item in the list it claims to govern'
    assert all(item.startswith('- ') for item in items)


def test_the_fixed_gate_asks_for_proof_when_a_keyed_item_leaves():
    gate = _load('core/hooks/checks/issues-gate.py', '_issues_gate_keyed')
    before = '## Open\n\n- **a bug** with id b20260921 in its text.\n\n- **another**, no id.\n'
    assert gate.bug_ids(before) == {'b20260921'}
    assert gate.bug_ids('## Open\n\n- **another**, no id.\n') == set()


def test_an_item_that_carries_no_id_is_not_invented_into_one():
    """The other direction. The gate holds KEYED items to proof; it must not start refusing every
    edit to a list whose entries predate the id, which is how a new gate breaks the tree it lands on.
    """
    gate = _load('core/hooks/checks/issues-gate.py', '_issues_gate_2')
    assert gate.bug_ids('## Open\n\n- **a bug nobody gave an id**, and its second line.\n') == set()


def test_the_spec_this_file_is_can_be_found_by_the_id_it_answers_to():
    """The gate's own matcher, run against the id the four entries carry. If this fails, deleting
    those entries is unprovable and the gate is right to refuse."""
    gate = _load('core/hooks/checks/issues-gate.py', '_issues_gate_3')
    assert gate.has_spec(WORKSPACE_ROOT, 'b20260921')
    assert not gate.has_spec(WORKSPACE_ROOT, 'b20260921-no-such-half')
    assert re.search(r'b20260921', __file__)
