# T0 list and vocabulary checks (Level 0, law in core/SCHEMA.md). Zero-token, runs in verify-fast.
#
# Two of these tests assert against the LIVE workspace and are meant to be green at all
# times, not baselined: a surviving retired token means a rename is unfinished, and a
# cross-list duplicate item id means v1 criterion 2 is false. Both were red when written,
# and the fix was to finish the work, not to widen the test.
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine
# sys.path for the enforcement layer is set once, by conftest.py — a second copy
# here would go stale the next time core/hooks is split.
import entropy_corpus  # noqa: E402

import entropy_list  # noqa: E402
import schema_law  # noqa: E402

# The three wos lists (ROADMAP.md header: "an item lives in exactly one of the three").
# All goal files share one namespace because their achievement item ids are per-goal
# vocabulary — six startapps each having a [build-mvp] is not six copies of one item.
LISTS = {
    'wos-roadmap': [WORKSPACE_ROOT / 'ROADMAP.md'],
    'core-roadmap': [WORKSPACE_ROOT / 'core/ROADMAP.md'],
    'goals': sorted((WORKSPACE_ROOT / 'brain/goals').glob('*.md')),
}


def test_retired_tokens_come_from_schema():
    """Declared, not hardcoded — the same design as the type allowlist."""
    retired = schema_law.load_retired()
    assert retired['loop-engineering'] == 'craft'
    assert retired['KNOWN-BUGS'] == 'ISSUES.md'
    assert 'SPEC.md' not in retired, 'that rename has not landed yet'


def test_a_longer_word_is_not_a_substring_hit(tmp_path):
    """Retired `gone-token` must not fire on `gone-tokenizer` — a different word."""
    target = tmp_path / 'note.md'
    target.write_text('the gone-tokenizer module is unrelated\n', encoding='utf-8', newline='\n')
    assert entropy_list.retired_hits([target], {'gone-token': 'kept'},
                                       set()) == []


def test_item_ids_read_item_position_only(tmp_path):
    target = tmp_path / 'ROADMAP.md'
    target.write_text(
        '- [ ] [real-item] do the thing\n'
        '> [x] [done-item] finished\n'
        '- **`[parked-item]`** — out of scope\n'
        'prose mentioning [a-reference] mid-sentence\n'
        '- see [a-link](http://x) for details\n', encoding='utf-8', newline='\n')
    assert entropy_list.item_ids(target) == {'real-item', 'done-item', 'parked-item'}


def test_sibling_namespaces_may_repeat_a_item_id(tmp_path):
    for name in ('goal-a.md', 'goal-b.md'):
        (tmp_path / name).write_text('> [ ] [build-mvp] ship it\n', encoding='utf-8', newline='\n')
    namespaces = {'goals': [tmp_path / 'goal-a.md', tmp_path / 'goal-b.md']}
    assert entropy_list.duplicate_ids(namespaces) == {}


def test_same_item_id_in_two_lists_is_a_duplicate(tmp_path):
    (tmp_path / 'ROADMAP.md').write_text('- [ ] [thing] do it\n', encoding='utf-8', newline='\n')
    (tmp_path / 'OTHER.md').write_text('- [ ] [thing] do it\n', encoding='utf-8', newline='\n')
    dups = entropy_list.duplicate_ids(
        {'roadmap': [tmp_path / 'ROADMAP.md'], 'other': [tmp_path / 'OTHER.md']})
    assert set(dups) == {'thing'}
    assert set(dups['thing']) == {'roadmap', 'other'}


def test_no_item_lives_in_two_lists():
    """v1 criterion 2, verified by scan rather than eyeball."""
    dups = entropy_list.duplicate_ids(LISTS)
    assert dups == {}, '; '.join(
        f'[{item_id}] in {sorted(claims)}' for item_id, claims in dups.items())


def test_goal_vocabulary_holds_files_and_their_items(tmp_path):
    (tmp_path / 'craft-flows.md').write_text(
        '# g\n> [ ] [prompt-dsl] dsl as a contract\n', encoding='utf-8', newline='\n')
    vocabulary = entropy_list.goal_vocabulary(tmp_path)
    assert vocabulary == {'craft-flows', 'prompt-dsl'}


def test_a_wiki_link_to_an_item_resolves(tmp_path):
    target = tmp_path / 'note.md'
    target.write_text('see [[prompt-dsl]] in [[craft-flows]]\n', encoding='utf-8', newline='\n')
    vocabulary = {'craft-flows', 'prompt-dsl'}
    assert entropy_list.wiki_link_hits([target], vocabulary, set()) == []


def test_a_wiki_link_naming_nothing_is_flagged(tmp_path):
    """[[dobra]] was exactly this: a project name, not a goal. Its goal is local-ai."""
    target = tmp_path / 'note.md'
    target.write_text('crosses with [[dobra]]\n', encoding='utf-8', newline='\n')
    hits = entropy_list.wiki_link_hits([target], {'local-ai'}, set())
    assert len(hits) == 1 and 'dobra' in hits[0]


def test_every_wiki_link_in_the_workspace_resolves():
    """The last piece of pointer integrity."""
    hits = entropy_list.wiki_link_hits(
        entropy_list.tracked_files(WORKSPACE_ROOT),
        entropy_list.goal_vocabulary(WORKSPACE_ROOT / 'brain/goals'),
        entropy_corpus.enforcement_paths(WORKSPACE_ROOT))
    assert hits == [], '\n'.join(hits)


# --- finished work: the one thing no link-checker can see -------------------------
# Completion is deletion (core/SCHEMA.md § No archive types): a list's length should
# measure remaining work. Corpus-wide cap: test/workspace/. These cover the boundaries,
# where the design is — a tick is finished work only in a list, a date alone is not a report.


def _doc(tmp_path, name, body):
    doc = tmp_path / name
    doc.write_text(body, encoding='utf-8', newline='\n')
    return doc


def test_strikethrough_is_finished_work(tmp_path):
    doc = _doc(tmp_path, 'NOTES.md', 'the plan ~~ship it Friday~~ is replaced\n')
    hits = entropy_list.finished_work_hits([doc], set())
    assert len(hits) == 1 and 'strikethrough' in hits[0]


def test_a_dated_completion_report_is_finished_work(tmp_path):
    doc = _doc(tmp_path, 'NOTES.md', 'The file law shipped 2026-07-31 after five tries.\n')
    assert 'dated completion report' in entropy_list.finished_work_hits([doc], set())[0]


def test_a_date_without_a_completion_verb_is_not_finished_work(tmp_path):
    """This workspace cites decisions by date. Only a *report* is history."""
    doc = _doc(tmp_path, 'NOTES.md', 'Decided 2026-07-30 by Lucas: types are closed.\n')
    assert entropy_list.finished_work_hits([doc], set()) == []


def test_a_tick_is_finished_work_only_in_a_list(tmp_path):
    roadmap = _doc(tmp_path, 'ROADMAP.md', 'intro\n\nbody\n- [x] done\n')
    hit = entropy_list.finished_work_hits([roadmap], set())[0]
    assert 'ticked item' in hit
    assert hit.startswith(f'{roadmap}:4:'), 'file:line, so the finding can be opened'
    # The same glyph in a spec is a legend marker — core/SCHEMA.md flags required
    # frontmatter fields this way and must not report itself.
    spec = _doc(tmp_path, 'SPECS.md', '- [x] done\n')
    assert entropy_list.finished_work_hits([spec], set()) == []


def test_a_generated_mirror_is_not_reported(tmp_path):
    """sync-skills rewrites mirrors, so the fix belongs at the generator."""
    mirror = tmp_path / '.claude' / 'skills'
    mirror.mkdir(parents=True)
    assert entropy_list.finished_work_hits([_doc(mirror, 'SKILL.md', '~~x~~\n')], set()) == []


def test_the_law_may_state_the_rules_it_enforces():
    """core/SCHEMA.md defines these rules and has to be able to quote them."""
    exempt = entropy_list.enforcement_paths(WORKSPACE_ROOT)
    assert entropy_list.finished_work_hits(
        [WORKSPACE_ROOT / 'core/SCHEMA.md'], exempt) == []
