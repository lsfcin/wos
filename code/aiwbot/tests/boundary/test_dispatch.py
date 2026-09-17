# test_dispatch.py — free unit test: AgentEvent list -> TurnResult, using Phase A fixtures.
import pathlib
import pytest
from backend.base import AgentEvent
from backend.providers.claude import parse_events as claude_parse
from backend.providers.opencode import parse_events as opencode_parse
from frontend.turn.dispatch import DispatchError, events_to_result

_FIX = pathlib.Path(__file__).parent.parent / "fixtures"


def test_claude_fixture_consolidates_to_result():
    events = claude_parse((_FIX / "claude_pong.json").read_text(encoding='utf-8'))
    result = events_to_result(events)
    assert result.text == "PONG"
    assert result.session_id == "abc12345-6789-42ab-9cde-0123456789ab"
    assert result.cost_usd == 0.1021


def test_opencode_fixture_consolidates_to_result():
    events = opencode_parse((_FIX / "opencode_pong.jsonl").read_text(encoding='utf-8'))
    result = events_to_result(events)
    assert "PONG" in result.text
    assert result.session_id


def test_error_event_raises_dispatch_error():
    events = [AgentEvent(kind="error", text="boom")]
    with pytest.raises(DispatchError, match="boom"):
        events_to_result(events)


def test_missing_result_event_raises_dispatch_error():
    events = [AgentEvent(kind="text", text="hi")]
    with pytest.raises(DispatchError):
        events_to_result(events)


def test_model_flows_from_result_event():
    events = [
        AgentEvent(kind="text", text="hi", session_id="s1"),
        AgentEvent(kind="result", session_id="s1", cost_usd=0.01, model="claude-sonnet-5"),
    ]
    result = events_to_result(events)
    assert result.model == "claude-sonnet-5"
