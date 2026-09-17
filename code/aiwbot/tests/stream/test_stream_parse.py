# test_stream_parse.py — F4 Stage 1: claude's stream-json becomes deltas, and the turn still
# reassembles into exactly the answer the batch path would have produced.
import asyncio
import json
import pathlib
from backend.base import AgentEvent, check_contract
from backend.providers.claude import ClaudeBackend
from backend.providers.claudeparse import StreamParser
from backend.providers.opencode import OpencodeBackend
from frontend.turn.dispatch import join_texts
from ..streamkit import FakeStream, deltas, result

_FIX = pathlib.Path(__file__).parent.parent / "fixtures"
# Captured live 2026-07-27 from `claude -p "count from 1 to 12, one number per line"
# --output-format stream-json --verbose --include-partial-messages`.
_STREAM = (_FIX / "claude_stream.jsonl").read_text(encoding='utf-8')
_EXPECTED = "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12"


def _drain(parser, text: str) -> list[AgentEvent]:
    events = []
    for line in text.splitlines():
        if line.strip():
            events.extend(parser.feed(line))
    events.extend(parser.finish())
    return events


def test_the_stream_yields_deltas_that_rebuild_the_exact_answer():
    events = _drain(StreamParser(), _STREAM)
    texts = [e for e in events if e.kind == "text"]
    assert all(e.partial for e in texts)
    assert len(texts) > 1
    assert join_texts(events) == _EXPECTED


def test_deltas_concatenate_with_nothing_not_newlines():
    """A delta boundary falls wherever the tokenizer cut — routinely mid-word. Joining those
    with "\\n" is the bug this reducer exists to prevent."""
    assert join_texts(deltas("Bom ", "di", "a, Lu", "cas")) == "Bom dia, Lucas"


def test_whole_segments_still_join_with_newlines():
    """opencode emits whole segments, not deltas: today's meaning must survive untouched."""
    segments = [AgentEvent(kind="text", text="um"), AgentEvent(kind="text", text="dois")]
    assert join_texts(segments) == "um\ndois"


def test_the_terminal_result_carries_session_cost_and_window():
    events = _drain(StreamParser(), _STREAM)
    last = [e for e in events if e.kind == "result"][-1]
    assert last.session_id == "71732f79-1e45-42cb-94bb-1538504ea58b"
    assert last.cost_usd is not None
    assert events[-1].kind == "result"


def test_the_streamed_turn_satisfies_the_backend_contract():
    ok, reason = check_contract(_drain(StreamParser(), _STREAM))
    assert ok, reason


def test_the_completed_assistant_message_is_not_double_counted():
    """The `assistant` line repeats, in full, the text the deltas just built."""
    assert join_texts(_drain(StreamParser(), _STREAM)).count("12") == 1


def test_the_session_id_is_known_before_any_text_arrives():
    """`system:init` carries it, which is what lets a bubble be anchored the moment it is born."""
    parser = StreamParser()
    for line in _STREAM.splitlines():
        if not line.strip():
            continue
        parser.feed(line)
        if parser.session_id:
            break
    assert parser.session_id
    assert not parser.saw_delta


def test_a_stream_without_deltas_degrades_to_the_result_text():
    """If --include-partial-messages ever regresses, the turn must fall back to today's answer
    rather than to an empty one. This is the rollback net, so it gets a test."""
    obj = {"type": "result", "session_id": "s9", "result": "PONG", "total_cost_usd": 0.1}
    events = _drain(StreamParser(), json.dumps(obj))
    texts = [e for e in events if e.kind == "text"]
    assert [e.text for e in texts] == ["PONG"]
    assert not any(e.partial for e in texts)
    assert join_texts(events) == "PONG"


def test_a_stream_that_never_produced_a_result_is_an_error():
    events = _drain(StreamParser(), '{"type":"system","subtype":"init","session_id":"s1"}')
    assert [e.kind for e in events] == ["error"]


def test_thinking_and_tool_argument_deltas_are_never_painted():
    """Same envelope as text; painting a tool call's JSON arguments into the chat is nonsense."""
    lines = [
        '{"type":"stream_event","event":{"type":"content_block_delta",'
        '"delta":{"type":"thinking_delta","thinking":"hmm"}}}',
        '{"type":"stream_event","event":{"type":"content_block_delta",'
        '"delta":{"type":"input_json_delta","partial_json":"{\\"a\\":"}}}',
        '{"type":"result","session_id":"s1","result":"ok"}',
    ]
    events = _drain(StreamParser(), "\n".join(lines))
    assert join_texts(events) == "ok"


def test_streaming_is_opt_in_on_both_backends():
    """Default off — the knob is the rollback Lucas can reach from his phone."""
    for backend in (ClaudeBackend(), OpencodeBackend()):
        assert backend.stream_parser() is not None


def test_claude_only_asks_for_stream_json_when_streaming():
    from backend.base import TurnOptions
    backend = ClaudeBackend()
    batch = backend.build_args("oi", None, TurnOptions())
    assert "--output-format" in batch and "json" in batch
    assert "--include-partial-messages" not in batch
    streamed = backend.build_args("oi", None, TurnOptions(stream=True))
    assert "stream-json" in streamed
    assert "--include-partial-messages" in streamed
    assert "--verbose" in streamed


def test_the_fake_stream_really_yields_over_time():
    """Guards the new test boundary itself: if `send` collected first and yielded after, every
    streaming test below would pass while proving nothing."""
    events = deltas("a", "b") + [result()]
    seen = []

    async def consume():
        async for event in FakeStream(events).send("p"):
            seen.append(len(seen))

    asyncio.run(consume())
    assert len(seen) == 3
