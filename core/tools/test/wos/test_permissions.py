# T0/T1 the permission registry and its renderer: every level is fully declared, and the rendered
# config is a function of the declaration rather than of whatever the last session clicked.
#
# The sharpest assertion here is test_a_rendered_config_is_not_versioned. The whole design rests on
# the split -- policy in git, answer per machine -- and the failure mode it guards is silent: a
# `bypassPermissions` block committed once arrives switched on for everyone who clones next, and
# nothing about the repo looks wrong afterwards.
import importlib.machinery as machinery
import importlib.util as importutil
import json
import subprocess

from conftest import WORKSPACE_ROOT

TOOL = WORKSPACE_ROOT / 'core/tools/wos/permissions'
REGISTRY = WORKSPACE_ROOT / 'core/permissions.txt'
LEVELS = {'guarded', 'standard', 'open'}


def _tool():
    """Load the extensionless CLI as a module — the house pattern for testing one."""
    spec = importutil.spec_from_loader('permtool', machinery.SourceFileLoader('permtool', str(TOOL)))
    module = importutil.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_level_declares_what_it_means_and_what_it_costs():
    """A level with no sentences cannot be offered to anyone, which is the step's whole job."""
    levels = _tool().levels()
    assert set(levels) == LEVELS
    for name, spec in levels.items():
        assert spec['summary'].strip(), f'{name} has no summary to read out'
        assert spec['tradeoff'].strip(), f'{name} names no cost — a level with no cost is a lie'
        assert spec['mode'].strip(), f'{name} declares no default mode'


def test_the_levels_really_are_ordered_by_how_much_they_permit():
    """guarded ⊂ standard ⊂ open. Three names nobody can rank are three arbitrary presets."""
    render = _tool().render_claude
    counts = [len(render(t)['allow']) for t in ('guarded', 'standard', 'open')]
    assert counts[0] < counts[1] < counts[2], f'allow-counts are not ordered: {counts}'
    assert render('guarded')['deny'], 'the safest level denies nothing'


def test_only_the_open_level_stops_asking_about_secrets():
    """Reading a credential is the one thing the two cautious levels must never do silently."""
    render = _tool().render_claude
    for level in ('guarded', 'standard'):
        assert any('.credentials' in p for p in render(level)['deny']), \
            f'{level} does not deny credential reads'


def test_a_harness_pattern_never_appears_in_the_registry():
    """The registry is read by whoever is choosing a level; the syntax belongs to the adapter.

    This is the property that makes a second harness a second table instead of a second policy.
    """
    body = '\n'.join(line for line in REGISTRY.read_text(encoding='utf-8').splitlines()
                     if not line.startswith('#'))
    for token in ('Bash(', 'Read(', 'Edit(', 'Write(', 'Glob(', 'Grep('):
        assert token not in body, f'{token} is harness syntax and belongs in the adapter, not here'


def test_a_rendered_config_is_not_versioned():
    """git must not be able to see the rendered answer — see this file's head for why."""
    done = subprocess.run(['git', 'ls-files', '--error-unmatch', '.claude/settings.local.json'],
                          cwd=WORKSPACE_ROOT, capture_output=True, text=True, encoding='utf-8')
    assert done.returncode != 0, \
        'the rendered permission config is tracked; a committed bypassPermissions arrives ' \
        'switched on for whoever clones next'


def test_check_notices_a_config_that_no_longer_matches(tmp_path):
    """--check is the step's Verify check, so it has to actually catch a drifted file.

    Both halves are written against whatever level THIS machine answered, never a hard-coded one:
    a check that only passes on the author's profile is the drift it was built to catch.
    """
    module = _tool()
    declared = module.law.setting('permissions', module.DEFAULT_LEVEL)
    other = next(iter(LEVELS - {declared}))
    target = tmp_path / 'settings.local.json'
    module._target = lambda: target

    target.write_text(json.dumps({'permissions': module.render_claude(declared)}), encoding='utf-8', newline='\n')
    assert module._check() == 0

    target.write_text(json.dumps({'permissions': module.render_claude(other)}), encoding='utf-8', newline='\n')
    assert module._check() == 1, '--check passed a config that does not match the answer'
