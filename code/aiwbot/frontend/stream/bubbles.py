# bubbles.py — the messages one answer is written into: which are live, which are sealed, and what
# each currently holds. Split out of painter.py (2026-07-29) when a question interrupting a turn
# made "the bubbles of this answer" a structure rather than a list: painter owns WHAT to write,
# this owns WHERE it went.
from __future__ import annotations
from .. import reply


class Bubbles:
    """One answer's bubbles, in segments.

    A segment is a contiguous run at the bottom of the chat. Something else being posted — a
    question the agent asked — ends the current one, because anything written afterwards has to
    appear BELOW that question rather than grow a bubble sitting above it.
    """

    def __init__(self, working, origin, anchors, clock):
        self.origin = origin
        self.anchors = anchors
        self.clock = clock
        # The current segment: what may still be edited.
        self.live = [working] if working is not None else []
        # Every bubble of the turn, in order — anchored, stamped and handed back at the end.
        self.all = list(self.live)
        # What each bubble was last given, undecorated. Telegram returns the plain rendering of a
        # message, never the HTML that was sent, so a bubble that needs restamping later can only
        # be rebuilt from a record kept here.
        self.bare: dict[int, str] = {}
        for bubble in self.live:
            self.anchors.add(bubble)

    async def write(self, bubble, text: str, markup=None, bare: str | None = None) -> bool:
        """Repaint one bubble and remember what it now holds."""
        self.bare[bubble.message_id] = bare if bare is not None else text
        return await reply.edit_text(bubble, text, markup)

    async def open(self, text: str, markup=None, bare: str | None = None):
        """A new bubble, below everything already in the chat."""
        bubble = await reply.safe_reply(self.origin, text, reply_markup=markup)
        if bubble is not None:
            self.bare[bubble.message_id] = bare if bare is not None else text
            self.live.append(bubble)
            self.all.append(bubble)
            self.anchors.add(bubble)
            self.clock.mark_bubble()
        return bubble

    def cut(self) -> None:
        """End the current segment. The bubbles stay on screen and stay in `all`; none of them may
        be repainted, because what comes next belongs under whatever is about to be posted."""
        self.live = []

    async def discard(self, bubble) -> None:
        """Take a bubble off the screen and out of the books — used for a status message that never
        got any answer text into it, so it would otherwise sit above a question saying "working"."""
        await reply.drop(bubble)
        self.bare.pop(bubble.message_id, None)
        if bubble in self.live:
            self.live.remove(bubble)
        if bubble in self.all:
            self.all.remove(bubble)

    def sealed(self) -> int:
        """How many bubbles belong to earlier segments — the offset the live ones are numbered from."""
        return len(self.all) - len(self.live)
