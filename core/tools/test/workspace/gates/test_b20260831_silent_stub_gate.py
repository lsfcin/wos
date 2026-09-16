# b20260831-silent-stub-gate regression — a gate that is OFF must say so.
#
# core/hooks/read/pre-read.py ranked its three states backwards, back when it was shell. A CURRENT
# stub hard-blocked the
# read, a STALE one warned and allowed, and a MISSING one hit `[ ! -f "$iface" ] && exit 0` and
# said nothing at all -- so the worst state was the quietest, and the hook read as passing while
# the interface-first discipline was switched off for that file. entropy_size.stub_signals knew
# ("a missing one does not break -- it silently switches the discipline off, and nothing said so")
# and counted 200 of them into nested ISSUES.md files that B5 says no clone has ever had.
#
# The fix allows the read -- blocking a reader because a GENERATOR never ran punishes the wrong
# side -- and never in silence. This spec holds all four states, because the guarantee is the
# ranking, not any one branch.
import json
import subprocess
import sys
from types import SimpleNamespace

from conftest import WORKSPACE_ROOT

GATE = 'hooks/read/pre-read.py'

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/stubgen'))
sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/commit'))
sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/entropy'))
from entropy_size import stub_signals  # noqa: E402
from generators import _sweep  # noqa: E402
from stubs import interface_for  # noqa: E402


def _read(path, session: str) -> subprocess.CompletedProcess:
    """The hook as the Read protocol delivers it: payload on stdin, verdict in the exit code."""
    payload = json.dumps({'session_id': session, 'tool_input': {'file_path': str(path)}})
    return subprocess.run(['sh', str(WORKSPACE_ROOT / 'core/run'), GATE], input=payload,
                          capture_output=True, text=True, check=False,
                          encoding='utf-8', errors='replace')


def test_a_missing_stub_is_announced_and_the_read_is_allowed(tmp_path):
    source = tmp_path / 'nostub.py'
    source.write_text('def f(x):\n    return x\n', encoding='utf-8', newline='\n')

    result = _read(source, 'missing-stub')

    assert result.returncode == 0, 'a missing stub must not block the reader'
    assert 'NO INTERFACE' in result.stdout, (
        f'the gate was OFF for {source.name} and said nothing:\n{result.stdout!r}')
    assert 'stubs.py' in result.stdout, 'the message must name the command that fixes it'


def test_the_announcement_is_made_once_per_file_per_session(tmp_path):
    """A loop over one file says this once — the codegraph nudge's rule, for the same reason."""
    source = tmp_path / 'nostub.py'
    source.write_text('def f(x):\n    return x\n', encoding='utf-8', newline='\n')

    _read(source, 'dedup-session')
    again = _read(source, 'dedup-session')

    assert again.stdout == '', f'the nudge repeated within one session:\n{again.stdout!r}'


def test_an_empty_stub_counts_as_absent(tmp_path):
    """tsc writes a zero-byte .d.ts for a .js that exports nothing.

    Blocking on it would hand the reader a blank file instead of the source — so backfilling
    code/ppc/partials/*.js would have zeroed three findings and broken the reading of three files.
    """
    source = tmp_path / 'partial.js'
    source.write_text('MODALS.edit = `<dialog></dialog>`;\n', encoding='utf-8', newline='\n')
    (tmp_path / 'partial.d.ts').write_text('', encoding='utf-8', newline='\n')

    result = _read(source, 'empty-stub')

    assert result.returncode == 0, 'an empty stub must never block a source read'
    assert 'NO INTERFACE' in result.stdout, 'an empty stub is absent, and absence must speak'


def test_a_type_with_no_interface_convention_stays_silent(tmp_path):
    """The other arm of the split line: no convention is not the same as a missing stub."""
    prose = tmp_path / 'notes.md'
    prose.write_text('# notes\n', encoding='utf-8', newline='\n')

    result = _read(prose, 'no-convention')

    assert result.returncode == 0
    assert result.stdout == '', f'a .md has no interface to miss:\n{result.stdout!r}'


def test_a_present_stub_still_blocks(tmp_path):
    """Guards the guard: if the split had swallowed the gate, every case above would pass."""
    source = tmp_path / 'stubbed.py'
    source.write_text('def f(x):\n    return x\n', encoding='utf-8', newline='\n')
    (tmp_path / 'stubbed.pyi').write_text('def f(x): ...\n', encoding='utf-8', newline='\n')

    result = _read(source, 'present-stub')

    assert result.returncode == 2, 'the interface-first gate must still block on a current stub'
    assert 'READ INTERFACE FIRST' in result.stderr


def test_the_interface_map_answers_for_javascript(tmp_path):
    """M2's premise: .js was unreachable to the sweep, and 31 of the 200 were isoroll-module's."""
    assert interface_for(tmp_path / 'a.js').name == 'a.d.ts'
    assert interface_for(tmp_path / 'a.ts').name == 'a.d.ts'
    assert interface_for(tmp_path / 'a.py').name == 'a.pyi'
    assert interface_for(tmp_path / 'a.md') is None


def test_the_commit_sweep_reaches_a_stubless_javascript_sibling(tmp_path):
    """The sweep was .py only, so a directory of .js could never be reached by staging one of them.

    The three negatives matter as much as the positive: a sibling that already has its .d.ts is
    not re-swept, and a minified or config file is not a source anyone stubs.
    """
    pkg = tmp_path / 'pkg'
    pkg.mkdir()
    for name, body in [('touched.js', 'export const a=1;\n'), ('orphan.js', 'export const b=2;\n'),
                       ('vendor.min.js', 'var x=1;\n'), ('stubbed.js', 'export const c=3;\n')]:
        (pkg / name).write_text(body, encoding='utf-8', newline='\n')
    (pkg / 'stubbed.d.ts').write_text('export declare const c: number;\n', encoding='utf-8', newline='\n')

    swept = _sweep(SimpleNamespace(toplevel=tmp_path), ['pkg/touched.js'], '*.js',
                   exclude=('.min.js', '.config.js'))

    assert swept == ['pkg/orphan.js', 'pkg/touched.js'], (
        f'the sweep must reach the stubless .js beside a staged one, and nothing else: {swept}')


def test_the_counter_names_the_interface_the_source_actually_wants(tmp_path):
    """The check behind all 200 findings had no test of its own until this one.

    The label is the trap: Path('a.d.ts').suffix is '.ts', so deriving the name from the interface
    path reports a .ts source as wanting '.ts'. It is read by whoever is about to fix the finding.
    """
    (tmp_path / 'a.ts').write_text('export const a = 1;\n', encoding='utf-8', newline='\n')
    (tmp_path / 'b.py').write_text('def f():\n    return 1\n', encoding='utf-8', newline='\n')
    (tmp_path / 'c.py').write_text('def g():\n    return 2\n', encoding='utf-8', newline='\n')
    (tmp_path / 'c.pyi').write_text('def g(): ...\n', encoding='utf-8', newline='\n')

    signals = stub_signals([tmp_path / 'a.ts', tmp_path / 'b.py', tmp_path / 'c.py'])

    assert [s.rsplit('—', 1)[1].strip() for s in signals] == ['no .d.ts', 'no .pyi']
    assert not any('c.py' in s for s in signals), 'a stubbed source is not a finding'


def test_a_facade_is_not_a_finding(tmp_path):
    """The counter and the gate must agree on what a facade is.

    pre-read.py exempts them ("already minimal interfaces") and code/CONTEXT.md tells agents to
    read them — so 41 of the 200 findings asked for a stub the gate would never consult.
    """
    for name in ('__init__.py', 'index.ts'):
        (tmp_path / name).write_text('', encoding='utf-8', newline='\n')

    assert stub_signals([tmp_path / '__init__.py', tmp_path / 'index.ts']) == []
