# T1 the branch lock (core/hooks/git/SPECS.md): one agent session per repo, people never gated.
# Zero-token, no network — every case builds a throwaway repo whose GitHub origin is rewritten to a
# local bare repo, so `governed` sees the profile's owner and every push lands on disk.
import json
import os
import re
import subprocess
import sys
import threading

import pytest

from conftest import WORKSPACE_ROOT, governed_repo, run

sys.path[:0] = [str(WORKSPACE_ROOT / 'core/hooks/git')]
import lock  # noqa: E402

A, B = 'test-lock-session-a', 'test-lock-session-b'
GATE = WORKSPACE_ROOT / 'core/hooks/git/lock-gate.py'
@pytest.fixture(autouse=True)
def _drop_locks(tmp_path):
    yield
    for path in lock.lock_file(WORKSPACE_ROOT).parent.glob('lock_*'):
        if re.sub(r'[^A-Za-z0-9]', '_', str(tmp_path.resolve())) in path.name:
            path.unlink(missing_ok=True)


def test_a_first_write_takes_a_clean_develop(tmp_path):
    repo = governed_repo(tmp_path)
    refusal, note = lock.verdict(repo / 'core/x.py', A)
    branch = run(repo, 'branch', '--show-current')
    assert not refusal and branch.startswith('feature/core-') and A in note
    assert lock.holder(repo) == (A, branch) and repo.resolve() in lock.held_by(A)


def test_another_session_is_refused_until_claim(tmp_path):
    repo = governed_repo(tmp_path)
    lock.verdict(repo / 'a.md', A)
    refusal, _ = lock.verdict(repo / 'a.md', B)
    assert 'held by session' in refusal and f'claim {repo}' in refusal
    lock.claim(repo, B)
    assert lock.verdict(repo / 'a.md', B) == ('', '') and lock.verdict(repo / 'a.md', A)[0]


def test_two_racing_sessions_get_one_lock(tmp_path):
    repo = governed_repo(tmp_path)
    results = {}
    threads = [threading.Thread(target=lambda s=s: results.update({s: lock.verdict(repo / 'a', s)[0]}))
               for s in (A, B)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(bool(r) for r in results.values()) == [False, True]
    assert len(run(repo, 'branch', '--list', 'feature/*').splitlines()) == 1


def test_an_own_switch_is_followed_and_a_shared_branch_is_not(tmp_path):
    repo = governed_repo(tmp_path)
    lock.verdict(repo / 'a', A)
    run(repo, 'branch', '-m', 'feature/renamed')
    assert lock.verdict(repo / 'a', A) == ('', '') and lock.holder(repo)[1] == 'feature/renamed'
    run(repo, 'switch', '-q', 'develop')
    assert 'switch feature/renamed' in lock.verdict(repo / 'a', A)[0]


def test_an_unheld_feature_and_stray_dirt_are_refused(tmp_path):
    repo = governed_repo(tmp_path)
    (repo / 'README.md').write_text('someone else\n', encoding='utf-8', newline='\n')
    assert 'nobody holds' in lock.verdict(repo / 'a', A)[0]
    run(repo, 'checkout', '-q', '--', '.')
    run(repo, 'switch', '-q', '-c', 'feature/orphan')
    assert 'held by nobody' in lock.verdict(repo / 'a', A)[0]


def test_outside_scope_nothing_is_gated(tmp_path):
    repo = governed_repo(tmp_path)
    run(repo, 'remote', 'set-url', 'origin', 'https://github.com/someone-else/x.git')
    assert lock.verdict(repo / 'a', A) == ('', '')
    trunk = tmp_path / 'trunk'
    subprocess.run(['git', 'init', '-q', '-b', 'main', str(trunk)], check=True)
    assert lock.verdict(trunk / 'a', A) == ('', '')


def _gate(payload):
    return subprocess.run([sys.executable, str(GATE)], input=json.dumps(payload),
                          capture_output=True, text=True, encoding='utf-8')


def test_an_agent_commit_on_develop_is_refused_at_the_shell(tmp_path):
    repo = governed_repo(tmp_path)
    done = _gate({'tool_name': 'Bash', 'session_id': A, 'cwd': str(tmp_path),
                  'tool_input': {'command': f'cd {repo} && git commit -qm x'}})
    assert done.returncode == 2 and 'shared branch' in done.stderr
    # A read whose name merely starts with a history verb is not one (merge-base, 2026-11-19).
    read = _gate({'tool_name': 'Bash', 'session_id': A, 'cwd': str(tmp_path),
                  'tool_input': {'command': f'git -C {repo} merge-base develop develop'}})
    assert read.returncode == 0, read.stderr


def test_a_person_commits_on_develop_and_an_agent_cannot(tmp_path):
    repo = governed_repo(tmp_path)
    env = {k: v for k, v in os.environ.items() if k not in lock.SESSION_ENV}
    hooks = ['-c', f'core.hooksPath={WORKSPACE_ROOT / "core/hooks"}']
    (repo / 'b.md').write_text('# B\n', encoding='utf-8', newline='\n')
    run(repo, 'add', 'b.md')
    person = subprocess.run(['git', *hooks, 'commit', '-qm', 'person'], cwd=repo, env=env,
                            capture_output=True, text=True, encoding='utf-8')
    assert person.returncode == 0, person.stdout + person.stderr
    (repo / 'c.md').write_text('# C\n', encoding='utf-8', newline='\n')
    run(repo, 'add', 'c.md')
    agent = subprocess.run(['git', *hooks, 'commit', '-qm', 'agent'], cwd=repo,
                           env={**env, 'CLAUDE_CODE_SESSION_ID': A}, capture_output=True, text=True, encoding='utf-8')
    assert agent.returncode != 0 and 'BRANCH LOCK' in agent.stdout + agent.stderr
