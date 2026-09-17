# test_b4_opencode_cwd.py — regression spec for [b4]: turns ran in the daemon's launch directory.
#
# Measured live 2026-07-29: `cwd=` on the subprocess is not enough, because opencode trusts `PWD`
# over `getcwd()` — a daemon started from /home/lucas filed every Telegram opencode session there
# and pointed its file/shell tools at it, while /resume listed the workspace root.
import asyncio
from backend import TurnOptions
from backend import proc
from backend.providers.claude import ClaudeBackend
from backend.providers.opencode import OpencodeBackend

_CWD = "/a/project"


class _FakeProc:
    returncode = 0

    async def communicate(self):
        return b"", b""


def _spawn_recorder(seen: list):
    async def fake_exec(*args, **kwargs):
        seen.append(kwargs)
        return _FakeProc()
    return fake_exec


def _run(backend, monkeypatch, options: TurnOptions) -> dict:
    seen: list = []
    recorder = _spawn_recorder(seen)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", recorder)
    args = backend.build_args("oi", None, options)
    extra = backend.env(options)
    asyncio.run(proc.run_capture(args, _CWD, extra))
    return seen[0]


def test_pwd_names_the_directory_the_turn_was_given(monkeypatch):
    """The bug: PWD came from wherever the daemon was launched, so it disagreed with cwd on every
    turn. They are the same fact and must not be able to disagree."""
    kwargs = _run(OpencodeBackend(), monkeypatch, TurnOptions())
    env = kwargs["env"]
    assert kwargs["cwd"] == _CWD
    assert env["PWD"] == _CWD, "opencode reads PWD in preference to its real working directory"


def test_both_backends_are_pinned_the_same_way(monkeypatch):
    """Symmetry: it is the subprocess driver that pins PWD, not one provider's override, so a
    third backend cannot inherit the bug by forgetting to opt in."""
    kwargs = _run(ClaudeBackend(), monkeypatch, TurnOptions())
    env = kwargs["env"]
    assert env["PWD"] == _CWD
    assert env["CLAUDE_CODE_ENTRYPOINT"], "the backend's own knobs still reach the child"


def test_a_backend_knob_cannot_take_pwd_over(monkeypatch):
    """A backend that sets PWD itself would resurrect the bug quietly, so the driver has the last
    word — it applies PWD after the backend's own environment."""
    env = proc.child_env({"PWD": "/somewhere/else", "OPENCODE_CONFIG_CONTENT": "{}"}, _CWD)
    assert env["PWD"] == _CWD
    assert env["OPENCODE_CONFIG_CONTENT"] == "{}"


def test_the_streaming_path_pins_it_too(monkeypatch):
    """Streaming spawns through a different function, and b4 would have survived in half the code
    if only the batch path were fixed."""
    seen: list = []
    recorder = _spawn_recorder(seen)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", recorder)

    async def drain():
        async for _ in proc.stream_lines(["echo"], _CWD, None):
            break

    try:
        asyncio.run(drain())
    except AttributeError:
        pass  # the fake process has no stdout; the spawn is what this asserts
    env = seen[0]["env"]
    assert env["PWD"] == _CWD
