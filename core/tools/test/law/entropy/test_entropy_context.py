# T0 CONTEXT.md rules (Level 0, law in core/SCHEMA.md). Zero-token, runs in verify-fast.
#
# The goal-link check was written AFTER the backfill, not before: all 14 projects already
# declared line 3, so the check could go straight to blocking instead of warning. That
# order is the point — a check introduced against a red tree teaches people to ignore it.
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine
# sys.path for the enforcement layer is set once, by conftest.py — a second copy
# here would go stale the next time core/hooks is split.

import entropy_context  # noqa: E402
import entropy_corpus  # noqa: E402


def test_every_project_declares_its_goal():
    failures = [f for path in sorted((WORKSPACE_ROOT / 'code').glob('*/CONTEXT.md'))
                if (f := entropy_context.check_goal_link(path))]
    assert failures == [], '\n'.join(failures)


def test_no_routing_block_publishes_half_a_sentence():
    """Asserted at ZERO, not against a baseline: the three that existed were fixed first.

    A check introduced against a red tree teaches people to ignore it — the same order the goal-link
    check above was written in.

    THIS REPO ONLY, like every other zero-assert here. The dashboard scans the nested repos and
    reports their truncations; asserting on them would fail this build for a fix that has to land in
    somebody else's repo.
    """
    failures = [f for path in entropy_corpus.tracked_files(WORKSPACE_ROOT)
                if (f := entropy_context.check_truncation(path))]
    assert failures == [], '\n'.join(failures)


def _routed(tmp_path, description):
    doc = tmp_path / 'CONTEXT.md'
    doc.write_text('# t\n> what it is\n\n<!-- routing:start -->\n## Routing\n\n'
                   '| File | Description |\n|------|-------------|\n'
                   f'| [`thing.py`](thing.py) | {description} |\n'
                   '<!-- routing:end -->\n', encoding='utf-8', newline='\n')
    return doc


def test_a_truncated_row_names_the_file_whose_source_to_shorten(tmp_path):
    """The fix is at the source, so the finding has to say which source."""
    failure = entropy_context.check_truncation(_routed(tmp_path, 'a long description that ran…'))
    assert 'thing.py' in failure and 'never edit the table' in failure


def test_an_ellipsis_outside_the_block_is_prose(tmp_path):
    """Authors write `…` in prose and several do; only the generated half is the generator's."""
    doc = _routed(tmp_path, 'a complete description')
    doc.write_text(doc.read_text(encoding='utf-8').replace('> what it is', '> what it is…'),
                   encoding='utf-8', newline='\n')
    assert entropy_context.check_truncation(doc) is None


def test_a_file_with_no_routing_block_is_not_asked(tmp_path):
    doc = tmp_path / 'SPECS.md'
    doc.write_text('# s\n> a rule that trails off…\n', encoding='utf-8', newline='\n')
    assert entropy_context.check_truncation(doc) is None


def _project(tmp_path, line3):
    project = tmp_path / 'code' / 'thing'
    (project / '../../brain/goals').resolve().mkdir(parents=True, exist_ok=True)
    project.mkdir(parents=True)
    target = project / 'CONTEXT.md'
    target.write_text(f'# thing\n> what it is\n{line3}\n', encoding='utf-8', newline='\n')
    return target


def test_a_declared_goal_passes(tmp_path):
    (tmp_path / 'brain/goals').mkdir(parents=True)
    (tmp_path / 'brain/goals/real.md').write_text('# g\n', encoding='utf-8', newline='\n')
    target = _project(tmp_path, '> goal: [real](../../brain/goals/real.md)')
    assert entropy_context.check_goal_link(target) is None


def test_a_deliberate_none_passes(tmp_path):
    assert entropy_context.check_goal_link(_project(tmp_path, '> goal: none')) is None


def test_a_missing_declaration_is_flagged(tmp_path):
    failure = entropy_context.check_goal_link(_project(tmp_path, 'some prose instead'))
    assert failure is not None and 'line 3 must declare' in failure


def test_a_goal_in_a_tree_this_checkout_lacks_is_not_a_dead_link(tmp_path):
    """b20260917 — code/aiwbot crosses into the public repo, brain/ is refused there.

    The pair with the case below is the whole rule: no goals/ directory means the tree stayed
    behind and there is nothing to answer; a goals/ directory with the file gone is a real
    finding, and silencing that one would hide the only case this check exists for."""
    project = tmp_path / 'code' / 'thing'
    project.mkdir(parents=True)
    target = project / 'CONTEXT.md'
    target.write_text('# thing\n> what it is\n> goal: [x](../../brain/goals/x.md)\n',
                      encoding='utf-8', newline='\n')
    assert entropy_context.check_goal_link(target) is None


def test_a_dead_goal_link_is_flagged(tmp_path):
    """Worse than `none`, because it reads as an answer."""
    target = _project(tmp_path, '> goal: [gone](../../brain/goals/gone.md)')
    failure = entropy_context.check_goal_link(target)
    assert failure is not None and 'does not exist' in failure


def test_scaffolding_is_not_a_project(tmp_path):
    templates = tmp_path / 'code' / '_templates'
    templates.mkdir(parents=True)
    target = templates / 'CONTEXT.md'
    target.write_text('# t\n> templates\nno goal line\n', encoding='utf-8', newline='\n')
    assert entropy_context.check_goal_link(target) is None


def test_a_non_project_context_is_not_asked(tmp_path):
    other = tmp_path / 'brain' / 'goals'
    other.mkdir(parents=True)
    target = other / 'CONTEXT.md'
    target.write_text('# goals\n> one file per goal\n', encoding='utf-8', newline='\n')
    assert entropy_context.check_goal_link(target) is None


# --- misplaced answers: a contract trapped in a CONTEXT.md head -------------------
# SCHEMA says each type answers exactly one question; this is the first check that a file
# answers only its OWN. The corpus-wide ratchet lives in test/workspace/. Size alone is a
# weak signal — a long head may be honest navigation — so the boundary is what matters.
from file_law import load_limits  # noqa: E402

HEAD_WARN = load_limits()['CONTEXT_HEAD_WARN']


def _head(tmp_path, tokens, constrained, name='CONTEXT.md'):
    rule = 'A module must never import around its facade. ' if constrained else ''
    doc = tmp_path / name
    doc.write_text(rule + 'x' * (tokens * 4) + '\n<!-- routing:start -->\n| f |\n',
                   encoding='utf-8', newline='\n')
    return doc


def test_an_over_size_head_carrying_a_constraint_is_flagged(tmp_path):
    hit = entropy_context.check_misplaced_answer(
        _head(tmp_path, HEAD_WARN + 50, True), HEAD_WARN)
    assert hit and 'create a' in hit, 'no sibling SPECS.md, so the advice is: create'


def test_a_long_head_that_only_navigates_is_clean(tmp_path):
    assert entropy_context.check_misplaced_answer(
        _head(tmp_path, HEAD_WARN + 50, False), HEAD_WARN) is None


def test_a_thin_head_may_carry_a_constraint(tmp_path):
    """A thin head is the goal; a rule inside one is cheap and stays put."""
    assert entropy_context.check_misplaced_answer(
        _head(tmp_path, 10, True), HEAD_WARN) is None


def test_an_existing_sibling_spec_changes_the_advice(tmp_path):
    doc = _head(tmp_path, HEAD_WARN + 50, True)
    (tmp_path / 'SPECS.md').write_text('# specs\n', encoding='utf-8', newline='\n')
    assert 'move them to the' in entropy_context.check_misplaced_answer(doc, HEAD_WARN)


def test_only_context_files_are_checked(tmp_path):
    assert entropy_context.check_misplaced_answer(
        _head(tmp_path, HEAD_WARN + 50, True, name='SPECS.md'), HEAD_WARN) is None


def test_the_generated_block_is_not_part_of_the_head(tmp_path):
    """The routing table's size is the crowding signal's business, not this check's."""
    doc = tmp_path / 'CONTEXT.md'
    doc.write_text('# t\n<!-- routing:start -->\n' + 'x' * (HEAD_WARN * 8), encoding='utf-8', newline='\n')
    assert entropy_context.context_head(doc).strip() == '# t'


def test_a_generated_mirror_is_not_flagged(tmp_path):
    """sync-skills rewrites mirrors, so the fix belongs at the generator."""
    mirror = tmp_path / '.opencode'
    mirror.mkdir()
    assert entropy_context.check_misplaced_answer(
        _head(mirror, HEAD_WARN + 50, True), HEAD_WARN) is None
