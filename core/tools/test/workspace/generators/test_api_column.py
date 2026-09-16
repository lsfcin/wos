# What the routing table's API column may name (core/hooks/SPECS.md). Zero-token, runs in verify-fast.
#
# Split from test_routing_table.py 2026-08-17 at the 200-line block: that file owns which columns
# the table emits and how a row is described, this one owns what counts as a module's public API.
#
# The rule is keyed on the SYMBOL, never on the path. A `tests/`-directory exemption would be a
# door to walk production code through, dodging the facade and interface-stub gates.
# test_a_production_symbol_in_a_test_directory_still_appears is that guarantee — it must never be
# deleted to make another test pass.
from conftest import WORKSPACE_ROOT  # noqa: F401  (imported for the sys.path it sets up)

from workspace_meta import extract_api  # noqa: E402


def test_test_symbols_are_not_listed_as_api(tmp_path) -> None:
    p = tmp_path / 'test_thing.py'
    p.write_text('def test_a_thing_holds():\n    pass\n', encoding='utf-8', newline='\n')
    assert extract_api(p) == '—'


def test_a_shared_fixture_is_still_api(tmp_path) -> None:
    """Suppression must not swallow the helpers a conftest genuinely exports."""
    p = tmp_path / 'conftest.py'
    p.write_text('def make_scene():\n    pass\n\ndef test_ignored():\n    pass\n',
                 encoding='utf-8', newline='\n')
    assert '`make_scene`' in extract_api(p)
    assert 'test_ignored' not in extract_api(p)


def test_a_production_symbol_in_a_test_directory_still_appears(tmp_path) -> None:
    """The anti-circumvention guarantee: no path-shaped door out of the API column.

    Moving a module into `tests/` must not hide what it exports, or an agent could park
    production code there to escape the facade and interface-stub gates.
    """
    d = tmp_path / 'tests'
    d.mkdir()
    p = d / 'helpers.py'
    p.write_text('def build_payload():\n    pass\n', encoding='utf-8', newline='\n')
    assert '`build_payload`' in extract_api(p)


def test_a_nested_closure_is_not_importable_api(tmp_path) -> None:
    """A walk of the whole tree advertised closures as exports (found in hoist.py's `fix`).

    It was masked for months by the five-name cap: only a module exporting fewer than five real
    names had room to show one, so the table was quietly wrong wherever it did.
    """
    p = tmp_path / 'thing.py'
    p.write_text('def rebase():\n    def fix():\n        pass\n    return fix\n',
                 encoding='utf-8', newline='\n')
    assert extract_api(p) == '`rebase`'


def test_a_class_method_is_api_but_never_at_a_top_level_name_s_expense(tmp_path) -> None:
    """The cap makes ordering load-bearing, so methods fill only what top level leaves.

    Listing each class's methods directly after it pushed real module-level functions out of the
    column — trading one wrong entry for a missing right one.
    """
    p = tmp_path / 'thing.py'
    p.write_text('class Result:\n    def add(self):\n        pass\n\n'
                 'def one():\n    pass\n', encoding='utf-8', newline='\n')
    api = extract_api(p)
    assert '`Result`' in api and '`one`' in api and '`add`' in api

    crowded = tmp_path / 'crowded.py'
    crowded.write_text(
        'class Result:\n' + ''.join(f'    def m{i}(self):\n        pass\n' for i in range(6))
        + '\n' + ''.join(f'def top{i}():\n    pass\n' for i in range(4)), encoding='utf-8', newline='\n')
    assert all(f'`top{i}`' in extract_api(crowded) for i in range(4))
