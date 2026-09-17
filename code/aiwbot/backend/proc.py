# proc.py — subprocess driver + run-result → events handling (shared by all CLI backends).
from __future__ import annotations
import asyncio
import os
from typing import AsyncIterator, Callable
from .base import AgentEvent

# asyncio's stream reader defaults to a 64 KB line limit and raises once a line exceeds it. One
# stream-json line carrying a big tool result blows past that, so the limit is raised to 1 MB —
# a failure that only ever appears live, on exactly the long turns streaming exists to serve.
_STREAM_LIMIT = 1 << 20


async def run_capture(args: list[str], cwd: str, extra_env: dict | None = None) -> tuple[str, str, int]:
    """Run args in cwd, wait, return (stdout, stderr, returncode). communicate() drains pipes safely.
    extra_env overlays the daemon's environment (backends use it for provider-specific knobs)."""
    pipe = asyncio.subprocess.PIPE
    env = child_env(extra_env, cwd)
    proc = await asyncio.create_subprocess_exec(*args, cwd=cwd, stdout=pipe, stderr=pipe, env=env)
    out_bytes, err_bytes = await proc.communicate()
    code = proc.returncode
    out = out_bytes.decode()
    err = err_bytes.decode()
    return out, err, code


def child_env(extra_env: dict | None, cwd: str) -> dict:
    """The child's environment: the daemon's, plus the backend's knobs, plus `PWD` forced to the
    directory the turn was actually given (b4).

    PWD is not decoration. Measured 2026-07-29: opencode reads it in preference to its real
    working directory, so a daemon launched from `/home/lucas` ran every opencode turn's tools —
    and FILED every opencode session — in his home directory while the boundary, and the `/resume`
    picker, believed the workspace root. `cwd=` on the subprocess is necessary and was never
    sufficient, because a shell exports PWD and children trust it over `getcwd()`."""
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    env["PWD"] = cwd
    return env


async def _drain(stream) -> str:
    """Read a pipe to EOF. stderr MUST be drained by its own task while stdout is being read:
    a child whose stderr pipe fills simply blocks forever, and it would do so only on long
    turns — the ones streaming exists for."""
    data = await stream.read()
    return data.decode(errors="replace")


async def stream_lines(args: list[str], cwd: str, extra_env: dict | None = None
                       ) -> AsyncIterator[tuple[str, str, int]]:
    """Run args and yield `("line", text, 0)` as each stdout line arrives, then exactly one
    `("end", stderr, returncode)` after the process has EXITED.

    The terminal tuple is not decoration: occupancy is read from the provider's store, which is
    only written when the CLI exits, so a caller that emits its result event before the "end"
    would silently regress b3/AD-24."""
    env = child_env(extra_env, cwd)
    pipe = asyncio.subprocess.PIPE
    proc = await asyncio.create_subprocess_exec(*args, cwd=cwd, stdout=pipe, stderr=pipe,
                                                env=env, limit=_STREAM_LIMIT)
    errors = asyncio.create_task(_drain(proc.stderr))
    async for raw in proc.stdout:
        text = raw.decode(errors="replace").strip()
        if text:
            yield ("line", text, 0)
    await proc.wait()
    err = await errors
    code = proc.returncode or 0
    yield ("end", err, code)


_TAIL_CHARS = 500
_SILENT = ("the CLI exited {code} and produced output this backend does not recognize. "
           "Raw tail:\n{tail}")


def silent_run(err: str, code: int) -> str:
    """The message for a run that produced nothing a parser recognized. Shared by both paths so
    a streaming failure reads exactly like the batch one it replaced."""
    tail = _tail("", err)
    return _SILENT.format(code=code, tail=tail)


def _tail(out: str, err: str) -> str:
    """Whatever the CLI actually said. stdout first — a CLI that streamed something we failed
    to parse put the reason there; stderr is the fallback for one that never streamed at all."""
    source = out.strip() or err.strip()
    return source[-_TAIL_CHARS:]


def events_from_run(out: str, err: str, code: int, parse: Callable[[str], list[AgentEvent]]) -> list[AgentEvent]:
    """Hard-fail (nonzero + empty stdout) -> one error event; otherwise delegate to the backend
    parser. A parser that recognizes NOTHING is also a failure: b2 had opencode exit 0 while
    streaming an error shape no `_line_to_event` branch matched, so zero events reached the
    frontend and `check_contract` reported the useless "no text event" instead of the real
    reason. Quoting the raw tail means the next unrecognized shape names itself."""
    failed = code != 0 and not out.strip()
    events: list[AgentEvent] = []
    if failed:
        tail = _tail(out, err)
        events.append(AgentEvent(kind="error", text=tail))
    else:
        events = parse(out)
    if not events:
        tail = _tail(out, err)
        text = _SILENT.format(code=code, tail=tail)
        events = [AgentEvent(kind="error", text=text)]
    return events
