#!/usr/bin/env python3
# Directory crowding: how many files one directory asks a reader to hold at once.
#
# The rule is not new. A files-per-directory threshold has always existed, and
# `context_synchronizer.sync` has always warned when a directory crosses it — but it warned
# to stdout, during a sync nobody reads, so the tail grew unopposed. This module is that
# same law, surfaced where the other Level 0 checks are read. Both the threshold and the
# definition of "code file" are imported from limits.env / file_law.py, never restated:
# a second copy of a limit is the drift these checks exist to catch.
#
# Why it belongs next to the size signals: a large routing table is not a formatting
# problem, it is the directory telling you it holds more than one responsibility. Splitting
# it costs one routing hop, so this is a SIGNAL, never a cap — see core/SCHEMA.md
# § Routing depth and locality for when the hop is worth paying.
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from file_law import is_authored, load_limits  # noqa: E402
from platform_law import rel as _rel  # noqa: E402


def crowding_counts(files: list, root: Path) -> Counter:
    """Directory -> number of code files, using the one definition in file_law.

    Deliberately not every file: a flat collection of documents is a legitimate shape
    (`brain/goals/` is 57 goal files and splitting it would be wrong), while a directory
    holding dozens of modules is one responsibility too many. Vendored trees are excluded —
    upstream chose their layout and we are not going to split it.
    """
    counts = Counter()
    for path in files:
        if is_authored(path, root):
            counts[path.parent] += 1
    return counts


def crowding_signals(files: list, root: Path, limit: int = None) -> list:
    """Directories whose routing table is large because the directory is.

    Switched off by the `crowding-limit` feature, one of the four the ablation names. The switch
    sits here rather than at the dashboard's call site so that counting stays available to
    anything that wants the number without the judgement — off means this workspace stops
    *asking* about crowding, not that it stops being able to see it.
    """
    if not feature_law.is_enabled('crowding-limit'):
        return []
    limits = load_limits()
    warn = limits['WARN_FILES'] if limit is None else limit
    block = limits['BLOCK_FILES']
    signals = []
    for directory, count in crowding_counts(files, root).items():
        if count <= warn:
            continue
        rel = _rel(directory, root)
        # EACH SIGNAL SAYS WHAT HAPPENED, not which number was crossed — the rule
        # core/hooks/checks/line_counts.py earned on 2026-09-15 and this check never got. Naming
        # only the threshold it crossed is what let 11 files in core/hooks/session/ read as a
        # refusal to Lucas AND to the agent on 2026-09-17, while limits.env stopped nothing until
        # 15. A WARN is a WARN everywhere (Lucas, 2026-09-21), so it says where refusal starts.
        verdict = (f'REFUSED — over the cap of {block}' if count > block else
                   f'NOT REFUSED — this is the warning at {warn}. Nothing stops until {block}')
        signals.append(f'{rel} — {count} code files in one directory. {verdict}; split by '
                       f'responsibility if the split removes more table than the hop adds')
    return sorted(signals)
