#!/usr/bin/env python3
# SessionStart — warn Lucas + agent when brain/INBOX.md has piled up past a threshold,
# so capture doesn't silently grow and scatter. The drain runs HERE, at session start where context
# is cheap — /roundup only counts, and hands /inbox to the next session (core/skills/roundup.md § Phase 3).
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from platform_law import WORKSPACE_ROOT  # noqa: E402

INBOX = WORKSPACE_ROOT / 'brain/INBOX.md'
WARN_AT = 15
LOUD_AT = 25
STALE_DAYS = 10


def read_body(text):
    marker = '<!-- add entries below'
    idx = text.find(marker)
    if idx == -1:
        return text
    nl = text.find('\n', idx)
    body = text[nl + 1:] if nl != -1 else ''
    return body


def count_entries(body):
    blocks = re.split(r'\n\s*\n', body)
    entries = []
    for block in blocks:
        stripped = block.strip()
        is_empty = not stripped
        is_comment = stripped.startswith('<!--')
        is_rule = stripped == '---'
        skip = is_empty or is_comment or is_rule
        if not skip:
            entries.append(stripped)
    return len(entries)


def main():
    if not feature_law.is_enabled('inbox-nudge'):
        return 0  # switched off: capture still lands, nothing says the queue has piled up
    exists = os.path.exists(INBOX)
    if not exists:
        return 0
    with open(INBOX, encoding='utf-8') as f:
        text = f.read()
    body = read_body(text)
    n = count_entries(body)
    if n < WARN_AT:
        return 0
    age_days = (time.time() - os.path.getmtime(INBOX)) / 86400
    level = 'LOUD' if n >= LOUD_AT else 'warn'
    lines = []
    lines.append(f'INBOX-NUDGE [{level}]: brain/INBOX.md holds {n} untriaged entries '
                 f'(threshold {WARN_AT}; last touched {age_days:.0f}d ago).')
    lines.append('Tell Lucas at the start of your reply and offer to run /inbox.')
    sys.stdout.write('\n'.join(lines) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
