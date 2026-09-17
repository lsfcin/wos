# painter.py — keep the chat showing the answer as it arrives, throttled. One object per turn.
from __future__ import annotations
import time
from . import answer
from ..text import markdown
from .. import reply
from ..session import Anchors
from .bubbles import Bubbles
from .cadence import Cadence
from . import landing

# Stage 3's rollback: off, a streamed answer stays in one bubble that freezes when it outgrows a
# message, exactly as Stage 2 shipped. Independent of the `stream` knob on purpose, so sealing
# can be reverted without giving up live text.
STREAM_SEAL = True


class Painter:
    """Owns the accumulating answer and the bubbles it is being written into.

    Per turn, never global: it dies with the turn, so nothing has to be reset or cleaned up.
    The buffer lives here rather than in `dispatch` because `on_text` receives DELTAS — the
    authoritative join still happens in `events_to_result` at the end, so even a painter that
    drifted could not corrupt the delivered answer."""

    def __init__(self, working, pin: str, clock=time.monotonic, origin=None,
                 on_bubble=None, seal: bool = STREAM_SEAL, lead: str = ""):
        self.pin = pin
        # The quoted transcript that opens every bubble of a voice turn; "" for a typed one.
        self.lead = lead
        self.clock = Cadence(clock)
        self.origin = origin
        self.seal = seal and origin is not None
        self.anchors = Anchors(on_bubble)
        self.bubbles = Bubbles(working, origin, self.anchors, self.clock)
        # Where the current segment starts in `text`. Everything before it is on screen, sealed
        # above a question, and must never be repainted.
        self.base = 0
        # The undecorated chunks behind the frame most recently computed, so what a bubble is
        # given can be recorded without its counter.
        self.bare_now: list[str] = []
        self.text = ""
        self.busy = False
        self.frozen = False

    @property
    def sent(self) -> list:
        """The bubbles still being written into — the current segment."""
        return self.bubbles.live

    @property
    def answers(self) -> list:
        """Every bubble of this answer, across segments."""
        return self.bubbles.all

    # --- anchoring ---------------------------------------------------------------------------

    async def note_session(self, session_id: str | None) -> None:
        """AD-23: a bubble is repliable only once it is mapped to its session."""
        self.anchors.note_session(session_id)

    # --- throttle ----------------------------------------------------------------------------

    def _due(self) -> bool:
        """Is a repaint worth a round trip right now? Timing is `cadence`'s call; what this adds
        is the painter's own state.

        `busy` DROPS a paint rather than queueing it, which is lossless: every frame is recomputed
        from the whole accumulated text, so a skipped one is simply superseded by the next. That
        is what stops a fast stream from piling up requests behind a slow round trip."""
        result = False
        if not self.frozen and not self.busy and (self.sent or self.text[self.base:].strip()):
            result = self.clock.due(len(self.text))
        return result

    async def _keep_typing(self) -> None:
        """Re-light Telegram's own "typing…" indicator while the gate above says nothing else
        should move."""
        lit = self.clock.typing_due()
        if lit and self.answers:
            await reply.send_typing(self.answers[0])

    # --- painting ----------------------------------------------------------------------------

    def frames(self, pinned: bool = True) -> list[str]:
        """The bubbles the CURRENT segment occupies right now: settled markdown rendered, the still
        arriving tail as plain text, pin on the last one.

        Only the current segment: text written before a question was posted is already sealed above
        it, and repainting it would put the answer to a question above the question (Lucas,
        2026-07-29). `pinned=False` drops the status line, which is what a bubble being closed
        wants — the pin belongs on whatever is now last."""
        self.bare_now: list[str] = []
        settled, unsettled = markdown.stable_prefix(self.text[self.base:])
        soft = reply.SOFT_CHARS if self.seal else None
        pin = self.pin if pinned else None
        # Numbered from where earlier segments left off, so an interview does not restart the
        # count at 1 after every question.
        opening = self.bubbles.sealed() + 1
        bare = answer.bare_frames(settled, unsettled, pin, limit=reply.TELEGRAM_MSG_LIMIT,
                                  soft=soft, lead=self.lead)
        chunks = answer.decorate(bare, self.lead, start=opening)
        if pin:
            chunks[-1] = chunks[-1] + "\n\n" + pin
        self.bare_now = bare
        if not self.seal and len(chunks) > 1:
            # Stage 2 behaviour: one bubble that stops updating once the answer outgrows a
            # message, leaving the finished delivery to do the splitting.
            self.frozen = True
        return chunks

    async def _grow(self, chunks: list[str]) -> None:
        """New bubbles were born since the last paint.

        Safe only because `split_html` is prefix-stable: every chunk but the last is final, so a
        bubble can be sent the moment it appears and never touched again. It is anchored on
        arrival, which makes AD-23 continuous — Lucas can reply to bubble 1 while bubble 3 is
        still being written."""
        closing = len(self.sent) - 1
        await self.bubbles.write(self.sent[closing], chunks[closing],
                                 bare=self.bare_now[closing])
        # Exactly ONE bubble per paint, however far the stream has run ahead. Posting every chunk
        # that fits would land three bubbles in the same second and undo the pause entirely — the
        # rest wait for their own gap, and `finish` ships whatever is still owed at the end.
        await self.bubbles.open(chunks[len(self.sent)], bare=self.bare_now[len(self.sent)])

    async def cut(self) -> None:
        """Close the live bubble because something else is about to be posted below it.

        A question asked mid-turn is its own message, so anything the agent writes AFTER it must
        appear BELOW it — and a live bubble that kept growing would put the answer to a question
        above the question (Lucas, 2026-07-29). The pin goes too: while a question is waiting, the
        status line would be claiming work that is actually blocked on him."""
        if self.sent:
            chunks = self.frames(pinned=False)
            written = chunks[-1].strip()
            if written:
                await self.bubbles.write(self.sent[-1], chunks[-1], bare=self.bare_now[-1])
            else:
                # Nothing but the status ever reached this bubble — the agent asked before it wrote
                # anything — so it is removed rather than left above the question claiming to be
                # working on something that is actually waiting on Lucas.
                await self.bubbles.discard(self.sent[-1])
        self.base = len(self.text)
        self.bubbles.cut()

    def tail_of(self, text: str) -> str:
        """The part of the answer that still belongs to the CURRENT segment.

        Everything before `base` is already on screen above a question and final. Re-rendering the
        whole answer at the end would post it a second time below the questions (seen 2026-07-29),
        so the closing delivery is given only the tail."""
        cut = min(self.base, len(text))
        return text[cut:]

    async def finish(self, block: str, markup=None) -> list:
        """Hand the finished answer to `landing`, which owns everything that happens once the text
        has stopped arriving. Kept as a method because callers think in terms of the painter."""
        return await landing.land(self, block, markup)

    async def paint(self, delta: str, session_id: str | None = None) -> None:
        self.text += delta
        await self.note_session(session_id)
        await self._keep_typing()
        if not self._due():
            return
        chunks = self.frames()
        growing = self.seal and len(chunks) > len(self.sent)
        if growing and not self.clock.spaced():
            # The live bubble is already past its soft size, so there is nothing worth showing in
            # it meanwhile: the held text lands whole as the next bubble once the gap has passed.
            return
        self.busy = True
        if not self.sent:
            # First bubble of a segment that opened after a question: it has to be a new message,
            # below that question, rather than an edit of anything already on screen.
            await self.bubbles.open(chunks[0], bare=self.bare_now[0])
            ok = True
        elif growing:
            await self._grow(chunks)
            ok = True
        else:
            index = len(self.sent) - 1
            ok = await self.bubbles.write(self.sent[-1], chunks[index], bare=self.bare_now[index])
        self.busy = False
        self.clock.mark_paint(len(self.text), ok)
