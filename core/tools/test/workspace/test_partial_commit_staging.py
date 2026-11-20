# T0 commit hygiene: a PARTIAL commit (`git commit -- <paths>`) must never gain a file the committer
# did not name. The generators that stage an aggregate (ISSUES.md, GOALS.md, .gitignore) used to
# `git add` it regardless, so a commit of one file carried someone else's regenerated list.
#
# Real git, real hook: a throwaway repo whose pre-commit hook writes ISSUES.md and calls `stage`.
# The global core.hooksPath is the workspace pipeline and must never fire in the fixture, so every
# commit here passes its own -c core.hooksPath.
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import HOOKS

sys.path.insert(0, str(HOOKS / 'commit'))
import pre_commit  # noqa: E402


def _git(repo: Path, *args: str, hooks: Path | None = None) -> str:
    base = ['git', '-C', str(repo), '-c', f'core.hooksPath={hooks or repo / "nohooks"}']
    return subprocess.run([*base, *args], capture_output=True, text=True, check=True,
                          encoding='utf-8').stdout


def _repo(tmp_path: Path, hook_body: str) -> tuple[Path, Path]:
    repo = tmp_path / 'repo'
    (repo / 'nohooks').mkdir(parents=True)
    _git(repo, 'init', '-q')
    _git(repo, 'config', 'user.name', 't')
    _git(repo, 'config', 'user.email', 't@t')
    (repo / 'ISSUES.md').write_text('original\n', encoding='utf-8', newline='\n')
    (repo / 'a.txt').write_text('one\n', encoding='utf-8', newline='\n')
    (repo / '.gitignore').write_text('core/*\n', encoding='utf-8', newline='\n')
    (repo / 'core/newdir').mkdir(parents=True)
    (repo / 'core/newdir/CONTEXT.md').write_text('x\n', encoding='utf-8', newline='\n')
    _git(repo, 'add', '-f', '-A')
    _git(repo, 'commit', '-q', '-m', 'init')
    hooks = tmp_path / 'hooks'
    hooks.mkdir()
    script = tmp_path / 'hook.py'
    script.write_text(
        f'import sys\nfrom pathlib import Path\n'
        f'sys.path[:0] = [{str(HOOKS)!r}, {str(HOOKS / "commit")!r}, {str(HOOKS / "git")!r}]\n'
        f'from pre_commit import stage\n{hook_body}\n', encoding='utf-8', newline='\n')
    hook = hooks / 'pre-commit'
    hook.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}"\n', encoding='utf-8', newline='\n')
    hook.chmod(0o755)
    return repo, hooks


def _issues_hook(named_only: bool) -> str:
    return ("Path('ISSUES.md').write_text('regenerated\\n', encoding='utf-8', newline='\\n')\n"
            f"stage(Path.cwd(), 'ISSUES.md', named_only={named_only})")


def _commit(repo: Path, hooks: Path, *args: str) -> str:
    _git(repo, 'commit', '-q', '-m', 'x', *args, hooks=hooks)
    return _git(repo, 'show', 'HEAD:ISSUES.md')


def _edit_a(repo: Path) -> None:
    (repo / 'a.txt').write_text('two\n', encoding='utf-8', newline='\n')


def test_a_partial_commit_does_not_gain_the_regenerated_list(tmp_path):
    repo, hooks = _repo(tmp_path, _issues_hook(True))
    _edit_a(repo)
    assert _commit(repo, hooks, '--', 'a.txt') == 'original\n'


def test_without_named_only_the_fixture_does_reach_the_bug(tmp_path):
    """The control: if this passed trivially the test above would prove nothing."""
    repo, hooks = _repo(tmp_path, _issues_hook(False))
    _edit_a(repo)
    assert _commit(repo, hooks, '--', 'a.txt') == 'regenerated\n'


def test_a_full_commit_still_carries_the_regenerated_list(tmp_path):
    repo, hooks = _repo(tmp_path, _issues_hook(True))
    _edit_a(repo)
    _git(repo, 'add', 'a.txt')
    assert _commit(repo, hooks) == 'regenerated\n'


def test_commit_dash_a_still_carries_the_regenerated_list(tmp_path):
    repo, hooks = _repo(tmp_path, _issues_hook(True))
    _edit_a(repo)
    assert _commit(repo, hooks, '-a') == 'regenerated\n'


def test_a_partial_commit_that_names_the_list_gets_it_regenerated(tmp_path):
    repo, hooks = _repo(tmp_path, _issues_hook(True))
    _edit_a(repo)
    (repo / 'ISSUES.md').write_text('user\n', encoding='utf-8', newline='\n')
    assert _commit(repo, hooks, '--', 'a.txt', 'ISSUES.md') == 'regenerated\n'


@pytest.mark.parametrize('value, expected', [
    (None, False),
    ('.git/index', False),
    ('/x/.git/index.lock', False),
    ('/x/.git/next-index-123.lock', True),
])
def test_is_partial_reads_the_index_file_the_hook_was_handed(monkeypatch, value, expected):
    if value is None:
        monkeypatch.delenv('GIT_INDEX_FILE', raising=False)
    else:
        monkeypatch.setenv('GIT_INDEX_FILE', value)
    assert pre_commit.is_partial() is expected


def test_a_partial_commit_does_not_gain_the_healed_gitignore(tmp_path):
    body = ("import gitignore_heal\n"
            "gitignore_heal._add_missing_lines(Path.cwd(), Path.cwd() / '.gitignore')")
    repo, hooks = _repo(tmp_path, body)
    _edit_a(repo)
    _git(repo, 'commit', '-q', '-m', 'x', '--', 'a.txt', hooks=hooks)
    assert '!core/newdir/' not in _git(repo, 'show', 'HEAD:.gitignore')
    _edit_a(repo)
    _git(repo, 'commit', '-q', '-a', '-m', 'y', hooks=hooks)
    assert '!core/newdir/' in _git(repo, 'show', 'HEAD:.gitignore')


def _recorder(calls):
    return lambda *paths, **kw: calls.append(kw)


def test_the_brain_dashboard_asks_for_named_only(monkeypatch, tmp_path):
    import brain_stats
    goal = tmp_path / 'g.md'
    goal.write_text('g\n', encoding='utf-8', newline='\n')
    calls = []
    monkeypatch.setattr(brain_stats, 'load_goal_files', lambda: {'g': goal})
    monkeypatch.setattr(brain_stats, 'Attention', lambda _f: SimpleNamespace(missing=[]))
    monkeypatch.setattr(brain_stats, 'staged_goal_files', lambda _f: {})
    monkeypatch.setattr(brain_stats.feature_law, 'is_enabled', lambda *_: False)
    monkeypatch.setattr(brain_stats, 'GOALS_FILE', goal)
    monkeypatch.setattr(brain_stats, 'check_compass_reminder', lambda: None)
    monkeypatch.setattr(brain_stats, 'git', lambda *a, **k: '')
    monkeypatch.setattr(brain_stats, 'stage', lambda *a, **k: calls.append(k), raising=False)
    brain_stats.pre_commit()
    assert calls and calls[0].get('named_only') is True


def test_the_brain_dashboard_really_reaches_the_index(monkeypatch, tmp_path):
    """The real `git add`, from the brain repo's root (2026-11-06; brain/ its own repo 2026-11-19).

    A path that did not start where the add ran once failed in silence, leaving the stats on disk
    only. The test above mocks `stage`, which is how it missed that.
    """
    import brain_stats
    repo, _hooks = _repo(tmp_path, '')
    goals = Path('GOALS.md')
    (repo / goals).write_text('old\n', encoding='utf-8', newline='\n')
    _git(repo, 'add', str(goals))
    _git(repo, 'commit', '-q', '-m', 'goals')
    monkeypatch.chdir(repo)
    monkeypatch.delenv('GIT_INDEX_FILE', raising=False)

    def regenerate(*_a):
        goals.write_text('regenerated\n', encoding='utf-8', newline='\n')
    monkeypatch.setattr(brain_stats, 'load_goal_files', lambda: {'g': goals})
    monkeypatch.setattr(brain_stats, 'Attention', lambda _f: SimpleNamespace(missing=[]))
    monkeypatch.setattr(brain_stats, 'staged_goal_files', lambda _f: {})
    monkeypatch.setattr(brain_stats.feature_law, 'is_enabled', lambda *_: True)
    monkeypatch.setattr(brain_stats, 'update_goals_md', regenerate)
    monkeypatch.setattr(brain_stats, 'update_goals_table', lambda *_a: None)
    monkeypatch.setattr(brain_stats, 'GOALS_FILE', goals)
    monkeypatch.setattr(brain_stats, 'check_compass_reminder', lambda: None)
    brain_stats.pre_commit()
    assert _git(repo, 'diff', '--name-only').strip() == ''
    assert _git(repo, 'diff', '--cached', '--name-only').strip() == 'GOALS.md'


def test_a_failed_stage_says_so(tmp_path, capsys):
    repo, _hooks = _repo(tmp_path, '')
    pre_commit.stage(repo, 'brain/brain/GOALS.md')
    assert 'could not stage brain/brain/GOALS.md' in capsys.readouterr().err
