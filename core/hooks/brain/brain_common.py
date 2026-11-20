#!/usr/bin/env python3
"""Brain stats — shared config, git helpers, and block replacement."""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_law import rel  # noqa: E402

# Paths are relative to the brain repo's root: brain/ is its own repo since 2026-11-19, and these
# run as its pre-commit generator with cwd there, so a path compares directly to what git prints.
# WORKSPACE is the one absolute, needed to resolve an owned path to the repo holding its history.
WORKSPACE  = Path(__file__).resolve().parents[3]
BRAIN      = Path(".")
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

# THE AREAS ARE THE LAW'S, NOT THIS FILE'S. They were a list here, a prose line in core/hooks/brain/SPECS.md
# and a comment in the goal template — three declarations, and on 2026-09-18 all three
# disagreed: the spec had dropped `craft`, the template had dropped `career`, and this list had
# dropped `craft` too, so twelve goals drew no area bar at all and the workspace goal only showed up
# because it was filed under `health`. Read from the file that owns the definition, same as every
# other law module in this workspace reads its answer out of a data file rather than holding one.
# The list wraps over several lines and `Horizon:` is the next thing in the file, so the capture
# has to stop there — reading one line would have found three of the six and reading to the blank
# line finds the horizons as well, which is how a parser invents an area called `dream`.
_AREA_LINE = re.compile(r'^Area\s+—\s+((?:.*\n?)*?)(?=^\s*$|^Horizon)', re.M)


def areas(spec=Path(__file__).resolve().parent / "SPECS.md"):
    """The goal areas core/hooks/brain/SPECS.md declares, in the order it declares them.

    Empty when the spec is missing — a clone before install — and every caller draws no area bar
    rather than inventing five. A default here would be a fourth declaration.
    """
    try:
        text = Path(spec).read_text(encoding="utf-8")
    except OSError:
        return []
    found = _AREA_LINE.search(text)
    return list(dict.fromkeys(re.findall(r'`([a-z]+)`', found.group(1)))) if found else []


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
