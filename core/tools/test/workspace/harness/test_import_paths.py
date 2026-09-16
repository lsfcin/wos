# T0 harness invariant: the suite's sys.path cannot silently shadow a module.
#
# conftest.py walks core/hooks and core/tools and inserts every directory, so the suite can
# `import entropy_crowding` or `import video_core` without knowing which family owns them.
# That convenience has one failure mode: two modules with the same basename in different
# directories resolve by insertion order, and the loser is never imported — silently, with
# the tests still green because they exercised the wrong file.
#
# Written 2026-08-01 during the VERIFY audit, after core/hooks and core/tools were both
# split into families. There were no collisions at the time; this keeps it that way.
from collections import defaultdict

from conftest import HOOKS, TOOLS


def _search_path():
    """The directories conftest puts on sys.path, derived the same way it derives them."""
    for root in (HOOKS, TOOLS):
        yield root
        for child in sorted(root.rglob('*')):
            if child.is_dir() and not any(part.startswith(('.', '_'))
                                          for part in child.relative_to(root).parts):
                yield child


def test_no_module_basename_is_claimed_twice() -> None:
    owners = defaultdict(list)
    for directory in _search_path():
        for module in directory.glob('*.py'):
            owners[module.stem].append(str(module))
    clashes = {name: paths for name, paths in owners.items() if len(paths) > 1}
    assert not clashes, (
        f'two modules share a basename on the test sys.path, so one shadows the other: '
        f'{clashes}. Rename one, or narrow the walk in conftest.py.')
