# test_b2_opencode_error.py — regression spec for [b2]: opencode failures collapsing to the
# useless "no text event". The fixture is a REAL payload captured off the CLI (b2 asked for
# exactly that, twice unsuccessfully): `opencode run --format json -m <bogus model>`, which
# streams a type=error line AND exits 0 — the pair that made the old code fall silent.
import pathlib
import pytest
from backend.providers.opencode import parse_events
from backend.proc import events_from_run
from backend.base import AgentEvent, check_contract
from frontend.turn.dispatch import events_to_result, DispatchError

_FIXTURE = pathlib.Path(__file__).parent.parent / "fixtures" / "opencode_error.jsonl"
_REAL_MESSAGE = "Unexpected server error. Check server logs for details."


def _stdout() -> str:
    return _FIXTURE.read_text(encoding='utf-8')


def test_an_error_line_becomes_an_error_event_carrying_the_real_reason():
    events = parse_events(_stdout())
    errors = [e for e in events if e.kind == "error"]
    assert len(errors) == 1
    assert errors[0].text == _REAL_MESSAGE


def test_the_error_event_keeps_the_session_it_belongs_to():
    events = parse_events(_stdout())
    assert events[0].session_id == "ses_05fcb5a5fffeb5XeVjsspgn62Z"


def test_the_nested_message_wins_over_the_useless_outer_name():
    """opencode labels everything UnknownError; the cause lives one level down."""
    events = parse_events(_stdout())
    assert "UnknownError" not in events[0].text


def test_a_bare_name_is_used_when_there_is_no_nested_message():
    line = '{"type":"error","sessionID":"s1","error":{"name":"RateLimited"}}'
    events = parse_events(line)
    assert events[0].text == "RateLimited"


def test_an_unrecognized_error_shape_still_names_itself():
    """No branch matches, so the raw object is quoted rather than dropped."""
    line = '{"type":"error","sessionID":"s1","error":"just a string"}'
    events = parse_events(line)
    assert events[0].kind == "error"
    assert "just a string" in events[0].text


def test_the_user_sees_the_reason_not_the_contract_complaint():
    """End to end: the old path raised DispatchError('no text event') here."""
    events = parse_events(_stdout())
    with pytest.raises(DispatchError) as caught:
        events_to_result(events)
    assert _REAL_MESSAGE in str(caught.value)
    assert "no text event" not in str(caught.value)


# --- the net: a parser recognizing NOTHING must not hand the frontend an empty list ---

def test_zero_recognized_events_on_a_clean_exit_still_reports_something():
    """The exact b2 pathing: exit 0, stdout present, no branch matches it."""
    out = '{"type":"some_future_shape","detail":"reason nobody parsed"}\n'
    events = events_from_run(out, "", 0, lambda _: [])
    assert len(events) == 1
    assert events[0].kind == "error"
    assert "reason nobody parsed" in events[0].text


def test_the_net_falls_back_to_stderr_when_the_cli_streamed_nothing():
    events = events_from_run("", "segfault in provider", 0, lambda _: [])
    assert "segfault in provider" in events[0].text


def test_a_parser_that_did_recognize_events_is_left_alone():
    parsed = [AgentEvent(kind="text", text="hi"), AgentEvent(kind="result", session_id="s1")]
    events = events_from_run("whatever", "", 0, lambda _: parsed)
    assert events == parsed
    ok, _ = check_contract(events)
    assert ok
