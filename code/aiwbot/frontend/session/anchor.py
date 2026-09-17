# anchor.py — map each answer bubble to its session, so any of them can be replied to (AD-23).
#
# Split out of painter.py (2026-07-29) when segments arrived and the file hit its size gate:
# painting owns what a bubble SAYS, this owns what a reply to it MEANS. No I/O — the callback is
# the caller's, and every rule here is about ordering, which is where this went wrong once before.
from __future__ import annotations


class Anchors:
    """Bubbles waiting for a session id, and the callback that claims them once it exists."""

    def __init__(self, on_bubble=None):
        self.on_bubble = on_bubble
        self.session_id: str | None = None
        self.pending: list = []

    def note_session(self, session_id: str | None) -> None:
        """The id usually arrives before any text (claude's `system:init`), but nothing may DEPEND
        on that: bubbles born earlier queue up and are claimed retroactively, here."""
        if not session_id or self.session_id:
            return
        self.session_id = session_id
        # Drained into a snapshot and emptied BEFORE claiming, never iterated in place: an `add`
        # that re-queued while this loop walked the same list would append forever and eat the
        # machine's memory. Structural, so the loop is impossible rather than merely unlikely
        # (found 2026-07-28 by a Painter built without `on_bubble`).
        queued = self.pending
        self.pending = []
        for bubble in queued:
            self.add(bubble)

    def add(self, bubble) -> None:
        """Queue only for the reason queuing exists — the session id is not known yet. Having no
        callback is a different condition and must not re-queue: conflating the two is what made
        the drain above unbounded."""
        if not self.session_id:
            self.pending.append(bubble)
        elif self.on_bubble is not None:
            self.on_bubble(bubble, self.session_id)
