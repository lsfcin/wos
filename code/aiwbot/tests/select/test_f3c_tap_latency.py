# test_f3c_tap_latency.py — F3c: a panel tap costs ONE Telegram round trip, not two or three.
#
# The bot-side work was measured at under 1 ms on every warm path, so the felt latency is round
# trips (222 ms median each from Lucas's machine). These assert the count, which is the only
# part we control — a client renders an inline keyboard from server state, so one is the floor.
import asyncio
from frontend.select import choices, panel
from frontend.session import msgmap, registry
from ..panelkit import Fake


class _Query:
    """Records not just WHAT was called but WHEN it started, so a sequential await and a
    concurrent one are distinguishable: gathered, both calls start before either finishes."""

    def __init__(self, message_id=100):
        self.message = type("M", (), {"message_id": message_id, "chat_id": 1})()
        self.trace = []
        self.notes = []
        self.drawn = []

    async def answer(self, text=None, show_alert=False):
        self.notes.append(text)
        self.trace.append("answer:start")
        await asyncio.sleep(0)
        self.trace.append("answer:end")

    async def edit_message_reply_markup(self, reply_markup=None):
        self.drawn.append(reply_markup)
        self.trace.append("edit:start")
        await asyncio.sleep(0)
        self.trace.append("edit:end")


def _tap(query, scope, data):
    asyncio.run(panel._route(query, scope, data.split(":", 3)))


def test_a_tap_answers_and_redraws_concurrently_not_one_after_the_other(store):
    """Sequential these are two round trips (~445 ms); overlapped they are one (~222 ms)."""
    query = _Query()
    _tap(query, "s1", "p:menu")
    assert query.trace == ["answer:start", "edit:start", "answer:end", "edit:end"]


def test_choosing_a_value_answers_exactly_once(store):
    """It used to answer twice — once in `_choose`, once again in the `_open` it routed into —
    making the most common tap of all cost three sequential round trips."""
    msgmap.remember_reply(100, "s1")
    query = _Query()
    _tap(query, "s1", "p:s:m:opencode/b")
    assert len(query.notes) == 1
    assert len(query.drawn) == 1


def test_the_choice_toast_survives_the_single_answer(store):
    """Collapsing two answers into one must not cost the toast that explains what changed."""
    msgmap.remember_reply(100, "s1")
    query = _Query()
    _tap(query, "s1", "p:s:m:opencode/b")
    assert "model" in query.notes[0]


def test_every_navigation_tap_is_one_answer_and_one_redraw(store):
    """`‹`, `···`, `all` and a provider page are all pure navigation — none may drift back into
    the two-call shape."""
    msgmap.remember_reply(100, "s1")
    for data in ("p:menu", "p:root", "p:d:m", "p:x:m:0", "p:g", "p:p:big:0"):
        query = _Query()
        _tap(query, "s1", data)
        assert len(query.notes) == 1, data
        assert len(query.drawn) == 1, data


def test_a_mode_button_left_in_the_chat_redraws_instead_of_setting_a_mode(store):
    """Mode is gone (2026-07-28, build only), but keyboards already sent still carry its buttons.
    A tap on one must resolve to the panel as it is now — still inside the one-round-trip rule."""
    query = _Query()
    _tap(query, "s1", "p:mode:build")
    assert len(query.notes) == 1
    assert len(query.drawn) == 1


def test_a_dimension_with_nothing_to_offer_alerts_without_redrawing(store):
    """An empty picker reports itself and leaves the keyboard alone — one call, no edit."""
    registry.set_setting("s1", "model", None)
    query = _Query()
    _tap(query, "s1", "p:d:e")
    assert len(query.notes) == 1
    assert query.drawn == []


def test_warm_asks_every_backend_for_its_declaration(monkeypatch):
    """The 839 ms `opencode models` shell belongs to startup, not to Lucas's first tap. Asked
    through the boundary, so a third backend is warmed by existing rather than by editing this."""
    asked = []

    class _Counting(Fake):
        def capabilities(self):
            asked.append("caps")
            return Fake.capabilities(self)

        def efforts(self, model=None):
            asked.append(f"efforts:{model}")
            return Fake.efforts(self, model)

    monkeypatch.setattr(choices, "backend_names", lambda: ["claude", "opencode"])
    monkeypatch.setattr(choices, "get_backend", lambda name: _Counting())
    choices.warm()
    assert asked.count("caps") == 2
    assert asked.count("efforts:opencode/a") == 2
