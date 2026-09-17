# cadence.py — when a streamed answer is allowed to move: repaint rate, typing, bubble spacing.
# Split out of painter.py when the inter-bubble pause arrived (2026-07-28) and the file hit its
# size gate: painting owns BUBBLES, this owns TIME. Pure state machine, no I/O and no Telegram —
# so every rule below is asserted against a fake clock rather than waited for.
from __future__ import annotations
import time

# Telegram tolerates roughly one edit per second per message, so this is a UX number rather than
# a rate-limit one: the answer should arrive like someone typing, not like a progress bar. Set to
# 5 s and then to 3 s by Lucas on 2026-07-27, reading real turns in the chat — tune it there, not
# from theory. The chunky bursts claude actually streams in suit a slower cadence anyway.
MIN_INTERVAL = 3.0
# How long the newest bubble stays alone before another may appear. This is the one that paces the
# CONVERSATION: MIN_INTERVAL only paces repaints of the live bubble, which is why the cadence
# looked like it did nothing (Lucas, 2026-07-28: "o tempo entre bubbles não funcionou"). A stream
# that outruns it waits — the text is not lost, it lands whole as the next bubble.
# 4 s → 6 s once Lucas saw that the wait is not silent (2026-07-28): Telegram's own typing
# indicator is re-lit throughout it, so a longer pause reads as someone writing rather than as a
# stall. Keep TYPING_EVERY below this, or the gap gets a dead patch in the middle.
BUBBLE_GAP = 6.0
# Telegram's typing indicator lasts about five seconds, so it has to be re-sent to stay lit. Sent
# slightly ahead of that, it reads as continuous. This is the signal that carries the gap BETWEEN
# repaints — without it a 3 s pause looks like the bot died (Lucas's ask, 2026-07-27).
TYPING_EVERY = 4.0
# Below this a repaint spends a ~200 ms round trip (AD-20) to move almost nothing.
MIN_GROWTH = 40
# A failed paint widens the gap rather than retrying, so a rate-limited stream backs off instead
# of piling on. Success decays it back toward the floor.
MAX_INTERVAL = 10.0
_BACKOFF = 2.0
_DECAY = 0.5


class Cadence:
    """The clock side of a streamed answer: what may happen now, and what has happened."""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.interval = MIN_INTERVAL
        self.last_at = 0.0
        self.typing_at = 0.0
        # When the newest bubble appeared — construction time, because the working message the
        # painter is handed IS bubble one and has just been sent. Starting at 0.0 instead would
        # let bubble two appear a second later, which is the gap Lucas is trying to remove. It
        # does not delay the first TEXT: that goes into bubble one, paced by `interval`.
        self.born_at = self.clock()
        self.painted = 0

    def due(self, size: int) -> bool:
        """Is a repaint worth a round trip? Only once the text has actually grown enough to be
        worth one, and only once the interval has elapsed."""
        grown = size - self.painted
        result = False
        if grown >= MIN_GROWTH:
            result = self.clock() - self.last_at >= self.interval
        return result

    def spaced(self) -> bool:
        """Has the newest bubble been alone long enough for a successor to read as a new message?"""
        return self.clock() - self.born_at >= BUBBLE_GAP

    def typing_due(self) -> bool:
        """Re-light the indicator? Independent of the repaint gate on purpose: it fires on the
        FIRST delta, long before enough text exists to be worth painting, so the wait before the
        first visible words is never silent."""
        now = self.clock()
        due = now - self.typing_at >= TYPING_EVERY
        if due:
            self.typing_at = now
        return due

    def mark_paint(self, size: int, ok: bool) -> None:
        """A paint went out. Success decays the interval toward the floor, failure widens it, so
        a rate-limited stream backs off instead of retrying into the same wall."""
        self.last_at = self.clock()
        self.painted = size
        if ok:
            self.interval = max(MIN_INTERVAL, self.interval * _DECAY)
        else:
            self.interval = min(MAX_INTERVAL, self.interval * _BACKOFF)

    def mark_bubble(self) -> None:
        self.born_at = self.clock()
