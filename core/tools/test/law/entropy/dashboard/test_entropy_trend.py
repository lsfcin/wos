# T0 the entropy trend (core/hooks/entropy/dashboard/entropy_trend.py): a bare count let every
# session write "flat" while the real number climbed, so the header carries a baseline instead.
# Zero-token, runs in verify-fast.
#
# The window and the rename are the two things to get right — a baseline picked from outside the
# window is invented, and one that stops at entropy.md -> ISSUES.md is the same blindness the
# original bug had, in a new place. Both are asserted here against a throwaway repo, the same
# pattern test_branch_debt.py uses for its own git-reading checks.
import os
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest

from entropy_trend import baseline, format_trend


def git(repo: Path, *args):
    subprocess.run(['git', '-C', str(repo), *args], check=True,
                   capture_output=True, text=True, encoding='utf-8')


def commit(repo: Path, files: dict, days_ago: int):
    """One commit writing every path in `files`, dated `days_ago` days before now."""
    for name, content in files.items():
        (repo / name).write_text(content, encoding='utf-8', newline='\n')
        git(repo, 'add', name)
    when = f'{(date.today() - timedelta(days=days_ago)).isoformat()}T12:00:00'
    subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'x', '--no-verify'],
                   check=True, capture_output=True, text=True,
                   env={**os.environ, 'GIT_AUTHOR_DATE': when, 'GIT_COMMITTER_DATE': when}, encoding='utf-8')


@pytest.fixture
def repo(tmp_path):
    subprocess.run(['git', 'init', '-q', '-b', 'main', str(tmp_path)], check=True)
    git(tmp_path, 'config', 'user.email', 'test@test')
    git(tmp_path, 'config', 'user.name', 'test')
    commit(tmp_path, {'README.md': 'x\n'}, days_ago=30)
    return tmp_path


def test_no_matching_revision_is_no_baseline(repo):
    """Neither tracked file has ever stated a count — inventing a trend here would be worse
    than printing none."""
    assert baseline(repo) is None


def test_a_revision_outside_the_window_is_not_a_baseline(repo):
    commit(repo, {'entropy.md': '50 findings here\n'}, days_ago=15)
    assert baseline(repo, window_days=12) is None


def test_the_oldest_revision_inside_the_window_is_the_baseline(repo):
    commit(repo, {'entropy.md': '50 findings here\n'}, days_ago=10)
    commit(repo, {'entropy.md': '80 findings here\n'}, days_ago=5)
    found_date, found_count = baseline(repo, window_days=12)
    assert found_date == (date.today() - timedelta(days=10)).isoformat()
    assert found_count == 50


def test_the_baseline_spans_the_rename_from_entropy_md_to_issues_md(repo):
    """The count lived in entropy.md until 2026-08-19 and in ISSUES.md after — a window that
    stops at the rename would report a baseline from the wrong side of it."""
    commit(repo, {'entropy.md': '50 findings here\n'}, days_ago=10)
    git(repo, 'rm', '-q', 'entropy.md')
    commit(repo, {'ISSUES.md': '80 findings here\n'}, days_ago=5)
    found_date, found_count = baseline(repo, window_days=12)
    assert found_date == (date.today() - timedelta(days=10)).isoformat()
    assert found_count == 50


def test_issues_md_wins_over_entropy_md_in_the_same_revision(repo):
    """Where a single commit carries both, the live name states the current number."""
    commit(repo, {'entropy.md': '999 findings here\n', 'ISSUES.md': '50 findings here\n'}, days_ago=5)
    _, found_count = baseline(repo, window_days=12)
    assert found_count == 50


def test_a_smaller_window_excludes_a_revision_the_default_keeps(repo):
    commit(repo, {'entropy.md': '50 findings here\n'}, days_ago=10)
    assert baseline(repo) is not None
    assert baseline(repo, window_days=3) is None


def test_format_trend_prints_the_dated_baseline_and_the_day_delta():
    trend = format_trend(766, ('2026-08-13', 94), today=date(2026, 8, 24))
    assert trend == ' (2026-08-13: 94 · +672 over 11 days)'


def test_format_trend_marks_a_falling_count_without_a_plus_sign():
    trend = format_trend(50, ('2026-08-01', 94), today=date(2026, 8, 24))
    assert trend == ' (2026-08-01: 94 · -44 over 23 days)'


def test_format_trend_with_no_baseline_is_the_empty_string():
    assert format_trend(100, None) == ''


def test_the_trend_flows_into_the_rendered_header():
    """The point of the whole change: the header line the dashboard writes actually carries
    the trend text, not just the function that formats it."""
    from entropy_report import SECTIONS, render
    findings = {key: [] for key, _, _ in SECTIONS}
    block = render(findings, scanned=10, root=Path('/x'),
                   trend=' (2026-08-13: 94 · +672 over 11 days)')
    assert '**0 findings here** (2026-08-13: 94 · +672 over 11 days)' in block


def test_no_trend_argument_leaves_the_bare_count_unwriteable_as_flat():
    """Default trend is '' — a caller that forgets to pass one gets the bare count, not a
    silently wrong trend."""
    from entropy_report import SECTIONS, render
    findings = {key: [] for key, _, _ in SECTIONS}
    block = render(findings, scanned=10, root=Path('/x'))
    assert '**0 findings here**\n' in block
