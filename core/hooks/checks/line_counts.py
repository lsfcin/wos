#!/usr/bin/env python3
# The line-count gate: warn and block on authored lines, at the two numbers limits.env declares.
#
# Two callers, one implementation, which core/hooks/SPECS.md promises explicitly -- the pre-commit
# pipeline passes the staged files, and a bare run audits every tracked file in the repo.
#
# WHICH FILES ARE AUTHORED IS file_law.py'S ANSWER, never a regex here. This script carrying its own
# extension list is what let .sh and extensionless scripts past the gate for months, during which
# core/hooks/pre-commit itself reached 385 lines unblocked. The thresholds are limits.env's answer
# for the same reason.
#
# PROSE JOINED IT 2026-09-12 (Lucas: every folder, every authored type). limits.env has held one
# number for code and prose alike since 2026-08-18, but only the BLOCK half reached .md -- through
# the write gate and the entropy dashboard after the fact -- so the WARN, the half that
# asks for a look before a file is unreadable, existed for code alone.
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
import file_law  # noqa: E402

for _stream in (sys.stdout, sys.stderr):
    _stream.reconfigure(encoding='utf-8', errors='replace')


# A file may waive the WARN by carrying this marker plus its reason, in whatever comment syntax it
# already uses. The BLOCK is never waivable: over that number a file is CUT, not excused. The reason
# travels with the file rather than sitting in a list somewhere else, because the reader who needs it
# is the one who just opened the file and found it long.
#
# It must OPEN a comment line. Naming the marker in prose is not claiming it: the sentence
# documenting this waiver, in core/hooks/SPECS.md, silently exempted that file the moment it was
# written — a gate a document switches off by describing it.
WARN_EXEMPT = re.compile(r'^\s*(?:#|//|%|<!--)\s*warn-exempt:', re.M)


def _content(path, root, staged):
    """What the caller is actually asking about, or None when there is nothing to read.

    THE GATE MUST WEIGH THE BLOB GIT WILL COMMIT, NOT THE FILE ON DISK. Those differ whenever a trim
    is written but not staged, and the gate then answers a question about a file nobody is
    committing -- which is how `git/branch_debt.py` and `tools/wos/roundup` landed at 202 and 201
    lines against WARN_LINES=200 while printing `No authored files exceed thresholds` (ISSUES.md,
    found 2026-09-13). It failed in both directions: silent on what it should warn about, and noisy
    about a fix already staged. A bare audit run has no index to consult and reads the disk, which
    is the right answer for that caller and the wrong one for the pipeline.
    """
    if staged:
        done = subprocess.run(['git', 'show', f':{path}'], cwd=root, capture_output=True,
                              text=True, encoding='utf-8', errors='replace')
        return done.stdout if done.returncode == 0 else None
    target = root / path
    return target.read_text(encoding='utf-8', errors='replace') if target.is_file() else None


def report(paths, root=None, staged=False) -> tuple:
    """(lines of report, blocked) for `paths`. Never raises, never prints -- the caller decides.

    Returned rather than printed because the pre-commit pipeline must fold this into its own single
    reject path, and a checker that prints its own verdict cannot be composed into one.

    `staged` says the paths came from the index, so read them from there -- see `_content`.
    """
    limits = file_law.load_limits()
    warn, block = int(limits['WARN_LINES']), int(limits['BLOCK_LINES'])
    warn_chars, block_chars = int(limits['WARN_CHARS']), int(limits['BLOCK_CHARS'])
    root = Path(root) if root else Path.cwd()
    lines, blocked, warned = [], False, False
    for path in paths:
        # Code or prose, asked of the law rather than of a suffix. is_authored answers for our own
        # code and is_authored_prose for our own .md; both already waive vendored AND generated, so
        # a tool's own output is out here without a third question -- `generated.txt` promises the
        # cap is waived, and a separate check restating that had drifted into asking it twice.
        if not (file_law.is_authored(Path(path), root)
                or file_law.is_authored_prose(Path(path), root)):
            continue
        text = _content(path, root, staged)
        if text is None:
            continue
        count = len(text.splitlines())
        if count >= block:
            lines.append(f'🚨 BLOCK: {path} ({count} lines)')
            blocked = True
        elif count >= warn and not WARN_EXEMPT.search(text):
            lines.append(f'⚠ WARN: {path} ({count} lines)')
            warned = True
        # The document cap, at the same two levels and through the same waiver. It is the half that
        # stops the line count being satisfied by writing longer lines, so it is asked of every
        # authored file this loop already admitted -- never of a different set.
        size = len(text)
        if size >= block_chars:
            lines.append(f'🚨 BLOCK: {path} ({size} characters)')
            blocked = True
        elif size >= warn_chars and not WARN_EXEMPT.search(text):
            lines.append(f'⚠ WARN: {path} ({size} characters)')
            warned = True
    # EACH SUMMARY SAYS WHAT HAPPENED, not which number was crossed (2026-09-15). The warn line
    # used to name only its own threshold, so a reader with the whole tree in context still read
    # it as the cap and cut a file that was 46 lines clear of refusal. A gate that reports a
    # number and not a verdict leaves the verdict to be guessed.
    if blocked:
        lines.append(f'\nREFUSED — over the cap of {block} lines / {block_chars} characters. '
                     f'Cut the file; a sibling needs Lucas\'s OK (core/norms/cap.md).')
    elif warned:
        lines.append(f'\nNOT REFUSED — this is the warning at {warn} lines / {warn_chars} '
                     f'characters. Nothing stops until {block} lines / {block_chars} characters.')
    else:
        lines.append('No authored files exceed thresholds.')
    return lines, blocked


def main() -> int:
    # Off means it stops rejecting, not that it fails. Same arm, same reason, as every other gate.
    if not feature_law.is_enabled('line-limit'):
        return 0
    argv = sys.argv[1:]
    if argv == ['--from-stdin']:
        paths = [line.strip() for line in sys.stdin if line.strip()]
    elif argv:
        paths = argv
    else:
        done = subprocess.run(['git', 'ls-files'], capture_output=True, text=True,
                              encoding='utf-8', errors='replace')
        paths = done.stdout.splitlines()
    lines, blocked = report(paths)
    print('\n'.join(lines))
    return 1 if blocked else 0


if __name__ == '__main__':
    sys.exit(main())
