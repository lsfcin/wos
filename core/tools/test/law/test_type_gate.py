# T0 type gate (Level 0, law in core/SCHEMA.md): the uppercase allowlist. Zero-token, runs in verify-fast.
#
# The no-hand-inventory rule moved to entropy/test_entropy_inventory.py 2026-08-15 — it
# tests `entropy_context.py`, not this gate, which only decides WHEN a check runs.
#
# The point of these tests is that the checker reads core/SCHEMA.md as its single
# source. If someone edits the law, the gate follows without a code change; if
# someone hardcodes the names back into the checker, test_law_comes_from_schema
# stops proving anything and should be read as a warning, not deleted.
from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine
# sys.path for the enforcement layer is set once, by conftest.py — a second copy
# here would go stale the next time core/hooks is split.

import importlib.util

spec = importlib.util.spec_from_file_location(
    'type_gate', WORKSPACE_ROOT / 'core/hooks/checks/type-gate.py')
type_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(type_gate)

SCHEMA = WORKSPACE_ROOT / 'core/SCHEMA.md'


def test_law_comes_from_schema():
    """The allowlist is parsed, not restated — the whole design of this gate."""
    allowed, exempt = type_gate.load_law(SCHEMA)
    # Types the workspace cannot function without; a parse regression drops them all.
    assert {'AGENTS.md', 'CONTEXT.md', 'ROADMAP.md', 'SPECS.md', 'README.md'} <= allowed
    assert 'SETUP.md' in allowed, 'SETUP.md was allowlisted 2026-07-30'
    # SPEC.md was deliberately collapsed into SPECS.md and must NOT be a type.
    assert 'SPEC.md' not in allowed
    # The transient-initiative exemption is parsed from its own section.
    assert 'ROADMAP-spec-drive.md' in exempt
    # Membership only shrinks; each is routed to a ROADMAP-<name>.md or a SPECS.md. VERIFY.md left
    # on 2026-08-17 when its rename landed — the exemption covers the old name, never the new one.
    # REFACTOR.md left on 2026-08-19 by DELETION rather than rename: it recorded a refactor whose
    # phases were complete and whose branch no longer existed. A row outliving its file is not
    # harmless here, because every backticked name in that section is parsed as an exemption.
    assert exempt == {'ROADMAP-spec-drive.md', 'DECISIONS.md'}, (
        'the exemption is a closed list that only shrinks — a new name here means someone '
        'invented a type instead of using ROADMAP-<name>.md'
    )


def test_scopes_come_from_schema():
    """The third parse of the law, and the only one whose loss is silent.

    A heading rename is already caught: it empties `load_retired` (KeyError in
    test_retired_tokens_come_from_schema) or `exempt` (the closed-list assert above).
    `load_scopes` has no such tripwire — it reads the type table's second column, so
    reformatting that table empties it, `check_placement` stops flagging anything, and
    the naming suite still passes because it only asserts findings stay within a baseline.
    Fewer findings is exactly what a broken parse looks like.
    """
    scopes = type_gate.load_scopes(SCHEMA)
    assert scopes == {'AGENTS.md': 'root', 'README.md': 'repo-root',
                      'PROJECTS.md': 'root'}, (
        'the scope column of the type table stopped parsing — check_placement is now '
        'silently checking nothing'
    )


def test_allowlisted_name_passes(tmp_path):
    allowed, exempt = type_gate.load_law(SCHEMA)
    target = tmp_path / 'ROADMAP.md'
    target.write_text('# r\n', encoding='utf-8', newline='\n')
    assert type_gate.check_name(target, allowed, exempt) is None


def test_invented_type_is_blocked(tmp_path):
    allowed, exempt = type_gate.load_law(SCHEMA)
    target = tmp_path / 'LEXICON.md'
    target.write_text('# l\n', encoding='utf-8', newline='\n')
    failure = type_gate.check_name(target, allowed, exempt)
    assert failure is not None
    assert 'LEXICON.md' in failure
    assert 'four disposal routes' in failure


def test_lowercase_instance_is_never_checked(tmp_path):
    allowed, exempt = type_gate.load_law(SCHEMA)
    for name in ('tree.md', 'labels.md', 'draft.md', 'some-notes.md'):
        target = tmp_path / name
        target.write_text('# x\n', encoding='utf-8', newline='\n')
        assert type_gate.check_name(target, allowed, exempt) is None


def test_harness_mandated_name_is_exempt(tmp_path):
    allowed, exempt = type_gate.load_law(SCHEMA)
    for name in ('CLAUDE.md', 'GEMINI.md'):
        target = tmp_path / name
        target.write_text('# harness\n', encoding='utf-8', newline='\n')
        assert type_gate.check_name(target, allowed, exempt) is None


def test_prose_describing_finished_work_blocks_a_file_the_commit_adds(tmp_path):
    """Detected by the dashboard since the rule was written, enforced only from 2026-08-18.

    Completion is deletion, and a detector nobody blocks on is what let the corpse queue grow to
    nineteen. Ratcheted like every other check this gate runs: it fires on what a commit ADDS, so
    the inherited queue stays the dashboard's and the gate does not fail on the day it lands.
    """
    allowed, exempt = type_gate.load_law(SCHEMA)
    target = tmp_path / 'SPECS.md'
    target.write_text('# s\n> one line about it.\n\nThe old gate was ~~cut~~ and replaced.\n',
                      encoding='utf-8', newline='\n')
    failures = type_gate.failures_for(target, allowed, exempt, {}, set())
    assert any('finished work' in failure for failure in failures), failures


def test_present_tense_state_is_not_a_corpse(tmp_path):
    """The rule is about prose describing work that landed, not about mentioning the past.

    Without this the gate would be a ban on dates, and the guidance it prints — rewrite the line
    as present-tense state — would have nothing to rewrite into.
    """
    allowed, exempt = type_gate.load_law(SCHEMA)
    target = tmp_path / 'SPECS.md'
    target.write_text('# s\n> one line about it.\n\nThe gate blocks a staged clone.\n',
                      encoding='utf-8', newline='\n')
    failures = type_gate.failures_for(target, allowed, exempt, {}, set())
    assert not any('finished work' in failure for failure in failures), failures
