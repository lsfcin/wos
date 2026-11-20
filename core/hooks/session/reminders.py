#!/usr/bin/env python3
# SessionStart — the soft reminders, in one voice: what has piled up, what has gone unreviewed, what
# has not reached the public repo, a disk filling up, and the PRs waiting on a watched repo. One file,
# five switches, and at most one message.
#
# THREE FILES BECAME ONE ON 2026-09-17, and the reason is in the prose the third would have copied.
# The compass file of the day ended with an instruction to the agent: *"if the INBOX one already
# fired, fold both into a single gentle line (never stack them)"* — a structural problem being
# solved by asking a model nicely, once per sibling, and an instruction that gets weaker with every
# sibling added. Here the folding is the code: main() collects and prints ONCE. Adding a fourth
# costs a function, not another plea.
#
# It also paid for itself. core/hooks/session/ was at the crowding signal, and the honest options
# were split the directory, grow a baseline the check says may only shrink, or stop writing one file
# per reminder. Three reminders were never three responsibilities.
#
# TONE IS LOAD-BEARING AND LIVES IN brain/FOUNDATIONS.md — *what has good wind*, never guilt. A
# reminder is ignorable by design: it says the number, offers the command, and never asks twice.
import json
import os
import re
import shutil
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
DISK_WARN, DISK_LOUD = 0.85, 0.95


def read_body(text: str) -> str:
    marker = '<!-- add entries below'
    idx = text.find(marker)
    if idx == -1:
        return text
    nl = text.find('\n', idx)
    return text[nl + 1:] if nl != -1 else ''


def count_entries(body: str) -> int:
    """Blank lines separate entries; comments and rules are structure, not capture."""
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
    a price this may charge. Two `git log` calls cost 16 ms and answer what a REMINDER needs: has work
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


def disk() -> str:
    """The partition holding ~ filling up, said before it is full rather than after.

    ASKED OF THE HOME DIRECTORY, NOT OF `/`: home is where every cache lands, it names a partition on
    every system, and on 2026-10-24 it was the one at 100% while the workspace beside it had 113 GB.
    """
    u = shutil.disk_usage(Path.home())
    if u.used / u.total < DISK_WARN:
        return ''
    level = 'LOUD' if u.used / u.total >= DISK_LOUD else 'warn'
    return (f'DISK [{level}]: the partition holding ~ is {u.used / u.total:.0%} full '
            f'({u.free / 1024 ** 3:.1f} GB free) — offer this system\'s leaf in core/tools/disk/ (diagnose, then clean).')


PR_STATE = WORKSPACE_ROOT / 'core/pr-reminder.json'   # per-machine, outside git (core/ is an allowlist)
PR_EVERY = 6 * 3600
PR_MARK = 'PR aberto em '


def _open_prs(repo: str) -> list | None:
    """The repo's open PRs, or None when gh cannot answer (offline, logged out): then nothing changes."""
    try:
        done = subprocess.run(['gh', 'pr', 'list', '-R', repo, '--state', 'open', '--json', 'number,title,author,url'],
                              capture_output=True, text=True, encoding='utf-8', timeout=8)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    try:
        return json.loads(done.stdout)
    except ValueError:
        return None


def prs(now: float | None = None) -> str:
    """Each open PR of a watched repo is one INBOX entry until it closes (Lucas, 2026-11-13).

    NOT TRIAGED, MIRRORED: the entry says what is waiting, and leaves by itself when the PR is merged
    or closed, so /inbox never has to route it. Asked of gh at most every six hours, because a
    SessionStart is paid by every session; a failed call keeps the INBOX as it was, so an offline
    session never deletes the entry of a PR that is still open. The repos are a profile setting
    (`pr-watch`, comma-separated), so the capability carries no one's repo name.
    """
    repos = [r.strip() for r in feature_law.setting('pr-watch').split(',') if r.strip()]
    now = time.time() if now is None else now
    try:
        state = json.loads(PR_STATE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        state = {}
    if not repos or now - state.get('checked', 0) < PR_EVERY or not INBOX.exists():
        return ''
    open_now = {}
    for repo in repos:
        found = _open_prs(repo)
        if found is None:
            return ''
        open_now.update({f'{PR_MARK}{repo} #{p["number"]}:': p for p in found})
    text = INBOX.read_text(encoding='utf-8')
    head, sep, body = text.partition('<!-- add entries below, newest first -->\n')
    blocks = [b.strip('\n') for b in re.split(r'\n\s*\n', body) if b.strip()]
    kept = [b for b in blocks if not b.startswith(PR_MARK) or b.split('"')[0].strip() in open_now]
    present = {b.split('"')[0].strip() for b in kept if b.startswith(PR_MARK)}
    today = date.fromtimestamp(now).isoformat()
    new = [f'{key} "{p["title"]}" (de {p.get("author", {}).get("login", "?")}) — {p["url"]}\n'
           f'revisar e aceitar ou fechar; esta entrada sai sozinha quando o PR fechar, não precisa triar.\n'
           f'— via pr-reminder · {today}' for key, p in open_now.items() if key not in present]
    if sep and (new or len(kept) != len(blocks)):
        INBOX.write_text(head + sep + '\n' + '\n\n'.join(new + kept) + '\n', encoding='utf-8', newline='\n')
    PR_STATE.write_text(json.dumps({'checked': now}), encoding='utf-8', newline='\n')
    return f'PRS: {len(new)} PR(s) novo(s) em brain/INBOX.md — mention them.' if new else ''


# Feature name → the question it asks. The registry switches each one independently, which is what
# keeps three reminders in one file from becoming one feature with three reasons.
ASKS = (('inbox-reminder', inbox), ('compass-reminder', compass), ('publish-reminder', publish),
        ('disk-reminder', disk), ('pr-reminder', prs))


def main() -> int:
    said = [text for name, ask in ASKS
            if feature_law.is_enabled(name) and (text := ask())]
    if not said:
        return 0
    sys.stdout.write('REMINDER — mention what fits, in ONE gentle line, and never insist:\n'
                     + '\n'.join(f'  {line}' for line in said) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
