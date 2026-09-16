# b20260913 regression — the line gate weighs what git will COMMIT, not what sits on disk.
#
# The pre-commit pipeline hands line_counts.report the STAGED path list, and the gate then read
# each one with read_text() — the working copy. Whenever a trim was written but never staged, the
# two disagreed and the gate answered about a file nobody was committing: `branch_debt.py` and
# `wos/roundup` went in at 202 and 201 lines against WARN_LINES=200 while it printed
# `No authored files exceed thresholds`.
#
# Both directions are pinned here, because the mirror case is the one a narrower fix would leave
# broken: a staged fix must not be warned about on account of an unstaged working copy.
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from conftest import WORKSPACE_ROOT  # noqa: E402

import file_law  # noqa: E402
import line_counts  # noqa: E402

OVER, UNDER = int(file_law.load_limits()['WARN_LINES']) + 2, 10


def _repo(tmp_path, staged_lines, disk_lines):
    """A throwaway repo where `notes.md` is one length in the index and another on disk.

    The gate is called directly rather than through the hook: what is under test is which of the
    two copies it reads, and routing that through a real commit would make the hook's own refusal
    the thing being measured.
    """
    def git(*args):
        subprocess.run(['git', *args], cwd=tmp_path, check=True, capture_output=True)

    git('init', '-q')
    git('config', 'user.email', 't@e.com')
    git('config', 'user.name', 't')
    git('config', 'core.hooksPath', '/dev/null')  # the real hooks are not under test
    target = tmp_path / 'notes.md'
    target.write_text('\n'.join(f'line {n}' for n in range(staged_lines)),
                      encoding='utf-8', newline='\n')
    git('add', 'notes.md')
    target.write_text('\n'.join(f'line {n}' for n in range(disk_lines)),
                      encoding='utf-8', newline='\n')
    return tmp_path


def test_a_file_staged_over_the_cap_warns_though_the_working_copy_is_short(tmp_path):
    repo = _repo(tmp_path, staged_lines=OVER, disk_lines=UNDER)
    lines, _ = line_counts.report(['notes.md'], root=repo, staged=True)
    assert any('WARN' in line for line in lines), (
        f'the blob being committed is {OVER} lines and the gate stayed silent: {lines}')


def test_a_staged_fix_is_not_warned_about_by_a_long_working_copy(tmp_path):
    repo = _repo(tmp_path, staged_lines=UNDER, disk_lines=OVER)
    lines, _ = line_counts.report(['notes.md'], root=repo, staged=True)
    assert not any('WARN' in line for line in lines), (
        f'the commit carries {UNDER} lines and the gate warned anyway: {lines}')


def test_a_bare_audit_still_reads_the_disk(tmp_path):
    """The other caller has no index to consult: `main()` over `git ls-files` audits the tree as
    it stands, and reading the blob there would report on the last commit instead of on today."""
    repo = _repo(tmp_path, staged_lines=UNDER, disk_lines=OVER)
    lines, _ = line_counts.report(['notes.md'], root=repo)
    assert any('WARN' in line for line in lines), (
        f'the file on disk is {OVER} lines and the audit stayed silent: {lines}')


def test_the_pipeline_asks_for_the_staged_blob():
    """The fix is only live if the one caller holding an index passes `staged`. Read rather than
    run: spawning the whole pre-commit to observe one keyword costs seconds and proves less."""
    source = (WORKSPACE_ROOT / 'core/hooks/commit/gates.py').read_text(encoding='utf-8')
    assert 'staged=True' in source, (
        'core/hooks/commit/gates.py calls line_counts.report without staged=True, so the gate is '
        'back to weighing the working copy')
