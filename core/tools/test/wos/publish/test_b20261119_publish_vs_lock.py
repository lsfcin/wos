# b20261119-publish-vs-lock regression — the sync takes the target's branch lock and gives it back.
#
# push() used to branch the target itself, after the sync had already dirtied develop. Every refused
# commit left a feature/sync-* that nobody held, which the lock then refused to everyone: code/wos
# sat on one for 18 days. Now the sync's first write takes the lock like any other, and a push that
# lands returns the repo to develop, deletes the branch on both sides and drops the lock.
import importlib.machinery
import importlib.util
import re
import types

import pytest

from conftest import WORKSPACE_ROOT, governed_repo, run

LOADER = importlib.machinery.SourceFileLoader(
    'publish_repo', str(WORKSPACE_ROOT / 'core/tools/wos/publish/repo'))
publish = importlib.util.module_from_spec(importlib.util.spec_from_loader(LOADER.name, LOADER))
LOADER.exec_module(publish)
SESSION = 'test-publish-session'


@pytest.fixture
def target(tmp_path, monkeypatch):
    repo = governed_repo(tmp_path)
    run(repo, 'config', 'core.hooksPath', '/dev/null')
    run(repo, 'branch', 'master')
    run(repo, 'push', '-q', 'origin', 'master')
    monkeypatch.setenv('CLAUDE_CODE_SESSION_ID', SESSION)
    yield types.SimpleNamespace(target=repo)
    for path in publish.lock.lock_file(WORKSPACE_ROOT).parent.glob('lock_*'):
        if re.sub(r'[^A-Za-z0-9]', '_', str(tmp_path.resolve())) in path.name:
            path.unlink(missing_ok=True)


def test_the_sync_takes_the_lock_before_its_first_byte(target):
    assert publish._take(target) == 0
    branch = run(target.target, 'branch', '--show-current')
    assert branch.startswith('feature/sync-')
    assert publish.lock.holder(target.target) == (SESSION, branch)


def test_a_landed_push_leaves_the_repo_free(target):
    publish._take(target)
    branch = run(target.target, 'branch', '--show-current')
    (target.target / 'new.md').write_text('crossed\n', encoding='utf-8', newline='\n')
    assert publish.push(target) == 0
    assert run(target.target, 'branch', '--show-current') == 'develop'
    assert not run(target.target, 'branch', '--list', branch)
    assert not run(target.target, 'ls-remote', '--heads', 'origin', branch)
    assert publish.lock.holder(target.target) == ('', '')
    for into in publish.FLOW:
        assert 'new.md' in run(target.target, 'ls-tree', '--name-only', f'origin/{into}')
