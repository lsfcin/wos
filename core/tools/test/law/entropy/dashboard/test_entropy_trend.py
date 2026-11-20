# T0 the entropy trend (core/hooks/entropy/dashboard/entropy_trend.py): a bare count let every
# session write "flat" while the real number climbed, so the header carries a baseline instead.
# Zero-token, runs in verify-fast. The window is the thing to get right: a baseline from outside
# it is invented.
from datetime import date
from pathlib import Path

from entropy_trend import baseline, format_trend, record

TODAY = date(2026, 8, 24)


def test_no_history_is_no_baseline(tmp_path):
    assert baseline(tmp_path / 'h.tsv', today=TODAY) is None


def test_the_oldest_run_inside_the_window_is_the_baseline(tmp_path):
    history = tmp_path / 'h.tsv'
    for day, count in ((date(2026, 8, 1), 9), (date(2026, 8, 14), 94), (date(2026, 8, 20), 120)):
        record(history, count, today=day)
    assert baseline(history, window_days=12, today=TODAY) == ('2026-08-14', 94)
    assert baseline(history, window_days=3, today=TODAY) is None


def test_format_trend_prints_the_dated_baseline_and_the_day_delta():
    assert format_trend(766, ('2026-08-13', 94), today=TODAY) == ' (2026-08-13: 94 · +672 over 11 days)'
    assert format_trend(50, ('2026-08-01', 94), today=TODAY) == ' (2026-08-01: 94 · -44 over 23 days)'
    assert format_trend(100, None) == ''


def test_the_trend_flows_into_the_rendered_header():
    from entropy_report import SECTIONS, render
    findings = {key: [] for key, _, _ in SECTIONS}
    page = render(findings, scanned=10, root=Path('/x'), trend=' (2026-08-13: 94 · +672 over 11 days)')
    assert '**0 findings here** (2026-08-13: 94 · +672 over 11 days)' in page
    assert '**0 findings here**\n' in render(findings, scanned=10, root=Path('/x'))
