# T0 the branch-drift warning (core/hooks/SPECS.md § Branch drift): HEAD moving under a session
# must be said out loud, exactly once, and must never block.
#
# The silence cases are the ones that decide whether this survives. A warning that repeats on every
# commit after a deliberate branch switch is one people learn to skip, and a repo with no marker —
# every nested repo, every non-agent commit — must not hear from this at all. So each case here
# runs the real script against a real git repo and reads its behaviour, rather than reading the
# source for a branch that looks right: a guard on an unreachable path passes that reading.
import subprocess
import tempfile
from pathlib import Path

import pytest

from conftest import WORKSPACE_ROOT
from platform_law import interpreter

MARKER = WORKSPACE_ROOT / 'core/hooks/git/branch_marker.py'


def marker_path(repo: Path) -> Path:
	"""The same key the script derives, restated here on purpose.

	This is the one thing a test may duplicate from its subject: if the formula drifts, `record`
	and `check` stop finding each other and every case below would pass while the feature was dead.

	The FORMULA is restated; the temp directory is asked for. `/tmp` was spelled here literally
	until the port, and it is not a directory Windows has -- so the marker went to a path that
	could not exist, and the warning this file exists to prove could never have fired there.
	"""
	sanitized = ''.join(c if c.isalnum() else '_' for c in str(repo.resolve()))
	return Path(tempfile.gettempdir()) / f'claude_branch_{sanitized}.txt'


@pytest.fixture
def repo(tmp_path):
	"""A real repo on a feature branch, with its marker file cleaned up afterwards."""
	subprocess.run(['git', 'init', '-q', '-b', 'feature/mine', str(tmp_path)], check=True)
	yield tmp_path
	marker_path(tmp_path).unlink(missing_ok=True)


def run(repo: Path, mode: str):
	done = subprocess.run([interpreter(), str(MARKER), mode], cwd=repo,
	                      capture_output=True, text=True, encoding='utf-8')
	assert done.returncode == 0, f'the warning must never block: {done.stderr}'
	return done.stdout


def test_a_session_that_stayed_on_its_branch_hears_nothing(repo):
	run(repo, 'record')
	assert run(repo, 'check') == ''


def test_head_moving_under_the_session_is_named_with_its_recovery(repo):
	run(repo, 'record')
	marker_path(repo).write_text('feature/someone-else\n', encoding='utf-8', newline='\n')
	out = run(repo, 'check')
	assert 'feature/someone-else' in out and 'feature/mine' in out, out
	# Naming one action is the contract for agent-facing text (AGENTS.md): the recovery is the
	# non-destructive one, never a reset or a force-push of the other session's branch.
	assert 'git branch -f' in out and 'merge-base --is-ancestor' in out, out


def test_the_warning_fires_once_per_divergence_not_once_per_commit(repo):
	run(repo, 'record')
	marker_path(repo).write_text('feature/someone-else\n', encoding='utf-8', newline='\n')
	assert run(repo, 'check') != ''
	assert run(repo, 'check') == '', 'a repeated warning is one people learn to skip'


def test_a_repo_with_no_marker_is_silent(repo):
	marker_path(repo).unlink(missing_ok=True)
	assert run(repo, 'check') == ''


def test_a_detached_head_is_a_rebase_not_a_drift(repo):
	"""Mid-rebase and mid-bisect HEAD is detached by design; a branch warning there is noise."""
	(repo / 'f.txt').write_text('x', encoding='utf-8', newline='\n')
	subprocess.run(['git', '-C', str(repo), 'add', 'f.txt'], check=True)
	subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'x', '--no-verify'], check=True)
	run(repo, 'record')
	subprocess.run(['git', '-C', str(repo), 'checkout', '-q', '--detach'], check=True)
	assert run(repo, 'check') == ''


def test_outside_a_repo_it_says_nothing(tmp_path):
	done = subprocess.run([interpreter(), str(MARKER), 'check'], cwd=tmp_path,
	                      capture_output=True, text=True, encoding='utf-8')
	assert done.returncode == 0 and done.stdout == ''
