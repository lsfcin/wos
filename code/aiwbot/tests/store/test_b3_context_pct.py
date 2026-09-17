# test_b3_context_pct.py — regression spec for [b3]: context occupancy over 100% (even 200%).
#
# Root cause: the numerator was a SUM over every API request in the turn. A turn that used tools
# re-read the whole context from cache on each request, so the sum measured spend, not how full
# the window was. Measured over Lucas's real transcripts, those sums reach 6190% and 32533%.
import asyncio
from backend.base import AgentEvent
from backend.providers.claude import parse_events
from backend.cli import CliBackend
from frontend.text.format import context_pct

# One tool-using turn: three requests, each re-reading a context that only grew a little.
_REQUESTS = [180_000, 190_000, 200_000]
_WINDOW = 1_000_000


def _result_object() -> dict:
    total = sum(_REQUESTS)
    return {"type": "result", "session_id": "s1", "result": "hi", "total_cost_usd": 0.1,
            "modelUsage": {"claude-opus-5": {"inputTokens": total, "cacheReadInputTokens": 0,
                                             "cacheCreationInputTokens": 0,
                                             "contextWindow": _WINDOW}}}


def test_the_run_summary_no_longer_supplies_occupancy():
    """It only ever knew the total. Reporting that as occupancy is the whole bug."""
    import json
    events = parse_events(json.dumps(_result_object()))
    result = [e for e in events if e.kind == "result"][-1]
    assert result.context_used is None
    assert result.context_window == _WINDOW


def test_occupancy_comes_from_the_last_request_not_the_sum():
    """570k summed vs 200k actually resident — 57% vs the true 20%."""
    class _Backend(CliBackend):
        def occupancy(self, session_id, cwd):
            return _REQUESTS[-1]

    events = [AgentEvent(kind="result", session_id="s1", context_window=_WINDOW)]
    _Backend()._attach_measured(events, "/tmp")
    assert events[0].context_used == _REQUESTS[-1]
    assert context_pct(events[0].context_used, _WINDOW) == "20%"


def test_a_backend_that_cannot_measure_leaves_the_number_alone():
    """The default hook returns None, which must not erase a window a backend did report."""
    events = [AgentEvent(kind="result", session_id="s1", context_used=42, context_window=_WINDOW)]
    CliBackend()._attach_measured(events, "/tmp")
    assert events[0].context_used == 42


def test_only_the_result_event_is_touched():
    events = [AgentEvent(kind="text", text="oi", session_id="s1"),
              AgentEvent(kind="result", session_id="s1")]

    class _Backend(CliBackend):
        def occupancy(self, session_id, cwd):
            return 123

    _Backend()._attach_measured(events, "/tmp")
    assert events[0].context_used is None
    assert events[1].context_used == 123


def test_an_impossible_percentage_is_withheld_rather_than_shown():
    """Belt and braces: a share of the window cannot exceed the window, so if any provider ever
    reports such a pair again it goes missing instead of going on screen as '200%'."""
    assert context_pct(2_000_000, _WINDOW) is None
    assert context_pct(sum(_REQUESTS) * 10, _WINDOW) is None
    # A hair over the window is rounding, not nonsense — it still reads as full.
    assert context_pct(1_000_001, _WINDOW) == "100%"


def test_a_real_percentage_still_renders():
    assert context_pct(_WINDOW, _WINDOW) == "100%"
    assert context_pct(320_000, _WINDOW) == "32%"
    assert context_pct(None, _WINDOW) is None
    assert context_pct(320_000, None) is None
