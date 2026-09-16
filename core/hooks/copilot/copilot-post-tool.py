# Copilot PostToolUse hook: regenerate interfaces, sync context, record read-trackers.

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from copilot_shared import (
    build_payload,
    collect_paths,
    load_input,
    run_script,
)


HOOKS = Path(__file__).resolve().parents[1]


def emit_allow(messages: list[str] | None = None) -> None:
    output: dict[str, Any] = {"continue": True}
    if messages:
        text = "\n\n".join(message for message in messages if message)
        if text:
            output["hookSpecificOutput"] = {
                "hookEventName": "PostToolUse",
                "additionalContext": text,
            }
    print(json.dumps(output, ensure_ascii=False))


# WHICH GATES RUN IS NOT DECIDED HERE, and this file decided it twice (b20260905). It named
# facade-tracker.py and context-tracker.py itself — a hand-copy of the two `post read` rows in
# core/hooks/gates.txt — and reached them through READ_HINTS/EDIT_HINTS, the tool-name whitelist
# b20260901 retired. The pre-tool shim beside this one stopped doing both on 2026-09-05; this one
# was left behind, so a Copilot tool nobody has met yet would have been tracked by neither.
#
# What stays this shim's job is the PAYLOAD: Copilot spells a path seven ways and content four, and
# only a translation can flatten that. The capability is then read off the payload, exactly as
# Claude Code's own PostToolUse registration does.
#
# post-edit.sh keeps its own spawn and cannot join the table: gates.txt's rows are imported into
# the dispatcher's own process and post-edit.sh is bash.
def main() -> int:
    data = load_input()
    workspace_root = Path(data.get("cwd") or os.getcwd()).resolve()
    tool_input = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    paths = collect_paths(workspace_root, tool_input)
    if not paths:
        emit_allow()
        return 0

    messages: list[str] = []
    for file_path in paths:
        payload = build_payload(file_path, tool_input)
        writes = any(key in payload for key in ("content", "new_string"))
        canonical = ("Write" if "content" in payload else "Edit") if writes else "Read"
        run_script(HOOKS / "dispatch.py", {**payload, "hook_event_name": "PostToolUse"},
                   canonical, workspace_root, via_env=True)
        if not writes:
            continue
        result = run_script(HOOKS / "post-edit.sh", payload, canonical, workspace_root, via_env=True)
        if result.stdout.strip():
            messages.append(result.stdout.strip())
        if result.stderr.strip():
            messages.append(result.stderr.strip())

    emit_allow(messages)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
