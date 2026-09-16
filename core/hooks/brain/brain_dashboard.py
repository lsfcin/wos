#!/usr/bin/env python3
"""Brain stats — GOALS.md dashboard rendering (area/goal bars, active-goals table)."""

import re
from datetime import datetime

from brain_common import AREAS, GOALS_FILE, replace_block


def bar(count, max_val, width=10):
    if max_val == 0:
        max_val = 1
    filled = count * width // max_val
    return "█" * filled + "░" * (width - filled)


def area_from_file(path):
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^# \[ *(\w+) ', line)
            if m:
                return m.group(1).lower()
    return None


def timing_display(text):
    """Shorten long timing strings to a date-like fragment for table display."""
    if not text or text == "—":
        return "—"
    if len(text) <= 18:
        return text
    m = re.search(
        r'(mid-|before\s+|after\s+|early\s+|late\s+)?'
        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d*',
        text, re.IGNORECASE
    )
    if m:
        return m.group(0).strip()
    m = re.search(r'\d+\s+\w+', text)
    if m:
        return m.group(0)
    return text[:18] + "…"


def parse_goal_file(path):
    content = path.read_text(encoding='utf-8')
    lines   = content.splitlines()
    result  = {}

    for line in lines:
        # Header may be 2-field [ area | horizon ] or 3-field [ area | subarea | horizon ]
        m = re.match(r'^# \[ *(\w+)(?: *\| *\w+)* *\| *(\w+) *\] *(.+)', line)
        if m:
            result['area']    = m.group(1).lower()
            result['horizon'] = m.group(2).lower()
            result['title']   = m.group(3).strip()
            break
    if 'title' not in result:
        return None

    # Timing block: anchor first, target as fallback
    timing_block = []
    in_timing = False
    for line in lines:
        if '>**timing**' in line:
            in_timing = True
            continue
        if in_timing:
            if re.match(r'^>?\*\*\w', line) or re.match(r'^##', line):
                break
            timing_block.append(line)

    timing_str = "\n".join(timing_block)
    t_display  = "—"
    am = re.search(r'anchor\s*·\s*([^\n*\\]+)', timing_str)
    tm = re.search(r'target\s*·\s*([^\n*\\]+)', timing_str)
    if am:
        val = am.group(1).strip()
        if val and val != "—":
            t_display = timing_display(val)
    if t_display == "—" and tm:
        val = tm.group(1).strip()
        if val and val != "—":
            t_display = timing_display(val)
    result['timing'] = t_display

    # Selected next achievement: first content line after the heading
    selected = "—"
    in_sel = False
    for line in lines:
        if re.match(r'^## selected next achievement', line, re.IGNORECASE):
            in_sel = True
            continue
        if in_sel:
            s = line.strip()
            if s and not s.startswith('**ease') and not s.startswith('<!--'):
                selected = s[:55] + ("…" if len(s) > 55 else "")
                break

    result['selected'] = selected
    result['file']     = path.name
    return result


def update_goals_table(goal_files):
    if not GOALS_FILE.exists():
        return

    rows = []
    for name, path in sorted(goal_files.items()):
        g = parse_goal_file(path)
        if not g:
            continue
        rows.append(
            f"| {g['title']} | {g['area']} | {g['horizon']} | {g['timing']} "
            f"| {g['selected']} | [→](goals/{g['file']}) |"
        )

    new_table = (
        "<!-- goals:start -->\n"
        "## active goals\n\n"
        "| goal | area | horizon | timing | selected achievement | file |\n"
        "|------|------|---------|--------|---------------------|------|\n"
        + "\n".join(rows) + "\n"
        "<!-- goals:end -->"
    )

    content = GOALS_FILE.read_text(encoding='utf-8')
    result  = replace_block(content, "<!-- goals:start -->", "<!-- goals:end -->", new_table)
    if result and result != content:
        GOALS_FILE.write_text(result, encoding='utf-8', newline='\n')
        print("[Brain] GOALS.md active goals updated")


def update_goals_md(goal_files, attention):
    if not GOALS_FILE.exists():
        return

    goal_touches = {name: attention.count(name, 14) for name in goal_files}

    # Areas union their goals' commit sets instead of summing their counts: one commit can
    # advance two goals (workspace-os owns core/, craft-flows owns core/flows/craft/), and
    # summing would count it twice for the area while both goal bars rightly show it.
    by_area = {a: [] for a in AREAS}
    for name, path in goal_files.items():
        area = area_from_file(path)
        if area in by_area:
            by_area[area].append(name)
    area_touches = {a: attention.area_count(names, 14) for a, names in by_area.items()}

    area_max = max(area_touches.values()) or 1
    goal_max = max(goal_touches.values()) or 1
    now      = datetime.now().strftime("%Y-%m-%d %H:%M")

    area_lines = "".join(
        f"{a:<12} {bar(area_touches[a], area_max)}   {area_touches[a]} touches\n"
        for a in AREAS
    )
    goal_lines = "".join(
        f"{name:<24} {bar(goal_touches[name], goal_max)}   {goal_touches[name]} touches\n"
        for name in sorted(goal_touches)
    )

    # Hook only replaces the data block — pareto/gap sections are preserved between commits
    new_data = (
        "<!-- data:start -->\n"
        f"## attention dashboard  _(auto-updated on every commit)_\n"
        f"last-updated: {now}\n\n"
        f">**areas** — last 14 days  \n"
        f"```\n{area_lines}```\n\n"
        f">**goals** — last 14 days  \n"
        f"```\n{goal_lines}```\n"
        "<!-- data:end -->"
    )

    content = GOALS_FILE.read_text(encoding='utf-8')

    # Prefer data markers (preserves agent-written pareto/gap sections)
    result = replace_block(content, "<!-- data:start -->", "<!-- data:end -->", new_data)

    if result is None:
        # Bootstrap: first run — build full stats block including agent section placeholders
        full_block = (
            "<!-- stats:start -->\n"
            + new_data + "\n\n"
            ">**pareto**  \n"
            "*— (run compass review)*\n\n"
            ">**gap**  \n"
            "*— (run compass review)*\n"
            "<!-- stats:end -->"
        )
        result = replace_block(content, "<!-- stats:start -->", "<!-- stats:end -->", full_block)

    if result and result != content:
        GOALS_FILE.write_text(result, encoding='utf-8', newline='\n')
        print("[Brain] GOALS.md updated")
