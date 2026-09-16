#!/usr/bin/env python3
"""Brain stats — shared config, git helpers, and block replacement."""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_law import rel  # noqa: E402

# Paths stay workspace-relative: the hooks run with cwd at the workspace root and git
# reports --name-only against the same origin, so a relative path compares directly to
# what git prints. WORKSPACE is the one absolute, needed to resolve an owned path to the
# nested repo that actually holds its history.
WORKSPACE  = Path(__file__).resolve().parents[3]
BRAIN      = Path("brain")
GOALS_FILE = BRAIN / "GOALS.md"
LOG_DIR    = BRAIN / ".log"        # runtime state only (compass-last.txt), never an archive
GOALS_DIR  = BRAIN / "goals"


def workspace_rel(path, root=WORKSPACE):
    """`path` relative to the workspace (or to `root`), in the one path vocabulary we write.

    Kept as a name because brain/ reads better with it, but the answer now comes from
    platform_law.rel — a second implementation of "make this path relative" is what let this one
    hand back a backslash while every test it feeds compares against a forward slash.
    """
    return rel(path, root)

PERIODS = [
    ("month",     30),
    ("trimester", 90),
    ("semester",  180),
    ("year",      365),
    ("2-year",    730),
    ("4-year",    1460),
]

DONE_KEEP = 3

AREAS = ["health", "career", "finances", "fun", "spiritual"]


def git(*args):
    r = subprocess.run(["git"] + list(args), capture_output=True, text=True, encoding='utf-8')
    return r.stdout.strip() if r.returncode == 0 else ""


# touch_count / last_touch_date lived here and counted commits against a goal's own .md
# file. That is the defect brain_attention.py exists to fix, and leaving them would leave a
# second, wrong definition of "a touch" for the next caller to reach for. Deleted 2026-08-13.


def replace_block(content, start, end, new_block):
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(content):
        return None
    return pattern.sub(lambda _: new_block, content)
