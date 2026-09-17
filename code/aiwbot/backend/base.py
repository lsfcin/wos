# base.py — the provider-agnostic boundary: AgentEvent + AgentBackend contract + shared primitives.
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import AsyncIterator, Literal, Protocol, runtime_checkable
from .caps import Capabilities

EventKind = Literal["text", "thinking", "tool", "result", "error"]
# What the daemon's ask server calls itself in a CLI's config. It lives here rather than in the
# frontend that hosts the server, because both backends have to write it into their own config shape
# and a backend may not import the frontend — and because the model SEES it: claude exposes the tool
# as `mcp__aiwbot__ask_user`, opencode as `aiwbot_ask_user` (AD-31).
ASK_SERVER_NAME = "aiwbot"


@dataclass
class AgentEvent:
    kind: EventKind
    text: str = ""
    tool: str | None = None
    session_id: str | None = None
    cost_usd: float | None = None
    model: str | None = None
    # Context-window occupancy after this turn. Providers that don't report it leave both None.
    context_used: int | None = None
    context_window: int | None = None
    # Is this text a DELTA or a whole segment? Whole segments (the default, and every non-streaming
    # backend's behaviour) are joined with "\n"; deltas are concatenated with "", because a delta
    # boundary falls mid-word and a newline there would corrupt the answer. Defaulting to False is
    # what keeps every existing fixture and pure-parser test correct without touching them.
    partial: bool = False


@dataclass
class TurnOptions:
    """Per-turn knobs threaded from the frontend to a backend's build_args.
    Provider-agnostic: each backend maps what it can and ignores the rest.
    mode ∈ {build, plan}. title names a new session (claude --name -> visible in its /resume).
    model/effort are opaque strings the backend declared itself (see caps.Capabilities and
    AgentBackend.efforts) — the frontend never invents one, so no value needs translating."""
    mode: str = "build"
    title: str | None = None
    model: str | None = None
    effort: str | None = None
    # Ask the CLI to stream, so text can be painted as it arrives instead of after the turn.
    # Default off: it changes the CLI's invocation, so the rollback Lucas needs from his phone is
    # one line in config.json plus a restart, never a code change (F4).
    stream: bool = False
    # Where this turn may reach the daemon's own ask server, or None to leave the invocation exactly
    # as it was. A URL is the whole provider-agnostic fact; the CONFIG that carries it is not — it is
    # a different shape per provider and does not even travel the same road (claude takes JSON on the
    # argv, opencode takes it in the environment, AD-31). So each backend wraps this itself.
    ask_url: str | None = None


def add_flag(args: list[str], name: str, value: str | None) -> None:
    """Append `--name value` when value is set. Every backend builds its argv this way, so
    the guard lives here once instead of as an if/append/append triple per knob."""
    if value:
        args.append(name)
        args.append(value)


@runtime_checkable
class AgentBackend(Protocol):
    name: str

    def send(self, prompt: str, *, session_id: str | None, cwd: str,
             options: TurnOptions = TurnOptions()) -> AsyncIterator[AgentEvent]:
        ...

    def list_sessions(self, cwd: str) -> list[dict]:
        """Resumable sessions for cwd from the provider's own store, newest-first-agnostic.
        Each item: {session_id, title, updated_at}. Lets the frontend picker show sessions
        started anywhere (e.g. VSCode), not just ones the bot created."""
        ...

    def last_response(self, session_id: str, cwd: str) -> str:
        """Full text of that session's last agent answer, or "" if the provider can't say."""
        ...

    def session_detail(self, session_id: str, cwd: str) -> dict:
        """Extra picker fields (preview, context_used) that cost a per-session query, so the
        frontend asks only for the page it renders. {} when list_sessions already had them."""
        ...

    def capabilities(self) -> Capabilities:
        """Modes + models this backend can be given. The frontend offers only what lands here."""
        ...

    def efforts(self, model: str | None = None) -> list[str]:
        """Effort vocabulary for a model — per-model because opencode's `--variant` values are
        (claude's `--effort low..max` is one ladder for everything). Empty = no effort knob."""
        ...

    def supports_ask(self, options: TurnOptions) -> bool:
        """Can this backend, WITH these options, call back into the bot to ask the user? Takes
        the options because the answer is not a property of the provider alone: claude hosts MCP
        happily in build mode and refuses every MCP tool in plan mode (F4 Stage 4)."""
        ...


def try_json(text: str) -> dict | None:
    """Parse one line as a JSON object, or None if it isn't valid JSON / isn't an object."""
    result: dict | None = None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        result = parsed
    return result


@runtime_checkable
class LineParser(Protocol):
    """Turns one line of a CLI's streaming output into events, as it arrives. Stateful on
    purpose — a stream carries facts (the session id, whether any delta was seen) that only
    make sense across lines. `finish()` is the last call and is where a parser emits whatever
    it could only decide once the stream ended."""

    def feed(self, line: str) -> list[AgentEvent]:
        ...

    def finish(self) -> list[AgentEvent]:
        ...


def check_contract(events: list[AgentEvent]) -> tuple[bool, str]:
    """Minimum backend contract: >=1 text event AND a terminal result carrying a session_id."""
    texts = [e for e in events if e.kind == "text"]
    results = [e for e in events if e.kind == "result"]
    ok = True
    reason = "ok"
    if not texts:
        ok = False
        reason = "no text event"
    elif not results:
        ok = False
        reason = "no result event"
    else:
        last = results[-1]
        if not last.session_id:
            ok = False
            reason = "result missing session_id"
    return ok, reason
