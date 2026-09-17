# conftest.py — the one place the suite learns where things are: workspace root, core/tools,
# and the enforcement layer. Also registers the network marker for the video tests.
#
# Every test used to spell out `parents[3]` for the workspace root — nine copies of a depth,
# which is a number that changes the moment a test moves into a subdirectory. Import it from
# here instead; pytest loads this file before any test module.
import os, sys, pathlib, tempfile

HERE = pathlib.Path(__file__).resolve().parent
WORKSPACE_ROOT = HERE.parents[2]

# A git hook exports GIT_DIR, GIT_INDEX_FILE and friends, and every child process inherits them.
# Dozens of tests here build a throwaway repo in tmp_path and run git inside it; under those
# variables git ignores the cwd and operates on THIS repo instead. The tests then assert against
# the workspace's own history and fail — but only when the suite is run BY THE PRE-COMMIT HOOK,
# which is the one moment verify:fast is acting as a gate. Run by hand it is green, so the gate
# was red and its operator was told otherwise. Found 2026-08-19; the failure is loud (19 tests)
# and was invisible for as long as it existed because nobody reproduces a hook's environment.
for _var in ('GIT_DIR', 'GIT_INDEX_FILE', 'GIT_WORK_TREE', 'GIT_OBJECT_DIRECTORY',
             'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_PREFIX', 'GIT_COMMON_DIR'):
    os.environ.pop(_var, None)

# THE SUITE MUST NOT BE IN THE MEASUREMENT. core/hooks/scoreboard.py counts what each feature did in
# real use, and feature_law.is_enabled() is on the hot path of nearly every test here: one run wrote
# 47,000 rows into the real store, which would have made a two-week reading almost entirely a
# recording of pytest. Pointed at a throwaway file, and inherited by every subprocess a test spawns.
os.environ['WOS_SCOREBOARD'] = str(
    pathlib.Path(tempfile.gettempdir()) / 'wos-scoreboard-test.tsv')

# Own directory first, so tests in subdirectories can `from conftest import WORKSPACE_ROOT`.
sys.path.insert(0, str(HERE))

# core/hooks and core/tools are each one root plus one directory per responsibility. Both
# are derived by scan, never listed: a spelled-out list would go stale the next time either
# is split, and the tests would fail for a reason that has nothing to do with what they
# assert. That is exactly what happened when core/tools/test itself was split.
HOOKS = WORKSPACE_ROOT / 'core/hooks'
TOOLS = WORKSPACE_ROOT / 'core/tools'


def _tree(root):
    """The root, then every directory under it that holds importable modules."""
    yield root
    for child in sorted(root.rglob('*')):
        if child.is_dir() and not any(part.startswith(('.', '_')) for part in
                                      child.relative_to(root).parts):
            yield child


for _dir in [*_tree(HOOKS), *_tree(TOOLS)]:
    sys.path.insert(0, str(_dir))


def floor_of(**kw):
    """A `crossing.Floor` with every kind empty but the ones a case names.

    Two b20260917 regressions build one, and the duplication gate is right that the shape belongs in
    one place: a Floor gained `trees` after the first was written, and a second hand-built base dict
    is how one of them would have kept testing the four-field shape forever. Imported inside the
    function on purpose — `crossing` reads the floor and the registry off disk at import, and every
    test in the suite would pay for that to serve the two that ask.
    """
    sys.path.insert(0, str(TOOLS / 'wos/publish'))
    import crossing  # noqa: PLC0415
    return crossing.Floor(**{**dict(target=WORKSPACE_ROOT, roots=(), files=(), trees=(),
                                    absent={}), **kw})


def git_lines(*args) -> list:
    """Lines of a git query against the workspace, minus the ratchet files themselves.

    Shared because a ratchet necessarily NAMES what it forbids: a test asserting nobody spells the
    authoring machine's absolute root has to spell it to search for it, and would otherwise be its
    own only finding. Any path containing `_ratchet` is dropped for that reason — the rule is the
    file kind, not a list of filenames, so splitting the ratchets into a second file cannot
    silently make one of them count itself.

    The ratchets get the needle itself from `platform_law.AUTHORING_ROOT` rather than spelling it,
    so this docstring names it in words. That is not evasion of the count — it is the same rule
    ROADMAP.md § Portability already follows for the same reason.
    """
    import subprocess
    done = subprocess.run(['git', *args], cwd=WORKSPACE_ROOT, capture_output=True, text=True, encoding='utf-8')
    hits = [line for line in done.stdout.splitlines() if line and '_ratchet' not in line]
    return [line for line in hits if not _inside_generated_block(line)]


def _inside_generated_block(hit: str) -> bool:
    """Whether a `path:line:text` hit lands in a block no author wrote.

    The same exemption `_ratchet` gets, for the same reason: the file necessarily carries what the
    ratchet forbids, and rewriting it would falsify rather than fix. ISSUES.md's `verify:` block
    QUOTES the last red suite log, so a traceback naming the venv path made four ratchets red over
    a record — and the only fix would have been to hand-edit a generated block, which
    core/SCHEMA.md forbids outright.

    Scoped to the block, never the file: the hand-written half stays held to every rule. A hit with
    no line number cannot be placed and is kept, so the tolerant direction reports rather than hides.
    """
    import file_law
    path, _, rest = hit.partition(':')
    number, _, _ = rest.partition(':')
    target = WORKSPACE_ROOT / path
    if not number.isdigit() or not path.endswith('.md') or not target.is_file():
        return False
    return file_law.is_generated_line(target.read_text(encoding='utf-8', errors='replace'),
                                      int(number))


import pytest  # noqa: E402 — after the env scrub above, which must run before anything imports git


def needs(*paths: str) -> None:
    """Skip when the SUBJECT of the test is not in this checkout.

    This suite runs in two repos now. The workspace has brain/, branches/, academy/ and code/; the
    public repo core/tools/wos/publish syncs into does not, by a refusal written in core/public.txt,
    and a test asserting about a directory that was deliberately left out is not a red suite, it is
    a question with no subject. Ruled 2026-09-16 (Lucas): the test declares the precondition, rather
    than the floor carrying a list of tests to withhold — an exception the floor cannot see rots,
    because nothing tells it when a NEW test should join.

    It buys something here too. These cases read green in the workspace by luck of the tree being
    there, and nothing said they depended on it: delete brain/drafts/ and the red would name an
    assertion, never the missing precondition."""
    missing = [p for p in paths if not carries(p)]
    if missing:
        pytest.skip(f'subject not in this checkout: {", ".join(missing)} — see core/public.txt')


def carries(path: str) -> bool:
    """Does this checkout carry the tree `path` sits in? Asked of GIT, not of the filesystem: a
    test that builds a scratch directory under code/ makes `code/` exist for the length of a run, and
    a guard reading the disk answers yes to a tree with nothing in it. Judged at the top segment,
    so a row pointing at a file deleted from a tree that IS here still reports."""
    return bool(git_lines('ls-files', '--', path.split('/')[0]))

# THE SUBTREES A TEST MAY NOT LEAVE CHANGED, and why these two. `core/skills/` is where the proven
# offender seeded drift, `code/` is where two others created a real check directory and removed it.
# Both are scanned by other cases while a case is inside that window, which is what made the suite
# a coin flip. Kept to two directories on purpose: the guard runs around EVERY test, so it has to
# cost microseconds -- os.scandir over two directories, no subprocess, no git.
_WATCHED = ('code', 'core/skills')


def _shape():
    """Name, size and mtime of everything directly under each watched directory.

    NOT a hash and not a walk: this has to be cheap enough to run twice per test. It sees a created
    or removed path, and a tracked file whose content changed -- the two shapes b20260902 recorded.
    A change deeper than one level that leaves the top level identical is not caught, and that is
    the stated limit rather than an oversight.
    """
    import os
    shape = {}
    for relative in _WATCHED:
        directory = WORKSPACE_ROOT / relative
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    stat = entry.stat()
                    shape[f'{relative}/{entry.name}'] = (stat.st_size, stat.st_mtime_ns)
        except OSError:
            shape[relative] = 'unreadable'
    return shape


@pytest.fixture(autouse=True)
def _no_test_dirties_the_real_tree(request):
    """core/tools/test/wos/CONTEXT.md states the law -- "nothing touches the real workspace" -- and
    until 2026-09-05 nothing checked it, so it was broken three times without anyone noticing.

    A case that really must mutate the tree says so with `serial`, and verify.py gives it a pass of
    its own where no worker is reading beside it. That marker is the exemption here, so declaring
    it is the only way to be allowed, and forgetting it is now a failure in the offending test
    rather than a random red in a file its author never touched.
    """
    if request.node.get_closest_marker('serial'):
        yield
        return
    before = _shape()
    yield
    after = _shape()
    if before != after:
        changed = sorted(set(before) ^ set(after)
                         | {k for k in set(before) & set(after) if before[k] != after[k]})
        pytest.fail(
            f'this test changed the real workspace tree: {changed[:8]}. Build what you need under '
            f'tmp_path, or mark the case `serial` if it genuinely has no boundary -- see '
            f'core/tools/test/wos/CONTEXT.md and b20260902.')


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "network: hits real network/models; excluded from verify:fast")
    # A TEST THAT DIRTIES THE REAL TREE CANNOT SHARE THE CLOCK WITH ONE THAT READS IT. The suite
    # went parallel 2026-09-01 and this class of case became a coin flip: the mirror-heal spec seeds
    # drift into core/skills/compass.md and restores it in a finally, and two OTHER cases failed
    # inside that window here — the sync-skills check, and the diagram's determinism (two renders of
    # a tree that changed between them). Two of three full runs were red on 2026-09-02, on a suite
    # the Windows clone had seen green three times running, because how wide the window opens is a
    # core count. verify.py runs these in a second, serial pass.
    config.addinivalue_line(
        "markers", "serial: mutates the real workspace tree; never run beside another case")
    # Every gate and tool this suite spawns is spawned through core/run in production, and core/run
    # exports this. Declared once here rather than per spawn: a spec that runs a gate barer than the
    # harness ever does is testing a gate that does not exist, and it fails as a TypeError about
    # NoneType — the child writes a glyph, the parent cannot decode it, the reader thread dies and
    # stdout comes back None. The law: core/tools/test/workspace/test_encoding_ratchet.py
    os.environ['PYTHONIOENCODING'] = 'utf-8'
