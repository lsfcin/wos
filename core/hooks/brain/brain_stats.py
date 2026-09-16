#!/usr/bin/env python3
"""Brain attention tracker — per-file stats, done compression, commit orchestration."""

import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from brain_attention import Attention  # noqa: E402
from brain_common import (
    DONE_KEEP, GOALS_DIR, GOALS_FILE, LOG_DIR, PERIODS,
    git, replace_block,
)
from brain_dashboard import update_goals_md, update_goals_table

# ── Trend heuristic (quantitative, git-only) ───────────────────────────────────

def trend_label(counts):
    month     = counts["month"]
    trimester = counts["trimester"]
    year      = counts["year"]
    four_year = counts["4-year"]

    if four_year == 0:   return "new"
    if year      == 0:   return "dormant"
    if trimester == 0:   return "always-postponed"
    if month     == 0:   return "stalled"

    avg = trimester / 3
    if avg == 0:              return "advancing"
    if month >= avg * 1.5:    return "advancing"
    if month <= avg * 0.5:    return "decelerating"
    return "steady"

# ── Per-file stats block ───────────────────────────────────────────────────────

def build_stats_block(name, attention):
    """One line, not a table.

    This was a six-row `| period | touches |` table until 2026-08-31 — 9 lines in each of 36 goal
    files, ~320 lines of the corpus, and NOTHING read them: GOALS.md builds its dashboard straight
    from `brain_attention.harvest`, and no checker, tool or skill parses a goal file's stats. It was
    36 copies of a number that already lives on the dashboard. Every count survives here; only the
    table scaffolding went.
    """
    counts = {period: attention.count(name, days) for period, days in PERIODS}
    lt     = attention.last_touch(name)

    # The six periods are named once, in brain/SPECS.md, instead of on 36 goal files. Spelling
    # them here costs 43 characters a line across 36 files — and it is the same restatement the
    # table was.
    return (
        "<!-- stats:start -->\n"
        f"last-touch: {lt or '—'}  ·  trend: {trend_label(counts)}  ·  touches: "
        + "/".join(str(counts[period]) for period, _ in PERIODS) + "\n"
        "<!-- stats:end -->"
    )

# ── Done compression ───────────────────────────────────────────────────────────

DONE_RE = re.compile(r'\[x\]', re.IGNORECASE)


def compress_done(content, name):
    start   = "<!-- done:start -->"
    end     = "<!-- done:end -->"
    pattern = re.compile(re.escape(start) + r"(.*?)" + re.escape(end), re.DOTALL)
    m       = pattern.search(content)
    if not m:
        return content, []

    inner      = m.group(1)
    lines      = inner.split("\n")
    done_lines = [l for l in lines if DONE_RE.search(l)]

    if len(done_lines) <= DONE_KEEP:
        return content, []

    keep    = done_lines[:DONE_KEEP]   # newest first → keep first N
    archive = done_lines[DONE_KEEP:]
    other   = [l for l in lines if not DONE_RE.search(l)]

    new_inner = "\n".join(other + keep)
    if not new_inner.endswith("\n"):
        new_inner += "\n"          # else the last entry glues to the done:end marker
    new_content = pattern.sub(lambda _: start + new_inner + end, content)
    return new_content, archive

# ── Commit orchestration ───────────────────────────────────────────────────────

def load_goal_files():
    files = {}
    for f in sorted(GOALS_DIR.glob("*.md")):
        name = f.stem
        # `_`-prefixed files are scaffolding, never goals. This replaces an
        # ALL-CAPS skip that only worked while the template was ARCHETYPE.md.
        if name.startswith("_"):
            continue
        files[name] = f
    return files


def staged_goal_files(goal_files):
    """Goal files the user actually staged this commit — the real-attention set.

    Decorating *every* goal file on every commit made each commit "touch" all
    of them, flattening touch_count to ~total-commits for every goal and
    destroying the attention signal. We only enrich what the user really edited.
    """
    out    = git("diff", "--cached", "--name-only")
    staged = {l.strip() for l in out.splitlines() if l.strip()}
    return {name: p for name, p in goal_files.items() if str(p) in staged}


def pre_commit():
    """Decorate only user-staged goal files, then refresh the aggregate dashboard."""
    goal_files = load_goal_files()
    if not goal_files:
        return

    # One harvest per declared repo, reused for every goal and every period below. The
    # previous shape ran a `git log` per goal per period — ~52 subprocesses each commit.
    attention = Attention(goal_files)
    for name, rel in attention.missing:
        print(f"[Brain] ⚠ {name}: owns '{rel}', which resolves to no repo — not counted")

    targets  = staged_goal_files(goal_files)
    modified = []

    for name, path in targets.items():
        original = path.read_text(encoding='utf-8')
        content  = original

        updated = replace_block(content, "<!-- stats:start -->", "<!-- stats:end -->",
                                 build_stats_block(name, attention))
        if updated:
            content = updated

        # Overflow entries are dropped, not archived: git is the history
        # (core/SCHEMA.md, No archive types). The done-log was deleted 2026-07-30.
        content, _ = compress_done(content, name)

        if content != original:
            path.write_text(content, encoding='utf-8', newline='\n')
            modified.append(str(path))
            print(f"[Brain] {name}: updated")

    # Dashboard aggregates live git history for ALL goals — always fresh. GOALS.md
    # churn is not itself a measured signal, so refreshing it every commit is safe.
    # The `brain-dashboard` boundary (core/SPECS.md § AD-14). brain_dashboard.py has no main()
    # and two public writers, and it sits on the 200-line cap with no room for a guard in
    # each; this is its only caller, so one gate here switches the whole render off.
    if feature_law.is_enabled('brain-dashboard'):
        update_goals_md(goal_files, attention)
        update_goals_table(goal_files)

    to_stage = modified[:]
    if GOALS_FILE.exists():
        to_stage.append(str(GOALS_FILE))
    if to_stage:
        git("add", *to_stage)

    check_compass_reminder()


def check_compass_reminder():
    compass_log = LOG_DIR / "compass-last.txt"
    if not compass_log.exists():
        print("[Brain] ⚠ compass review never run — try /compass")
        return
    try:
        last = date.fromisoformat(compass_log.read_text(encoding='utf-8').strip())
        days = (date.today() - last).days
        if days >= 30:
            print(f"[Brain] ⚠ no compass review in {days} days — run /compass")
    except Exception:
        pass


def main():
    pre_commit()


if __name__ == "__main__":
    main()
