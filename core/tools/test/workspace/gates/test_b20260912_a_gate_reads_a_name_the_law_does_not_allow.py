# b20260912 regression — two gates recognised a shape by a spelling of their own instead of by the
# law, and both refused correct code. Found when code/aiwbot was absorbed into this repo and its
# 261 files met these gates for the first time.
#
# 1. context-tracker.py recorded a spec read only for a file literally named SPEC.md, while
#    spec-read-gate.py resolves whatever the module's CONTEXT.md names in `> spec:`. SPEC.md is not
#    even in core/SCHEMA.md's type allowlist, so a module whose spec carried the LEGAL spelling
#    could be read and the gate would still refuse every edit, with no way out inside the session.
# 2. check-facade-imports.py matched `from .. import x` — the import that goes THROUGH the parent
#    facade — as a descent past it, because `\S+` ate the second dot. It then printed a violation
#    naming no module at all.
import re
import subprocess
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT

HOOKS = WORKSPACE_ROOT / 'core/hooks'
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(HOOKS / 'facade'))


def _tracker_source() -> str:
    return (HOOKS / 'read/context-tracker.py').read_text(encoding='utf-8')


def _facade_module():
    """Imported by path: the file's name carries hyphens, so it has no importable name."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'check_facade_imports', HOOKS / 'facade/check-facade-imports.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_spec_named_the_legal_way_is_recorded_as_read():
    """SPECS.md is the spelling core/SCHEMA.md allows; the tracker must count it as a spec read."""
    source = _tracker_source()
    marker = re.search(r"name == 'CONTEXT\.md' or .*?startswith\('SPEC'\)", source)
    assert marker, ("context-tracker.py must record a spec read by shape, not by one filename — "
                    "spec-read-gate.py resolves whatever `> spec:` names")


def test_every_declared_spec_is_a_name_the_tracker_records():
    """The end-to-end shape: a spec-locked module nobody can unlock is a module nobody can edit.

    Read off the real declarations rather than a fixture — the gate resolves `> spec:` the same
    way, and this is the join the bug broke.
    """
    declared = re.compile(r'^>\s*spec:\s*(\S.*?)\s*$', re.MULTILINE)
    for context in sorted((WORKSPACE_ROOT / 'code').rglob('CONTEXT.md')):
        found = declared.search(context.read_text(encoding='utf-8'))
        if not found or found.group(1).lower() == 'none':
            continue
        spec_path = (context.parent / found.group(1)).resolve()
        assert spec_path.name.startswith('SPEC'), (
            f'{context} declares {spec_path.name}, which context-tracker.py never records — '
            f'the module would be refused every edit with no way to satisfy the gate')


def test_an_import_through_the_parent_facade_is_not_a_violation():
    module = _facade_module()
    assert module.py_violations(Path('a/b.py'), 'from .. import config\n') == []
    assert module.py_violations(Path('a/b.py'), 'from . import sibling\n') == []


def test_an_import_descending_past_a_facade_still_is():
    module = _facade_module()
    found = module.py_violations(Path('a/b.py'), 'from ..pkg.submod import thing\n')
    assert len(found) == 1
    assert '..pkg.submod' in found[0], 'the message must name the import it refuses'


def test_the_checker_runs_clean_over_the_tree_it_first_refused():
    """The 16 aiwbot files the bug reported. Run as the pre-commit runs it, not re-derived here."""
    targets = [str(p) for p in sorted((WORKSPACE_ROOT / 'code/aiwbot').rglob('*.py'))]
    done = subprocess.run([sys.executable, str(HOOKS / 'facade/check-facade-imports.py'), *targets],
                          capture_output=True, text=True, encoding='utf-8')
    assert done.returncode == 0, done.stdout + done.stderr
