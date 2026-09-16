# b20260905 regression — a registration is a registration whatever file type it lives in.
#
# .github/hooks/workspace-policy.json registered three Copilot hooks as `python3 core/hooks/...`
# with a `"windows": "python core/hooks/..."` arm beside each. On Windows both words reach a
# Microsoft Store execution alias that prints an advert and exits 9009, so the hook never ran and
# the caller read the advert as its output: the Copilot enforcement layer was off on that clone
# while the config read as correct.
#
# THE BUG IS THE CHECK, NOT THE CONFIG. core/hooks/SPECS.md § Agent lifecycle gates names
# test_no_shell_hook_spawns_the_bare_word_python3 as the enforcer of this ban across ALL shims, and
# that test grepped `*.sh`. Its corpus was narrower than its own rule, so the spec was true, the
# check was green, and the registration was dead. Two arms are needed because command position is
# spelled differently in the two families -- a shell file runs a bare word, a config quotes one --
# and this file drives BOTH over a planted repo rather than trusting the tree to still contain an
# example. Same reason test_shim_paths.py now reads the registration files at all.
import importlib.util
import subprocess

from conftest import WORKSPACE_ROOT

RATCHET = WORKSPACE_ROOT / 'core/tools/test/workspace/ratchets/test_port_ratchet.py'
# The historical spellings, verbatim from the commit that shipped the defect.
BROKEN_JSON = ('{"hooks": {"PreToolUse": [{"command": "python3 core/hooks/copilot/x.py",'
               ' "windows": "python core/hooks/copilot/x.py"}]}}\n')
FIXED_JSON = '{"hooks": {"PreToolUse": [{"command": "sh core/run hooks/copilot/x.py"}]}}\n'
BROKEN_SH = '#!/bin/sh\npython3 "$ROOT/core/hooks/x.py"\n'
# The shape that must stay legal: asking the boundary, and naming the word in a comment.
BOUNDARY_JS = ('// the bare word python3 is banned here\n'
           'const r = spawnSync("sh", [`${W}/core/run`, "--python"])\n')


def _patterns() -> tuple:
    """The ratchet's own two regexes, loaded from its source. A second copy here would let the
    check and its regression test disagree about what the ban even matches."""
    spec = importlib.util.spec_from_file_location('port_ratchet_under_test', RATCHET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SHELL_SPAWN, module.QUOTED_SPAWN, module.REGISTRATION_GLOBS


def _planted(tmp_path, files: dict):
    """A throwaway git repo, because the ratchet's instrument is `git grep` and a check running a
    different instrument than the thing it guards proves nothing about the thing it guards."""
    for name, body in files.items():
        (tmp_path / name).write_text(body, encoding='utf-8', newline='\n')
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(['git', 'add', '-A'], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


def _grep(repo, pattern: str, globs: tuple) -> list:
    done = subprocess.run(['git', 'grep', '--cached', '-nE', pattern, '--', *globs],
                          cwd=repo, capture_output=True, text=True, encoding='utf-8')
    return done.stdout.splitlines()


def _live_files(lines: list) -> set:
    """The ratchet's own comment filter: a line that only NAMES the word is not a spawn."""
    return {line.split(':', 1)[0] for line in lines
            if not line.split(':', 2)[-1].lstrip().startswith(('#', '//'))}


def test_the_registration_that_broke_it_is_caught(tmp_path):
    """Both spellings, in the file type that carried them. `python` without the 3 is the arm that
    would have survived a fix aimed only at the word in the ratchet's own name."""
    _shell, quoted, globs = _patterns()
    repo = _planted(tmp_path, {'broken.json': BROKEN_JSON, 'fixed.json': FIXED_JSON})
    assert _live_files(_grep(repo, quoted, globs)) == {'broken.json'}


def test_the_shell_arm_still_catches_what_it_always_did(tmp_path):
    """The original corpus is not traded away for the new one — this is a widening."""
    shell, _quoted, _globs = _patterns()
    repo = _planted(tmp_path, {'hook.sh': BROKEN_SH})
    assert _live_files(_grep(repo, shell, ('*.sh',))) == {'hook.sh'}


def test_asking_the_boundary_is_not_a_finding(tmp_path):
    """`--python` and a commented mention must both pass, or the ratchet fails on the fix itself
    and on every file that explains why the ban exists. The `-` before `python` saves the first;
    the comment filter saves the second."""
    _shell, quoted, globs = _patterns()
    repo = _planted(tmp_path, {'boundary.js': BOUNDARY_JS})
    live = _live_files(_grep(repo, quoted, globs))
    assert not live, f'the boundary spelling reads as a spawn: {live}'


def test_every_shim_reaches_the_trackers_through_the_table():
    """The other half of the same bug. Three shims hand-copied the two `post read` rows of
    core/hooks/gates.txt, and two of them reached those rows by TOOL NAME -- the b20260901 shape.
    A shim naming a tracker directly is a second copy of a table that exists to be the only one."""
    for relative in ('core/hooks/copilot/copilot-post-tool.py',
                     'core/hooks/antigravity/antigravity_policy.py',
                     '.opencode/plugins/workspace-policy.js'):
        body = (WORKSPACE_ROOT / relative).read_text(encoding='utf-8')
        text = '\n'.join(line for line in body.splitlines()
                         if not line.lstrip().startswith(('#', '//')))
        assert 'PostToolUse' in text and 'dispatch.py' in text, (
            f'{relative} no longer routes PostToolUse through dispatch.py, so the gates in '
            'core/hooks/gates.txt do not reach this harness on the way back out')
        for tracker in ('facade-tracker.py', 'context-tracker.py'):
            assert tracker not in text, (
                f'{relative} names {tracker} itself -- that is a hand-copy of gates.txt, which '
                'drifts the moment either side changes')
