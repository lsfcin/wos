#!/usr/bin/env python3
"""Brain attention — what commits actually touched a goal, across every repo in the workspace.

The metric this replaces counted commits against the goal's own `.md` file, which measured
"how often did you write *about* this goal" and never "how often did you work *on* it". The
2026-08-13 compass rendered `workspace-os 1 touch` in the fortnight that goal absorbed 29 of
29 commits.

Two facts make the fix bigger than a pathspec swap:

1. `code/*`, `academy/papers/*` and `branches/*` are gitignored by the workspace repo and are
   **independent git repos**. `git log -- code/spacemantics` from the root returns nothing,
   forever, so every owned path must be resolved to its governing repo and queried there.
2. `/compass` writes back to the goal files it reviews, so a reviewed goal looks active next
   cycle *because it was reviewed*. Bookkeeping commits are dropped below.
"""

import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from brain_common import GOALS_DIR, GOALS_FILE, WORKSPACE, workspace_rel  # noqa: E402

# The deepest window any caller asks for (brain_common.PERIODS tops out at 4 years). One
# harvest at this depth serves every period, so history is read once per repo per commit.
MAX_DAYS = 1460

_SEP = re.compile(r"\s*·\s*|\s{2,}")


def parse_owns(path):
    """Paths declared in a goal file's `>**owns**` block, workspace-root-relative.

    Same block shape as `>**timing**`: content may wrap across lines, so it runs until the
    block ends. **A blank line ends it** — that is what actually separates a field from the
    prose beneath it, and it is the terminator the first version was missing. Without it the
    parser ran on into the goal's body and offered whole paragraphs as paths: nine warnings
    per commit, each quoting an essay, on the one surface an agent reads at commit time.
    Nothing was miscounted (an unresolvable path is skipped) but noise on a warning channel is
    how a real warning gets missed.

    The second miss was narrower: `> **Bold**` has a space after the `>`, so a following
    blockquote paragraph did not read as the next field either. Both are fixed here; either
    alone would have left craft-flows contributing six of the nine.
    """
    owns, in_block = [], False
    for line in path.read_text(encoding='utf-8').splitlines():
        if re.match(r'^>?\s*\*\*owns\*\*', line.strip()):
            in_block = True
            continue
        if in_block:
            stripped = line.strip()
            if not stripped or stripped == '>':
                break
            if re.match(r'^>?\s*\*\*\w', stripped) or line.startswith('##'):
                break
            for chunk in _SEP.split(stripped.lstrip('>').strip()):
                chunk = chunk.strip().strip('`').rstrip('/')
                if chunk:
                    owns.append(chunk)
    return owns


def governing_repo(rel_path):
    """The repo that has history for `rel_path`, and the path relative to it.

    Returns (repo_dir, path_within_repo) or None when nothing on disk backs the path —
    a silent zero is how this whole class of bug survived, so callers report the miss.
    """
    target = (WORKSPACE / rel_path).resolve()
    if not target.exists():
        return None
    here = target if target.is_dir() else target.parent
    while True:
        if (here / ".git").exists():
            within = workspace_rel(target, here)
            # Resolving to a repo is not the same as having history in it. `branches/*`
            # and `code/*` are gitignored by the workspace repo, so a path under one that
            # is not itself a repo would silently count zero forever — the exact failure
            # mode this module exists to end.
            ignored = subprocess.run(
                ["git", "-C", str(here), "check-ignore", "-q", within],
                capture_output=True,
            ).returncode == 0
            return None if ignored else (here, within)
        if here == WORKSPACE or here.parent == here:
            return None
        here = here.parent


def _is_bookkeeping(paths):
    """True when a commit only rearranged the list that records attention.

    Reads *what changed*, never the commit message, so no amount of commit-style
    discipline (or its absence) can move a goal's number.
    """
    if not paths:
        return False
    goals_dir, goals_file = str(GOALS_DIR), str(GOALS_FILE)
    return all(p == goals_file or p.startswith(goals_dir + "/") for p in paths)


def harvest(repo):
    """Every non-merge commit in `repo` within MAX_DAYS, as {sha: (datetime, {paths})}.

    Merges emit no --name-only output and drop out here, which is what we want: the
    develop/main promotions in core/tools/wos/roundup add no authorship of their own.

    The `brain-attention` boundary (core/SPECS.md § AD-14). This module has no main(); every
    path into it — Attention.__init__, and through it brain_stats and the dashboard —
    reaches history through this one call, so switching it off here leaves every caller
    intact with nothing harvested, rather than raising somewhere up the chain.
    """
    if not feature_law.is_enabled('brain-attention'):
        return {}
    out = subprocess.run(
        ["git", "-C", str(repo), "log", f"--since={MAX_DAYS} days ago",
         "--no-merges", "--format=%x00%H %cI", "--name-only"],
        capture_output=True, text=True, encoding='utf-8'
    )
    if out.returncode != 0:
        return {}

    commits = {}
    for block in out.stdout.split("\x00"):
        if not block.strip():
            continue
        head, *names = block.splitlines()
        sha, _, iso = head.partition(" ")
        try:
            when = datetime.fromisoformat(iso.strip())
        except ValueError:
            continue
        paths = {n.strip() for n in names if n.strip()}
        commits[sha] = (when, paths)
    return commits


class Attention:
    """Per-goal commit sets, harvested once and queried for every period and every goal."""

    def __init__(self, goal_files, owns_by_name=None):
        self.missing = []                    # (name, declared path) that resolves nowhere
        self._repos = {}                     # repo dir -> harvested commits
        self._sets = {}                      # name -> {(repo, sha): datetime}

        for name, path in goal_files.items():
            declared = owns_by_name.get(name) if owns_by_name else parse_owns(path)
            # The goal file is always owned. Life goals declare nothing and this is the
            # whole of their signal — for them the file genuinely is the artifact.
            targets = [workspace_rel(path)] + list(declared or [])
            self._sets[name] = self._collect(name, targets)

    def _collect(self, name, targets):
        found = {}
        for rel in targets:
            resolved = governing_repo(rel)
            if resolved is None:
                self.missing.append((name, rel))
                continue
            repo, within = resolved
            if repo not in self._repos:
                self._repos[repo] = harvest(repo)
            # "." means the declared path *is* the repo root, so every commit counts.
            prefix = "" if within == "." else within
            for sha, (when, paths) in self._repos[repo].items():
                if repo == WORKSPACE and _is_bookkeeping(paths):
                    continue
                if not prefix or any(p == prefix or p.startswith(prefix + "/")
                                     for p in paths):
                    found[(str(repo), sha)] = when
        return found

    def count(self, name, days):
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return sum(1 for when in self._sets.get(name, {}).values() if when >= cutoff)

    def last_touch(self, name):
        whens = self._sets.get(name, {}).values()
        return max(whens).strftime("%Y-%m-%d") if whens else None

    def area_count(self, names, days):
        """Distinct commits across several goals — a union, never a sum.

        One commit can advance two goals (workspace-os owns core/, craft-flows owns
        core/flows/craft/). Both goal bars should show it; the area must not count it twice.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        seen = set()
        for name in names:
            seen |= {k for k, when in self._sets.get(name, {}).items() if when >= cutoff}
        return len(seen)
