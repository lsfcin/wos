# test_f4_streaming.py — F4 Stage 2: the live bubble. Throttle mechanics, the pin, and the
# guarantee that a streamed turn still ends as byte-for-byte today's answer.
import asyncio
from frontend.stream import answer, cadence, painter
from frontend.text import markdown
from frontend import reply
from frontend.text.htmlsplit import split_html
from ..streamkit import Clock


class _Chat:
    def __init__(self):
        self.actions = []

    async def send_action(self, action):
        self.actions.append(action)


class _LiveMsg:
    """A Telegram message that records every repaint and typing action, and can be told to
    start failing."""

    def __init__(self):
        self.edits = []
        self.fail = False
        self.concurrent = 0
        self.overlapped = False
        self.chat = _Chat()
        self.message_id = 1

    async def edit_text(self, text, parse_mode=None, reply_markup=None):
        self.concurrent += 1
        if self.concurrent > 1:
            self.overlapped = True
        await asyncio.sleep(0)
        self.concurrent -= 1
        if self.fail:
            from telegram.error import TelegramError
            raise TelegramError("flood control exceeded")
        self.edits.append(text)


def _painter(msg, clock):
    return painter.Painter(msg, "pensando…", clock=clock)


def _feed(p, chunks, clock, gap=2.0):
    async def run():
        for chunk in chunks:
            clock.advance(gap)
            await p.paint(chunk)
    asyncio.run(run())


def test_a_trickle_of_deltas_does_not_spend_a_round_trip_each():
    """MIN_GROWTH: below it a repaint moves almost nothing and costs ~200 ms (AD-20)."""
    msg, clock = _LiveMsg(), Clock()
    p = _painter(msg, clock)
    _feed(p, ["a"] * 20, clock)
    assert msg.edits == []


def test_paints_are_spaced_by_the_throttle_interval():
    msg, clock = _LiveMsg(), Clock()
    p = _painter(msg, clock)
    big = "palavra " * 20
    _feed(p, [big] * 4, clock, gap=cadence.MIN_INTERVAL)
    assert len(msg.edits) == 4
    _feed(p, [big] * 4, clock, gap=0.1)
    assert len(msg.edits) == 4


def test_a_paint_in_flight_is_dropped_never_queued():
    """Dropping is lossless — every frame is recomputed from the whole accumulated text — and
    it is what stops a fast stream from piling requests up behind a slow round trip."""
    msg, clock = _LiveMsg(), Clock()
    p = _painter(msg, clock)

    async def run():
        clock.advance(10)
        await asyncio.gather(*[p.paint("palavra " * 20) for _ in range(6)])

    asyncio.run(run())
    assert not msg.overlapped
    assert len(msg.edits) == 1


def test_a_failed_paint_widens_the_gap_and_a_good_one_narrows_it():
    msg, clock = _LiveMsg(), Clock()
    p = _painter(msg, clock)
    msg.fail = True
    _feed(p, ["palavra " * 20] * 3, clock, gap=cadence.MAX_INTERVAL)
    assert p.clock.interval > cadence.MIN_INTERVAL
    msg.fail = False
    _feed(p, ["palavra " * 20] * 4, clock, gap=cadence.MAX_INTERVAL)
    assert p.clock.interval == cadence.MIN_INTERVAL


def test_the_interval_never_runs_away():
    msg, clock = _LiveMsg(), Clock()
    p = _painter(msg, clock)
    msg.fail = True
    _feed(p, ["palavra " * 20] * 30, clock, gap=cadence.MAX_INTERVAL)
    assert p.clock.interval <= cadence.MAX_INTERVAL


def test_the_pin_sits_at_the_end_of_the_live_bubble():
    msg, clock = _LiveMsg(), Clock()
    p = _painter(msg, clock)
    _feed(p, ["primeiro paragrafo aqui.\n\nsegundo em andamento " * 3], clock, gap=10)
    assert msg.edits[-1].endswith("pensando…")


def test_the_finished_answer_carries_no_pin():
    """The pin is a streaming artefact; `answer.block` is the finished shape and must not have
    absorbed it."""
    block = answer.block("corpo", "abc12345", "titulo", provider="claude")
    assert "pensando" not in block


# --- the typing indicator (Lucas, 2026-07-27) ------------------------------------------------

def test_typing_starts_on_the_very_first_delta():
    """It must not wait for the repaint gate: the whole point is that the gap BEFORE the first
    visible words is not silent."""
    msg, clock = _LiveMsg(), Clock()
    p = _painter(msg, clock)
    _feed(p, ["a"], clock, gap=0)
    assert len(msg.chat.actions) == 1
    assert msg.edits == []


def test_typing_is_relit_but_not_spammed():
    """It expires after ~5s, so it is re-sent — but once per interval, not per delta."""
    msg, clock = _LiveMsg(), Clock()
    p = _painter(msg, clock)
    _feed(p, ["a"] * 10, clock, gap=0)
    assert len(msg.chat.actions) == 1
    _feed(p, ["a"] * 10, clock, gap=cadence.TYPING_EVERY)
    assert len(msg.chat.actions) == 11


def test_no_two_repaints_land_closer_than_the_configured_floor():
    """Lucas: the answer should land like someone typing, not like a progress bar. The number
    itself is a knob he tunes by reading real turns (5 s, then 3 s on 2026-07-27), so this pins
    the SPACING invariant against whatever the knob currently says — never a literal, which
    would have to be edited every time the feel is adjusted."""
    msg, clock = _LiveMsg(), Clock()
    p = _painter(msg, clock)
    at = []
    original = msg.edit_text

    async def timed(text, **kw):
        at.append(clock.now)
        await original(text, **kw)

    msg.edit_text = timed
    _feed(p, ["palavra " * 20] * 12, clock, gap=1.0)
    assert len(at) > 1, "a 12-second stream should repaint more than once"
    gaps = [b - a for a, b in zip(at, at[1:])]
    assert min(gaps) >= cadence.MIN_INTERVAL


def test_the_pin_hangs_a_blank_line_below_the_answer_and_carries_no_glyph():
    """Lucas, 2026-07-27: the `·` reads as a stray bullet under an answer, and the line needs
    distance so it looks like a status rather than the answer's next sentence."""
    from frontend import phrases
    frame = answer.frames("Pronto aqui.", "", pin="pensando…")[0]
    assert frame.endswith("\n\npensando…")
    for _ in range(20):
        assert not phrases.pin().startswith("·")
