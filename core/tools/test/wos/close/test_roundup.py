# T1 roundup tool (core/SPECS.md § AD-09): the deterministic half of the session-close ritual.
# Zero-token, no network — every case builds its own throwaway repo.
#
# warn-exempt: a suite file grows by CASE, and each case here builds a whole throwaway workspace
# before it can assert anything. Cutting to the warn deletes coverage. The block cap still applies.
#
# The one thing worth guarding hardest is the dirty stop. It used to assert that uncommitted work
# was work *this* session forgot to commit, and asked for a commit that would have swept a parallel
# session's half-finished goal merge into main. Dirt has two possible owners and the script cannot
# tell them apart, so it names both and lets --leave-dirty answer.
import shutil
import subprocess

from conftest import WORKSPACE_ROOT
from platform_law import interpreter

# The fake dashboard writes a BLOCK through the real writer, exactly as the real one does: a target
# that clobbered the file would pass while hiding the thing worth guarding — roundup writes the
# verify block first, so an entropy regen that does not preserve its neighbours destroys it. The
# header is the REAL shape, trend and all; a fake reading "**7 findings**" is what hid a pattern
# matching nothing. GREEN/RED are contracts declared as verify.py, the form roundup discovers first.
_HEAD = '**7 findings here** (2026-08-24: 9 · -2 over 1 days)'
DASHBOARD = ('import sys; sys.path.insert(0, "core/hooks/routing")\n'
             'from pathlib import Path\nfrom blocks import markers, replace_block\n'
             f'start, end = markers("entropy")\nbody = "\\n".join((start, {_HEAD!r}, end))\n'
             'page = Path("ISSUES.md")\npage.write_text(replace_block('
             'page.read_text(encoding="utf-8"), body, start, end), encoding="utf-8")\n')
GREEN, RED = 'print("3 passed")\n', 'raise SystemExit(1)\n'

SEEDED_ISSUES = ('# Issues\n\n## B1 — a hand-written issue the generators must not touch\n\n'
                 '<!-- entropy:start -->\n**9 findings**\n<!-- entropy:end -->\n')

# Every real file the script reaches for — what they do to the tree is the subject of these cases.
PARTS = ('core/tools/wos/roundup', 'core/tools/wos/close/artifacts.py', 'core/hooks/routing/blocks.py',
         'core/tools/wos/close/branches.py', 'core/tools/wos/close/projects.py',
         'core/tools/wos/close/repomap.py', 'core/tools/verify/contract.py',
         'core/hooks/platform_law.py', 'core/hooks/entropy/entropy_corpus.py')  # real: sweep asks it


def _git(repo, *args):
    return subprocess.run(('git',) + args, cwd=repo, capture_output=True, text=True, encoding='utf-8')


def _workspace(tmp_path, verify=GREEN):
    """A fake workspace: the real script at its real relative path, so ROOT == WORKSPACE and the
    gitflow and entropy branches of the code are reachable. main == develop, feature one ahead."""
    ws = tmp_path / 'ws'
    for part in PARTS:
        (ws / part).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(WORKSPACE_ROOT / part, ws / part)
    dashboard = ws / 'core/hooks/entropy/dashboard/entropy-dashboard.py'
    dashboard.parent.mkdir(parents=True)
    dashboard.write_text(DASHBOARD, encoding='utf-8', newline='\n')
    (ws / 'verify.py').write_text(verify, encoding='utf-8', newline='\n')
    (ws / 'ISSUES.md').write_text(SEEDED_ISSUES, encoding='utf-8', newline='\n')

    _git(ws, 'init', '-q', '-b', 'main')
    _git(ws, 'config', 'user.email', 'test@example.com')
    _git(ws, 'config', 'user.name', 'test')
    _git(ws, 'config', 'core.hooksPath', '/dev/null')  # the real hooks are not under test
    _git(ws, 'add', '-A')
    _git(ws, 'commit', '-q', '--no-verify', '-m', 'init')

    origin = tmp_path / 'origin.git'
    _git(tmp_path, 'init', '-q', '--bare', str(origin))
    _git(ws, 'remote', 'add', 'origin', str(origin))
    _git(ws, 'branch', 'develop')
    _git(ws, 'checkout', '-q', '-b', 'feature/x')
    (ws / 'shipped.txt').write_text('work\n', encoding='utf-8', newline='\n')
    _git(ws, 'add', '-A')
    _git(ws, 'commit', '-q', '--no-verify', '-m', 'feat: work')
    _git(ws, 'push', '-q', 'origin', 'main', 'develop', 'feature/x')
    return ws


def _run(ws, *args):
    return subprocess.run([interpreter(), str(ws / 'core/tools/wos/roundup'), *args],
                          cwd=ws, capture_output=True, text=True, encoding='utf-8')


def _dirty(ws):
    """A parallel session's work in progress: one staged add, one unstaged edit."""
    (ws / 'theirs.md').write_text('their draft\n', encoding='utf-8', newline='\n')
    _git(ws, 'add', 'theirs.md')
    (ws / 'shipped.txt').write_text('their edit\n', encoding='utf-8', newline='\n')


def test_dirty_stop_prints_the_paths_and_asks_whose(tmp_path):
    ws = _workspace(tmp_path)
    _dirty(ws)
    r = _run(ws)
    assert r.returncode == 2
    assert 'theirs.md' in r.stdout, 'the agent cannot judge ownership without the paths'
    assert '--leave-dirty' in r.stdout and 'commit' in r.stdout


def test_dirty_stop_does_not_assert_whose_work_it_is(tmp_path):
    """The defect, in one assertion: the old message said 'commit, then rerun' as a statement of
    fact about work it had not attributed."""
    ws = _workspace(tmp_path)
    _dirty(ws)
    first = _run(ws).stdout.splitlines()[0]
    assert 'whose' in first.lower(), f'the stop must ask, not assert: {first!r}'


def test_leave_dirty_promotes_without_touching_the_tree(tmp_path):
    ws = _workspace(tmp_path)
    _dirty(ws)
    before = _git(ws, 'status', '--porcelain').stdout
    r = _run(ws, '--leave-dirty')
    assert r.returncode == 0, r.stdout
    assert 'promoted' in r.stdout
    assert _git(ws, 'rev-parse', 'main').stdout == _git(ws, 'rev-parse', 'feature/x').stdout
    assert _git(ws, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip() == 'feature/x'
    assert _git(ws, 'status', '--porcelain').stdout == before, 'a fast-forward must not touch files'


def test_leave_dirty_never_commits_the_foreign_dirt(tmp_path):
    """The hazard that made this flag necessary: the entropy commit stages the whole index, so
    committing it while another session has files staged carries them into chore(entropy)."""
    ws = _workspace(tmp_path)
    _dirty(ws)
    r = _run(ws, '--leave-dirty')
    assert 'not committed' in r.stdout
    log = _git(ws, 'log', '--name-only', '--pretty=format:', 'feature/x').stdout
    assert 'theirs.md' not in log
    assert 'theirs.md' in _git(ws, 'status', '--porcelain').stdout


def test_clean_tree_still_commits_entropy(tmp_path):
    ws = _workspace(tmp_path)
    r = _run(ws)
    assert r.returncode == 0, r.stdout
    # The label too: a count the script cannot parse drops the whole entropy line, and a bare
    # substring assertion would still have passed on the header it happened to commit.
    assert 'entropy: 7 findings here' in r.stdout and 'not committed' not in r.stdout
    assert '-2 over 1 days' in r.stdout, 'the trend is read out of the header, never recomputed'
    assert 'chore(issues)' in _git(ws, 'log', '--oneline', 'main').stdout


def test_the_two_blocks_and_the_hand_written_issues_coexist(tmp_path):
    """Three writers share ISSUES.md and none of them owns the file.

    roundup writes the verify block, the dashboard rewrites the entropy block after it, and the
    hand-written issues above both are nobody's to touch. A generator that rebuilt the file instead
    of its own block would pass every other case here and silently eat the other two.
    """
    ws = _workspace(tmp_path)
    assert _run(ws).returncode == 0
    text = (ws / 'ISSUES.md').read_text(encoding='utf-8')
    assert '## B1 — a hand-written issue' in text, 'the hand-written half must survive both writers'
    assert '**7 findings here**' in text and '**9 findings**' not in text
    assert '<!-- verify:start -->' in text and 'green (3 passed)' in text


def test_a_red_suite_reports_itself_in_the_verify_block(tmp_path):
    """A red run still writes the block — that is the whole point of recording the last result."""
    ws = _workspace(tmp_path, verify=RED)
    _run(ws)
    assert '**red**' in (ws / 'ISSUES.md').read_text(encoding='utf-8')


def test_a_real_merge_lands_even_while_the_tree_holds_another_sessions_work(tmp_path):
    """A real merge runs inside a throwaway git worktree so HEAD in the session's own tree never
    moves, allowing diverged branches to merge even while the tree holds another session's work."""
    ws = _workspace(tmp_path)
    _git(ws, 'checkout', '-q', 'develop')
    (ws / 'diverged.txt').write_text('elsewhere\n', encoding='utf-8', newline='\n')
    _git(ws, 'add', '-A')
    _git(ws, 'commit', '-q', '--no-verify', '-m', 'chore: diverge')
    _git(ws, 'push', '-q', 'origin', 'develop')
    _git(ws, 'checkout', '-q', 'feature/x')
    _dirty(ws)
    r = _run(ws, '--leave-dirty')
    assert r.returncode == 0, r.stdout
    assert 'promoted' in r.stdout
    assert _git(ws, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip() == 'feature/x'
    assert _git(ws, 'log', '--oneline', 'develop').stdout.count('Merge') == 1
    assert _git(ws, 'rev-parse', 'main').stdout == _git(ws, 'rev-parse', 'develop').stdout


def test_foreign_dirty_file_survives_real_merge_untouched_and_uncommitted(tmp_path):
    """Foreign dirty files (both staged and unstaged) must remain untouched in the working tree
    and must not be swept into the real merge commit on develop or main."""
    ws = _workspace(tmp_path)
    _git(ws, 'checkout', '-q', 'develop')
    (ws / 'diverged.txt').write_text('elsewhere\n', encoding='utf-8', newline='\n')
    _git(ws, 'add', '-A')
    _git(ws, 'commit', '-q', '--no-verify', '-m', 'chore: diverge')
    _git(ws, 'push', '-q', 'origin', 'develop')
    _git(ws, 'checkout', '-q', 'feature/x')
    _dirty(ws)
    before_status = _git(ws, 'status', '--porcelain').stdout
    r = _run(ws, '--leave-dirty')
    assert r.returncode == 0, r.stdout
    assert _git(ws, 'status', '--porcelain').stdout == before_status
    assert (ws / 'theirs.md').read_text(encoding='utf-8') == 'their draft\n'
    assert (ws / 'shipped.txt').read_text(encoding='utf-8') == 'their edit\n'
    dev_files = _git(ws, 'log', '--name-only', '--pretty=format:', 'develop').stdout
    assert 'theirs.md' not in dev_files
    main_files = _git(ws, 'log', '--name-only', '--pretty=format:', 'main').stdout
    assert 'theirs.md' not in main_files
    # The throwaway worktree must be unregistered as well as deleted. A leaked entry costs nothing
    # visible on the close that leaked it and accumulates in `git worktree list` forever after.
    assert not (ws / '.git/worktrees').exists(), 'the throwaway worktree was left registered'


def test_red_verify_blocks_promotion(tmp_path):
    ws = _workspace(tmp_path, verify=RED)
    r = _run(ws)
    assert r.returncode == 1
    assert 'verify: red' in r.stdout and 'not promoted' in r.stdout
    assert _git(ws, 'rev-parse', 'main').stdout != _git(ws, 'rev-parse', 'feature/x').stdout


def test_no_promote_needs_a_reason(tmp_path):
    ws = _workspace(tmp_path)
    assert _run(ws, '--no-promote').returncode != 0


def test_unknown_flag_is_a_usage_error(tmp_path):
    ws = _workspace(tmp_path)
    r = _run(ws, '--commit-everything')
    assert r.returncode == 64 and '--leave-dirty' in r.stderr


def test_the_flags_compose(tmp_path):
    ws = _workspace(tmp_path)
    _dirty(ws)
    r = _run(ws, '--leave-dirty', '--no-promote', 'branch is incoherent')
    assert r.returncode == 0, r.stdout
    assert 'branch is incoherent' in r.stdout and 'not promoted' in r.stdout
