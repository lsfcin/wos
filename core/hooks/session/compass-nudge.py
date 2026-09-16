#!/usr/bin/env python3
# SessionStart — a soft, ignorable reminder that the compass review hasn't run in a while, so the
# inspiring work waiting can gently resurface. NOT a nag: one line, in-session only, trivial to skip.
# Paired with /compass (the gentle strategic review). Tone law lives in brain/FOUNDATIONS.md —
# "what has good wind", never guilt. Mirrors the inbox-nudge pattern.
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from platform_law import WORKSPACE_ROOT  # noqa: E402

COMPASS_LOG = WORKSPACE_ROOT / 'brain/.log/compass-last.txt'
STALE_DAYS = 14  # ~2x/month rhythm; below this, stay silent


def main():
    if not feature_law.is_enabled('compass-nudge'):
        return 0  # switched off: the strategic review goes unmentioned rather than unmentionable
    if not os.path.exists(COMPASS_LOG):
        return 0
    try:
        with open(COMPASS_LOG, encoding='utf-8') as f:
            last = date.fromisoformat(f.read().strip())
    except Exception:
        return 0
    days = (date.today() - last).days
    if days < STALE_DAYS:
        return 0
    lines = [
        f'COMPASS-NUDGE: last compass review was {days}d ago.',
        'Gently offer Lucas a /compass when it feels right — one soft line, no pressure. '
        'If the INBOX nudge already fired, fold both into a single gentle line (never stack nudges).',
    ]
    sys.stdout.write('\n'.join(lines) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
