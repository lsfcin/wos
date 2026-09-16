# Antigravity provider shim: translates Antigravity lifecycle events to canonical WOS gates.

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law
from platform_law import WORKSPACE_ROOT, interpreter

HOOKS = Path(__file__).resolve().parents[1]


def run_gate(script: str, payload: dict[str, Any], tool: str, extra_args: list[str] | None = None) -> tuple[int, str]:
    full_path = HOOKS / script
    cmd = [interpreter(), str(full_path)] if full_path.suffix == ".py" else ["bash", str(full_path)]
    if extra_args:
        cmd.extend(extra_args)
    env = {**os.environ, "CLAUDE_TOOL_NAME": tool}
    data = json.dumps(payload)
    env["CLAUDE_TOOL_INPUT"] = data
    proc = subprocess.run(cmd, input=data, text=True, capture_output=True, cwd=str(WORKSPACE_ROOT), env=env, check=False, encoding='utf-8')
    msg = (proc.stderr or proc.stdout).strip()
    return proc.returncode, msg


def said(msg: str) -> str:
    """A dispatcher's exit-0 stdout is a hookSpecificOutput document; Antigravity wants prose."""
    try:
        return str(json.loads(msg)["hookSpecificOutput"]["additionalContext"]).strip()
    except (ValueError, KeyError, TypeError):
        return msg


# ARGUMENT NAMES ARE THIS SHIM'S JOB; THE GATE LIST IS NOT. Antigravity spells one file path four
# ways (AbsolutePath, TargetFile, SearchPath, CommandLine), which only a per-tool branch can
# translate. Which gates then run used to be spelled out here too — five hand-copied orderings of
# core/hooks/gates.txt, drifting the moment either side changed. The branches now produce a
# canonical payload and stop; core/hooks/dispatch.py reads the capability off it.
def pre_tool(call: dict[str, Any], sid: str) -> dict[str, Any]:
    name = call.get("name", "")
    args = call.get("args") or {}
    payload: dict[str, Any] | None = None
    tool = ""

    if name == "view_file":
        payload, tool = {"file_path": args.get("AbsolutePath", "")}, "Read"
    elif name == "replace_file_content":
        payload, tool = {"file_path": args.get("TargetFile", ""),
                         "old_string": args.get("TargetContent", ""),
                         "new_string": args.get("ReplacementContent", "")}, "Edit"
    elif name == "write_to_file":
        payload, tool = {"file_path": args.get("TargetFile", ""),
                         "content": args.get("CodeContent", "")}, "Write"
    elif name == "run_command":
        payload, tool = {"command": args.get("CommandLine", "")}, "Bash"
    elif name == "grep_search":
        payload, tool = {"path": args.get("SearchPath", "")}, "Grep"
    elif name == "invoke_subagent":
        # Not in gates.txt: this fires on a moment (a worker being spawned) rather than on what a
        # call does to a file, so it keeps its own registration here and in every other harness.
        subs = args.get("Subagents", [])
        txt = "\n".join(s.get("Prompt", "") for s in subs if isinstance(s, dict))
        _, msg = run_gate("read/agent-context.py",
                          {"prompt": txt, "session_id": sid, "prompt_id": sid}, "Agent")
        return {"decision": "allow", "reason": msg} if msg else {"decision": "allow"}

    if payload is None:
        return {"decision": "allow"}

    rc, msg = run_gate("dispatch.py", {**payload, "session_id": sid}, tool)
    if rc == 2:
        return {"decision": "deny", "reason": msg or "Blocked by a workspace gate"}
    return {"decision": "allow", "reason": said(msg)} if msg else {"decision": "allow"}


# THE SAME RULE ON THE WAY BACK OUT (2026-09-06, b20260905). `pre_tool` above stopped hand-copying
# gates.txt on 2026-09-05 and this half was left naming facade-tracker.py and context-tracker.py
# itself — the two `post read` rows, in a second copy that drifts the moment the table changes.
# post-edit.sh is the one thing that cannot move into the table: its rows are imported into the
# dispatcher's own process and post-edit.sh is bash.
def post_tool(call: dict[str, Any], sid: str) -> dict[str, Any]:
    name = call.get("name", "")
    args = call.get("args") or {}
    if name == "view_file":
        run_gate("dispatch.py", {"file_path": args.get("AbsolutePath", ""), "session_id": sid,
                                 "hook_event_name": "PostToolUse"}, "Read")
    elif name in ("replace_file_content", "write_to_file"):
        path = args.get("TargetFile", "")
        tool = "Write" if name == "write_to_file" else "Edit"
        p = {"file_path": path, "session_id": sid}
        if name == "write_to_file":
            p["content"] = args.get("CodeContent", "")
        else:
            p["old_string"] = args.get("TargetContent", "")
            p["new_string"] = args.get("ReplacementContent", "")
        run_gate("post-edit.sh", p, tool)
    return {}


def pre_invocation(data: dict[str, Any]) -> dict[str, Any]:
    msgs: list[str] = []
    sid = str(data.get("conversationId", ""))
    inv_num = data.get("invocationNum", 0)
    if inv_num == 1:
        run_gate("session/session-prune.py", {}, "SessionStart")
        run_gate("git/branch_marker.py", {}, "SessionStart", extra_args=["record"])
        for script in ("session/mirror-heal.py", "session/inbox-nudge.py",
                       "session/compass-nudge.py"):
            _, msg = run_gate(script, {}, "SessionStart")
            if msg:
                msgs.append(msg)
    _, meter = run_gate("session/context-meter.py", {"session_id": sid}, "PreInvocation")
    if meter:
        msgs.append(meter)
    combined = "\n\n".join(m for m in msgs if m.strip())
    return {"injectSteps": [{"ephemeralMessage": combined}]} if combined else {}


def main() -> int:
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    if not feature_law.is_enabled("antigravity-hooks"):
        empty: dict[str, Any] = {"decision": "allow"} if event == "PreToolUse" else {}
        print(json.dumps(empty))
        return 0

    sid = str(data.get("conversationId") or os.getppid())
    res: dict[str, Any] = {}
    if event == "PreToolUse":
        res = pre_tool(data.get("toolCall") or {}, sid)
    elif event == "PostToolUse":
        res = post_tool(data.get("toolCall") or {}, sid)
    elif event == "PreInvocation":
        res = pre_invocation(data)

    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
