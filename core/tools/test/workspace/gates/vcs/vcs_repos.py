# The git repos every vcs case needs, built once instead of per file.
#
# These were copied between test files until the duplication gate caught the second copy. A fixture
# that describes "a repo with a base commit" is the same sentence wherever it is asked for, and two
# copies drift the moment one case needs a config the other does not.
import subprocess
from pathlib import Path

import pytest


def git(repo: Path, *args):
	subprocess.run(['git', '-C', str(repo), *args], check=True,
	               capture_output=True, text=True, encoding='utf-8')


def commit(repo: Path, name: str):
	(repo / name).write_text(name, encoding='utf-8', newline='\n')
	git(repo, 'add', name)
	git(repo, 'commit', '-qm', name, '--no-verify')


@pytest.fixture
def repo(tmp_path):
	"""A repo with a `main` carrying one commit, ready to branch off."""
	subprocess.run(['git', 'init', '-q', '-b', 'main', str(tmp_path)], check=True)
	git(tmp_path, 'config', 'user.email', 'test@test')
	git(tmp_path, 'config', 'user.name', 'test')
	commit(tmp_path, 'base.txt')
	return tmp_path


@pytest.fixture
def cloned(repo, tmp_path_factory):
	"""A clone, so `origin/*` refs are real rather than simulated."""
	work = tmp_path_factory.mktemp('clone')
	subprocess.run(['git', 'clone', '-q', str(repo), str(work / 'r')], check=True)
	clone = work / 'r'
	git(clone, 'config', 'user.email', 'test@test')
	git(clone, 'config', 'user.name', 'test')
	return clone
