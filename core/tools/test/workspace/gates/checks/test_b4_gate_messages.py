# T0: a hook must speak on the channel its class is read on. Two mirrored rules, one subject.
#
# A BLOCKING gate says why on stderr: Claude Code feeds a PreToolUse exit-2's stderr back to
# the model and drops stdout, so a gate printing to stdout blocks the edit with no reason
# attached — it reads as "No stderr output".
#
# An INFORMING hook says it in hookSpecificOutput.additionalContext, the only non-blocking
# channel that reaches the model. exit-0 stdout is transcript-only. Both halves are the same
# failure — a hook that runs, exits cleanly, and is heard by nobody. See core/hooks/SPECS.md.
import contextlib
import json
import re
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from conftest import WORKSPACE_ROOT
from platform_law import interpreter, rel

# Any file under a subtree carrying a CONTEXT.md chain; its content is irrelevant.
DEEP_FILE = WORKSPACE_ROOT / "core/hooks/brain/brain_attention.py"

# SERIAL: `payload()` builds a real module under code/ and removes it. b20260902's third case.
pytestmark = pytest.mark.serial

# Every gate wired as a blocking PreToolUse hook. The write pair were one file, pre-edit.py, until
# 2026-09-14, and it was the only one of six on stdout — which is why this went unnoticed for so
# long: five siblings were correct. They split so gates.txt could attribute a block to a feature.
BLOCKING_GATES = (
    "core/hooks/checks/first-line-gate.py",
    "core/hooks/checks/size-gate.py",
    "core/hooks/checks/issues-gate.py",
    "core/hooks/read/context-gate.py",
    "core/hooks/read/bash-context-gate.py",
    "core/hooks/read/spec-read-gate.py",
    "core/hooks/facade/facade-gate.py",
)

# The two halves of the former pre-edit.py, plus the module they share. Every message in all three
# is a rejection, so none of them belongs on stdout.
WRITE_GATE_SOURCES = (
    "core/hooks/checks/first-line-gate.py",
    "core/hooks/checks/size-gate.py",
    "core/hooks/checks/write_payload.py",
)


def _run_gate(gate: str, payload: dict) -> subprocess.CompletedProcess:
    payload.setdefault("session_id", f"test-{uuid.uuid4()}")
    payload.setdefault("cwd", str(WORKSPACE_ROOT))
    return subprocess.run(
        [interpreter(), str(WORKSPACE_ROOT / gate)], input=json.dumps(payload),
        capture_output=True, text=True, encoding='utf-8'
    )


@contextlib.contextmanager
def _blocking_case(gate: str, tmp_path: Path):
    """A payload that really makes `gate` block, and the marker its reason must carry.

    One per gate because there is no generic way to trip six different rules — which is
    exactly why the source-grep this replaced was tempting, and exactly what it cost.
    """
    # Matched on the exact basename, never endswith: "bash-context-gate.py" ends with
    # "context-gate.py", so a suffix test silently handed the Bash gate a Read payload and
    # the case passed by not blocking. Found while writing this, 2026-08-24.
    name = gate.rsplit("/", 1)[-1]
    if name == "first-line-gate.py":
        yield {"tool_name": "Write", "tool_input": {
            "file_path": str(tmp_path / "p.py"), "content": "x = 1\n"}}, "FIRST-LINE MISSING"
    elif name == "size-gate.py":
        yield {"tool_name": "Write", "tool_input": {
            "file_path": str(tmp_path / "big.py"),
            "content": "# big\n" + "x = 1\n" * 400}}, "SIZE GATE"
    elif name == "issues-gate.py":
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
        yield {"tool_name": "Write", "tool_input": {
            "file_path": str(tmp_path / "ISSUES.md"),
            "content": "## B99 — a bug — FIXED\n"}}, "ISSUES GATE"
    elif name == "bash-context-gate.py":
        yield {"tool_name": "Bash",
               "tool_input": {"command": f"wc -l {rel(DEEP_FILE)}"}}, "CONTEXT GATE"
    elif name == "context-gate.py":
        yield {"tool_name": "Read",
               "tool_input": {"file_path": str(DEEP_FILE)}}, "CONTEXT GATE"
    elif name == "facade-gate.py":
        mod = tmp_path / "code" / "proj" / "mod"
        mod.mkdir(parents=True)
        (mod / "__init__.py").write_text("from .a import alpha\n", encoding="utf-8", newline='\n')
        (mod / "a.py").write_text("# a\nalpha = 1\n", encoding="utf-8", newline='\n')
        yield {"tool_name": "Edit", "tool_input": {
            "file_path": str(mod / "a.py"),
            "old_string": "1", "new_string": "2"}}, "READ FACADE FIRST"
    else:
        # The gate walks up to the workspace root, so the check must really live under code/.
        mod = WORKSPACE_ROOT / "code" / f"_spec_gate_check_{uuid.uuid4().hex[:8]}"
        mod.mkdir(parents=True)
        try:
            (mod / "CONTEXT.md").write_text(
                "# check\n> check module, deleted by the test that made it\n"
                "> spec: SPECS.md\n", encoding="utf-8", newline='\n')
            (mod / "SPECS.md").write_text(
                "# check\n> check spec\nstatus: locked\n", encoding="utf-8", newline='\n')
            (mod / "a.py").write_text("# a\nx = 1\n", encoding="utf-8", newline='\n')
            yield {"tool_name": "Edit", "tool_input": {
                "file_path": str(mod / "a.py"),
                "old_string": "1", "new_string": "2"}}, "SPEC GATE"
        finally:
            shutil.rmtree(mod, ignore_errors=True)


@pytest.mark.parametrize("gate", BLOCKING_GATES)
def test_every_blocking_gate_writes_its_reason_to_stderr(gate: str, tmp_path: Path) -> None:
    """Trip the gate for real, then read the channel its reason arrived on.

    This replaced `"stderr" in body` on 2026-08-24. That grep proved nothing: a gate can
    name the word in a comment and still print to stdout, which is the defect it was
    written to catch. The stdout assert below is the half a source read cannot make.
    """
    with _blocking_case(gate, tmp_path) as (payload, marker):
        done = _run_gate(gate, payload)
    assert done.returncode == 2, (
        f"{gate} did not block on a payload built to trip it — either it stopped blocking "
        f"or this case is stale. stderr: {done.stderr[:200]}"
    )
    assert marker in done.stderr, (
        f"{gate} blocked but its reason did not reach stderr — Claude Code drops stdout on "
        f"a PreToolUse block, so the edit is refused with no reason attached"
    )
    assert not done.stdout.strip(), f"{gate} put its reason on stdout, which is dropped"


# Hooks core/hooks/SPECS.md classes as "Informs": they never block, so the ONLY evidence they
# work is that their text arrives. facade-scan.py printed to stdout until 2026-08-16 and was
# read by nobody for as long as it existed — it never errored, which is exactly why nothing
# said so. facade-scan's own run is test_facade_scan_emits_valid_hook_json below.
def test_the_heredoc_gate_informs_on_the_only_channel_that_reaches_the_model() -> None:
    """Run it: `"additionalContext" in body` passed on the word appearing anywhere."""
    done = _run_gate("core/hooks/checks/heredoc-gate.py", {
        "tool_name": "Bash",
        "tool_input": {"command": "cat > brain/INBOX.md <<'EOF'\nhi\nEOF"}})
    assert done.returncode == 0
    payload = json.loads(done.stdout)["hookSpecificOutput"]
    assert payload["hookEventName"] == "PreToolUse"
    assert "brain/INBOX.md" in payload["additionalContext"]


def test_facade_scan_emits_valid_hook_json(tmp_path: Path) -> None:
    """Run it, do not read it: the defect was invisible in the source and obvious in the output."""
    module = tmp_path / "code" / "mod"
    module.mkdir(parents=True)
    (module / "__init__.py").write_text("from .a import alpha, beta\n", encoding="utf-8", newline='\n')
    result = subprocess.run(
        [interpreter(), str(WORKSPACE_ROOT / "core/hooks/facade/facade-scan.py")],
        input=json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Write",
                          "tool_input": {"file_path": str(module / "new.py"),
                                         "content": "# new\n"}}),
        capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0
    payload = json.loads(result.stdout)["hookSpecificOutput"]
    assert payload["hookEventName"] == "PreToolUse"
    assert "alpha" in payload["additionalContext"]


@pytest.mark.parametrize("source", WRITE_GATE_SOURCES)
def test_no_bare_print_survives_in_a_write_gate(source: str) -> None:
    """Every message here is a rejection; none of them belongs on stdout.

    Asked of all three because the split multiplied the surface: the rule was proved once against
    one file, and a copy of `block()` landing in either half would be exactly the regression the
    original case was written for.
    """
    body = (WORKSPACE_ROOT / source).read_text(encoding="utf-8")
    bare = [line.strip() for line in body.splitlines()
            if re.match(r'\s*print\(', line) and "stderr" not in line]
    assert not bare, f"{source} prints to stdout again: {bare}"


# Four rejections, one shape. They were three copies of these six lines until 2026-09-05, when the
# file hit its cap and the duplication was the cheapest thing in it to spend. The fourth arrived
# 2026-09-14 with the document cap: few lines, many characters, so it can only trip the new half.
@pytest.mark.parametrize("gate, name, content, reason", [
    ("first-line-gate.py", "p.py", "x = 1\n", "FIRST-LINE MISSING"),
    ("first-line-gate.py", "CONTEXT.md", "# t\nno blockquote\n",
     "CONTEXT.md DESCRIPTION MISSING"),
    ("size-gate.py", "big.py", "# big\n" + "x = 1\n" * 400, "SIZE GATE"),
    ("size-gate.py", "wide.py", "# wide\nx = '" + "a" * 19000 + "'\n", "characters"),
])
def test_a_write_rejection_lands_on_stderr(tmp_path: Path, gate, name, content, reason) -> None:
    r = _run_gate(f"core/hooks/checks/{gate}", {
        "tool_name": "Write",
        "tool_input": {"file_path": str(tmp_path / name), "content": content}})
    assert r.returncode == 2
    assert reason in r.stderr
    assert not r.stdout.strip()


@pytest.mark.parametrize("gate", ["first-line-gate.py", "size-gate.py"])
def test_an_allowed_edit_is_silent_and_exits_zero(tmp_path: Path, gate: str) -> None:
    ok = tmp_path / "ok.py"
    ok.write_text("# ok\nx = 1\n", encoding="utf-8", newline='\n')
    r = _run_gate(f"core/hooks/checks/{gate}", {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(ok), "old_string": "x", "new_string": "y"}})
    assert r.returncode == 0
    assert not r.stdout.strip() and not r.stderr.strip()
