#!/usr/bin/env python3
# The dashboard's own history: one `date<TAB>count` line per run, in this machine's state.
#
# "Entropy is flat" was true every session because each compared itself only to the session before,
# where the delta really is +-1, while the count went ~94 -> 440 in four days. So the header asks
# where the count stood N days ago. It used to re-derive that from the committed ISSUES.md block;
# the block left git on 2026-11-19 (core/hooks/git/SPECS.md § Close), so the history is a file.
from datetime import date, datetime, timedelta
from pathlib import Path

WINDOW_DAYS = 12


def record(history: Path, count: int, today: date = None) -> None:
    history.parent.mkdir(parents=True, exist_ok=True)
    with history.open('a', encoding='utf-8', newline='\n') as handle:
        handle.write(f'{today or date.today()}\t{count}\n')


def baseline(history: Path, window_days: int = WINDOW_DAYS, today: date = None) -> tuple | None:
    """(date, count) of the oldest run inside the window, or None."""
    since = (today or date.today()) - timedelta(days=window_days)
    rows = [line.split('\t') for line in history.read_text(encoding='utf-8').splitlines()] \
        if history.is_file() else []
    inside = [(day, int(n)) for day, n in rows if datetime.strptime(day, '%Y-%m-%d').date() >= since]
    return inside[0] if inside else None


def format_trend(current: int, base: tuple | None, today: date = None) -> str:
    """The header suffix, e.g. ' (2026-08-13: 94 · +672 over 11 days)' — '' with no baseline."""
    if base is None:
        return ''
    base_date, base_count = base
    days = ((today or date.today()) - datetime.strptime(base_date, '%Y-%m-%d').date()).days
    delta = current - base_count
    return f' ({base_date}: {base_count} · {"+" if delta >= 0 else ""}{delta} over {days} days)'
