# T0 the feature registry's declaration half (core/SPECS.md § AD-14): every feature is declared,
# answered, and inside the closed sets its columns may draw from.
#
# The other half — whether a row that CLAIMS a switch really has one — is behaviour, not data, and
# lives in test_features_wiring.py. Splitting them was forced by the size gate and was right: this
# file reads three declaration files against each other and never runs a feature.
import re
import subprocess
import sys

import feature_law as law
from conftest import WORKSPACE_ROOT

SETUP = WORKSPACE_ROOT / 'SETUP.md'
DEPS = WORKSPACE_ROOT / 'core' / 'tools' / 'deps.txt'


def _setup_names():
    return set(re.findall(r'^> feature: `([a-z0-9-]+)`', SETUP.read_text(encoding='utf-8'), re.M))


def _deps_names():
    lines = [ln for ln in DEPS.read_text(encoding='utf-8').splitlines()
             if ln.strip() and not ln.startswith('#')]
    header = lines[0].split('\t')
    return {dict(zip(header, ln.split('\t')))['feature'] for ln in lines[1:]}


def test_every_setup_step_maps_to_a_declared_feature():
    """SETUP.md's names are install-shaped, so they join on the `install` column.

    This is half of what keeps three files one vocabulary instead of three. Adding an install step
    with a new name fails here until the registry says which feature that step installs.
    """
    installs = {r['install'] for r in law.load_registry()} - {'-', ''}
    missing = sorted(_setup_names() - installs)
    assert not missing, (
        'SETUP.md declares install steps no registry row claims:\n  ' + '\n  '.join(missing))


def test_every_dependency_feature_is_a_declared_feature():
    """deps.txt's names are breakage-shaped: each names a feature, so they join on `name`."""
    missing = sorted(_deps_names() - law.names())
    assert not missing, (
        'core/tools/deps.txt names features absent from core/features.txt:\n  ' +
        '\n  '.join(missing))


def test_a_skill_name_names_the_skill_file():
    """A name and the file it governs carry the same name (Lucas, 2026-08-17).

    Only the skills group can be checked this way — a hook's name names a behavior spread over
    several files, not one path. The failure this catches is the one that produced it: the name
    was `craft-flow`, the file was `loops.md`, and the flow was `craft`, so nothing disagreed
    with anything *adjacent* and the drift stayed legible at every single site.
    """
    skills = WORKSPACE_ROOT / 'core' / 'skills'
    orphans = [r['name'] for r in law.load_registry() if law.groups(r) == ['skills']
               and not (skills / f"{r['name']}.md").exists()
               and not (skills / r['name']).is_dir()]
    assert not orphans, (
        'these skill names name no file in core/skills/:\n  ' + '\n  '.join(orphans))


def test_every_row_is_complete_and_in_its_closed_set():
    for row in law.load_registry():
        assert law.groups(row), f"{row['name']} names no layer"
        for group in law.groups(row):
            assert group in law.GROUPS, row
        assert row['runs'] in law.RUNS, row
        assert row['enforcement'] in law.ENFORCEMENT, row
        assert row['scope'] in law.SCOPES, row
        assert len(row['buys'].split()) >= 8, (
            f"{row['name']}'s `buys` must say what the feature buys you, not restate its name — "
            'nobody accepts an enforcement layer whose value they cannot see')


def test_every_need_is_a_declared_feature():
    """A misspelled need would fail open, and the feature would stay on with its dependency off."""
    declared = law.names()
    for row in law.load_registry():
        for need in law.needs(row):
            assert need in declared and need != row['name'], (row['name'], need)


def test_runs_is_not_recoverable_from_enforcement():
    """The column exists because the two axes cross, and a later tidy-up would collapse them back.

    Both crossing sets must stay populated: features that fire by themselves and push on nobody
    (a compactor, a recorder), and features you invoke by hand that still push (the entropy scan's
    checks). Collapse either one and `enforcement: none` goes back to meaning two things, which is
    the ambiguity that made a reader of this registry report its capability layer as dead weight.
    """
    rows = law.load_registry()
    quiet = [r['name'] for r in rows if r['runs'] == 'automatic' and r['enforcement'] == 'none']
    called = [r['name'] for r in rows if r['runs'] == 'on-demand' and r['enforcement'] != 'none']
    assert quiet, 'no automatic feature enforces nothing — did `runs` get derived from enforcement?'
    assert called, 'no on-demand feature pushes — did `runs` get derived from enforcement?'


def test_every_declared_feature_has_an_answer():
    """A name added to the registry and never answered would default silently to on."""
    declared, answered = law.names(), set(law.load_profile()['toggle'])
    assert declared == answered, (
        f'unanswered: {sorted(declared - answered)}\n'
        f'answered but undeclared: {sorted(answered - declared)}')


def test_the_cli_agrees_with_this_file():
    """One parser, not two. If `features` drifts from the registry, the answers stop being real."""
    out = subprocess.run([sys.executable, str(WORKSPACE_ROOT / 'core/tools/wos/features'),
                          '--check'], capture_output=True, text=True, cwd=WORKSPACE_ROOT, encoding='utf-8')
    assert out.returncode == 0, out.stdout + out.stderr


