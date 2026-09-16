# B5 regression — the list's writer owns its artifact, so a written list is never left loose.
#
# 26 nested repos carried untracked ISSUES.md lists nobody ever committed: invisible to clones,
# to history, and to anyone who did not run the dashboard locally — the findings were addressed to
# readers who could not see them. That is the law, and it still holds.
#
# WHAT CHANGED 2026-09-04 (Lucas's ruling): the writer is no longer the workspace root reaching in
# from outside. The root used to scan every nested repo and commit a list into each one behind
# the session — commits nobody typed, so nobody pushed them
# (b20260831-scattered-lists-never-push). Now each repo's OWN pre-commit writes its own list
# and STAGES it, so it rides the commit the operator is already making: one repo, one session, one
# commit, and no artifact left loose. The push half of that ruling lives in core/tools/wos/roundup.
import os
import subprocess
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/commit'))
import generators  # noqa: E402
from pre_commit import Commit  # noqa: E402

ENV = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
       'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}


def _git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True,
                          encoding='utf-8', env=ENV)


def _repo(tmp_path) -> Path:
    """A throwaway repo with one tracked file. Nothing here touches the real workspace."""
    repo = tmp_path / 'proj'
    repo.mkdir(parents=True)
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    (repo / 'file.py').write_text('# a file\nx = 1\n', encoding='utf-8', newline='\n')
    _git(repo, 'add', '.')
    _git(repo, 'commit', '-qm', 'init', '--no-verify')
    return repo


def _commit(repo: Path) -> Commit:
    return Commit(root=WORKSPACE_ROOT, toplevel=repo, staged=['file.py'])


def test_the_repo_writes_its_own_list_and_stages_it(tmp_path):
    """Written AND staged, in one stage: an artifact the writer leaves loose is B5 all over again."""
    repo = _repo(tmp_path)
    generators.issues(_commit(repo))

    issues = repo / 'ISSUES.md'
    assert issues.is_file(), 'the repo wrote no issues of its own'
    staged = _git(repo, 'diff', '--cached', '--name-only').stdout.split()
    assert 'ISSUES.md' in staged, 'the issues was written and left out of the commit under way'


def test_the_list_says_it_is_about_this_repo(tmp_path):
    """Each list reports ITS OWN repo. A local file stating a workspace-wide total was the
    self-description failure this scatter was rebuilt to end."""
    repo = _repo(tmp_path)
    generators.issues(_commit(repo))
    text = (repo / 'ISSUES.md').read_text(encoding='utf-8')
    assert 'findings here' in text
    assert 'more across' not in text, 'a repo may not report on repos it cannot see'


def test_writing_a_list_never_refuses_the_commit(tmp_path):
    """Ruled: writes and warns. A gate here would refuse a commit over debt it did not create."""
    repo = _repo(tmp_path)
    generators.issues(_commit(repo))  # raising Blocked would fail this test by escaping
    generators.issues(_commit(repo))  # and a second run over its own output must be stable too
