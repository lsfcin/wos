# T0: Antigravity provider shim unit test suite.
import json
import subprocess
import uuid
from pathlib import Path

from conftest import WORKSPACE_ROOT
from platform_law import interpreter

SHIM = WORKSPACE_ROOT / "core/hooks/antigravity/antigravity_policy.py"


def _run_shim(event: str, payload: dict, env: dict | None = None) -> dict:
    proc = subprocess.run(
        [interpreter(), str(SHIM), event],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_ROOT),
        env=env, encoding='utf-8'
    )
    assert proc.returncode == 0, f"Shim failed: {proc.stderr}"
    return json.loads(proc.stdout) if proc.stdout.strip() else {}


def test_feature_toggle_disabled(monkeypatch):
    monkeypatch.setenv("WOS_FEATURES_OFF", "antigravity-hooks")
    res = _run_shim("PreToolUse", {
        "conversationId": str(uuid.uuid4()),
        "toolCall": {"name": "run_command", "args": {"CommandLine": "ls"}},
    })
    assert res == {"decision": "allow"}


def test_pre_tool_run_command_allowed():
    sid = str(uuid.uuid4())
    res = _run_shim("PreToolUse", {
        "conversationId": sid,
        "toolCall": {"name": "run_command", "args": {"CommandLine": "echo 'hello world'"}},
    })
    assert res.get("decision") == "allow"


def test_pre_tool_run_command_blocked_context_gate():
    sid = str(uuid.uuid4())
    cmd = "wc -l core/hooks/brain/brain_attention.py"
    res = _run_shim("PreToolUse", {
        "conversationId": sid,
        "toolCall": {"name": "run_command", "args": {"CommandLine": cmd}},
    })
    assert res.get("decision") == "deny"
    assert "CONTEXT GATE" in res.get("reason", "")


def test_pre_tool_run_command_warns_heredoc():
    sid = str(uuid.uuid4())
    cmd = "cat << 'EOF' > notes.md\nsome content\nEOF"
    res = _run_shim("PreToolUse", {
        "conversationId": sid,
        "toolCall": {"name": "run_command", "args": {"CommandLine": cmd}},
    })
    assert res.get("decision") == "allow"
    assert "UNGATED WRITE" in res.get("reason", "")


def test_pre_tool_view_file_unseen_subtree_blocked():
    sid = str(uuid.uuid4())
    target = WORKSPACE_ROOT / "core/hooks/brain/brain_attention.py"
    res = _run_shim("PreToolUse", {
        "conversationId": sid,
        "toolCall": {"name": "view_file", "args": {"AbsolutePath": str(target)}},
    })
    assert res.get("decision") == "deny"
    assert "CONTEXT GATE" in res.get("reason", "") or "READ INTERFACE FIRST" in res.get("reason", "")


def test_pre_tool_grep_search_unseen_subtree_blocked():
    sid = str(uuid.uuid4())
    target = WORKSPACE_ROOT / "core/hooks/brain"
    res = _run_shim("PreToolUse", {
        "conversationId": sid,
        "toolCall": {"name": "grep_search", "args": {"SearchPath": str(target), "Query": "test"}},
    })
    assert res.get("decision") == "deny"
    assert "CONTEXT GATE" in res.get("reason", "")


def test_pre_tool_write_to_file_size_gate_blocked():
    sid = str(uuid.uuid4())
    target = WORKSPACE_ROOT / "core/hooks/test_large_file.py"
    long_content = "# Description\n" + "\n".join(f"x_{i} = {i}" for i in range(250))
    res = _run_shim("PreToolUse", {
        "conversationId": sid,
        "toolCall": {"name": "write_to_file", "args": {"TargetFile": str(target), "CodeContent": long_content}},
    })
    assert res.get("decision") == "deny"
    assert "SIZE GATE" in res.get("reason", "") or "CONTEXT GATE" in res.get("reason", "")


def test_post_tool_view_file_records_tracker():
    sid = str(uuid.uuid4())
    target = WORKSPACE_ROOT / "core/hooks/antigravity/CONTEXT.md"
    res = _run_shim("PostToolUse", {
        "conversationId": sid,
        "toolCall": {"name": "view_file", "args": {"AbsolutePath": str(target)}},
    })
    assert res == {}


def test_pre_invocation_returns_dict():
    sid = str(uuid.uuid4())
    res = _run_shim("PreInvocation", {
        "conversationId": sid,
        "invocationNum": 2,
    })
    assert isinstance(res, dict)
