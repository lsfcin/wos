#!/usr/bin/env python3
# SessionStart — the soft reminders, in one voice: what has piled up, what has gone unreviewed, and
# what has not reached the public repo. One file, three switches, and at most one message.
#
# THREE FILES BECAME ONE ON 2026-09-17, and the reason is in the prose the third would have copied.
# compass-nudge.py ended with an instruction to the agent: *"if the INBOX nudge already fired, fold
# both into a single gentle line (never stack nudges)"* — a structural problem being solved by
# asking a model nicely, once per sibling, and an instruction that gets weaker with every nudge
# added. Here the folding is the code: main() collects and prints ONCE. Adding a fourth costs a
# function, not another plea.
#
# It also paid for itself. core/hooks/session/ was at the crowding signal, and the honest options
# were split the directory, grow a baseline the check says may only shrink, or stop writing one file
# per reminder. Three reminders were never three responsibilities.
#
# TONE IS LOAD-BEARING AND LIVES IN brain/FOUNDATIONS.md — *what has good wind*, never guilt. A
# nudge is ignorable by design: it says the number and offers the command, and never asks twice.
import os
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from platform_law import WORKSPACE_ROOT  # noqa: E402

INBOX = WORKSPACE_ROOT / 'brain/INBOX.md'
INBOX_WARN, INBOX_LOUD = 15, 25
COMPASS_LOG = WORKSPACE_ROOT / 'brain/.log/compass-last.txt'
COMPASS_STALE_DAYS = 14   # ~2x/month rhythm; below this, stay silent
PUBLISH_WARN = 5


def read_body(text: str) -> str:
    marker = '<!-- add entries below'
    idx = text.find(marker)
    if idx == -1:
        return text
    nl = text.find('\n', idx)
    return text[nl + 1:] if nl != -1 else ''


def count_entries(body: str) -> int:
    """Blank lines separate entries; comments and rules are scaffolding, not capture."""
    entries = []
    for block in re.split(r'\n\s*\n', body):
        stripped = block.strip()
        if stripped and not stripped.startswith('<!--') and stripped != '---':
            entries.append(stripped)
    return len(entries)


def inbox() -> str:
    """How much untriaged capture is waiting, and how long it has been waiting.

    The drain runs at session START, where context is cheap — /roundup only counts and hands /inbox
    to the next session (core/skills/roundup.md § Phase 3).
    """
    if not os.path.exists(INBOX):
        return ''
    n = count_entries(read_body(INBOX.read_text(encoding='utf-8')))
    if n < INBOX_WARN:
        return ''
    age = (time.time() - os.path.getmtime(INBOX)) / 86400
    level = 'LOUD' if n >= INBOX_LOUD else 'warn'
    return (f'INBOX [{level}]: {n} untriaged entries in brain/INBOX.md '
            f'(threshold {INBOX_WARN}; last touched {age:.0f}d ago) — offer /inbox.')


def compass() -> str:
    """How long since the strategic review, so the inspiring work waiting can resurface."""
    if not os.path.exists(COMPASS_LOG):
        return ''
    try:
        last = date.fromisoformat(COMPASS_LOG.read_text(encoding='utf-8').strip())
    except (ValueError, OSError):
        return ''   # an unreadable log is not a reason to say anything at all
    days = (date.today() - last).days
    if days < COMPASS_STALE_DAYS:
        return ''
    return f'COMPASS: last review was {days}d ago — offer /compass when it feels right.'


def _git(*args, cwd=WORKSPACE_ROOT) -> str:
    done = subprocess.run(['git', '-C', str(cwd), *args], capture_output=True,
                          text=True, encoding='utf-8', errors='replace')
    return done.stdout.strip() if done.returncode == 0 else ''


def publish() -> str:
    """Work that landed here and has not reached the repo his students clone.

    ASKED OF GIT, NOT OF THE SYNC. The honest question — which crossing files differ — is
    `publish/repo --check`, and it walks 1150 files for 3.1 s. A SessionStart is paid by EVERY
    session (core/experiments/hook-latency.md), so three seconds to tell most of them nothing is not
    a price this may charge. Two `git log` calls cost 16 ms and answer what a NUDGE needs: has work
    landed that COULD have crossed. /roundup asks the exact question once, at the end.

    The target's last commit is the timestamp, because the target is rebuilt and never edited: its
    history IS the publish log, so no state file of ours has to be kept in step with it. Scoped to
    the floor's own roots, so a session spent entirely in brain/ or academy/ stays silent.
    """
    sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools/wos/publish'))
    import crossing  # noqa: PLC0415 — only reached when the switch is on
    floor = crossing.floor()
    if not floor.target.is_dir():
        return ''
    last = _git('log', '-1', '--format=%cI', cwd=floor.target)
    if not last:
        return ''
    log = _git('log', f'--since={last}', '--format=%h', '--',
               *(floor.roots + floor.files + floor.trees))
    behind = len(log.split('\n')) if log else 0
    if behind < PUBLISH_WARN:
        return ''
    return (f'PUBLISH: {behind} commits have touched trees that cross since the public repo was '
            f'last rebuilt — the improvements are written but have not reached the clone. '
            f'Offer /publish.')


# Feature name → the question it asks. The registry switches each one independently, which is what
# keeps three reminders in one file from becoming one feature with three reasons.
ASKS = (('inbox-nudge', inbox), ('compass-nudge', compass), ('publish-nudge', publish))


def main() -> int:
    said = [text for name, ask in ASKS
            if feature_law.is_enabled(name) and (text := ask())]
    if not said:
        return 0
    sys.stdout.write('NUDGE — mention what fits, in ONE gentle line, and never insist:\n'
                     + '\n'.join(f'  {line}' for line in said) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
