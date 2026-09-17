# dispatch.py — one call site that drains any AgentBackend.send() into a single reply.
from __future__ import annotations
from dataclasses import dataclass
from backend import get_backend, TurnOptions
from backend.base import check_contract


@dataclass
class TurnResult:
    text: str
    session_id: str
    cost_usd: float | None
    model: str | None = None
    context_used: int | None = None
    context_window: int | None = None


class DispatchError(Exception):
    pass


def join_texts(events: list) -> str:
    """Reassemble the answer from its text events.

    Whole segments join with a newline (two `text` events from opencode are two paragraphs), but
    DELTAS must concatenate with nothing: a delta boundary falls wherever the model's tokenizer
    happened to cut, routinely mid-word, and a newline there would corrupt the answer (F4)."""
    parts: list[str] = []
    for event in events:
        if event.kind != "text":
            continue
        joiner = "" if event.partial else "\n"
        if parts:
            parts.append(joiner)
        parts.append(event.text)
    return "".join(parts)


def events_to_result(events: list) -> TurnResult:
    """Pure (free to unit-test): AgentEvent list -> single reply, or raises DispatchError."""
    errors = [e for e in events if e.kind == "error"]
    if errors:
        raise DispatchError(errors[-1].text)
    ok, reason = check_contract(events)
    if not ok:
        raise DispatchError(reason)
    result = [e for e in events if e.kind == "result"][-1]
    body = join_texts(events)
    return TurnResult(text=body, session_id=result.session_id, cost_usd=result.cost_usd,
                      model=result.model, context_used=result.context_used,
                      context_window=result.context_window)


async def turn(prompt: str, *, session_id: str | None, backend_name: str, cwd: str,
               options: TurnOptions = TurnOptions(), on_text=None) -> TurnResult:
    """`on_text` is called with each text event's payload as it arrives — the DELTA, not the
    accumulation, so the caller owns its own buffer and this stays one append per event. The
    authoritative text is still joined here at the end, so a painter is a side channel that
    cannot corrupt the delivered answer."""
    backend = get_backend(backend_name)
    stream = backend.send(prompt, session_id=session_id, cwd=cwd, options=options)
    events = []
    async for event in stream:
        events.append(event)
        if on_text is not None and event.kind == "text":
            await on_text(event.text, event.session_id)
    if options.stream:
        _log_stream(events)
    return events_to_result(events)


def _log_stream(events: list) -> None:
    """Stage 1 has no visible change by design, so this line is the only evidence the streaming
    path ran at all — and, tailed during a turn, that events arrive BEFORE the CLI exits."""
    chunks = [e for e in events if e.kind == "text"]
    body = join_texts(events)
    print(f"stream: {len(body)} chars, {len(chunks)} chunks")
