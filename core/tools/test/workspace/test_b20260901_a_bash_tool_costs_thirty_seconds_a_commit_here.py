# b20260901-a-bash-tool-costs-thirty-seconds-a-commit-here regression.
#
# `sync-skills --check` cost 22.0 s on a Windows clone with the mirrors in sync, and
# core/hooks/commit/generators.py runs the tool TWICE, so every commit touching a skill paid ~30 s.
# The cause was fork, not work: ~300 forks at ~48 ms each under Git Bash -- a `basename` per skill
# per mirror, a `cmp` per copy, a `grep` per frontmatter field, and one whole Python interpreter per
# command file inside render_command. Nobody had measured it, and on Linux nobody would feel it.
#
# The fix was the port, and these hold the two things that could bring the cost back: a bash tool
# reappearing under core/tools/, and the check quietly becoming slow again.
import ast
import importlib.machinery
import importlib.util
import subprocess
import sys
from unittest import mock

from conftest import WORKSPACE_ROOT


def test_no_bash_tool_remains_under_core_tools():
    """The port's own thesis (test_port_ceiling.py): porting bash to Python removes the per-OS
    axis. These two were the half of B12 that was left undecided -- the launcher learned to
    dispatch on the shebang, and *why these two were still bash* never got an answer."""
    listed = subprocess.run(['git', 'ls-files', 'core/tools'], cwd=WORKSPACE_ROOT,
                            capture_output=True, text=True, encoding='utf-8')
    shell = [line for line in listed.stdout.splitlines() if line.endswith('.sh')]
    assert not shell, f'bash is back under core/tools/: {shell}'


def test_the_mirror_check_still_answers():
    """The check the SessionStart heal depends on runs, end to end, and exits clean.

    THIS USED TO ASSERT A CEILING IN SECONDS, and b20260905 is what that cost: it failed twice
    under `pytest -n auto` and passed both times on a rerun with nothing changed, because sixteen
    workers were competing for the same cores. The pre-commit gate runs this suite, so a wall-clock
    bound refuses commits at random — and a ceiling that cries wolf gets raised until it means
    nothing. A duration is not a property of the code; it is a property of the machine on the day.

    What actually regressed was FORKS — ~300 of them at ~48 ms under Git Bash. That is asserted
    next door, on the source and on the run, and both forms hold on a loaded box and on an idle
    one."""
    done = subprocess.run(['sh', str(WORKSPACE_ROOT / 'core/run'), 'tools/wos/sync-skills',
                           '--check'],
                          cwd=WORKSPACE_ROOT, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=180, encoding='utf-8', errors='replace')
    assert done.returncode == 0, done.stdout + done.stderr


def test_the_check_spawns_nothing_while_it_runs():
    """The fork count, asserted at RUN TIME rather than read off the imports.

    The source check below proves these three modules do not import `subprocess`. It cannot see a
    fork reached any other way — `os.system`, `os.posix_spawn`, a helper they import that does it
    for them — and the defect this file exists for was 300 forks, not one import. So run `check()`
    in-process with every spawn primitive booby-trapped: it is read-only over WORKSPACE_ROOT, which
    is why it needs no `serial` marker and no boundary."""
    import os

    # An explicit SourceFileLoader, because `sync-skills` has no extension and nothing can infer a
    # loader from the name — spec_from_file_location returns None on its own.
    sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools/wos/skills'))
    source = WORKSPACE_ROOT / 'core/tools/wos/sync-skills'
    spec = importlib.util.spec_from_loader(
        'sync_skills_under_test',
        importlib.machinery.SourceFileLoader('sync_skills_under_test', str(source)))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def refuse(*args, **kwargs):
        raise AssertionError(
            'sync-skills --check spawned a process. The port exists to stop spawning per item; '
            '22 s of a 30 s commit was fork overhead, not work.')

    with mock.patch.object(subprocess, 'run', refuse), \
            mock.patch.object(subprocess, 'Popen', refuse), \
            mock.patch.object(os, 'system', refuse), \
            mock.patch.object(os, 'posix_spawn', refuse, create=True):
        mirrors, commands = module.harnesses()
        assert module.check(mirrors, commands) == 0


def test_the_check_does_not_spawn_a_process_per_skill():
    """The shape of the old cost, asserted on the source rather than on the clock: these modules
    may not shell out at all. A timing bound alone would pass on a fast machine while the defect
    sat there waiting for a slow one.

    PARSED, NOT GREPPED. The first version of this looked for the word `subprocess` with comment
    lines stripped, and mirror.py's own docstring says "the cache the bash needed to avoid a
    subprocess buys nothing" -- prose about the fix reading as the defect. An import is a syntax
    node, so ask the syntax.
    """
    for relative in ('core/tools/wos/skills/mirror.py', 'core/tools/wos/skills/validate.py',
                     'core/tools/wos/sync-skills'):
        tree = ast.parse((WORKSPACE_ROOT / relative).read_text(encoding='utf-8'))
        imported = {alias.name.split('.')[0]
                    for node in ast.walk(tree) if isinstance(node, ast.Import)
                    for alias in node.names}
        imported |= {node.module.split('.')[0]
                     for node in ast.walk(tree)
                     if isinstance(node, ast.ImportFrom) and node.module}
        assert 'subprocess' not in imported, (
            f'{relative} imports subprocess; the port exists to stop spawning per item')
