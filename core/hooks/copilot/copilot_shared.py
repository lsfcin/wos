# Shared plumbing for the Copilot pre/post tool shims: payload extraction + canonical hook exec.
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_law import interpreter

# READ_HINTS / EDIT_HINTS / TERMINAL_HINTS are all gone (2026-09-05 pre, 2026-09-06 post). They
# were a whitelist of tool NAMES, which goes stale the moment Copilot adds a tool — silently, in
# the direction where nothing reports it. Both shims read the capability off the payload now, so
# what is left here is the payload translation: how Copilot spells a path, content, an edit pair
# and a command line, which is the one thing a shim genuinely owns.
PATH_KEYS = (
    "filePath",
    "file_path",
    "path",
    "file",
    "filepath",
    "targetPath",
    "target_path",
)
CONTENT_KEYS = ("content", "text", "newCode", "new_code")
OLD_KEYS = ("oldString", "old_string", "oldText", "old_text")
NEW_KEYS = ("newString", "new_string", "newText", "new_text")
COMMAND_KEYS = ("command", "commandLine", "command_line", "cmd")


def load_input() -> dict[str, Any]:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def session_id() -> str:
    # Copilot host process pid — stable across one editor session, spawner of the shims.
    return f"copilot{os.getppid()}"


def normalize_path(workspace_root: Path, raw: Any) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    return str(candidate.resolve())


def collect_paths(workspace_root: Path, value: Any) -> list[str]:
    paths: list[str] = []

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key in PATH_KEYS:
                    normalized = normalize_path(workspace_root, child)
                    if normalized:
                        paths.append(normalized)
                elif key == "files" and isinstance(child, list):
                    for item in child:
                        if isinstance(item, str):
                            normalized = normalize_path(workspace_root, item)
                            if normalized:
                                paths.append(normalized)
                        else:
                            visit(item)
                else:
                    visit(child)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(value)
    unique_paths: list[str] = []
    for path in paths:
        if path not in unique_paths:
            unique_paths.append(path)
    return unique_paths


def first_string(value: Any, keys: tuple[str, ...]) -> str:
    if not isinstance(value, dict):
        return ""
    for key in keys:
        candidate = value.get(key)
        if isinstance(candidate, str):
            return candidate
    return ""


def build_payload(file_path: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {"file_path": file_path, "session_id": session_id()}
    content = first_string(tool_input, CONTENT_KEYS)
    if content:
        payload["content"] = content
    old_string = first_string(tool_input, OLD_KEYS)
    if old_string:
        payload["old_string"] = old_string
    new_string = first_string(tool_input, NEW_KEYS)
    if new_string:
        payload["new_string"] = new_string
    return payload


def run_script(script: Path, payload: dict[str, Any], tool_name: str, workspace_root: Path, via_env: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CLAUDE_TOOL_NAME"] = tool_name
    payload = {**payload, "session_id": payload.get("session_id") or session_id()}
    serialized = json.dumps(payload)
    if via_env:
        env["CLAUDE_TOOL_INPUT"] = serialized
    return subprocess.run(
        [interpreter(), str(script)] if script.suffix == ".py" else ["bash", str(script)],
        input=None if via_env else serialized,
        text=True,
        capture_output=True,
        cwd=str(workspace_root),
        env=env,
        check=False, encoding='utf-8'
    )


def forward_block(result: subprocess.CompletedProcess[str]) -> int:
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    return 2
