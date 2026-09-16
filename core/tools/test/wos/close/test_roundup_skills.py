# T0 the session-close skills (core/SPECS.md § AD-09): what bash cannot assert about the other layer.
# Zero-token, no network.
#
# The split only holds if the skill keeps *not* doing the script's work. Prose has no compiler, so
# a later session re-inlining `make entropy` or the merges — the exact shape this frente deleted —
# would pass every other check in the suite. These guard the boundary and the hand-off's agreed shape.
import re

from conftest import WORKSPACE_ROOT

ROUNDUP_SKILL = (WORKSPACE_ROOT / 'core/skills/roundup.md').read_text(encoding='utf-8')
HANDOFF_SKILL = (WORKSPACE_ROOT / 'core/skills/handoff.md').read_text(encoding='utf-8')
TOOL = (WORKSPACE_ROOT / 'core/tools/wos/roundup').read_text(encoding='utf-8')


def _blocks(text):
    return re.findall(r'```(?:bash|sh)?\n(.*?)```', text, re.S)


def _phase_naming(text, needle):
    """The number of the `## Phase N` heading whose body first mentions `needle`."""
    phase = None
    for line in text.splitlines():
        heading = re.match(r'##\s*Phase\s*(\d+)', line)
        if heading:
            phase = heading.group(1)
        elif phase and needle in line:
            return phase
    return None


def test_the_skill_does_not_reinline_the_script():
    """The whole point: these ran as prose at the session's most expensive turns."""
    for block in _blocks(ROUNDUP_SKILL):
        for inlined in ('make entropy', 'git merge', 'git push', 'verify-fast'):
            assert inlined not in block, (
                f'{inlined!r} is back in core/skills/roundup.md — it belongs to '
                'core/tools/wos/roundup, which the skill calls once')


def test_the_skill_calls_the_tool_by_path():
    assert 'core/tools/wos/roundup' in ROUNDUP_SKILL


def test_a_skipped_handoff_deletes_the_artifact():
    """Decided 2026-08-13: the file's existence means a thread is open. A stale block left in
    place would let the next window resume a thread that closed sessions ago."""
    assert re.search(r'rm -f\s+outputs/handoff\.md', HANDOFF_SKILL), (
        'core/skills/handoff.md must name the deletion — skipping is what makes the path a signal')


def test_the_handoff_may_decline_to_write_one():
    assert 'do not emit a resume prompt' in HANDOFF_SKILL
    assert 'manufactures' in HANDOFF_SKILL, 'keep the reason: a resume prompt invents a next action'


def test_the_roundup_skill_does_not_promise_a_handoff_that_may_not_exist():
    """Phase 5 closes by telling the next session to read the artifact. That instruction is wrong
    whenever /handoff declined to write it."""
    tail = ROUNDUP_SKILL.split('## Phase 5')[-1]
    assert 'skipped' in tail, 'Phase 5 still assumes a hand-off was always written'


def _template():
    for block in _blocks(HANDOFF_SKILL):
        if '## Resume' in block:
            return block
    raise AssertionError('core/skills/handoff.md no longer carries a resume template')


def test_the_template_has_no_placeholder_to_fill():
    """`Open threads` is omitted, not answered with a "none." placeholder — the output rule
    applied to a section. A placeholder is a shape the model fills rather than a fact it
    reports. Scoped to the template: the prose above it may quote what it forbids."""
    template = _template()
    assert '"none."' not in template
    assert 'Omit the whole section' in template


def _state_labels() -> list:
    """The close's state labels, in order, read out of the one place that declares them.

    Read from the script rather than restated here for the same reason the skills may not name
    them: a second copy of this list rots without failing anything.
    """
    return _declared('STATE')


def _declared(name: str) -> list:
    declared = re.search(rf'^{name} = \(([^)]*)\)', TOOL, re.MULTILINE)
    return re.findall(r"'([a-z]+)'", declared.group(1)) if declared else []


def test_the_state_block_is_whatever_the_tool_printed():
    """Re-deriving the facts costs a second round of git at the most expensive turn, and lets the
    two disagree. Naming the lines is the same defect one level up: both skills promised three
    (`verify:`/`entropy:`/`sync:`) while the script printed six, and nothing failed. So the skills
    name none, and this asserts they name none — the label list lives only in the script."""
    printed = set(_state_labels())
    assert printed, 'core/tools/wos/roundup no longer declares its state labels'
    state = _template().split('### State')[-1]
    assert 'verbatim' in state
    for skill, text in (('roundup.md', ROUNDUP_SKILL), ('handoff.md', HANDOFF_SKILL)):
        named = {lbl for lbl in printed if f'`{lbl}:`' in text or f'{lbl}: /' in text}
        assert not named, (
            f'core/skills/{skill} names {sorted(named)} — the script owns that list; '
            'a copy in prose goes stale without failing anything')


def test_what_the_session_cost_prints_before_the_state():
    """Ruled 2026-08-25: the cost line printed fifth and was read last, though it is the fact that
    opened the whole cost frente. What the session spent and whether the workspace shrank lead;
    verify/sync/entropy follow, because those are for the next session rather than for Lucas.

    The rule is which GROUP leads, so that is what this asserts. It used to assert two fixed indices
    instead, which made adding a third Lucas-facing line (`trace`, 2026-09-15) fail a case about
    ordering — the count of lines Lucas reads first was never the ruling.
    """
    printed, lucas = _state_labels(), _declared('BARE')
    assert lucas and printed[:len(lucas)] == lucas, (
        f'the close no longer leads with what Lucas reads it for: {printed} against {lucas}')
    assert printed[len(lucas):len(lucas) + 2] == ['verify', 'sync'], printed


def test_the_inbox_phase_counts_instead_of_draining():
    """Ruled 2026-08-25: a drain opens links with the video and web tools — the most expensive
    work here — at the most expensive turn. The close hands /inbox to the next session, where the
    same work costs a fraction. A phase that starts triaging again is the regression."""
    phase = ROUNDUP_SKILL.split('## Phase 3')[-1].split('## Phase 4')[0]
    assert 'Next action' in phase, 'Phase 3 no longer hands the drain to the next session'
    for reinlined in ('triage them now', 'get confirmation'):
        assert reinlined not in phase, f'{reinlined!r} is back: Phase 3 counts, it does not drain'


def test_the_template_caps_what_it_repeats():
    """Last session's hand-off ran 48 lines, and 3 of its 5 open threads were already written in
    ROADMAP.md. The caps are the fix; losing them is how it grows back."""
    assert '≤3 bullets' in HANDOFF_SKILL
    assert re.search(r'≤2 files', HANDOFF_SKILL)
    assert 'no list already holds' in HANDOFF_SKILL


def test_both_skills_agree_on_which_phase_promotes():
    """/handoff points at the phase that promotes instead of merging itself. The pointer went
    stale once already when the skill collapsed six phases into three."""
    promoting = _phase_naming(ROUNDUP_SKILL, 'core/tools/wos/roundup')
    assert promoting, 'no phase of core/skills/roundup.md calls the tool'
    cited = re.search(r'/roundup`?\s*Phase\s*(\d+)', HANDOFF_SKILL)
    assert cited, 'core/skills/handoff.md no longer points anywhere for promotion'
    assert cited.group(1) == promoting, (
        f'handoff.md sends promotion to Phase {cited.group(1)}; the tool runs in Phase {promoting}')


def test_the_dirty_flag_is_documented_where_it_is_decided():
    """--leave-dirty answers a question only the agent can answer, so the script's own stop names
    it at the moment it applies. The skill must not pre-load it as a routine step."""
    for block in _blocks(ROUNDUP_SKILL):
        assert '--leave-dirty' not in block, (
            'the skill must not run --leave-dirty by default — the stop offers it when it applies')
