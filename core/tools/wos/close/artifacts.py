#!/usr/bin/env python3
# The generated artifacts a session close regenerates, and what happens to each one afterwards.
#
# Imported by core/tools/wos/roundup. It was `artifacts.sh`, SOURCED — a fragment that could only
# work because it shared the caller's shell variables, so running it any other way silently did
# nothing. Here the caller passes what each function needs and the coupling is in the signature.
#
# Every artifact follows one rule: regenerate, then commit it — unless the tree holds another
# session's work, in which case report the number and roll the write back, because a regenerated
# file left behind rides into that session's next `git add -A`.
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

WOS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WOS.parents[1] / 'hooks/routing'))
sys.path.insert(0, str(WOS.parents[1] / 'hooks'))
from blocks import markers, replace_block  # noqa: E402
from platform_law import interpreter  # noqa: E402

DASHBOARD = 'core/hooks/entropy/dashboard/entropy-dashboard.py'


def git(repo, *args) -> subprocess.CompletedProcess:
    return subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True,
                          encoding='utf-8', errors='replace')


def out(repo, *args) -> str:
    """What git said, or nothing. Four callers had a private copy of these two lines.

    It answers "" for a command that FAILED as well as for one that said nothing, which is
    load-bearing where the question has no answer and fatal where it does — the reason six
    projects went 22 commits unpushed. Ask the returncode when the difference matters.
    """
    done = git(repo, *args)
    return done.stdout.strip() if done.returncode == 0 else ''


def spawn(root, *command) -> subprocess.CompletedProcess:
    """A child of the close: stdin closed, and no bytecode written.

    STDIN, because a child that inherits an interactive one waits there instead of failing, and a
    close that can HANG is worse than one that can go red — nothing reports a hang. BYTECODE,
    because these children import from the tree the close is about to inspect for uncommitted work:
    the dashboard alone leaves a __pycache__ beside the block writer it loads, and a tool that
    judges a tree may not dirty it first.
    """
    return subprocess.run(command, cwd=root, capture_output=True, text=True,
                          encoding='utf-8', errors='replace', stdin=subprocess.DEVNULL,
                          env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})


def settle(repo, name: str, was_clean: bool, message: str, leave_dirty: bool) -> str:
    """The suffix its caller appends to a status line.

    Silent and empty when the artifact did not move, which is the common case and the point:
    deterministic output means a file changes when the WORKSPACE changed, never merely because a
    generator ran.
    """
    tracked = git(repo, 'ls-files', '--error-unmatch', name).returncode == 0
    if tracked and git(repo, 'diff', '--quiet', name).returncode == 0:
        return ''
    if leave_dirty:
        if was_clean:
            # An untracked file has no committed version to restore, so `git checkout -- <name>`
            # fails and the artifact stays in the other session's tree — the one outcome this
            # function exists to make impossible. The first generated artifact to land in a repo
            # that lacks it reaches this: undoing a create is a delete.
            if tracked:
                git(repo, 'checkout', '-q', '--', name)
            else:
                (Path(repo) / name).unlink(missing_ok=True)
        return " · reported only, not committed (tree holds another session's work)"
    if git(repo, 'add', name).returncode or git(repo, 'commit', '-q', '-m', message).returncode:
        return f' · commit failed, {name} left dirty'
    return ''


def write_block(target: Path, name: str, body: str) -> None:
    """One generated block, rewritten in place, its neighbours untouched.

    Imported rather than shelled out to. The bash piped into `python3 blocks.py`, which is both a
    second process and the bare word this port exists to remove — and it meant the close could only
    write a block on a machine where that name resolved to the right interpreter.
    """
    start, end = markers(name)
    text = target.read_text(encoding='utf-8') if target.exists() else ''
    block = '\n'.join((start, body.strip(), end))
    target.write_text(replace_block(text, block, start, end), encoding='utf-8', newline='\n')


def verify_block(target: Path, label: str, verdict: str, log: str) -> None:
    """The verification result, into ISSUES.md beside the entropy findings.

    A red suite and a drift finding are both answers to "what is currently untrue that we know
    about" (core/SCHEMA.md § The `.md` type system). This is the only thing that may write it: the
    suite already ran, and re-running it to report it would double the one cost the pre-commit gate
    exists to keep small.
    """
    body = ['## Verification', '',
            '> Generated by `core/tools/wos/roundup` at session close. The suite is the authority; '
            'this is its last result, never a claim that it is still true.', '',
            f'{date.today().isoformat()} · `{label}` · **{verdict}**']
    if verdict == 'red':
        body += ['', '```', '\n'.join(log.splitlines()[-20:]), '```']
    write_block(target, 'verify', '\n'.join(body))


def regenerate(root: Path, leave_dirty: bool, clean: bool, promoting: str = '') -> tuple:
    """(entropy, diagram) — both rewritten, then settled.

    `clean` is measured by the CALLER, before the verify block is written. Measuring it here would
    read this close's own write as pre-existing dirt, so under --leave-dirty the rollback would
    never fire and the regenerated file would ride into the other session's next `git add -A` —
    the exact incident settle() exists to make unrepeatable.

    `promoting` comes from the CALLER for the same shape of reason: this close runs the dashboard
    BEFORE it merges, so without a name the block published a finding against the close's own
    branch every single time. Only roundup holds the three facts that decide whether the merge
    happens — the verify verdict, --no-promote, and whether the repo is in gitflow scope — so it
    passes the name and this step only relays it. branch_debt.unmerged_branches carries the rest.
    """
    dashboard = [interpreter(), str(root / DASHBOARD)]
    if promoting:
        dashboard += ['--promoting', promoting]
    if spawn(root, *dashboard).returncode == 0:
        # The count AND how it moved are both read out of the header the dashboard just wrote.
        # roundup used to compute a second delta of its own, against the session immediately
        # before it — which is how "flat" got written into hand-off after hand-off while the real
        # number climbed 95 → 645. Matched to the closing stars: a pattern anchored on
        # "findings**" printed no entropy line at all (fixed 2026-08-25).
        found = re.search(r'\*\*(\d+ findings[^*]*)\*\*( \([^)]*\))?',
                          (root / 'ISSUES.md').read_text(encoding='utf-8', errors='replace'))
        entropy = (found.group(1) + (found.group(2) or '')) if found else ''
    else:
        entropy = 'regen failed'
    entropy += settle(root, 'ISSUES.md', clean, 'chore(issues): regenerate the entropy and verify '
                      'blocks at session close', leave_dirty)

    was_clean = git(root, 'diff', '--quiet', 'ARCHITECTURE.html').returncode == 0
    drawn = spawn(root, interpreter(), str(WOS / 'diagram/architecture'))
    text = drawn.stdout + drawn.stderr
    if drawn.returncode == 0:
        hit = [line for line in text.splitlines() if 'routing blocks' in line]
        diagram = hit[0].strip() if hit else ''
    else:
        diagram = f'regen incomplete · {text.count("UNPARSED")} unparsed routing block(s)'
    return entropy, diagram + settle(root, 'ARCHITECTURE.html', was_clean,
                                     'chore(diagram): regenerate at session close', leave_dirty)
