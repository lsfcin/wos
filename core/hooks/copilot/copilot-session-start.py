# Copilot SessionStart hook: inject workspace policy context + caveman rules.

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys


def load_input() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def read_workspace_excerpt(workspace_root: Path, max_lines: int = 120) -> str:
    workspace_file = workspace_root / "AGENTS.md"
    if not workspace_file.exists():
        return "AGENTS.md was not found in the workspace root."

    lines: list[str] = []
    with workspace_file.open("r", encoding="utf-8") as handle:
        for _ in range(max_lines):
            line = handle.readline()
            if not line:
                break
            lines.append(line.rstrip("\n"))

    return "\n".join(lines)


def load_caveman_context() -> str:
    # Read mode from ~/.config/caveman/config.json; default "full" if absent.
    config_path = Path.home() / ".config" / "caveman" / "config.json"
    mode = "full"
    if config_path.exists():
        try:
            mode = json.loads(config_path.read_text(encoding="utf-8")).get("defaultMode", "full")
        except Exception:
            pass

    if mode == "off":
        return ""

    # Try to read rules from installed SKILL.md (follows symlink automatically).
    skill_path = Path.home() / ".claude" / "skills" / "caveman" / "SKILL.md"
    if skill_path.exists():
        try:
            body = re.sub(r"^---[\s\S]*?---\s*", "", skill_path.read_text(encoding="utf-8"))
            return f"CAVEMAN MODE ACTIVE — level: {mode}\n\n{body}"
        except Exception:
            pass

    # Fallback: compact inline rules (used when SKILL.md not installed).
    return (
        f"CAVEMAN MODE ACTIVE — level: {mode}\n\n"
        "Respond terse like smart caveman. Drop articles/filler/pleasantries/hedging. "
        "Fragments OK. Short synonyms. Technical terms exact. Code blocks unchanged.\n"
        "Active every response. Off only: \"stop caveman\" / \"normal mode\".\n"
        "Drop caveman for: security warnings, irreversible actions, academic/paper prose."
    )


def main() -> int:
    data = load_input()
    workspace_root = Path(data.get("cwd") or os.getcwd()).resolve()
    excerpt = read_workspace_excerpt(workspace_root)
    caveman = load_caveman_context()

    parts = ["Workspace policy excerpt:\n" + excerpt]
    if caveman:
        parts.append(caveman)

    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n\n---\n\n".join(parts),
        },
    }
    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
