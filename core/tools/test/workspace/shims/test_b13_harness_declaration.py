# B13 regression — the harness mirror list is declared once, in a data file something reads.
#
# sync-skills carried MIRRORS=(...) in its own source; adding a harness meant editing a bash
# array by hand — done twice in one week. The list now lives in core/harnesses.txt, sync-skills
# reads it, and .gitignore restates only what the declaration says. A declaration nothing can
# check fails silently in the direction that leaves stale mirrors on disk; this spec is the check.
import re
import subprocess

from conftest import WORKSPACE_ROOT

HARNESS_FILE = WORKSPACE_ROOT / 'core/harnesses.txt'


def _rows():
    rows = []
    for line in HARNESS_FILE.read_text(encoding='utf-8').splitlines():
        line = line.rstrip('\n')
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        name, sdir, cdir = line.split('\t')
        rows.append((name, sdir, cdir))
    return rows


def _gitignore():
    return (WORKSPACE_ROOT / '.gitignore').read_text(encoding='utf-8')


def test_the_declaration_itself_is_tracked():
    listed = subprocess.run(['git', 'ls-files', '--cached', '--', 'core/harnesses.txt'],
                            cwd=WORKSPACE_ROOT, capture_output=True, text=True, encoding='utf-8').stdout.strip()
    assert listed, ('core/harnesses.txt is not in the index — the declaration must be versioned, '
                    'or a clone loses the mirror list silently.')


def test_no_literal_mirror_path_survives_in_the_source():
    src = (WORKSPACE_ROOT / 'core/tools/wos/sync-skills').read_text(encoding='utf-8')
    assert 'core/harnesses.txt' in src, 'sync-skills must read the declaration'
    assert '"$WORKSPACE/.' not in src, 'a mirror path is spelled in the source again'


def test_every_declared_mirror_has_its_gitignore_line():
    gitignore = _gitignore()
    for name, sdir, _ in _rows():
        assert f'{sdir}/*/' in gitignore, f'{name}: mirror {sdir} has no .gitignore line'


def test_no_gitignore_mirror_names_an_undeclared_harness():
    declared = {sdir for _, sdir, _ in _rows()}
    ghosts = []
    for line in _gitignore().splitlines():
        m = re.match(r'^(\.[\w-]+/skills)/\*/$', line.strip())
        if m and m.group(1) not in declared:
            ghosts.append(line)
    assert not ghosts, f'mirror lines no declaration backs: {ghosts}'
