# Copilot PreToolUse hook: enforce workspace read/edit/terminal policy via the canonical
# core/hooks scripts. The gates are located relative to THIS file, never from the workspace
# root: pointing at a spelled-out directory is what left this shim calling a dead `.hooks/`
# for a full day after the hooks moved into core/ (2026-07-31).

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from copilot_shared import (
    COMMAND_KEYS,
    build_payload,
    collect_paths,
    first_string,
    forward_block,
    load_input,
    run_script,
    session_id,
)
import json


def emit_allow(message: str = "") -> None:
    output: dict[str, Any] = {"continue": True}
    if message:
        output["systemMessage"] = message
    print(json.dumps(output, ensure_ascii=False))


DISPATCH = Path(__file__).resolve().parents[1] / "dispatch.py"


def gate(payload: dict[str, Any], tool: str, root: Path, messages: list[str]) -> bool:
    """One dispatcher run over one canonical payload. True when it blocked."""
    result = run_script(DISPATCH, payload, tool, root)
    if result.stdout.strip():
        messages.append(result.stdout.strip())
    if result.returncode == 2:
        forward_block(result)
        return True
    return False


# WHICH GATES RUN IS NO LONGER THIS FILE'S QUESTION, and the three hint sets that used to answer it
# (READ_HINTS / EDIT_HINTS / TERMINAL_HINTS) are gone with the branches they fed. They were a
# whitelist of tool names — the shape b20260901 retired when the question moved to the payload —
# and every gate order they encoded was a hand-copy of core/hooks/gates.txt. This shim now does
# only what a shim is for: turn Copilot's schema into a canonical payload, once per target.
def main() -> int:
    data = load_input()
    workspace_root = Path(data.get("cwd") or os.getcwd()).resolve()
    tool_name = str(data.get("tool_name") or "")
    tool_input = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    messages: list[str] = []

    command = first_string(tool_input, COMMAND_KEYS)
    if command:
        payloads = [{"command": command, "session_id": session_id()}]
    else:
        payloads = [build_payload(p, tool_input) for p in collect_paths(workspace_root, tool_input)]

    for payload in payloads:
        if gate(payload, tool_name, workspace_root, messages):
            return 2

    emit_allow("\n\n".join(messages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
