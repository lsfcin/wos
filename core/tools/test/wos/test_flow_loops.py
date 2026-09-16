# T0 the flow layer's loop bound (core/flows/CONTEXT.md § Rules that hold for every flow): a step
# that declares a loop must declare its numeric cap. Zero-token, no network.
#
# WHY THIS RULE AND NOT THE ONE THAT WAS PROPOSED. core/flows/craft/SPECS.md rejected a gate
# demanding an adversarial review step: an adversary always finds something, so demanding the step
# without demanding a bound builds the death loop the source itself warns about. Requiring the
# BOUND is what makes requiring the step safe, and it is true of every flow rather than of one
# technique.
#
# IMPORTED, NOT SOURCED, since the 2026-09-01 port. The validator was a shell fragment that
# `sync-skills` supplied $WORKSPACE to, so a check had to spawn `bash -c 'WORKSPACE=…; source …'`
# and spell both paths as POSIX text -- the Windows spelling arrived with every separator eaten,
# bash reported the validator missing, and the case read as the rule having stopped firing. The
# functions take their root as an argument now, so a throwaway tree is just an argument.
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools/wos/skills'))
import validate  # noqa: E402

BOUNDED = """---
description: d
args: a
type: utility
confirm: none
---
## Execution Loops
Return to the plan step while FATALs remain. **Iteration cap: at most 3 passes.**
"""

UNBOUNDED = """---
description: d
args: a
type: utility
confirm: none
---
## Execution Loops
Return to the plan step and re-review until the review passes.
"""

# The law files name the rule's own words. They state it; they do not run it.
STATES_THE_RULE = 'Loops are bounded: every loop declares an exit condition and an iteration cap.\n'


def _validate(tmp_path, files: dict) -> list:
    flows = tmp_path / 'core' / 'flows'
    flows.mkdir(parents=True)
    for name, body in files.items():
        (flows / name).write_text(body, encoding='utf-8', newline='\n')
    return validate.validate_flow_loops(tmp_path)


def test_a_loop_with_a_numeric_cap_passes(tmp_path):
    assert _validate(tmp_path, {'bounded.md': BOUNDED}) == []


def test_a_loop_with_no_number_is_rejected(tmp_path):
    """"Until the review passes" is exactly the wording that made this workspace's own adversarial
    review the unbounded case, so it is the wording the check uses."""
    problems = _validate(tmp_path, {'unbounded.md': UNBOUNDED})
    assert len(problems) == 1
    assert 'unbounded.md' in problems[0]
    assert 'no numeric cap' in problems[0]


def test_a_flow_declaring_no_loop_is_never_asked_for_a_cap(tmp_path):
    """Most flows run start to finish. A gate that asked all of them for a number would be a gate
    against the word `iteration` rather than against a hang."""
    assert _validate(tmp_path, {'straight.md': '---\ndescription: d\n---\nRun it once.\n'}) == []


def test_the_files_that_state_the_rule_are_not_judged_by_it(tmp_path):
    """CONTEXT.md and SPECS.md spell out `iteration cap` because they declare the law. Judging them
    by it makes the law its own first violation, which is how a checker teaches people to add
    exemptions instead of caps."""
    assert _validate(tmp_path, {'CONTEXT.md': STATES_THE_RULE,
                                'SPECS.md': STATES_THE_RULE}) == []


def test_a_cut_flow_is_checked_against_its_whole_family(tmp_path):
    """The unit is the FLOW, not the file: a flow that outgrew the line cap and split still has one
    cap, and it may be stated in any part."""
    assert _validate(tmp_path, {'part.md': UNBOUNDED,
                                'part-two.md': 'Iteration cap: at most 4 passes.\n'}) == []


def test_the_real_flow_corpus_is_clean():
    """The rule is in force, so core/flows must satisfy it. This is the row that turns the check
    from a capability into a fact about the workspace."""
    assert validate.validate_flow_loops(WORKSPACE_ROOT) == []
