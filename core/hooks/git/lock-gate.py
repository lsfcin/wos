#!/usr/bin/env python3
# PreToolUse write and shell — the branch lock, asked at every write and every git command that
# moves history. A write takes a free repo; a git command never does. Rules: git/lock.py.
#
# FAILS OPEN on a crash only: a gate that dies must never cost a session its edits (Lucas,
# 2026-11-09). A refusal is never an error.
import json
import re
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
from hook_input import capability, parse_stdin  # noqa: E402

GIT = re.compile(r'\bgit\b((?:\s+-C\s+\S+)?)[^;&|\n]*?\s(commit|merge|rebase|reset|cherry-pick|revert|'
                 r'switch|checkout|push|pull|stash|branch)(?![\w-])')
CD = re.compile(r'(?:^|[;&|]\s*)cd\s+([^\s;&|]+)')
HISTORY = ('commit', 'merge', 'rebase', 'reset', 'cherry-pick', 'revert')


def main() -> int:
    raw, tool, data, session, cwd = parse_stdin()
    try:
        import lock
        cap = capability(tool, data)
        if cap == 'write' and data.get('file_path'):
            refusal, note = lock.verdict(Path(data['file_path']), session)
        elif cap == 'shell' and (found := GIT.search(str(data.get('command', '')))):
            # The repo is `git -C <dir>`, else the last `cd <dir>` before it, else the shell's cwd.
            moved = CD.findall(str(data['command'])[:found.start()])
            base = Path(cwd or '.') / (moved[-1] if moved else '')
            where = base / found.group(1).split()[-1] if found.group(1) else base
            refusal, note = lock.verdict(where, session, take=False)
            repo = lock.repo_of(where)
            if not refusal and found.group(2) in HISTORY and repo and lock.governed(repo) and \
                    lock.out(repo, 'branch', '--show-current') in lock.SHARED and \
                    lock.feature_law.is_enabled('branch-lock'):
                refusal = (f'⛔ BRANCH LOCK — an agent never runs git {found.group(2)} on a shared '
                           'branch. Write a file first: the lock creates the feature branch.')
        else:
            return 0
    except Exception:   # noqa: BLE001 — fail open, see the head
        return 0
    if refusal:
        print(refusal, file=sys.stderr)
        return 2
    if note:
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'additionalContext': note}}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
