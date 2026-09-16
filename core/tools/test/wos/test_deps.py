# T0 declared dependencies (core/tools/SPECS.md § Declared dependencies): a third-party import the
# tool surface uses must be declared, and every tool must run under the workspace venv.
#
# LIMIT, stated so nobody reads more assurance into this than it gives: the IMPORT half is
# automatic — an ast walk cannot be fooled. The BINARY half (pandoc, ffmpeg, flutter, gallery-dl,
# invoked through a shell string) is declaration-only, because deciding which binaries a program
# shells out to is not decidable by a scan. Those rows are kept honest by `core/tools/wos/deps`
# checking them, not by this file.
import ast
import subprocess
import sys

from conftest import TOOLS, WORKSPACE_ROOT
from platform_law import rel

DECLARED = TOOLS / 'deps.txt'


def _rows():
    lines = [ln for ln in DECLARED.read_text(encoding='utf-8').splitlines()
             if ln.strip() and not ln.startswith('#')]
    header = lines[0].split('\t')
    return [dict(zip(header, ln.split('\t'))) for ln in lines[1:]]


def _is_python(path):
    """A tool is python by extension or by shebang — most of them carry no extension at all."""
    if path.suffix == '.py':
        return True
    if path.suffix or not path.is_file():
        return False
    head = path.open('rb').read(80)
    return head[:2] == b'#!' and b'python' in head


def _python_files():
    return [p for p in sorted(TOOLS.rglob('*')) if _is_python(p)]


def _local_modules():
    """Anything importable from within core/ — conftest puts every such directory on the path."""
    names = set()
    for p in (WORKSPACE_ROOT / 'core').rglob('*'):
        if p.is_file() and _is_python(p):
            names.add(p.stem if p.suffix == '.py' else p.name)
    return names


def _imports(path):
    for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split('.')[0]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split('.')[0]


def test_every_third_party_import_is_declared():
    """The class fix. Adding a tool with a new dependency fails here until deps.txt names it."""
    declared = {r['import'] for r in _rows() if r['import'] != '-'}
    local = _local_modules()
    undeclared = {}
    for path in _python_files():
        for module in _imports(path):
            if module in sys.stdlib_module_names or module in local or module in declared:
                continue
            undeclared.setdefault(module, []).append(rel(path, WORKSPACE_ROOT))
    assert not undeclared, (
        'third-party imports missing from core/tools/deps.txt:\n' +
        '\n'.join(f'  {m}  <- {", ".join(f)}' for m, f in sorted(undeclared.items())))


def test_every_declared_row_is_complete():
    for row in _rows():
        assert row['kind'] in {'pip', 'apt', 'system', 'npm', 'npx', 'binary', 'service'}, row
        assert row['check'].strip(), f"{row['name']} declares no check"
        assert row['feature'].strip(), f"{row['name']} declares no feature"
        assert len(row['breaks'].split()) >= 5, (
            f"{row['name']}'s `breaks` must say what the failure looks like, not name the dep")


def test_every_tool_runs_under_the_workspace_venv():
    """A tool on /usr/bin/env python3 gets whatever python the caller happens to have.

    That is how core/tools/paper/terms could import yaml here and fail on a clean machine: the
    venv holds the declared deps, the system interpreter does not. The path is absolute because
    a shebang cannot resolve a relative one; `core/run` is what removes that per-machine value
    from a versioned file, which is why this test reads the line from disk.
    """
    wrong = [rel(p, WORKSPACE_ROOT) for p in _python_files() if p.suffix == ''
             and p.read_text(encoding='utf-8').splitlines()[0].endswith('/usr/bin/env python3')]
    assert not wrong, (
        'these tools run under the system interpreter, which has none of the declared deps:\n  ' +
        '\n  '.join(wrong) + '\nSpawn them through `core/run <path>`, which finds this clone\'s '
        'interpreter, instead of giving them a shebang.')


def test_the_check_runner_agrees_with_this_file():
    """One parser, not two. If `deps` drifts from deps.txt, the install steps stop being checkable."""
    out = subprocess.run([sys.executable, str(WORKSPACE_ROOT / 'core/tools/wos/deps'), '--feature',
                          'verify-suite'], capture_output=True, text=True, cwd=WORKSPACE_ROOT, encoding='utf-8')
    assert 'pytest' in out.stdout, out.stderr
