#!/usr/bin/env python3
# The dashboard's own history, re-derived from git rather than stored.
#
# "Entropy is flat" was true every session because each one compared itself only to the session
# before it, where the delta really is +-1. The real count went ~94 -> 440 over four days and
# nobody re-checked the baseline before writing "flat" into the hand-off. This module asks a
# different question than the one that kept lying: not "did the count move since yesterday" but
# "where did it stand N days ago" — re-derived every run, never stored, from the two files the
# count has lived in: entropy.md until 2026-08-19, the entropy block of ISSUES.md after. Spanning
# both is deliberate — a trend that stops at a rename is the same blindness in a new place.
import re
import subprocess
from datetime import date, datetime
from pathlib import Path

WINDOW_DAYS = 12
# "findings here", not "findings": the header stopped charging this repo for the whole tree's
# count on 2026-08-25, and a baseline read in the old scope would print a 570-finding "drop" that
# nothing did. Revisions older than that state no comparable count, so the window returns None and
# the header prints a bare count until 12 days of same-scope history exist — which is this
# module's documented behaviour for a baseline it cannot compare against, not a regression.
_COUNT = re.compile(r'(\d+) findings here')
# ISSUES.md first: it is where the count lives today, and a commit that touches both in one
# revision states the current number there.
_PATHS = ('ISSUES.md', 'entropy.md')


def _git(root: Path, *args) -> str:
    done = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, encoding='utf-8')
    return done.stdout if done.returncode == 0 else ''


def _count_at(root: Path, commit: str) -> int | None:
    """The finding count a commit's tree states, checking ISSUES.md then entropy.md."""
    for path in _PATHS:
        shown = _git(root, 'show', f'{commit}:{path}')
        if match := _COUNT.search(shown):
            return int(match.group(1))
    return None


def baseline(root: Path, window_days: int = WINDOW_DAYS) -> tuple | None:
    """The oldest revision inside the window that states a count, as (date, count).

    None when nothing in the window states one — the header then prints the bare count rather
    than inventing a trend from a baseline outside the window it claims to be.
    """
    commits = _git(root, 'log', '--format=%h', f'--since={window_days} days ago',
                   '--', *_PATHS).split()
    oldest = None
    for commit in commits:  # git log is newest first; the last match found is the oldest revision
        if (count := _count_at(root, commit)) is not None:
            oldest = (commit, count)
    if oldest is None:
        return None
    commit, count = oldest
    commit_date = _git(root, 'log', '-1', '--format=%ad', '--date=short', commit).strip()
    return commit_date, count


def format_trend(current: int, base: tuple | None, today: date = None) -> str:
    """The header suffix, e.g. ' (2026-08-13: 94 · +672 over 11 days)' — '' with no baseline."""
    if base is None:
        return ''
    base_date, base_count = base
    since = today or date.today()
    days = (since - datetime.strptime(base_date, '%Y-%m-%d').date()).days
    delta = current - base_count
    sign = '+' if delta >= 0 else ''
    return f' ({base_date}: {base_count} · {sign}{delta} over {days} days)'
