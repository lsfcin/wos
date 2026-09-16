# b20260831 regression — a project's commits reach its remote, and the session close is where.
#
# Committing in the workspace made the list scatter write AND commit a regenerated ISSUES.md into
# every nested repo it touched — 25 in one go on 2026-08-31 — and push none. The commits were
# correct; they simply stayed on this disk, which is exactly what code/SPECS-git.md § Push policy
# forbids. Worse, it happened BEHIND the session: nobody typed those commits, so nobody thought to
# push them, and the audit that found it had to push 25 repos by hand twenty minutes after
# declaring the tree clean.
#
# Ruled 2026-09-04 (Lucas): the ghost commit is gone — each repo writes and stages its own list
# in its own commit (test_b5_list_commits.py) — and the push is a sweep at session close, where a
# person is present to read what happened. A repo with no remote is NAMED, never silently skipped:
# that one cannot be fixed from here, and the old failure was precisely a repo nothing reported on.
#
# The same failure came back a second way (2026-09-09): the sweep asked `git log @{upstream}..HEAD`,
# which FAILS on a branch with no upstream, and read the failure as "nothing to push". Six projects
# held 22 unpushed commits each, and every close called them quiet. A branch nobody can ask about
# is not a branch with nothing to say — it gets an upstream and a push.
#
# And the promotion half was declared but never run: close/branches.py said the workspace repo AND
# the code/* projects promote, while only the root ever did. Nine projects sat with develop 22
# commits ahead of main. The docstring was right; the caller was the half that was missing.
import importlib.machinery
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import WORKSPACE_ROOT

ENV = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
       'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}


@pytest.fixture
def roundup():
	"""The close tool loaded as a module — it is extensionless, so import needs the path spelled."""
	for directory in ('core/tools/wos/close', 'core/hooks', 'core/tools/verify',
	                  'core/hooks/entropy'):
		sys.path.insert(0, str(WORKSPACE_ROOT / directory))
	loader = importlib.machinery.SourceFileLoader('roundup_cli',
	                                              str(WORKSPACE_ROOT / 'core/tools/wos/roundup'))
	spec = importlib.util.spec_from_loader('roundup_cli', loader)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def _git(repo, *args):
	return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True,
	                      encoding='utf-8', env=ENV)


def _commit(project, text: str, message: str) -> None:
	(project / 'file.py').write_text(f'# a file\n{text}\n', encoding='utf-8', newline='\n')
	_git(project, 'add', '.')
	_git(project, 'commit', '-qm', message, '--no-verify')


def _workspace(tmp_path, with_remote=True, upstream=True) -> Path:
	"""A throwaway workspace holding one nested project, with a bare origin of its own.

	Its own repo and its own origin: nothing here touches the real workspace, which is the law
	core/tools/test/wos/CONTEXT.md states.

	`upstream=False` is the second shape of the same bug: a remote exists, and the branch has
	never been pushed to it, so there is nothing to ask `@{upstream}` about.
	"""
	root, project = tmp_path / 'ws', tmp_path / 'ws/code/proj'
	project.mkdir(parents=True)
	subprocess.run(['git', 'init', '-q', str(root)], check=True)
	subprocess.run(['git', 'init', '-q', str(project)], check=True)
	_commit(project, 'x = 1', 'work nobody has seen')
	if with_remote:
		origin = tmp_path / 'origin.git'
		subprocess.run(['git', 'init', '-q', '--bare', str(origin)], check=True)
		_git(project, 'remote', 'add', 'origin', str(origin))
		if upstream:
			_git(project, 'push', '-q', '--set-upstream', 'origin', 'HEAD')
			_commit(project, 'x = 2', 'the commit that used to stay on this disk')
	return root


def _gitflow_workspace(tmp_path) -> Path:
	"""A code/ project shaped the way every real one is: main pushed, develop ahead of it."""
	root = _workspace(tmp_path, upstream=False)
	project = root / 'code/proj'
	_git(project, 'checkout', '-qB', 'main')
	_git(project, 'push', '-q', '--set-upstream', 'origin', 'main')
	_git(project, 'checkout', '-qb', 'develop')
	_commit(project, 'x = 2', 'chore(issues): regenerate the entropy list')
	return root


def test_a_project_ahead_of_its_remote_is_pushed(tmp_path, roundup) -> None:
	root = _workspace(tmp_path)
	project = root / 'code/proj'
	assert _git(project, 'log', '--oneline', '@{upstream}..HEAD').stdout.strip(), 'setup is wrong'

	said = roundup.sweep(root)

	assert '1 pushed' in said, said
	assert not _git(project, 'log', '--oneline', '@{upstream}..HEAD').stdout.strip(), (
		'the sweep reported a push that did not happen')


def test_a_project_with_no_remote_is_named(tmp_path, roundup) -> None:
	"""Nothing here can fix it, so the only honest act is to say which repo it is."""
	said = roundup.sweep(_workspace(tmp_path, with_remote=False))
	assert 'no remote' in said and 'code/proj' in said, said


def test_a_project_already_pushed_says_nothing(tmp_path, roundup) -> None:
	"""A close that reports on every quiet repo is a close nobody reads to the end."""
	root = _workspace(tmp_path)
	roundup.sweep(root)
	assert roundup.sweep(root) == ''


def test_a_branch_with_no_upstream_is_pushed_rather_than_called_quiet(tmp_path, roundup) -> None:
	"""`git log @{upstream}..HEAD` fails here, and a failure is not an empty answer."""
	root = _workspace(tmp_path, upstream=False)
	project = root / 'code/proj'
	assert _git(project, 'rev-parse', '@{upstream}').returncode != 0, 'setup is wrong'

	said = roundup.sweep(root)

	assert '1 pushed' in said, said
	assert _git(project, 'rev-parse', '@{upstream}').returncode == 0, (
		'the branch was pushed without being given an upstream, so the next close goes blind again')


def test_a_code_project_leaves_the_close_with_main_on_develop(tmp_path, roundup) -> None:
	"""close/branches.py has always said code/* projects promote. This is the caller saying it too."""
	root = _gitflow_workspace(tmp_path)
	project = root / 'code/proj'
	assert _git(project, 'rev-list', '--count', 'main..develop').stdout.strip() == '1', 'setup'

	roundup.sweep(root)

	assert _git(project, 'rev-list', '--count', 'main..develop').stdout.strip() == '0'
	assert _git(project, 'rev-parse', 'origin/main').stdout == _git(
		project, 'rev-parse', 'develop').stdout, 'main was merged and never pushed'
