# streamkit.py — shared streaming-test scaffolding: an async-generator fake backend and a clock.
# The suite had no async-generator fake at all before F4 — every backend was faked at the pure
# parser boundary or by monkeypatching `dispatch.turn` as a plain coroutine, neither of which can
# exercise "events arrive over time". This is that missing boundary.
from __future__ import annotations
import asyncio
from backend.base import AgentEvent


def deltas(*texts: str, session_id: str = "s1") -> list[AgentEvent]:
    """Text events as DELTAS — what a streaming claude turn looks like."""
    return [AgentEvent(kind="text", text=t, session_id=session_id, partial=True) for t in texts]


def result(session_id: str = "s1", **kw) -> AgentEvent:
    return AgentEvent(kind="result", session_id=session_id, **kw)


class FakeStream:
    """A backend whose `send` yields a scripted list one event at a time, surrendering control
    between each so a consumer really does observe them arriving rather than all at once."""

    def __init__(self, events: list[AgentEvent]):
        self.events = events
        self.sent_with: dict | None = None

    async def send(self, prompt: str, *, session_id=None, cwd="", options=None):
        self.sent_with = {"prompt": prompt, "session_id": session_id, "options": options}
        for event in self.events:
            await asyncio.sleep(0)
            yield event


class Clock:
    """Monotonic time under test control, so throttle behaviour is asserted rather than waited
    for. Matches `time.monotonic`'s signature so it can be injected in its place."""

    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds
