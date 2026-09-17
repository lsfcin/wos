# claudeparse.py — claude's output → AgentEvents, both shapes: one result object, and stream-json.
# Split out of claude.py for F4: that file was 194/200 and a stream parser does not fit under the
# gate. claude.py keeps the backend class and its store reads; parsing lives here.
from __future__ import annotations
from ..base import AgentEvent, try_json

# What a streaming line can be. Measured live 2026-07-27 against
# `claude -p --output-format stream-json --verbose --include-partial-messages`:
#   system(subtype=init|status|hook_*)  — the FIRST carrier of session_id, before any text
#   stream_event(event.type=content_block_delta, event.delta.type=text_delta)  — the deltas
#   assistant  — the COMPLETED message; its text duplicates the deltas, so it is ignored
#   rate_limit_event / result
_TEXT_DELTA = "text_delta"


def _last_json_object(stdout: str) -> dict | None:
    """claude -p --output-format json prints one result object; scan from the end for it."""
    lines = stdout.splitlines()
    found: dict | None = None
    for line in reversed(lines):
        stripped = line.strip()
        if stripped.startswith("{"):
            found = try_json(stripped)
        if found is not None:
            break
    return found


def _model_of(obj: dict) -> str | None:
    """claude reports the model as the key of `modelUsage` (e.g. claude-sonnet-5)."""
    usage = obj.get("modelUsage") or {}
    keys = list(usage)
    result = keys[0] if keys else None
    return result


def _context_of(obj: dict, model: str | None) -> tuple[int | None, int | None]:
    """Only the WINDOW comes from the result object; occupancy does not (b3).

    `modelUsage[model]` aggregates every API request the invocation made, and a turn that used
    tools re-read the whole context from cache on each one — so summing its token fields
    measures SPEND, not how full the window is. Measured over real transcripts, those sums reach
    6190% and 32533% of the window, and even a modest 4-8 request turn lands at the 100-200%
    Lucas reported. `ocstore.py` already carried this exact warning for opencode's `tokens_*`
    columns; the claude path walked into it anyway.

    Occupancy is a property of the LAST request alone, and the transcript records it per
    message — so it is read there, via `ClaudeBackend.occupancy`. The window is static metadata
    and stays safe to take from here."""
    usage = obj.get("modelUsage") or {}
    entry = usage.get(model or "") or {}
    window = entry.get("contextWindow")
    return None, window


def _result_events(obj: dict, with_text: bool) -> list[AgentEvent]:
    """The terminal result object → events. `with_text` is False when the stream already
    delivered the answer as deltas, so re-emitting `result` would duplicate every word."""
    sid = obj.get("session_id")
    events: list[AgentEvent] = []
    if obj.get("is_error"):
        events.append(AgentEvent(kind="error", text=obj.get("result", ""), session_id=sid))
    else:
        model = _model_of(obj)
        used, window = _context_of(obj, model)
        if with_text:
            events.append(AgentEvent(kind="text", text=obj.get("result", ""), session_id=sid))
        events.append(AgentEvent(kind="result", session_id=sid, cost_usd=obj.get("total_cost_usd"),
                                 model=model, context_used=used, context_window=window))
    return events


def _object_to_events(obj: dict) -> list[AgentEvent]:
    return _result_events(obj, with_text=True)


def parse_events(stdout: str) -> list[AgentEvent]:
    """Pure normalizer (free to unit-test): claude result object -> AgentEvents."""
    obj = _last_json_object(stdout)
    events: list[AgentEvent] = []
    if obj is None:
        events.append(AgentEvent(kind="error", text="no JSON result in claude output"))
    else:
        events = _object_to_events(obj)
    return events


def _delta_text(obj: dict) -> str | None:
    """The text of a `content_block_delta`, or None for any other stream_event. Filtering on
    `text_delta` matters: the same envelope also carries `thinking_delta` and `input_json_delta`
    (a tool call's arguments), and painting those into the chat would be nonsense."""
    event = obj.get("event") or {}
    result = None
    if event.get("type") == "content_block_delta":
        delta = event.get("delta") or {}
        if delta.get("type") == _TEXT_DELTA:
            result = delta.get("text") or ""
    return result


class StreamParser:
    """One line of `--output-format stream-json` at a time.

    Emits text as DELTAS (`partial=True`) so the frontend can paint them as they land. The
    `assistant` line that follows a run of deltas is the same text completed, so it is dropped —
    honouring it would double every word."""

    def __init__(self) -> None:
        self.session_id: str | None = None
        self.saw_delta = False
        self.result: dict | None = None

    def feed(self, line: str) -> list[AgentEvent]:
        obj = try_json(line)
        events: list[AgentEvent] = []
        if obj is None:
            return events
        sid = obj.get("session_id")
        if sid:
            self.session_id = sid
        kind = obj.get("type")
        if kind == "stream_event":
            text = _delta_text(obj)
            if text:
                self.saw_delta = True
                events.append(AgentEvent(kind="text", text=text, session_id=self.session_id,
                                         partial=True))
        elif kind == "result":
            self.result = obj
        return events

    def finish(self) -> list[AgentEvent]:
        """The terminal events, held back until the stream ends so occupancy can be read after
        the CLI exits. If no delta ever arrived — `--include-partial-messages` unsupported or
        regressed — the result object's own text is emitted instead, so the turn degrades to the
        non-streaming behaviour rather than to an empty answer."""
        events: list[AgentEvent] = []
        if self.result is None:
            events.append(AgentEvent(kind="error", text="no JSON result in claude output",
                                     session_id=self.session_id))
        else:
            events = _result_events(self.result, with_text=not self.saw_delta)
        return events
